# app/routers/glucose.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.db_models import GlucoseReading, Patient
from app.models.schemas import GlucoseReadingCreate, GlucoseReadingBulk

router = APIRouter()


@router.post("/reading/")
def add_glucose_reading(reading: GlucoseReadingCreate, db: Session = Depends(get_db)):
    """
    Registra una lectura individual de glucosa
    
    Args:
        reading: Datos de la lectura (patient_id, timestamp, value)
        db: Sesión de base de datos
        
    Returns:
        Mensaje de confirmación
        
    Raises:
        HTTPException 404: Si el paciente no existe
    """
    # Verificar que el paciente existe
    patient = db.query(Patient).filter(Patient.id == reading.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Crear lectura
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
    """
    Registra múltiples lecturas de glucosa de una vez
    
    Args:
        bulk: Contiene patient_id y lista de readings [{timestamp, value}, ...]
        db: Sesión de base de datos
        
    Returns:
        Mensaje con cantidad de lecturas registradas
        
    Raises:
        HTTPException 404: Si el paciente no existe
        HTTPException 400: Si hay errores en el formato de datos
        
    Example:
        ```json
        {
            "patient_id": "P001",
            "readings": [
                {"timestamp": "2024-01-15T08:00:00", "value": 5.5},
                {"timestamp": "2024-01-15T12:00:00", "value": 8.2}
            ]
        }
        ```
    """
    # Verificar paciente
    patient = db.query(Patient).filter(Patient.id == bulk.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Crear lecturas en batch
    readings_to_add = []
    for idx, reading_data in enumerate(bulk.readings):
        try:
            # Validar que tenga las claves necesarias
            if 'timestamp' not in reading_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Lectura {idx}: falta el campo 'timestamp'"
                )
            if 'value' not in reading_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Lectura {idx}: falta el campo 'value'"
                )
            
            # Parsear timestamp
            if isinstance(reading_data['timestamp'], str):
                timestamp = datetime.fromisoformat(reading_data['timestamp'])
            else:
                timestamp = reading_data['timestamp']
            
            # Validar rango de glucosa
            value = float(reading_data['value'])
            if not 2.0 <= value <= 25.0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Lectura {idx}: valor {value} fuera de rango (2.0-25.0 mmol/L)"
                )
            
            db_reading = GlucoseReading(
                patient_id=bulk.patient_id,
                timestamp=timestamp,
                value=value,
                created_at=datetime.utcnow()
            )
            readings_to_add.append(db_reading)
            
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Lectura {idx}: error en formato de datos - {str(e)}"
            )
    
    db.bulk_save_objects(readings_to_add)
    db.commit()
    
    return {"message": f"{len(readings_to_add)} lecturas registradas exitosamente"}


@router.get("/{patient_id}/readings/")
def get_patient_readings(
    patient_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Obtiene las últimas lecturas de glucosa de un paciente
    
    Args:
        patient_id: ID del paciente
        limit: Cantidad máxima de lecturas a retornar (default: 100)
        db: Sesión de base de datos
        
    Returns:
        Lista de lecturas ordenadas por timestamp descendente
    """
    # Verificar paciente
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Obtener lecturas
    readings = db.query(GlucoseReading).filter(
        GlucoseReading.patient_id == patient_id
    ).order_by(GlucoseReading.timestamp.desc()).limit(limit).all()
    
    return {
        "patient_id": patient_id,
        "count": len(readings),
        "readings": [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "value": r.value,
                "created_at": r.created_at
            }
            for r in readings
        ]
    }


@router.delete("/{patient_id}/readings/")
def delete_patient_readings(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Elimina todas las lecturas de glucosa de un paciente
    
    Args:
        patient_id: ID del paciente
        db: Sesión de base de datos
        
    Returns:
        Mensaje con cantidad de lecturas eliminadas
        
    Warning:
        Esta operación es irreversible
    """
    # Verificar paciente
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Contar y eliminar lecturas
    count = db.query(GlucoseReading).filter(
        GlucoseReading.patient_id == patient_id
    ).delete()
    
    db.commit()
    
    return {
        "message": f"{count} lecturas eliminadas exitosamente",
        "patient_id": patient_id
    }