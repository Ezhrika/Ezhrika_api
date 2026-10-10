# Tutor Booking API

Backend на FastAPI для записи учеников к частным репетиторам.

## Архитектура

```text
app/
├── auth/              # todo: Регистрация и вход
├── bookings/          # todo: Запись и отмена занятий 
├── core/              # Настройки
├── db/
│   ├── base.py         
│   ├── check.py        # Проверка подключения
│   └── session.py      
├── notifications/     # todo: Email-уведомления
├── slots/             # todo: Свободное время 
├── tutors/            # todo: Профили репетиторов
└── main.py            
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
