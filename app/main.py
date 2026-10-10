from fastapi import FastAPI

from app.core.config import settings
from app.tutors.router import router as tutors_router


app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(tutors_router)


@app.get("/", tags=["service"])
def root() -> dict[str, str]:
    return {"status": "ok"}
