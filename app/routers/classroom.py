# -> app/routers/classroom.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db

router = APIRouter(prefix="/classroom", tags=["classroom"])


def _check_refs(data: schemas.ClassroomCreate, db: Session) -> None:
    """Проверяет, что все FK из тела запроса указывают на существующие записи."""
    if db.get(models.Corpus, data.corpus) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Корпус не найден")
    if db.get(models.ClassroomType, data.type) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Тип кабинета не найден")
    if data.faculty is not None and db.get(models.Faculty, data.faculty) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Факультет не найден")


def _check_duplicate(data: schemas.ClassroomCreate, db: Session, exclude_id: int | None = None) -> None:
    """Один корпус — одно имя кабинета."""
    q = db.query(models.Classroom).filter(
        models.Classroom.corpus == data.corpus,
        models.Classroom.name == data.name,
    )
    if exclude_id is not None:
        q = q.filter(models.Classroom.id != exclude_id)
    if q.first():
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Кабинет с таким именем в этом корпусе уже есть"
        )


@router.get("", response_model=list[schemas.ClassroomOut])
def list_classroom(
    corpus: int | None = None,
    type: int | None = None,
    min_capacity: int | None = None,
    db: Session = Depends(get_db),
):
    """Список кабинетов. Фильтры: ?corpus=, ?type=, ?min_capacity= — пригодятся для подбора аудитории."""
    q = db.query(models.Classroom)
    if corpus is not None:
        q = q.filter(models.Classroom.corpus == corpus)
    if type is not None:
        q = q.filter(models.Classroom.type == type)
    if min_capacity is not None:
        q = q.filter(models.Classroom.capacity >= min_capacity)
    return q.all()


@router.get("/{classroom_id}", response_model=schemas.ClassroomOut)
def get_classroom(classroom_id: int, db: Session = Depends(get_db)):
    classroom = db.get(models.Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Кабинет не найден")
    return classroom


@router.post("", response_model=schemas.ClassroomOut, status_code=status.HTTP_201_CREATED)
def create_classroom(data: schemas.ClassroomCreate, db: Session = Depends(get_db)):
    _check_refs(data, db)
    _check_duplicate(data, db)
    classroom = models.Classroom(**data.model_dump())
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.put("/{classroom_id}", response_model=schemas.ClassroomOut)
def update_classroom(
    classroom_id: int, data: schemas.ClassroomCreate, db: Session = Depends(get_db)
):
    classroom = db.get(models.Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Кабинет не найден")
    _check_refs(data, db)
    _check_duplicate(data, db, exclude_id=classroom_id)
    for field, value in data.model_dump().items():
        setattr(classroom, field, value)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(classroom_id: int, db: Session = Depends(get_db)):
    classroom = db.get(models.Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Кабинет не найден")
    db.delete(classroom)
    db.commit()