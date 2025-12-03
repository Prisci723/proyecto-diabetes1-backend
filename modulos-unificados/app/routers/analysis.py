# app/routers/analysis.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

from app.database import get_db
from app.models.db_models import Patient, DailyMetrics, GlucoseReading, ClusterAssignment
from app.models.schemas import DailyMetricsResponse, PatientAnalysisResponse, ClusterInfo
from app.services.metrics import GlucoseMetricsCalculator
from app.services.clustering import ClusteringService
from app.services.recommendations import RecommendationEngine

router = APIRouter()

# Instanciar servicios
clustering_service = ClusteringService()
metrics_calculator = GlucoseMetricsCalculator()
recommendation_engine = RecommendationEngine()


@router.get("/{patient_id}/metrics/daily", response_model=DailyMetricsResponse)
def get_daily_metrics(
    patient_id: str,
    date: datetime = Query(None, description="Fecha específica (YYYY-MM-DD). Si no se proporciona, usa hoy"),
    db: Session = Depends(get_db)
):
    """
    Obtiene o calcula las métricas diarias de un paciente para una fecha específica
    
    Requiere al menos 10 lecturas de glucosa en el día para calcular métricas.
    
    Args:
        patient_id: ID del paciente
        date: Fecha para calcular métricas (default: hoy)
        db: Sesión de base de datos
        
    Returns:
        Métricas calculadas del día incluyendo TIR, CV, GMI, etc.
        
    Raises:
        HTTPException 400: Si no hay suficientes lecturas (mínimo 10)
    """
    if date is None:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Buscar métricas ya calculadas
    metrics = db.query(DailyMetrics).filter(
        DailyMetrics.patient_id == patient_id,
        DailyMetrics.date == date
    ).first()
    
    if metrics:
        return DailyMetricsResponse.from_orm(metrics)
    
    # Si no existen, calcular desde las lecturas
    start_of_day = date.replace(hour=0, minute=0, second=0)
    end_of_day = date.replace(hour=23, minute=59, second=59)
    
    readings = db.query(GlucoseReading).filter(
        GlucoseReading.patient_id == patient_id,
        GlucoseReading.timestamp >= start_of_day,
        GlucoseReading.timestamp <= end_of_day
    ).all()
    
    if len(readings) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Insuficientes lecturas para calcular métricas (mínimo 10, encontradas {len(readings)})"
        )
    
    # Calcular métricas
    values = [r.value for r in readings]
    calculated_metrics = metrics_calculator.calculate_daily_metrics(values)
    
    # Guardar en BD
    db_metrics = DailyMetrics(
        patient_id=patient_id,
        date=date,
        **calculated_metrics,
        created_at=datetime.utcnow()
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    
    return DailyMetricsResponse.from_orm(db_metrics)


@router.get("/{patient_id}", response_model=PatientAnalysisResponse)
def get_patient_analysis(
    patient_id: str,
    days: int = Query(7, ge=7, le=30, description="Días a analizar (7-30)"),
    db: Session = Depends(get_db)
):
    """
    Genera un análisis completo del paciente con:
    - Asignación a cluster basado en perfil glucémico
    - Métricas actuales (último día)
    - Recomendaciones personalizadas
    - Tendencia (mejorando/estable/empeorando)
    - Score de riesgo (0-100)
    
    Requiere al menos 7 días de datos con mínimo 10 lecturas por día.
    
    Args:
        patient_id: ID del paciente
        days: Cantidad de días a analizar (default: 7)
        db: Sesión de base de datos
        
    Returns:
        Análisis completo con recomendaciones y cluster asignado
        
    Raises:
        HTTPException 404: Si el paciente no existe
        HTTPException 400: Si no hay suficientes datos
    """
    # Verificar paciente
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Obtener rango de fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Buscar métricas existentes
    daily_metrics_records = db.query(DailyMetrics).filter(
        DailyMetrics.patient_id == patient_id,
        DailyMetrics.date >= start_date,
        DailyMetrics.date <= end_date
    ).all()
    
    # Si no hay suficientes métricas, calcularlas desde las lecturas
    if len(daily_metrics_records) < 7:
        # Obtener todas las lecturas en el rango
        readings_in_range = db.query(GlucoseReading).filter(
            GlucoseReading.patient_id == patient_id,
            GlucoseReading.timestamp >= start_date,
            GlucoseReading.timestamp <= end_date
        ).order_by(GlucoseReading.timestamp).all()
        
        if not readings_in_range:
            raise HTTPException(
                status_code=400,
                detail=f"No hay lecturas de glucosa en los últimos {days} días"
            )
        
        # Agrupar lecturas por día
        readings_by_day = defaultdict(list)
        for reading in readings_in_range:
            day_key = reading.timestamp.date()
            readings_by_day[day_key].append(reading.value)
        
        # Calcular y guardar métricas para cada día
        calculated_metrics = []
        for day, values in readings_by_day.items():
            if len(values) >= 10:  # Mínimo de lecturas por día
                day_metrics = metrics_calculator.calculate_daily_metrics(values)
                
                db_metrics = DailyMetrics(
                    patient_id=patient_id,
                    date=datetime.combine(day, datetime.min.time()),
                    **day_metrics,
                    created_at=datetime.utcnow()
                )
                db.add(db_metrics)
                calculated_metrics.append(db_metrics)
        
        db.commit()
        
        # Refrescar objetos
        for m in calculated_metrics:
            db.refresh(m)
        
        daily_metrics_records = calculated_metrics
        
        if len(daily_metrics_records) < 7:
            raise HTTPException(
                status_code=400,
                detail=f"Insuficientes días de datos (mínimo 7 días con al menos 10 lecturas/día, encontrados {len(daily_metrics_records)})"
            )
    
    # Calcular promedios para clustering
    avg_metrics = {
        'avg_mean_glucose': float(np.mean([m.mean_glucose for m in daily_metrics_records])),
        'avg_cv': float(np.mean([m.cv for m in daily_metrics_records])),
        'avg_tir': float(np.mean([m.tir for m in daily_metrics_records])),
        'avg_tbr': float(np.mean([m.tbr for m in daily_metrics_records])),
        'avg_tar': float(np.mean([m.tar for m in daily_metrics_records])),
        'avg_gmi': float(np.mean([m.gmi for m in daily_metrics_records]))
    }
    
    # Asignar a cluster
    cluster_assignment = clustering_service.assign_cluster(avg_metrics)
    
    # Guardar asignación en BD
    db_cluster = ClusterAssignment(
        patient_id=patient_id,
        cluster_id=cluster_assignment['cluster_id'],
        cluster_name=cluster_assignment['cluster_name'],
        confidence_score=float(cluster_assignment['confidence_score']),
        assigned_at=datetime.utcnow(),
        avg_tir=float(avg_metrics['avg_tir']),
        avg_cv=float(avg_metrics['avg_cv']),
        avg_gmi=float(avg_metrics['avg_gmi'])
    )
    db.add(db_cluster)
    
    # Actualizar paciente
    patient.current_cluster = cluster_assignment['cluster_id']
    patient.last_analysis_date = datetime.now()
    
    db.commit()
    
    # Métricas actuales (último día con datos)
    latest_metrics = daily_metrics_records[-1]
    
    # Calcular tendencia (comparar primeros 3 días vs últimos 3 días)
    if len(daily_metrics_records) >= 6:
        early_tir = np.mean([m.tir for m in daily_metrics_records[:3]])
        recent_tir = np.mean([m.tir for m in daily_metrics_records[-3:]])
        
        if recent_tir > early_tir + 5:
            trend = "improving"
        elif recent_tir < early_tir - 5:
            trend = "worsening"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Generar recomendaciones
    current_metrics_dict = {
        'tir': latest_metrics.tir,
        'cv': latest_metrics.cv,
        'tbr': latest_metrics.tbr,
        'tbr_severe': latest_metrics.tbr_severe,
        'tar': latest_metrics.tar,
        'tar_severe': latest_metrics.tar_severe,
        'gmi': latest_metrics.gmi
    }
    
    recommendations = recommendation_engine.generate_recommendations(
        cluster_assignment,
        current_metrics_dict,
        trend
    )
    
    # Calcular risk score
    risk_score = calculate_risk_score(current_metrics_dict)
    
    # Construir respuesta
    return PatientAnalysisResponse(
        patient_id=patient_id,
        analysis_date=datetime.now(),
        cluster_info=ClusterInfo(
            cluster_id=cluster_assignment['cluster_id'],
            cluster_name=cluster_assignment['cluster_name'],
            confidence_score=cluster_assignment['confidence_score'],
            assigned_at=datetime.now(),
            metrics=avg_metrics
        ),
        current_metrics=DailyMetricsResponse.from_orm(latest_metrics),
        recommendations=recommendations,
        trend=trend,
        risk_score=risk_score
    )


def calculate_risk_score(metrics: dict[str, float]) -> float:
    """
    Calcula un score de riesgo de 0-100 basado en métricas.
    100 = máximo riesgo, 0 = sin riesgo
    """
    risk = 0.0
    
    # TIR contribuye negativamente (menos TIR = más riesgo)
    tir = metrics.get('tir', 70)
    if tir < 50:
        risk += 30
    elif tir < 70:
        risk += 15
    
    # CV contribuye positivamente
    cv = metrics.get('cv', 0)
    if cv > 40:
        risk += 25
    elif cv > 36:
        risk += 15
    
    # TBR severa es muy riesgosa
    tbr_severe = metrics.get('tbr_severe', 0)
    if tbr_severe > 1:
        risk += 30
    elif tbr_severe > 0:
        risk += 15
    
    # TBR general
    tbr = metrics.get('tbr', 0)
    if tbr > 4:
        risk += 15
    
    # TAR
    tar = metrics.get('tar', 0)
    if tar > 25:
        risk += 10
    
    return min(100, risk)


@router.get("/{patient_id}/history")
def get_patient_history(
    patient_id: str,
    days: int = Query(30, ge=1, le=90, description="Días de historial a obtener (1-90)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de métricas diarias del paciente
    
    Args:
        patient_id: ID del paciente
        days: Cantidad de días hacia atrás (default: 30)
        db: Sesión de base de datos
        
    Returns:
        Lista de métricas diarias ordenadas cronológicamente
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    metrics = db.query(DailyMetrics).filter(
        DailyMetrics.patient_id == patient_id,
        DailyMetrics.date >= start_date,
        DailyMetrics.date <= end_date
    ).order_by(DailyMetrics.date).all()
    
    return {
        "patient_id": patient_id,
        "period": {
            "start": start_date,
            "end": end_date,
            "days": days
        },
        "count": len(metrics),
        "metrics": [DailyMetricsResponse.from_orm(m) for m in metrics]
    }


@router.get("/clusters/info")
def get_clusters_info():
    """
    Devuelve información sobre los clusters disponibles en el sistema
    
    Returns:
        Lista de clusters con ID, nombre y descripción
    """
    return {
        "total_clusters": len(clustering_service.cluster_names),
        "clusters": [
            {
                "id": cluster_id,
                "name": name,
                "description": get_cluster_description(cluster_id)
            }
            for cluster_id, name in clustering_service.cluster_names.items()
        ]
    }


def get_cluster_description(cluster_id: int) -> str:
    """Descripciones detalladas de cada cluster"""
    descriptions = {
        0: "Pacientes con excelente control: TIR >70%, CV <36%, mínima hipoglucemia",
        1: "Pacientes con control moderado: TIR 50-70%, espacio para optimización",
        2: "Pacientes con alta variabilidad: CV >40%, requieren ajuste de tratamiento",
        3: "Pacientes con riesgo de hipoglucemia: TBR >4%, prioridad reducir insulina",
        4: "Pacientes con control subóptimo: TIR <50%, requieren revisión completa"
    }
    return descriptions.get(cluster_id, "Sin descripción disponible")


@router.get("/{patient_id}/cluster-history")
def get_cluster_history(
    patient_id: str,
    limit: int = Query(10, ge=1, le=50, description="Cantidad de registros a retornar"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de asignaciones de cluster del paciente
    
    Útil para ver la evolución del control glucémico en el tiempo
    
    Args:
        patient_id: ID del paciente
        limit: Cantidad máxima de registros (default: 10)
        db: Sesión de base de datos
        
    Returns:
        Lista de asignaciones ordenadas por fecha descendente
    """
    assignments = db.query(ClusterAssignment).filter(
        ClusterAssignment.patient_id == patient_id
    ).order_by(ClusterAssignment.assigned_at.desc()).limit(limit).all()
    
    return {
        "patient_id": patient_id,
        "count": len(assignments),
        "assignments": [
            {
                "cluster_id": a.cluster_id,
                "cluster_name": a.cluster_name,
                "confidence_score": a.confidence_score,
                "assigned_at": a.assigned_at,
                "metrics": {
                    "avg_tir": a.avg_tir,
                    "avg_cv": a.avg_cv,
                    "avg_gmi": a.avg_gmi
                }
            }
            for a in assignments
        ]
    }