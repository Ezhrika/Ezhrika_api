from fastapi import FastAPI

from app.core.config import settings
from app.routers.tutors import router as tutors_router
from app.routers.users import router as users_router
from app.routers.slots import router as slots_router
from app.routers.bookings import router as bookings_router
from app.routers.notifications import router as notifications_router
from app.routers.students import router as students_router


app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(tutors_router)
app.include_router(users_router)
app.include_router(slots_router)
app.include_router(bookings_router)
app.include_router(notifications_router)
app.include_router(students_router)


@app.get("/", tags=["service"])
def root() -> dict[str, str]:
    return {"status": "ok"}
