"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash,check_password_hash

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/account", tags=["account"])


@router.get("", response_model=list[schemas.AccountOut])
def list_account(db: Session = Depends(get_db)):
    return db.query(models.Account).all()


@router.get("/{account_id}", response_model=schemas.AccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(models.Account, account_id)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Аккаунт не найден")
    return account


@router.post("", response_model=schemas.AccountOut, status_code=201)
def create_account(data: schemas.AccountCreate, db=Depends(get_db)):
    exists = db.query(models.Account).filter(models.Account.login == data.login).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Аккаунт с таким названием уже есть")

    account = models.Account(
        login=data.login,
        role=data.role,
        password_hash=generate_password_hash(data.password),  # хешируем здесь
    )

    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.put("/{account_id}", response_model=schemas.AccountOut)
def update_account(
    account_id: int, data: schemas.AccountUpdate, db: Session = Depends(get_db)
):
    account = db.get(models.Account, account_id)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Аккаунт не найден")
    clash = (
        db.query(models.Account)
        .filter(models.Account.login == data.login, models.Account.id != account_id)
        .first()
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Аккаунт с таким названием уже есть")

    for field, value in data.model_dump().items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(models.Account, account_id)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Аккаунт не найден")
    db.delete(account)
    db.commit()

@router.post("/{account_id}/change-password", status_code=204)
def change_password(account_id: int, data: schemas.PasswordChange, db=Depends(get_db)):
    account = db.get(models.Account, account_id)
    if account is None:
        raise HTTPException(404, "Аккаунт не найден")

    # 1. проверяем, что старый пароль верный
    if not check_password_hash(account.password_hash, data.old_password):
        raise HTTPException(403, "Неверный текущий пароль")

    # 2. хешируем новый и сохраняем
    account.password_hash = generate_password_hash(data.new_password)
    db.commit()