"""Роутер записи на консультаций, дает доп роуты сущностям и создает свой отдельный
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date,datetime
from app import models, schemas
from app.db.session import get_db


router = APIRouter(prefix="", tags=["consult_reg"])

def _check_consult(consult_id,db: Session):
    if db.get(models.Consult, consult_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Консультация не найдена")

def _check_student(student_id,db: Session):
    if db.get(models.Student, student_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Студент не найден")

@router.get("/consult/{consult_id}/reg", response_model=list[schemas.ConsultRegOut])
def list_registration_cons(consult_id: int,db: Session = Depends(get_db)):
    _check_consult(consult_id, db)
    return (
        db.query(models.ConsultRegistration)
        .filter(models.ConsultRegistration.consult_id == consult_id)
        .order_by(models.ConsultRegistration.registration_time)
        .all()
    )



@router.get("/students/{student_id}/reg", response_model=list[schemas.ConsultRegOut])
def list_registration_stud(student_id: int,db: Session = Depends(get_db)):
    _check_consult(student_id, db)
    return (
        db.query(models.ConsultRegistration)
        .filter(models.ConsultRegistration.student_id == student_id)
        .order_by(models.ConsultRegistration.registration_time)
        .all()
    )


@router.post("/registrations", response_model=schemas.ConsultRegOut, status_code=status.HTTP_201_CREATED)
def create_registration(data: schemas.ConsultRegBase, db: Session = Depends(get_db)):
    _check_student(data.student_id, db)

    # with_for_update блокирует строку консультации до конца транзакции:
    # два одновременных запроса на последнее место выполняются по очереди,
    # и второй честно видит, что мест уже нет (работает на PostgreSQL;
    # sqlite сериализует записи сам).
    consult = (
        db.query(models.Consult)
        .filter(models.Consult.id == data.consult_id)
        .with_for_update()
        .first()
    )
    if consult is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Консультация не найдена")

    exists = db.query(models.ConsultRegistration).filter(
        models.ConsultRegistration.student_id == data.student_id,
        models.ConsultRegistration.consult_id == data.consult_id,
    ).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Такая запись уже есть")

    taken = db.query(models.ConsultRegistration).filter(
        models.ConsultRegistration.consult_id == data.consult_id,
    ).count()
    if taken >= consult.max_students:
        raise HTTPException(status.HTTP_409_CONFLICT, "Мест нет")

    cons_reg = models.ConsultRegistration(**data.model_dump())
    db.add(cons_reg)
    db.commit()
    db.refresh(cons_reg)  # подтянуть registration_time, проставленный БД
    return cons_reg




@router.delete("/consult/{consult_id}/registrations/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registration(consult_id: int, student_id: int, db: Session = Depends(get_db)):
    cons_reg = (
        db.query(models.ConsultRegistration)
        .filter(
            models.ConsultRegistration.consult_id == consult_id,
            models.ConsultRegistration.student_id == student_id,
        )
        .first()
    )
    if cons_reg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Такой записи нет")

    consult = db.get(models.Consult, consult_id)          # существует: FK гарантирует
    row = consult.timetable_row                            # relationship, без запроса
    slot = db.get(models.Slot, row.slot)

    starts_at = datetime.combine(row.day, slot.start_time)
    if datetime.now() >= starts_at:
        raise HTTPException(status.HTTP_409_CONFLICT, "Консультация уже началась — отписаться нельзя")

    db.delete(cons_reg)
    db.commit()