from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/subject", tags=["subject"])


@router.get("", response_model=list[schemas.SubjectOut])
def list_subject(name: str | None = None, faculty: int | None = None,
                 db: Session = Depends(get_db)):
    q = db.query(models.Subject)
    if name:
        q = q.filter(models.Subject.name.ilike(f"%{name}%"))
    if faculty is not None:
        q = q.filter(models.Subject.faculty == faculty)
    return q.all()

@router.get("/{subject_id}", response_model=schemas.SubjectOut)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.get(models.Subject, subject_id)
    if subject is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Предмет не найден")
    return subject


@router.post("", response_model=schemas.SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(data: schemas.SubjectCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Subject).filter(models.Subject.name == data.name).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Предмет с таким названием уже есть")
    subject = models.Subject(**data.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.put("/{subject_id}", response_model=schemas.SubjectOut)
def update_subject(
    subject_id: int, data: schemas.SubjectCreate, db: Session = Depends(get_db)
):
    subject = db.get(models.Subject, subject_id)
    if subject is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Предмет не найден")
    clash = (
        db.query(models.Subject)
        .filter(models.Subject.name == data.name, models.Subject.id != subject_id)
        .first()
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Предмет с таким названием уже есть")
    for field, value in data.model_dump().items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.get(models.Subject, subject_id)
    if subject is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Предмет не найден")
    db.delete(subject)
    db.commit()
