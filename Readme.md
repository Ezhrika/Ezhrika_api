# Tutor Booking API

Backend на FastAPI для записи учеников к частным репетиторам.

Из корня проекта в PowerShell установите зависимости (один раз):

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Запуск сервера:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- Документация API: http://127.0.0.1:8000/docs
- Остановка: `Ctrl+C`.

Сейчас `.env` и PostgreSQL для запуска не нужны. Пример настроек — в `.env.example`.

