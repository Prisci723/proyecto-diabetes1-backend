# app/routers/analysis.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import numpy as np

from app.database import get_db
from app.models.db_models import Patient, DailyMetrics, GlucoseReading, ClusterAssignment
from app.models.schemas import DailyMetricsResponse, PatientAnalysisResponse, ClusterInfo
from app.services.metrics import GlucoseMetricsCalculator
from app.services.clustering import ClusteringService
from app.services.recommendations import RecommendationEngine

router = APIRouter()

clustering_service = ClusteringService()

@router.get("/{patient_id}/metrics/daily")
def get_daily_metrics(
    patient_id: str,
    date: datetime = Query(None),
    db: Session = Depends(get_db)
):
    if date is None:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    metrics = db.query(DailyMetrics).filter(
        DailyMetrics.patient_id == patient_id,
        DailyMetrics.date == date
    ).first()
    if metrics:
        return DailyMetricsResponse.from_orm(metrics)
    start_of_day = date.replace(hour=0, minute=0, second=0)
    end_of_day = date.replace(hour=23, minute=59, second=59)
    readings = db.query(GlucoseReading).filter(
        GlucoseReading.patient_id == patient_id,
        GlucoseReading.timestamp >= start_of_day,
        GlucoseReading.timestamp <= end_of_day
    ).all()
    if len(readings) < 10:
        raise HTTPException(400, detail=f"Insuficientes lecturas (mínimo 10, encontradas {len(readings)})")
    values = [r.value for r in readings]
    calculated_metrics = GlucoseMetricsCalculator.calculate_daily_metrics(values)
    calculated_metrics.pop('median_glucose', None)  # ← AGREGAR ESTA LÍNEA
    calculated_metrics.pop('min_glucose', None)  # ← AGREGAR ESTA LÍNEA
    calculated_metrics.pop('max_glucose', None)  # ← AGREGAR ESTA LÍNEA
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

@router.get("/{patient_id}")
def get_patient_analysis(
    patient_id: str,
    days: int = Query(7, ge=7, le=30),
    db: Session = Depends(get_db)
) -> PatientAnalysisResponse:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, detail="Paciente no encontrado")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    daily_metrics_records = db.query(DailyMetrics).filter(
        DailyMetrics.patient_id == patient_id,
        DailyMetrics.date >= start_date,
        DailyMetrics.date <= end_date
    ).all()
    if len(daily_metrics_records) < 7:
        raise HTTPException(400, detail=f"Insuficientes días (mínimo 7, encontrados {len(daily_metrics_records)})")
    avg_metrics = {
        'avg_mean_glucose': np.mean([m.mean_glucose for m in daily_metrics_records]),
        'avg_cv': np.mean([m.cv for m in daily_metrics_records]),
        'avg_tir': np.mean([m.tir for m in daily_metrics_records]),
        'avg_tbr': np.mean([m.tbr for m in daily_metrics_records]),
        'avg_tar': np.mean([m.tar for m in daily_metrics_records]),
        'avg_gmi': np.mean([m.gmi for m in daily_metrics_records])
    }
    cluster_assignment = clustering_service.assign_cluster(avg_metrics)
    db_cluster = ClusterAssignment(
        patient_id=patient_id,
        cluster_id=cluster_assignment['cluster_id'],
        cluster_name=cluster_assignment['cluster_name'],
        confidence_score=cluster_assignment['confidence_score'],
        assigned_at=datetime.utcnow(),
        avg_tir=avg_metrics['avg_tir'],
        avg_cv=avg_metrics['avg_cv'],
        avg_gmi=avg_metrics['avg_gmi']
    )
    db.add(db_cluster)
    patient.current_cluster = cluster_assignment['cluster_id']
    patient.last_analysis_date = datetime.now()
    db.commit()
    latest_metrics = daily_metrics_records[-1]
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
    current_metrics_dict = {
        'tir': latest_metrics.tir,
        'cv': latest_metrics.cv,
        'tbr': latest_metrics.tbr,
        'tbr_severe': latest_metrics.tbr_severe,
        'tar': latest_metrics.tar,
        'tar_severe': latest_metrics.tar_severe,
        'gmi': latest_metrics.gmi
    }
    recommendations = RecommendationEngine.generate_recommendations(
        cluster_assignment,
        current_metrics_dict,
        trend
    )
    risk_score = calculate_risk_score(current_metrics_dict)
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
    risk = 0.0
    tir = metrics.get('tir', 70)
    if tir < 50:
        risk += 30
    elif tir < 70:
        risk += 15
    cv = metrics.get('cv', 0)
    if cv > 40:
        risk += 25
    elif cv > 36:
        risk += 15
    tbr_severe = metrics.get('tbr_severe', 0)
    if tbr_severe > 1:
        risk += 30
    elif tbr_severe > 0:
        risk += 15
    tbr = metrics.get('tbr', 0)
    if tbr > 4:
        risk += 15
    tar = metrics.get('tar', 0)
    if tar > 25:
        risk += 10
    return min(100, risk)

@router.get("/{patient_id}/history")
def get_patient_history(
    patient_id: str,
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    metrics = db.query(DailyMetrics).filter(
        DailyMetrics.patient_id == patient_id,
        DailyMetrics.date >= start_date,
        DailyMetrics.date <= end_date
    ).order_by(DailyMetrics.date).all()
    return {
        "patient_id": patient_id,
        "period": {"start": start_date, "end": end_date, "days": days},
        "metrics": [DailyMetricsResponse.from_orm(m) for m in metrics]
    }

@router.get("/clusters/info")
def get_clusters_info():
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
    descriptions = {
        0: "Pacientes con excelente control: TIR >70%, CV <36%, mínima hipoglucemia",
        1: "Pacientes con control moderado: TIR 50-70%, espacio para optimización",
        2: "Pacientes con alta variabilidad: CV >40%, requieren ajuste de tratamiento",
        3: "Pacientes con riesgo de hipoglucemia: TBR >4%, prioridad reducir insulina",
        4: "Pacientes con control subóptimo: TIR <50%, requieren revisión completa"
    }
    return descriptions.get(cluster_id, "Sin descripción disponible")