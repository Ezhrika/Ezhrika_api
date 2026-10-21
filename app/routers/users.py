from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.users import UserRead


router = APIRouter(prefix="/api/v1/users", tags=["users"])


# Получение всех аккаунтов пользователей из БД (для локальной отладки).
@router.get("", response_model=list[UserRead], summary="Get all users (debug)")
def get_all_users(db: Annotated[Session, Depends(get_db)]) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


# Получение данных текущего авторизованного пользователя.
@router.get("/me", response_model=UserRead, summary="Get current user")
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
