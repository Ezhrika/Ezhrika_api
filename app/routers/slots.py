from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.slot import Slot
from app.schemas.slots import SlotRead


router = APIRouter(prefix="/api/v1/slots", tags=["slots"])


# Получение всех слотов репетиторов из БД.
@router.get("", response_model=list[SlotRead], summary="Get all slots")
def get_all_slots(db: Annotated[Session, Depends(get_db)]) -> list[Slot]:
    return list(db.scalars(select(Slot).order_by(Slot.id)).all())


# TODO: Добавить создание, изменение и закрытие собственных слотов с проверкой доступа.
