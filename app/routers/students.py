from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.debug import require_debug
from app.db.session import get_db
from app.models.student import StudentProfile
from app.models.user import User
from app.schemas.students import StudentProfileRead, StudentProfileUpdate


router = APIRouter(prefix="/api/v1/students", tags=["students"])


# Получение всех профилей учеников из БД (для локальной отладки).
@router.get("", response_model=list[StudentProfileRead], summary="Get all student profiles (debug)", dependencies=[Depends(require_debug)])
def get_all_students(db: Annotated[Session, Depends(get_db)]) -> list[StudentProfile]:
    return list(db.scalars(select(StudentProfile).order_by(StudentProfile.id)).all())


# Получение собственного профиля ученика (для личного кабинета).
@router.get("/me", response_model=StudentProfileRead, summary="Get own student profile")
def get_my_student_profile(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudentProfile:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students have access to this profile.",
        )
    profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )
    return profile


# Обновление собственного профиля ученика.
@router.patch("/me", response_model=StudentProfileRead, summary="Update own student profile")
def update_my_student_profile(
    payload: StudentProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudentProfile:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students have access to this profile.",
        )
    profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    profile.name = payload.name.strip()
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
