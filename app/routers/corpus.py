"""Роутер преподавателей — образец для остальных сущностей.

Заметь: глаголов (/new, /del, /get) в путях нет. Что делаем — определяет
HTTP-метод (get/post/put/delete), а путь — это только существительное.
Это аналог Blueprint во Flask: свой файл на сущность, подключается в main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="/corpus", tags=["corpus"])


@router.get("", response_model=list[schemas.CorpusOut])
def list_corpus(db: Session = Depends(get_db)):
    return db.query(models.Corpus).all()


@router.get("/{corpus_id}", response_model=schemas.CorpusOut)
def get_corpus(corpus_id: int, db: Session = Depends(get_db)):
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Корпус не найден")
    return corpus


@router.post("", response_model=schemas.CorpusOut, status_code=status.HTTP_201_CREATED)
def create_corpus(data: schemas.CorpusCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Corpus).filter(models.Corpus.name == data.name).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Корпус с таким названием уже есть")

    corpus = models.Corpus(**data.model_dump())
    db.add(corpus)
    db.commit()
    db.refresh(corpus)  # подтянуть сгенерированный БД id
    return corpus


@router.put("/{corpus_id}", response_model=schemas.CorpusOut)
def update_corpus(
    corpus_id: int, data: schemas.CorpusCreate, db: Session = Depends(get_db)
):
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Корпус не найден")
    clash = (
        db.query(models.Corpus)
        .filter(models.Subject.name == data.name, models.Corpus.id != corpus_id)
        .first()
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Корпус с таким названием уже есть")

    for field, value in data.model_dump().items():
        setattr(corpus, field, value)
    db.commit()
    db.refresh(corpus)
    return corpus


@router.delete("/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corpus(corpus_id: int, db: Session = Depends(get_db)):
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Корпус не найден")
    db.delete(corpus)
    db.commit()
