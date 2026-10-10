from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.booking import Booking
from app.schemas.bookings import BookingRead


router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


# Получение всех записей на занятия из БД.

@router.get("", response_model=list[BookingRead], summary="Get all bookings")
def get_all_bookings(db: Annotated[Session, Depends(get_db)]) -> list[Booking]:
    return list(db.scalars(select(Booking).order_by(Booking.id)).all())


# TODO: Реализовать бронирование в транзакции и отмену до начала занятия; показывать только свои записи.
