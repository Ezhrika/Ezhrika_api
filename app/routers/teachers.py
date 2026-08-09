"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db

# prefix — общее начало всех путей внутри (не надо повторять /teachers).
# tags — группировка в Swagger-документации.
router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=list[schemas.TeacherOut])
def list_teachers(db: Session = Depends(get_db)):
    return db.query(models.Teacher).all()


@router.get("/{teacher_id}", response_model=schemas.TeacherOut)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.get(models.Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Преподаватель не найден")
    return teacher


@router.post("", response_model=schemas.TeacherOut, status_code=status.HTTP_201_CREATED)
def create_teacher(data: schemas.TeacherCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Teacher).filter(models.Teacher.name == data.name).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Предмет с таким названием уже есть")

    teacher = models.Teacher(**data.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)  # подтянуть сгенерированный БД id
    return teacher


@router.put("/{teacher_id}", response_model=schemas.TeacherOut)
def update_teacher(
    teacher_id: int, data: schemas.TeacherCreate, db: Session = Depends(get_db)
):
    teacher = db.get(models.Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Преподаватель не найден")
    clash = (
        db.query(models.Teacher)
        .filter(models.Teacher.name == data.name, models.Teacher.id != teacher_id)
        .first()
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Предмет с таким названием уже есть")

    for field, value in data.model_dump().items():
        setattr(teacher, field, value)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.get(models.Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Преподаватель не найден")
    db.delete(teacher)
    db.commit()
