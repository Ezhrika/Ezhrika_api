"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("", response_model=list[schemas.FacultyOut])
def list_faculty(db: Session = Depends(get_db)):
    return db.query(models.Faculty).all()


@router.get("/{faculty_id}", response_model=schemas.FacultyOut)
def get_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.get(models.Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    return faculty


@router.post("", response_model=schemas.FacultyOut, status_code=status.HTTP_201_CREATED)
def create_faculty(data: schemas.FacultyCreate, db: Session = Depends(get_db)):
    faculty = models.Faculty(**data.model_dump())
    db.add(faculty)
    db.commit()
    db.refresh(faculty)  # подтянуть сгенерированный БД id
    return faculty


@router.put("/{faculty_id}", response_model=schemas.FacultyOut)
def update_faculty(
    faculty_id: int, data: schemas.FacultyCreate, db: Session = Depends(get_db)
):
    faculty = db.get(models.Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    for field, value in data.model_dump().items():
        setattr(faculty, field, value)
    db.commit()
    db.refresh(faculty)
    return faculty


@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.get(models.Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")
    db.delete(faculty)
    db.commit()
