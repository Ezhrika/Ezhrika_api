from datetime import datetime, timezone
import hashlib
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

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
)


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
    )
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found.",
        )
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

    # 3. Фиксация бронирования и перевод слота в статус booked
    slot.status = "booked"
    booking = Booking(
        slot_id=slot.id,
        student_id=student_id,
        student_name=student_name,
        student_email=student_email,
        question=payload.question.strip(),
        status="active",
        cancel_token_hash=cancel_token_hash,
    )
    db.add(booking)
    db.flush()

    # 4. Создание записи в очереди email-уведомлений
    notification = Notification(
        booking_id=booking.id,
        recipient_email=student_email,
        subject="Подтверждение записи на занятие",
        body=f"Здравствуйте, {student_name}! Вы успешно записаны на занятие: {slot.starts_at.isoformat()}.",
        status="pending",
    )
    db.add(notification)

    db.commit()
    db.refresh(booking)

    return BookingGuestResponse(
        id=booking.id,
        slot_id=booking.slot_id,
        student_id=booking.student_id,
        student_name=booking.student_name,
        student_email=booking.student_email,
        question=booking.question,
        status=booking.status,
        created_at=booking.created_at,
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
    return list(
        db.scalars(
            select(Booking)
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

    booking = db.get(Booking, booking_id)
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
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled.",
        )

    booking.status = "cancelled"
    slot = db.get(Slot, booking.slot_id)
    if slot and slot.starts_at > datetime.now(timezone.utc):
        slot.status = "open"

    db.add(
        Notification(
            booking_id=booking.id,
            recipient_email=booking.student_email,
            subject="Отмена записи на занятие",
            body="Ваша запись на занятие успешно отменена.",
            status="pending",
        )
    )
    db.commit()
    db.refresh(booking)
    return booking


# Отмена бронирования репетитором (закрывает слот).
@router.post(
    "/{booking_id}/cancel-by-tutor",
    response_model=BookingRead,
    summary="Cancel booking by tutor",
)
def cancel_booking_by_tutor(
    booking_id: int,
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

    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )
    slot = db.get(Slot, booking.slot_id)
    if not slot or slot.tutor_id != tutor_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel bookings for your own lessons.",
        )
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled.",
        )

    booking.status = "cancelled"
    slot.status = "cancelled"

    db.add(
        Notification(
            booking_id=booking.id,
            recipient_email=booking.student_email,
            subject="Занятие отменено преподавателем",
            body="Преподаватель отменил занятие.",
            status="pending",
        )
    )
    db.commit()
    db.refresh(booking)
    return booking


# Отмена бронирования гостем по одноразовому токену из письма.
@router.post(
    "/cancel-by-token",
    response_model=BookingRead,
    summary="Cancel booking by guest token",
)
def cancel_booking_by_token(
    payload: CancelByTokenRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Booking:
    token_hash = hashlib.sha256(payload.token.strip().encode("utf-8")).hexdigest()
    booking = db.scalar(
        select(Booking).where(Booking.cancel_token_hash == token_hash)
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid cancellation token.",
        )
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled.",
        )

    booking.status = "cancelled"
    slot = db.get(Slot, booking.slot_id)
    if slot and slot.starts_at > datetime.now(timezone.utc):
        slot.status = "open"

    db.add(
        Notification(
            booking_id=booking.id,
            recipient_email=booking.student_email,
            subject="Отмена записи на занятие",
            body="Ваша запись на занятие успешно отменена по ссылке.",
            status="pending",
        )
    )
    db.commit()
    db.refresh(booking)
    return booking


# Получение всех записей из БД (для локальной отладки).
@router.get("", response_model=list[BookingRead], summary="Get all bookings (debug)")
def get_all_bookings(db: Annotated[Session, Depends(get_db)]) -> list[Booking]:
    return list(db.scalars(select(Booking).order_by(Booking.id)).all())
