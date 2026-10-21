from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.booking import Booking
from app.models.slot import Slot


# Освобождение слота с просроченным подтверждением внутри транзакции владельца блокировки.
def expire_pending_booking(db: Session, slot: Slot) -> bool:
    if slot.status != "pending":
        return False
    booking = db.scalar(
        select(Booking)
        .where(Booking.slot_id == slot.id, Booking.status == "pending")
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if booking is None:
        return False
    now = datetime.now(timezone.utc)
    deadline = booking.created_at + timedelta(minutes=settings.guest_confirmation_minutes)
    if deadline > now and slot.starts_at > now:
        return False
    booking.status = "expired"
    slot.status = "open" if slot.starts_at > now else "cancelled"
    db.flush()
    return True


# Проверка просроченных броней перед показом расписания и при запуске воркера.
def expire_pending_bookings(db: Session, tutor_id: int | None = None) -> int:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=settings.guest_confirmation_minutes)
    expired = select(Booking.id).where(
        Booking.slot_id == Slot.id,
        Booking.status == "pending",
        (Booking.created_at <= cutoff) | (Slot.starts_at <= now),
    ).exists()
    query = select(Slot).where(Slot.status == "pending", expired).order_by(Slot.id)
    if tutor_id is not None:
        query = query.where(Slot.tutor_id == tutor_id)
    slots = db.scalars(query.with_for_update(skip_locked=True)).all()
    return sum(expire_pending_booking(db, slot) for slot in slots)


# Все изменения записи сначала блокируют слот, затем запись в одном порядке.
def lock_booking(db: Session, booking_id: int) -> tuple[Booking | None, Slot | None]:
    slot_id = db.scalar(select(Booking.slot_id).where(Booking.id == booking_id))
    if slot_id is None:
        return None, None
    slot = db.scalar(
        select(Slot).where(Slot.id == slot_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    booking = db.scalar(
        select(Booking).where(Booking.id == booking_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    return booking, slot
