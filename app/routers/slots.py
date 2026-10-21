from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.debug import require_debug
from app.db.session import get_db
from app.models.slot import Slot
from app.models.booking import Booking
from app.models.tutor import TutorProfile
from app.models.user import User
from app.schemas.slots import SlotCreate, SlotRead
from app.services.bookings import expire_pending_booking, expire_pending_bookings


router = APIRouter(prefix="/api/v1/slots", tags=["slots"])


# Создание свободного слота времени репетитором с проверкой накладок.
@router.post(
    "",
    response_model=SlotRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new time slot",
)
def create_slot(
    payload: SlotCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Slot:
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors can create time slots.",
        )

    tutor_profile = db.scalar(
        select(TutorProfile).where(TutorProfile.user_id == current_user.id).with_for_update()
    )
    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found.",
        )

    expire_pending_bookings(db, tutor_profile.id)

    # Проверка наложения времени: интервалы пересекаются, если start < existing_end и end > existing_start
    overlap = db.scalar(
        select(Slot).where(
            Slot.tutor_id == tutor_profile.id,
            Slot.status != "cancelled",
            Slot.starts_at < payload.ends_at,
            Slot.ends_at > payload.starts_at,
        )
    )
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot overlaps with an existing slot for this tutor.",
        )

    slot = Slot(
        tutor_id=tutor_profile.id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        status="open",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


# Получение всех слотов текущего репетитора (для личного кабинета).
@router.get(
    "/my",
    response_model=list[SlotRead],
    summary="Get own slots for current tutor",
)
def get_my_slots(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Slot]:
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors can view own slots.",
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
            select(Slot)
            .where(Slot.tutor_id == tutor_profile.id)
            .order_by(Slot.starts_at)
        ).all()
    )


# Получение списка слотов с опциональной фильтрацией по репетитору и статусу.
@router.get(
    "",
    response_model=list[SlotRead],
    summary="Get slots list with optional filters",
    dependencies=[Depends(require_debug)],
)
def get_slots(
    db: Annotated[Session, Depends(get_db)],
    tutor_id: int | None = None,
    slot_status: str | None = None,
) -> list[Slot]:
    query = select(Slot)
    if tutor_id is not None:
        query = query.where(Slot.tutor_id == tutor_id)
    if slot_status is not None:
        query = query.where(Slot.status == slot_status)
    return list(db.scalars(query.order_by(Slot.starts_at)).all())


# Удаление свободного слота репетитором.
@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a free slot",
)
def delete_slot(
    slot_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors can delete time slots.",
        )

    tutor_profile = db.scalar(
        select(TutorProfile).where(TutorProfile.user_id == current_user.id)
    )
    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found.",
        )

    slot = db.scalar(select(Slot).where(Slot.id == slot_id).with_for_update())
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found.",
        )

    if slot.tutor_id != tutor_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own slots.",
        )

    expire_pending_booking(db, slot)
    if slot.status in {"booked", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a booked slot. Please cancel the booking instead.",
        )

    has_history = db.scalar(select(Booking.id).where(Booking.slot_id == slot.id).limit(1))
    if has_history is not None:
        slot.status = "cancelled"
    else:
        db.delete(slot)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
