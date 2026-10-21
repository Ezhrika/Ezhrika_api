from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.student import StudentProfile
from app.models.tutor import TutorProfile
from app.models.user import User
from app.schemas.users import Token, UserCreate, UserLogin, UserRead


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# Регистрация нового пользователя с созданием профиля репетитора или ученика.
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    normalized_email = payload.email.strip().lower()
    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    display_name = payload.name.strip() if payload.name.strip() else normalized_email.split("@")[0]

    if user.role == "tutor":
        display_subject = payload.subject
        tutor_profile = TutorProfile(
            user_id=user.id,
            name=display_name,
            subject=display_subject,
            description="",
            timezone="UTC",
        )
        db.add(tutor_profile)
    elif user.role == "student":
        student_profile = StudentProfile(
            user_id=user.id,
            name=display_name,
        )
        db.add(student_profile)

    db.commit()
    db.refresh(user)
    return user


# Вход пользователя с проверкой пароля и выдачей JWT-токена.
@router.post(
    "/login",
    response_model=Token,
    summary="Login and obtain access token",
)
def login(
    payload: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    normalized_email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return Token(access_token=access_token, token_type="bearer")
