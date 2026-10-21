from fastapi import HTTPException, status

from app.core.config import settings


# Отладочные списки доступны без авторизации только при DEBUG=true.
def require_debug() -> None:
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
