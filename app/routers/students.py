from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.student import StudentProfile
from app.schemas.students import StudentProfileRead


router = APIRouter(prefix="/api/v1/students", tags=["students"])


# Получение всех профилей учеников из БД.
@router.get("", response_model=list[StudentProfileRead], summary="Get all student profiles")
def get_all_students(db: Annotated[Session, Depends(get_db)]) -> list[StudentProfile]:
    return list(db.scalars(select(StudentProfile).order_by(StudentProfile.id)).all())


# TODO: Добавить создание и изменение собственного профиля, ограничить доступ к списку.
