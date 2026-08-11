# -> app/routers/timetable.py
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db

router = APIRouter(prefix="/timetable", tags=["timetable"])


def _check_refs(data: schemas.TimetableCreate, db: Session) -> list["models.StudentGroup"]:
    """Проверяет FK; возвращает объекты групп (они нужны для записи m2m)."""
    if db.get(models.Slot, data.slot) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Слот не найден")
    if db.get(models.Classroom, data.classroom) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Кабинет не найден")
    if db.get(models.Teacher, data.teacher) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Преподаватель не найден")
    if db.get(models.Subject, data.subject) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Предмет не найден")

    groups = []
    for gid in data.groups:
        group = db.get(models.StudentGroup, gid)
        if group is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Группа {gid} не найдена")
        groups.append(group)
    return groups


def _check_conflicts(
    data: schemas.TimetableCreate, db: Session, exclude_id: int | None = None
) -> None:
    """Два конфликта расписания -> 409 с разными текстами."""
    base = db.query(models.Timetable).filter(
        models.Timetable.day == data.day,
        models.Timetable.slot == data.slot,
    )
    if exclude_id is not None:
        base = base.filter(models.Timetable.id != exclude_id)

    if base.filter(models.Timetable.classroom == data.classroom).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Кабинет занят в этот день и слот")
    if base.filter(models.Timetable.teacher == data.teacher).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Преподаватель занят в этот день и слот")


@router.get("", response_model=list[schemas.TimetableOut])
def list_timetable(
    day: date | None = None,
    teacher: int | None = None,
    classroom: int | None = None,
    subject: int | None = None,
    group: int | None = None,
    db: Session = Depends(get_db),
):
    """Расписание с фильтрами: ?day=2026-09-01&teacher=1 и т.д."""
    q = db.query(models.Timetable)
    if day is not None:
        q = q.filter(models.Timetable.day == day)
    if teacher is not None:
        q = q.filter(models.Timetable.teacher == teacher)
    if classroom is not None:
        q = q.filter(models.Timetable.classroom == classroom)
    if subject is not None:
        q = q.filter(models.Timetable.subject == subject)
    if group is not None:  # <- новое
        q = q.join(models.Timetable.groups).filter(models.StudentGroup.id == group)
    return q.order_by(models.Timetable.day, models.Timetable.slot).all()


@router.get("/{timetable_id}", response_model=schemas.TimetableOut)
def get_timetable(timetable_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Timetable, timetable_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Строка расписания не найдена")
    return row


@router.post("", response_model=schemas.TimetableOut, status_code=status.HTTP_201_CREATED)
def create_timetable(data: schemas.TimetableCreate, db: Session = Depends(get_db)):
    groups = _check_refs(data, db)
    _check_conflicts(data, db)
    row = models.Timetable(**data.model_dump(exclude={"groups"}))
    row.groups = groups
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{timetable_id}", response_model=schemas.TimetableOut)
def update_timetable(
    timetable_id: int, data: schemas.TimetableCreate, db: Session = Depends(get_db)
):
    row = db.get(models.Timetable, timetable_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Строка расписания не найдена")
    groups = _check_refs(data, db)
    _check_conflicts(data, db, exclude_id=timetable_id)
    for field, value in data.model_dump(exclude={"groups"}).items():
        setattr(row, field, value)
    row.groups = groups
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{timetable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable(timetable_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Timetable, timetable_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Строка расписания не найдена")
    db.delete(row)
    db.commit()