from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Annotated
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.debug import require_debug
from app.core.security import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.booking import Booking
from app.models.notification import Notification
from app.models.slot import Slot
from app.models.student import StudentProfile
from app.models.tutor import TutorProfile
from app.models.user import User
from app.schemas.bookings import (
    BookingCreate,
    BookingGuestResponse,
    BookingRead,
    CancelByTokenRequest,
    ConfirmByTokenRequest,
)
from app.services.bookings import expire_pending_booking, expire_pending_bookings, lock_booking
from app.services.email import send_notification_background
from app.routers.pages import page_file


router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


# Запись на занятие зарегистрированного ученика или гостя с защитой от двойной записи.
@router.post(
    "",
    response_model=BookingGuestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a lesson slot",
)
def create_booking(
    payload: BookingCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> BookingGuestResponse:
    # 1. Определение данных ученика (авторизованный пользователь vs гость)
    if current_user:
        if current_user.role == "tutor":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tutors cannot book lessons.",
            )
        student_profile = db.scalar(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        )
        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found.",
            )
        student_id = student_profile.id
        student_name = payload.student_name.strip() if (payload.student_name and payload.student_name.strip()) else student_profile.name
        student_email = str(current_user.email)
        raw_cancel_token = None
        cancel_token_hash = None
    else:
        if not payload.student_name or not payload.student_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_name is required for guest booking.",
            )
        if not payload.student_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_email is required for guest booking.",
            )
        student_id = None
        student_name = payload.student_name.strip()
        student_email = str(payload.student_email).strip().lower()
        raw_cancel_token = secrets.token_urlsafe(32)
        cancel_token_hash = hashlib.sha256(raw_cancel_token.encode("utf-8")).hexdigest()

    # 2. Атомарный захват слота с блокировкой строки (with_for_update)
    slot = db.scalar(
        select(Slot).where(Slot.id == payload.slot_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found.",
        )
    expire_pending_booking(db, slot)
    if slot.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot is already booked or not available.",
        )
    now_utc = datetime.now(timezone.utc)
    if slot.starts_at <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a slot in the past.",
        )

    # 3. Гостевая бронь ожидает подтверждения, запись ученика сразу активна.
    slot.status = "pending" if current_user is None else "booked"
    booking = Booking(
        slot_id=slot.id,
        student_id=student_id,
        student_name=student_name,
        student_email=student_email,
        question=payload.question.strip(),
        status="pending" if current_user is None else "active",
        cancel_token_hash=cancel_token_hash,
    )
    db.add(booking)
    db.flush()

    body = f"Здравствуйте, {student_name}! Занятие: {slot.starts_at.isoformat()}."
    if raw_cancel_token is not None:
        deadline = min(
            booking.created_at + timedelta(minutes=settings.guest_confirmation_minutes),
            slot.starts_at,
        )
        confirm_token = jwt.encode(
            {"sub": str(booking.id), "purpose": "guest_confirmation",
             "cancel_hash": cancel_token_hash, "exp": deadline},
            settings.secret_key.get_secret_value(), algorithm=settings.jwt_algorithm,
        )
        base_url = str(settings.public_base_url).rstrip("/")
        confirm_url = f"{base_url}/api/v1/bookings/confirm?{urlencode({'token': confirm_token})}"
        cancel_url = f"{base_url}/api/v1/bookings/cancel?{urlencode({'token': raw_cancel_token})}"
        body += (
            f"\nПодтвердите запись до {deadline.isoformat()}:\n{confirm_url}"
            f"\nБез подтверждения бронь будет снята.\nОтменить запись:\n{cancel_url}"
        )
    else:
        body += "\nВаша запись подтверждена. Отменить её можно в личном кабинете."

    # 4. Создание записи в очереди email-уведомлений
    notification = Notification(
        booking_id=booking.id,
        recipient_email=student_email,
        subject="Подтверждение записи на занятие",
        body=body,
        status="pending",
    )
    db.add(notification)
    db.flush()

    db.commit()
    db.refresh(booking)

    # 5. Фоновая отправка письма через FastAPI BackgroundTasks
    background_tasks.add_task(send_notification_background, notification.id)

    return BookingGuestResponse(
        **BookingRead.model_validate(booking).model_dump(),
        cancel_token=raw_cancel_token,
    )


# Получение всех записей текущего ученика (для личного кабинета).
@router.get(
    "/my",
    response_model=list[BookingRead],
    summary="Get own bookings for current student",
)
def get_my_bookings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Booking]:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their bookings.",
        )
    student_profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )
    return list(
        db.scalars(
            select(Booking)
            .options(joinedload(Booking.slot).joinedload(Slot.tutor))
            .where(Booking.student_id == student_profile.id)
            .order_by(Booking.created_at.desc())
        ).all()
    )


# Получение записей учеников ко мне на уроки (для кабинета репетитора).
@router.get(
    "/tutor",
    response_model=list[BookingRead],
    summary="Get bookings for current tutor lessons",
)
def get_tutor_bookings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Booking]:
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors can view their lessons bookings.",
        )
    tutor_profile = db.scalar(
        select(TutorProfile).where(TutorProfile.user_id == current_user.id)
    )
    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found.",
        )
    expire_pending_bookings(db, tutor_profile.id)
    db.commit()
    return list(
        db.scalars(
            select(Booking)
            .options(joinedload(Booking.slot).joinedload(Slot.tutor))
            .join(Slot, Booking.slot_id == Slot.id)
            .where(Slot.tutor_id == tutor_profile.id)
            .order_by(Booking.created_at.desc())
        ).all()
    )


# Отмена бронирования зарегистрированным учеником.
@router.post(
    "/{booking_id}/cancel",
    response_model=BookingRead,
    summary="Cancel booking by student",
)
def cancel_booking_by_student(
    booking_id: int,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Booking:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can cancel their bookings.",
        )
    student_profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    booking, slot = lock_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )
    if booking.student_id != student_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own bookings.",
        )
    if booking.status not in {"active", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is no longer active.",
        )

    booking.status = "cancelled"
    if slot and slot.starts_at > datetime.now(timezone.utc):
        slot.status = "open"

    notification = Notification(
        booking_id=booking.id,
        recipient_email=booking.student_email,
        subject="Отмена записи на занятие",
        body="Ваша запись на занятие успешно отменена.",
        status="pending",
    )
    db.add(notification)
    db.flush()
    db.commit()
    db.refresh(booking)

    background_tasks.add_task(send_notification_background, notification.id)
    return booking


# Отмена бронирования репетитором (закрывает слот).
@router.post(
    "/{booking_id}/cancel-by-tutor",
    response_model=BookingRead,
    summary="Cancel booking by tutor",
)
def cancel_booking_by_tutor(
    booking_id: int,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Booking:
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors can cancel lessons.",
        )
    tutor_profile = db.scalar(
        select(TutorProfile).where(TutorProfile.user_id == current_user.id)
    )
    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found.",
        )

    booking, slot = lock_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )
    if not slot or slot.tutor_id != tutor_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel bookings for your own lessons.",
        )
    if booking.status not in {"active", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is no longer active.",
        )

    booking.status = "cancelled"
    slot.status = "cancelled"

    notification = Notification(
        booking_id=booking.id,
        recipient_email=booking.student_email,
        subject="Занятие отменено преподавателем",
        body="Преподаватель отменил занятие.",
        status="pending",
    )
    db.add(notification)
    db.flush()
    db.commit()
    db.refresh(booking)

    background_tasks.add_task(send_notification_background, notification.id)
    return booking


# Отмена бронирования гостем по одноразовому токену из письма.
@router.post(
    "/cancel-by-token",
    response_model=BookingRead,
    summary="Cancel booking by guest token",
)
def cancel_booking_by_token(
    payload: CancelByTokenRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> Booking:
    token_hash = hashlib.sha256(payload.token.strip().encode("utf-8")).hexdigest()
    booking_id = db.scalar(
        select(Booking.id).where(Booking.cancel_token_hash == token_hash)
    )
    if booking_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid cancellation token.",
        )
    booking, slot = lock_booking(db, booking_id)
    if not booking or booking.status not in {"active", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is no longer active.",
        )

    booking.status = "cancelled"
    if slot and slot.starts_at > datetime.now(timezone.utc):
        slot.status = "open"

    notification = Notification(
        booking_id=booking.id,
        recipient_email=booking.student_email,
        subject="Отмена записи на занятие",
        body="Ваша запись на занятие успешно отменена по ссылке.",
        status="pending",
    )
    db.add(notification)
    db.flush()
    db.commit()
    db.refresh(booking)

    background_tasks.add_task(send_notification_background, notification.id)
    return booking


# Получение всех записей из БД (для локальной отладки).
@router.get("", response_model=list[BookingRead], summary="Get all bookings (debug)", dependencies=[Depends(require_debug)])
def get_all_bookings(db: Annotated[Session, Depends(get_db)]) -> list[Booking]:
    return list(db.scalars(
        select(Booking).options(joinedload(Booking.slot).joinedload(Slot.tutor))
        .order_by(Booking.id)
    ).all())


# Подтверждение владения email гостя отдельным подписанным токеном.
@router.post("/confirm-by-token", response_model=BookingRead, summary="Confirm guest booking")
def confirm_booking_by_token(
    payload: ConfirmByTokenRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Booking:
    try:
        data = jwt.decode(
            payload.token, settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "purpose", "cancel_hash"]},
        )
        if data["purpose"] != "guest_confirmation":
            raise ValueError("Invalid token purpose.")
        booking_id = int(data["sub"])
    except jwt.ExpiredSignatureError:
        expire_pending_bookings(db)
        db.commit()
        raise HTTPException(status_code=410, detail="Confirmation link has expired.")
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid confirmation token.")

    booking, slot = lock_booking(db, booking_id)
    if not booking or booking.student_id is not None or booking.cancel_token_hash != data["cancel_hash"]:
        raise HTTPException(status_code=404, detail="Guest booking not found.")
    if slot and expire_pending_booking(db, slot):
        db.commit()
        raise HTTPException(status_code=410, detail="Confirmation link has expired.")
    if booking.status == "active":
        return booking
    if booking.status != "pending" or slot is None or slot.status != "pending":
        raise HTTPException(status_code=409, detail="Booking cannot be confirmed.")
    booking.status = "active"
    slot.status = "booked"
    db.commit()
    db.refresh(booking)
    return booking


# Ссылки из ранее отправленных писем также открывают оформленные страницы frontend.
@router.get("/confirm", response_class=HTMLResponse, include_in_schema=False)
def confirmation_page(token: Annotated[str, Query(min_length=1, max_length=2048)]) -> FileResponse:
    return page_file("confirm")


@router.post("/confirm", response_class=HTMLResponse, include_in_schema=False)
def confirm_from_email(
    token: Annotated[str, Query(min_length=1, max_length=2048)],
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    confirm_booking_by_token(ConfirmByTokenRequest(token=token), db)
    return HTMLResponse('<html lang="ru"><meta charset="utf-8"><h1>Запись подтверждена</h1></html>')


@router.get("/cancel", response_class=HTMLResponse, include_in_schema=False)
def cancellation_page(token: Annotated[str, Query(min_length=1, max_length=512)]) -> FileResponse:
    return page_file("cancel")


@router.post("/cancel", response_class=HTMLResponse, include_in_schema=False)
def cancel_from_email(
    token: Annotated[str, Query(min_length=1, max_length=512)],
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    cancel_booking_by_token(CancelByTokenRequest(token=token), background_tasks, db)
    return HTMLResponse('<html lang="ru"><meta charset="utf-8"><h1>Запись отменена</h1></html>')
