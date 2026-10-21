from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.debug import require_debug
from app.db.session import get_db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.student import StudentProfile
from app.schemas.users import CurrentUserRead, UserRead


router = APIRouter(prefix="/api/v1/users", tags=["users"])


# Получение всех аккаунтов пользователей из БД (для локальной отладки).
@router.get("", response_model=list[UserRead], summary="Get all users (debug)", dependencies=[Depends(require_debug)])
def get_all_users(db: Annotated[Session, Depends(get_db)]) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


# Получение данных текущего авторизованного пользователя.
@router.get("/me", response_model=CurrentUserRead, summary="Get current user")
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUserRead:
    model = TutorProfile if current_user.role == "tutor" else StudentProfile
    profile = db.scalar(select(model).where(model.user_id == current_user.id))
    return CurrentUserRead(
        **UserRead.model_validate(current_user).model_dump(),
        name=profile.name if profile else "",
    )
