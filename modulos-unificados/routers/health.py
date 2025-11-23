# app/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.services.clustering import clustering_service
from app.services.prediction import model_manager
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    clustering_status = "healthy" if clustering_service.kmeans_model else "model_not_loaded"
    prediction_status = "healthy" if model_manager and model_manager.is_loaded else "unhealthy"
    overall_status = "healthy" if all(s == "healthy" for s in [db_status, clustering_status, prediction_status]) else "degraded"
    return HealthResponse(
        status=overall_status,
        model_loaded=clustering_service.kmeans_model is not None and model_manager.is_loaded,
        device=str(model_manager.device) if model_manager else "unknown",
        timestamp=datetime.now().isoformat()
    )