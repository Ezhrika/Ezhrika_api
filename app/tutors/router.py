# Маршруты API для профилей репетиторов.
# TODO: Добавить чтение одного профиля, создание и изменение собственного профиля.

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.tutors.models import TutorProfile
from app.tutors.schemas import TutorProfileRead


router = APIRouter(prefix="/api/v1/tutors", tags=["tutors"])


@router.get("", response_model=list[TutorProfileRead], summary="Get all tutor profiles")
def get_all_tutors(db: Annotated[Session, Depends(get_db)]) -> list[TutorProfile]:
    return list(db.scalars(select(TutorProfile).order_by(TutorProfile.id)).all())
