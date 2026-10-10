# Tutor Booking API

Backend на FastAPI для записи учеников к частным репетиторам.

## Архитектура

```text
Ezhrika_api/
├── app/
│   ├── auth/              # todo: Регистрация и вход
│   ├── bookings/          # todo: Запись и отмена занятий
│   ├── core/              # Настройки
│   ├── db/
│   │   ├── base.py
│   │   ├── check.py        # Проверка подключения
│   │   └── session.py
│   ├── notifications/     # todo: Email-уведомления
│   ├── slots/             # todo: Свободное время
│   ├── tutors/            # Профили репетиторов
│   │   ├── models.py      # Модель TutorProfile для БД
│   │   ├── router.py
│   │   └── schemas.py     # Формат ответа API
│   └── main.py
└── frontend/              # todo: Нужен фронт
```


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

Сайт с документацией (port 8000!)
```http://127.0.0.1:8000/docs#/```
