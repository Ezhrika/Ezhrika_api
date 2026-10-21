from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.bookings import router as bookings_router
from app.routers.notifications import router as notifications_router
from app.routers.slots import router as slots_router
from app.routers.students import router as students_router
from app.routers.tutors import router as tutors_router
from app.routers.users import router as users_router
from app.routers.pages import FRONTEND_DIR, router as pages_router


app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tutors_router)
app.include_router(students_router)
app.include_router(slots_router)
app.include_router(bookings_router)
app.include_router(notifications_router)
app.include_router(pages_router)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok"}
