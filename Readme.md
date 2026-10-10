# Tutor Booking API

Backend на FastAPI для записи учеников к частным репетиторам.


## Запуск приложения

Установка зависимостей из pyproject.toml:

```powershell
python -m pip install -e .
```

Запуск сервера:

```powershell
python -m uvicorn app.main:app --reload
```

Проверка подключения к PostgreSQL (после настройки `DATABASE_URL` в локальном `.env`):

```powershell
python -m app.db.check
```