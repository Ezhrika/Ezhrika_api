"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[schemas.StudentOut])
def list_student(name: str | None = None, student_group: int | None = None, user_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Student)
    if name:
        q = q.filter(models.Student.name.ilike(f"%{name}%"))
    if student_group is not None:
        q = q.filter(models.Student.student_group == student_group)
    if user_id is not None:
        q = q.filter(models.Student.user_id == user_id)
    return q.all()


@router.get("/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Студент не найден")
    return student


@router.post("", response_model=schemas.StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(data: schemas.StudentCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Student).filter(models.Student.name == data.name).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Предмет с таким названием уже есть")

    student = models.Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)  # подтянуть сгенерированный БД id
    return student


@router.put("/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: int, data: schemas.StudentCreate, db: Session = Depends(get_db)
):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Студент не найден")
    clash = (
        db.query(models.Student)
        .filter(models.Student.name == data.name, models.Student.id != student_id)
        .first()
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Предмет с таким названием уже есть")

    for field, value in data.model_dump().items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Студент не найден")
    db.delete(student)
    db.commit()
