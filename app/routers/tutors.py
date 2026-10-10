from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tutor import TutorProfile
from app.schemas.tutors import TutorProfileRead


router = APIRouter(prefix="/api/v1/tutors", tags=["tutors"])


# Получение всех профилей репетиторов из БД.
@router.get("", response_model=list[TutorProfileRead], summary="Get all tutor profiles")
def get_all_tutors(db: Annotated[Session, Depends(get_db)]) -> list[TutorProfile]:
    return list(db.scalars(select(TutorProfile).order_by(TutorProfile.id)).all())


# TODO: Добавить чтение одного профиля, создание и изменение собственного профиля.
