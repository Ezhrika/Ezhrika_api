from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend" / "yozhrika"
router = APIRouter(include_in_schema=False)


# Отдача страниц из фиксированного набора без обращения к БД.
def page_file(name: str) -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / f"{name}.html",
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/")
def home_page() -> FileResponse:
    return page_file("index")


@router.get("/for-tutors")
def for_tutors_page() -> FileResponse:
    return page_file("for-tutors")


@router.get("/features")
def features_page() -> FileResponse:
    return page_file("features")


@router.get("/for-students")
def for_students_page() -> FileResponse:
    return page_file("for-students")


@router.get("/help")
def help_page() -> FileResponse:
    return page_file("help")


@router.get("/tutors")
def tutor_catalog_page() -> FileResponse:
    return page_file("tutors")


@router.get("/login")
def login_page() -> FileResponse:
    return page_file("login")


@router.get("/register")
def register_page() -> FileResponse:
    return page_file("register")


@router.get("/t/{tutor_id:int}")
def tutor_page(tutor_id: int) -> FileResponse:
    return page_file("tutor")


@router.get("/tutor/dashboard")
def tutor_dashboard_page() -> FileResponse:
    return page_file("tutor-dashboard")


@router.get("/student/dashboard")
def student_dashboard_page() -> FileResponse:
    return page_file("student-dashboard")


@router.get("/confirm")
def confirm_page() -> FileResponse:
    return page_file("confirm")


@router.get("/cancel")
def cancel_page() -> FileResponse:
    return page_file("cancel")
