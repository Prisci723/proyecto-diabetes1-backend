# app/routers/glucose.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.db_models import GlucoseReading, Patient
from app.models.schemas import GlucoseReadingCreate, GlucoseReadingBulk

router = APIRouter()

@router.post("/reading/")
def add_glucose_reading(reading: GlucoseReadingCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == reading.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    db_reading = GlucoseReading(
        patient_id=reading.patient_id,
        timestamp=reading.timestamp,
        value=reading.value,
        created_at=datetime.utcnow()
    )
    db.add(db_reading)
    db.commit()
    return {"message": "Lectura registrada exitosamente"}

@router.post("/bulk/")
def add_bulk_readings(bulk: GlucoseReadingBulk, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == bulk.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    readings_to_add = []
    for reading_data in bulk.readings:
        db_reading = GlucoseReading(
            patient_id=bulk.patient_id,
            timestamp=datetime.fromisoformat(reading_data['timestamp']),
            value=float(reading_data['value']),
            created_at=datetime.utcnow()
        )
        readings_to_add.append(db_reading)
    db.bulk_save_objects(readings_to_add)
    db.commit()
    return {"message": f"{len(readings_to_add)} lecturas registradas exitosamente"}