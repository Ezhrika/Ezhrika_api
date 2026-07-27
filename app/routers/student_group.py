"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/student_group", tags=["student_group"])


@router.get("", response_model=list[schemas.StudentGroupOut])
def list_student_group(db: Session = Depends(get_db)):
    return db.query(models.StudentGroup).all()


@router.get("/{student_group_id}", response_model=schemas.StudentGroupOut)
def get_student_group(student_group_id: int, db: Session = Depends(get_db)):
    student_group = db.get(models.StudentGroup, student_group_id)
    if student_group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    return student_group


@router.post("", response_model=schemas.StudentGroupOut, status_code=status.HTTP_201_CREATED)
def create_student_group(data: schemas.StudentGroupCreate, db: Session = Depends(get_db)):
    student_group = models.StudentGroup(**data.model_dump())
    db.add(student_group)
    db.commit()
    db.refresh(student_group)  # подтянуть сгенерированный БД id
    return student_group


@router.put("/{student_group_id}", response_model=schemas.StudentGroupOut)
def update_student_group(
    student_group_id: int, data: schemas.StudentGroupCreate, db: Session = Depends(get_db)
):
    student_group = db.get(models.StudentGroup, student_group_id)
    if student_group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    for field, value in data.model_dump().items():
        setattr(student_group, field, value)
    db.commit()
    db.refresh(student_group)
    return student_group


@router.delete("/{student_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_group(student_group_id: int, db: Session = Depends(get_db)):
    student_group = db.get(models.StudentGroup, student_group_id)
    if student_group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    db.delete(student_group)
    db.commit()
