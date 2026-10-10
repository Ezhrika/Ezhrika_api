from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.users import UserRead


router = APIRouter(prefix="/api/v1/users", tags=["users"])


# Получение всех аккаунтов репетиторов из БД.
@router.get("", response_model=list[UserRead], summary="Get all users")
def get_all_users(db: Annotated[Session, Depends(get_db)]) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


# TODO: Реализовать регистрацию, вход и получение текущего пользователя; ограничить список аккаунтов.
# TODO: Нормализовать email и хешировать пароль при регистрации.
