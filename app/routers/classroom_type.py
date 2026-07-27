"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/classroom_type", tags=["classroom_type"])


@router.get("", response_model=list[schemas.ClassroomTypeOut])
def list_classroom_type(db: Session = Depends(get_db)):
    return db.query(models.ClassroomType).all()


@router.get("/{classroom_type_id}", response_model=schemas.ClassroomTypeOut)
def get_classroom_type(classroom_type_id: int, db: Session = Depends(get_db)):
    classroom_type = db.get(models.ClassroomType, classroom_type_id)
    if classroom_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    return classroom_type


@router.post("", response_model=schemas.ClassroomTypeOut, status_code=status.HTTP_201_CREATED)
def create_classroom_type(data: schemas.ClassroomTypeCreate, db: Session = Depends(get_db)):
    classroom_type = models.ClassroomType(**data.model_dump())
    db.add(classroom_type)
    db.commit()
    db.refresh(classroom_type)  # подтянуть сгенерированный БД id
    return classroom_type


@router.put("/{classroom_type_id}", response_model=schemas.ClassroomTypeOut)
def update_classroom_type(
    classroom_type_id: int, data: schemas.ClassroomTypeCreate, db: Session = Depends(get_db)
):
    classroom_type = db.get(models.ClassroomType, classroom_type_id)
    if classroom_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    for field, value in data.model_dump().items():
        setattr(classroom_type, field, value)
    db.commit()
    db.refresh(classroom_type)
    return classroom_type


@router.delete("/{classroom_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom_type(classroom_type_id: int, db: Session = Depends(get_db)):
    classroom_type = db.get(models.ClassroomType, classroom_type_id)
    if classroom_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    db.delete(classroom_type)
    db.commit()
