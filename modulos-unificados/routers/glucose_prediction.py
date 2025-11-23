"""
Router para predicción de glucosa usando LSTM
"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from app.models.schemas import (
    GlucosePredictionRequest, 
    GlucosePredictionResponse,
    GlucoseReading,
    UserInput
)
from app.services.glucose_prediction import glucose_model_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/predict-glucose", response_model=GlucosePredictionResponse)
async def predict_glucose(request: GlucosePredictionRequest):
    """
    Endpoint para predicción iterativa de glucosa usando LSTM
    
    Args:
        request: Datos históricos y user inputs
    
    Returns:
        Predicciones de glucosa con alertas
    """
    try:
        logger.info(f"Recibida solicitud de predicción para {request.n_steps} pasos")
        
        if not glucose_model_manager or not glucose_model_manager.is_loaded:
            raise HTTPException(
                status_code=503, 
                detail="Modelo de glucosa no cargado"
            )
        
        # Realizar predicción
        result = glucose_model_manager.predict(request)
        
        return GlucosePredictionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en predicción de glucosa: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error en predicción: {str(e)}"
        )


@router.get("/glucose-model-info")
async def get_glucose_model_info():
    """Obtener información del modelo LSTM de glucosa"""
    if not glucose_model_manager or not glucose_model_manager.is_loaded:
        raise HTTPException(
            status_code=503, 
            detail="Modelo de glucosa no cargado"
        )
    
    return glucose_model_manager.get_model_info()


@router.get("/glucose-health")
async def glucose_health_check():
    """Verificar estado del servicio de predicción de glucosa"""
    return {
        "status": "healthy",
        "model_loaded": glucose_model_manager.is_loaded if glucose_model_manager else False,
        "device": str(glucose_model_manager.device) if glucose_model_manager and glucose_model_manager.is_loaded else None
    }
