"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/slot", tags=["slot"])


@router.get("", response_model=list[schemas.SlotOut])
def list_slot(db: Session = Depends(get_db)):
    return db.query(models.Slot).order_by(models.Slot.number).all()


@router.get("/{slot_id}", response_model=schemas.SlotOut)
def get_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.get(models.Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Слот не найден")
    return slot


@router.post("", response_model=schemas.SlotOut, status_code=status.HTTP_201_CREATED)
def create_slot(data: schemas.SlotCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Slot).filter(models.Slot.number == data.number).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Слот с таким номером уже есть")
    slot = models.Slot(**data.model_dump())
    db.add(slot)
    db.commit()
    db.refresh(slot)  # подтянуть сгенерированный БД id
    return slot


@router.put("/{slot_id}", response_model=schemas.SlotOut)
def update_slot(
    slot_id: int, data: schemas.SlotCreate, db: Session = Depends(get_db)
):
    slot = db.get(models.Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Слот не найден")
    clash = (
        db.query(models.Slot)
        .filter(models.Slot.id == data.id, models.Slot.id != slot_id)
        .first()
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Слот с таким названием уже есть")

    for field, value in data.model_dump().items():
        setattr(slot, field, value)
    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.get(models.Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Слот не найден")
    db.delete(slot)
    db.commit()
