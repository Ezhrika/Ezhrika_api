"""Точка входа приложения.

Здесь только создаётся FastAPI и подключаются роутеры. Никакой логики —
она живёт в routers/

Запуск:  uvicorn app.main:app --reload
Docs:    http://localhost:8000/docs
"""
from fastapi import FastAPI

from app.routers import teachers, students, account,faculty, student_group,classroom_type,corpus


app = FastAPI(title="SmartConsult API")

# Каждый новый роутер (students, consults, classrooms, auth) добавляется строкой.
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(account.router)
app.include_router(faculty.router)
app.include_router(student_group.router)
app.include_router(classroom_type.router)
app.include_router(corpus.router)


from app.db.base import Base
from app.db.session import engine
from app import models  # важно: импорт, чтобы модели зарегистрировались

Base.metadata.create_all(engine)

@app.get("/")
def root():
    return {"service": "SmartConsult API", "docs": "/docs"}
