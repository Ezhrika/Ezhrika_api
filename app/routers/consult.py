"""Роутер Консультаций
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db

router = APIRouter(prefix="/consult", tags=["consult"])


def _check_refs(data: schemas.ConsultCreate, db: Session) -> "models.Timetable":
    row = db.get(models.Timetable, data.timetable)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Строка расписания не найдена")
    return row


def _check_rules(data: schemas.ConsultCreate, row: "models.Timetable", db: Session) -> None:
    if row.kind not in (models.TimetableKind.consultation, models.TimetableKind.practice):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Консультация возможна только на строке с kind=consultation или practice")
    classroom = db.get(models.Classroom, row.classroom)
    if data.max_students > classroom.capacity:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Вместимость кабинета — {classroom.capacity}")


@router.get("", response_model=list[schemas.ConsultOut])
def list_consult(name: str | None = None, timetable: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Consult)
    if name:
        q = q.filter(models.Consult.name.ilike(f"%{name}%"))
    if timetable is not None:
        q = q.filter(models.Consult.timetable == timetable)
    return q.all()


@router.get("/{consult_id}", response_model=schemas.ConsultOut)
def get_consult(consult_id: int, db: Session = Depends(get_db)):
    consult = db.get(models.Consult, consult_id)
    if consult is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Консультация не найдена")
    return consult


@router.post("", response_model=schemas.ConsultOut, status_code=status.HTTP_201_CREATED)
def create_consult(data: schemas.ConsultCreate, db: Session = Depends(get_db)):
    row = _check_refs(data, db)
    _check_rules(data, row, db)
    exists = db.query(models.Consult).filter(models.Consult.timetable == data.timetable).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "На этой строке расписания уже есть консультация")

    consult = models.Consult(**data.model_dump())
    db.add(consult)
    db.commit()
    db.refresh(consult)  # подтянуть сгенерированный БД id
    return consult


@router.put("/{consult_id}", response_model=schemas.ConsultOut)
def update_consult(
        consult_id: int, data: schemas.ConsultCreate, db: Session = Depends(get_db)
):
    consult = db.get(models.Consult, consult_id)
    if consult is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Консультация не найдена")
    row = _check_refs(data, db)
    _check_rules(data, row, db)
    clash = (
        db.query(models.Consult)
        .filter(models.Consult.timetable == data.timetable, models.Consult.id != consult_id)
        .first()
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "На этой строке расписания уже есть консультация")

    for field, value in data.model_dump().items():
        setattr(consult, field, value)
    db.commit()
    db.refresh(consult)
    return consult


@router.delete("/{consult_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_consult(consult_id: int, db: Session = Depends(get_db)):
    consult = db.get(models.Consult, consult_id)
    if consult is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Консультация не найдена")
    db.delete(consult)
    db.commit()
