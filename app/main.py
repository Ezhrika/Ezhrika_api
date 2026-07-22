"""Точка входа приложения.

Здесь только создаётся FastAPI и подключаются роутеры. Никакой логики —
она живёт в routers/

Запуск:  uvicorn app.main:app --reload
Docs:    http://localhost:8000/docs
"""
from fastapi import FastAPI

from app.routers import teachers, students


app = FastAPI(title="SmartConsult API")

# Каждый новый роутер (students, consults, classrooms, auth) добавляется строкой.
app.include_router(teachers.router)
app.include_router(students.router)

from app.db.base import Base
from app.db.session import engine
from app import models  # важно: импорт, чтобы модели зарегистрировались

Base.metadata.create_all(engine)

@app.get("/")
def root():
    return {"service": "SmartConsult API", "docs": "/docs"}
