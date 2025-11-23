# app/routers/patients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.db_models import Patient
from app.models.schemas import PatientCreate

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.id == patient.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Paciente ya existe")
    db_patient = Patient(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        diabetes_type=patient.diabetes_type,
        diagnosis_date=patient.diagnosis_date,
        created_at=datetime.utcnow()
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return {"message": "Paciente creado exitosamente", "patient_id": db_patient.id}