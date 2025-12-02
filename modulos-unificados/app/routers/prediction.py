# app/routers/prediction.py
from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.models.schemas import PredictionRequest, PredictionResponse
from app.services.prediction import model_manager

router = APIRouter()

@router.post("/", response_model=PredictionResponse)
def predict_bolus(request: PredictionRequest):
    if not model_manager or not model_manager.is_loaded:
        raise HTTPException(503, detail="Modelo no disponible. El servicio no está listo.")
    try:
        result = model_manager.predict(request)
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(500, detail=f"Error en la predicción: {str(e)}")

@router.get("/model-info")
def get_model_info():
    if not model_manager or not model_manager.is_loaded:
        raise HTTPException(503, detail="Modelo no disponible")
    return {
        "model_loaded": True,
        "input_dimension": len(model_manager.feature_names),
        "features": model_manager.feature_names[:10],
        "total_features": len(model_manager.feature_names),
        "device": str(model_manager.device),
        "architecture": "BolusEstimationNetwork with Attention"
    }