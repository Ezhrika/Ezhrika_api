from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.subjects import SUBJECTS, canonical_subject
from app.db.session import get_db
from app.models.slot import Slot
from app.models.tutor import TutorProfile
from app.models.user import User
from app.schemas.slots import SlotRead
from app.schemas.tutors import TutorProfileRead, TutorProfileUpdate
from app.services.bookings import expire_pending_bookings


router = APIRouter(prefix="/api/v1/tutors", tags=["tutors"])


# Получение всех публичных профилей репетиторов.
@router.get("", response_model=list[TutorProfileRead], summary="Get all tutor profiles")
def get_all_tutors(db: Annotated[Session, Depends(get_db)]) -> list[TutorProfile]:
    return list(db.scalars(select(TutorProfile).order_by(TutorProfile.id)).all())


# Общий список допустимых предметов, без обращения к БД.
@router.get("/subjects", response_model=list[str], summary="Get available subjects")
def get_subjects() -> list[str]:
    return list(SUBJECTS)


# Получение собственного профиля репетитора (для личного кабинета).
@router.get("/me", response_model=TutorProfileRead, summary="Get own tutor profile")
def get_my_tutor_profile(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TutorProfile:
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors have access to this profile.",
        )
    profile = db.scalar(
        select(TutorProfile).where(TutorProfile.user_id == current_user.id)
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found.",
        )
    return profile


# Обновление собственного профиля репетитора.
@router.patch("/me", response_model=TutorProfileRead, summary="Update own tutor profile")
def update_my_tutor_profile(
    payload: TutorProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TutorProfile:
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors have access to this profile.",
        )
    profile = db.scalar(
        select(TutorProfile).where(TutorProfile.user_id == current_user.id)
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if payload.subject is not None:
        canonical = canonical_subject(payload.subject)
        if canonical is None and payload.subject != profile.subject:
            raise HTTPException(status_code=422, detail="Choose a subject from the subject list.")
        update_data["subject"] = canonical or profile.subject
    for field, value in update_data.items():
        if value is not None:
            setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# Публичная карточка конкретного репетитора для учеников и гостей.
@router.get("/{tutor_id}", response_model=TutorProfileRead, summary="Get public tutor profile")
def get_tutor_by_id(
    tutor_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> TutorProfile:
    profile = db.get(TutorProfile, tutor_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found.",
        )
    return profile


# Публичный список свободных слотов конкретного репетитора для записи.
@router.get(
    "/{tutor_id}/slots",
    response_model=list[SlotRead],
    summary="Get open slots of a tutor",
)
def get_tutor_open_slots(
    tutor_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> list[Slot]:
    tutor = db.get(TutorProfile, tutor_id)
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found.",
        )
    expire_pending_bookings(db, tutor_id)
    db.commit()
    return list(
        db.scalars(
            select(Slot)
            .where(
                Slot.tutor_id == tutor_id,
                Slot.status == "open",
                Slot.starts_at > datetime.now(timezone.utc),
            )
            .order_by(Slot.starts_at)
        ).all()
    )
