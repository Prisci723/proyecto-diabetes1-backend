"""
Backend FastAPI para Predicción de Glucosa - Diabetes Tipo 1
Sistema de predicción iterativa de glucosa usando LSTM
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import torch
import torch.nn as nn
import numpy as np
import pickle
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DEFINICIÓN DEL MODELO LSTM (debe ser igual al usado en entrenamiento)
# ============================================================================

class GlucoseLSTM(nn.Module):
    """Modelo LSTM para predicción de glucosa"""
    
    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        super(GlucoseLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)
    
    def forward(self, x):
        lstm_out, (h_n, c_n) = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        last_output = self.dropout(last_output)
        output = self.fc(last_output)
        return output.squeeze()


# ============================================================================
# MODELOS DE DATOS (Pydantic)
# ============================================================================

class GlucoseReading(BaseModel):
    """Una lectura de glucosa con sus features asociados"""
    timestamp: str = Field(..., description="Timestamp en formato ISO (ej: 2024-11-22T15:30:00)")
    glucose: float = Field(..., ge=20, le=600, description="Nivel de glucosa en mg/dL")
    carbs: float = Field(default=0, ge=0, description="Carbohidratos en gramos")
    bolus: float = Field(default=0, ge=0, description="Dosis de insulina en unidades")
    exercise_intensity: float = Field(default=0, ge=0, le=10, description="Intensidad de ejercicio (0-10)")
    exercise_duration: float = Field(default=0, ge=0, description="Duración de ejercicio en minutos")


class UserInput(BaseModel):
    """Input del usuario para un timestep futuro"""
    carbs: float = Field(default=0, ge=0, description="Carbohidratos planificados (g)")
    bolus: float = Field(default=0, ge=0, description="Insulina planificada (U)")
    exercise_intensity: float = Field(default=0, ge=0, le=10, description="Intensidad de ejercicio planificado")
    exercise_duration: float = Field(default=0, ge=0, description="Duración de ejercicio planificado (min)")


class PredictionRequest(BaseModel):
    """Request para hacer predicción"""
    historical_data: List[GlucoseReading] = Field(..., min_items=12, max_items=12, 
                                                   description="Últimas 12 lecturas (60 min)")
    user_inputs: List[UserInput] = Field(..., min_items=1, max_items=24,
                                          description="Inputs del usuario para cada paso futuro")
    n_steps: int = Field(default=12, ge=1, le=24, description="Número de pasos a predecir (5 min cada uno)")


class PredictionResponse(BaseModel):
    """Response con las predicciones"""
    predictions: List[float] = Field(..., description="Predicciones de glucosa en mg/dL")
    timestamps: List[str] = Field(..., description="Timestamps de cada predicción")
    alerts: List[dict] = Field(..., description="Alertas de hipo/hiperglucemia")
    summary: dict = Field(..., description="Resumen de la predicción")


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def add_temporal_features_single(timestamp_str: str) -> dict:
    """
    Convierte un timestamp en features temporales cíclicos
    
    Args:
        timestamp_str: String con timestamp (ej: "2024-11-22T15:30:00")
    
    Returns:
        dict con features temporales
    """
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    
    hour_decimal = dt.hour + dt.minute / 60.0
    
    # Features cíclicos
    hour_sin = np.sin(2 * np.pi * hour_decimal / 24)
    hour_cos = np.cos(2 * np.pi * hour_decimal / 24)
    day_sin = np.sin(2 * np.pi * dt.weekday() / 7)
    day_cos = np.cos(2 * np.pi * dt.weekday() / 7)
    
    # Periodo del día (0-3)
    time_period = dt.hour // 6
    
    # Fin de semana (0 o 1)
    is_weekend = 1 if dt.weekday() >= 5 else 0
    
    return {
        'hour_sin': hour_sin,
        'hour_cos': hour_cos,
        'day_sin': day_sin,
        'day_cos': day_cos,
        'time_period': time_period,
        'is_weekend': is_weekend
    }


def reading_to_features(reading: GlucoseReading) -> np.ndarray:
    """
    Convierte una lectura de glucosa en vector de features
    
    Returns:
        Array de shape (11,) con todos los features
    """
    temporal = add_temporal_features_single(reading.timestamp)
    
    return np.array([
        reading.glucose,
        reading.carbs,
        reading.bolus,
        temporal['hour_sin'],
        temporal['hour_cos'],
        temporal['day_sin'],
        temporal['day_cos'],
        temporal['time_period'],
        temporal['is_weekend'],
        reading.exercise_intensity,
        reading.exercise_duration
    ])


def predict_next_glucose(model, sequence, scaler, device):
    """
    Predice el siguiente valor de glucosa
    
    Args:
        model: Modelo LSTM
        sequence: Secuencia normalizada (lookback, features)
        scaler: StandardScaler
        device: CPU o GPU
    
    Returns:
        Predicción de glucosa desnormalizada (mg/dL)
    """
    model.eval()
    with torch.no_grad():
        sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(device)
        prediction = model(sequence_tensor).cpu().numpy()
        
        # Manejar dimensiones
        if prediction.ndim == 0:
            prediction = prediction.item()
        else:
            prediction = prediction[0]
        
        # Desnormalizar
        glucose_mean = scaler.mean_[0]
        glucose_std = scaler.scale_[0]
        prediction_denorm = prediction * glucose_std + glucose_mean
        
    return prediction_denorm


def predict_iterative_with_timestamps(model, initial_sequence, scaler, device,
                                       user_inputs, n_steps, start_time):
    """
    Realiza predicción iterativa con timestamps
    
    Args:
        model: Modelo LSTM
        initial_sequence: Secuencia inicial normalizada
        scaler: StandardScaler
        device: CPU o GPU
        user_inputs: Lista de UserInput
        n_steps: Número de pasos
        start_time: Datetime del último dato histórico
    
    Returns:
        predictions: Lista de predicciones
        timestamps: Lista de timestamps
    """
    sequence = initial_sequence.copy()
    predictions = []
    timestamps = []
    
    for step in range(n_steps):
        # Predecir siguiente valor
        next_glucose = predict_next_glucose(model, sequence, scaler, device)
        predictions.append(float(next_glucose))
        
        # Calcular timestamp (cada paso = 5 minutos)
        from datetime import timedelta
        next_time = start_time + timedelta(minutes=5 * (step + 1))
        timestamps.append(next_time.isoformat())
        
        # Normalizar predicción
        glucose_mean = scaler.mean_[0]
        glucose_std = scaler.scale_[0]
        next_glucose_norm = (next_glucose - glucose_mean) / glucose_std
        
        # Crear nuevo vector de features
        new_features = sequence[-1].copy()
        new_features[0] = next_glucose_norm
        
        # Aplicar user input si está disponible
        if step < len(user_inputs):
            user_data = user_inputs[step]
            
            # Normalizar carbohidratos
            carbs_norm = (user_data.carbs - scaler.mean_[1]) / scaler.scale_[1]
            new_features[1] = carbs_norm
            
            # Normalizar bolus
            bolus_norm = (user_data.bolus - scaler.mean_[2]) / scaler.scale_[2]
            new_features[2] = bolus_norm
            
            # Ejercicio
            if len(new_features) > 9:
                exercise_int_norm = (user_data.exercise_intensity - scaler.mean_[9]) / scaler.scale_[9]
                new_features[9] = exercise_int_norm
            
            if len(new_features) > 10:
                exercise_dur_norm = (user_data.exercise_duration - scaler.mean_[10]) / scaler.scale_[10]
                new_features[10] = exercise_dur_norm
        else:
            # Sin input del usuario: asumir 0
            carbs_norm = (0 - scaler.mean_[1]) / scaler.scale_[1]
            bolus_norm = (0 - scaler.mean_[2]) / scaler.scale_[2]
            new_features[1] = carbs_norm
            new_features[2] = bolus_norm
            
            if len(new_features) > 9:
                new_features[9] = (0 - scaler.mean_[9]) / scaler.scale_[9]
            if len(new_features) > 10:
                new_features[10] = (0 - scaler.mean_[10]) / scaler.scale_[10]
        
        # Actualizar secuencia
        sequence = np.vstack([sequence[1:], new_features])
    
    return predictions, timestamps


def generate_alerts(predictions: List[float]) -> List[dict]:
    """
    Genera alertas basadas en las predicciones
    
    Args:
        predictions: Lista de predicciones de glucosa
    
    Returns:
        Lista de alertas
    """
    alerts = []
    
    for i, pred in enumerate(predictions):
        minutes = (i + 1) * 5
        
        if pred < 70:
            alerts.append({
                'time': f'+{minutes} min',
                'type': 'HIPOGLUCEMIA',
                'severity': 'CRÍTICO',
                'glucose': round(pred, 1),
                'message': f'¡ALERTA! Glucosa crítica: {pred:.1f} mg/dL. Consume carbohidratos rápidos.'
            })
        elif pred < 80:
            alerts.append({
                'time': f'+{minutes} min',
                'type': 'BAJO',
                'severity': 'ADVERTENCIA',
                'glucose': round(pred, 1),
                'message': f'Glucosa baja: {pred:.1f} mg/dL. Considera consumir carbohidratos.'
            })
        elif pred > 180:
            alerts.append({
                'time': f'+{minutes} min',
                'type': 'HIPERGLUCEMIA',
                'severity': 'ADVERTENCIA',
                'glucose': round(pred, 1),
                'message': f'Glucosa alta: {pred:.1f} mg/dL. Monitorear y considerar corrección.'
            })
        elif pred > 250:
            alerts.append({
                'time': f'+{minutes} min',
                'type': 'HIPERGLUCEMIA',
                'severity': 'CRÍTICO',
                'glucose': round(pred, 1),
                'message': f'¡ALERTA! Glucosa muy alta: {pred:.1f} mg/dL. Aplicar insulina de corrección.'
            })
    
    return alerts


# ============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN
# ============================================================================

app = FastAPI(
    title="API de Predicción de Glucosa",
    description="API para predecir niveles de glucosa usando LSTM",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales para el modelo
model = None
scaler = None
model_config = None
device = None


@app.on_event("startup")
async def load_model():
    """Cargar modelo y scaler al iniciar la aplicación"""
    global model, scaler, model_config, device
    
    try:
        logger.info("Cargando modelo...")
        
        # Detectar device
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Usando device: {device}")
        
        # Cargar configuración
        with open('model_config.pkl', 'rb') as f:
            model_config = pickle.load(f)
        logger.info(f"Configuración cargada: {model_config}")
        
        # Cargar scaler
        with open('scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        logger.info("Scaler cargado correctamente")
        
        # Crear y cargar modelo
        model = GlucoseLSTM(
            input_size=model_config['input_size'],
            hidden_size=model_config['hidden_size'],
            num_layers=model_config['num_layers'],
            dropout=model_config['dropout']
        )
        
        model.load_state_dict(torch.load('best_glucose_model.pth', map_location=device))
        model.to(device)
        model.eval()
        
        logger.info("✓ Modelo cargado exitosamente")
        
    except Exception as e:
        logger.error(f"Error al cargar modelo: {str(e)}")
        raise


# ============================================================================
# ENDPOINTS DE LA API
# ============================================================================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "API de Predicción de Glucosa para Diabetes Tipo 1",
        "version": "1.0.0",
        "status": "activo",
        "model_loaded": model is not None
    }


@app.get("/health")
async def health_check():
    """Verificar estado del servicio"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "device": str(device) if device else None
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_glucose(request: PredictionRequest):
    """
    Endpoint principal para predicción de glucosa
    
    Args:
        request: PredictionRequest con datos históricos y user inputs
    
    Returns:
        PredictionResponse con predicciones y alertas
    """
    try:
        logger.info(f"Recibida solicitud de predicción para {request.n_steps} pasos")
        
        if model is None or scaler is None:
            raise HTTPException(status_code=503, detail="Modelo no cargado")
        
        # Validar que tenemos exactamente 12 lecturas históricas
        if len(request.historical_data) != 12:
            raise HTTPException(
                status_code=400, 
                detail=f"Se requieren exactamente 12 lecturas históricas, recibidas: {len(request.historical_data)}"
            )
        
        # Convertir datos históricos a array de features
        historical_features = []
        for reading in request.historical_data:
            features = reading_to_features(reading)
            historical_features.append(features)
        
        historical_array = np.array(historical_features)
        logger.info(f"Historical array shape: {historical_array.shape}")
        
        # Normalizar
        historical_normalized = scaler.transform(historical_array)
        
        # Obtener timestamp del último dato
        last_timestamp = datetime.fromisoformat(
            request.historical_data[-1].timestamp.replace('Z', '+00:00')
        )
        
        # Hacer predicción iterativa
        predictions, timestamps = predict_iterative_with_timestamps(
            model=model,
            initial_sequence=historical_normalized,
            scaler=scaler,
            device=device,
            user_inputs=request.user_inputs,
            n_steps=request.n_steps,
            start_time=last_timestamp
        )
        
        # Generar alertas
        alerts = generate_alerts(predictions)
        
        # Calcular resumen
        summary = {
            'current_glucose': round(request.historical_data[-1].glucose, 1),
            'final_glucose': round(predictions[-1], 1),
            'change': round(predictions[-1] - request.historical_data[-1].glucose, 1),
            'min_glucose': round(min(predictions), 1),
            'max_glucose': round(max(predictions), 1),
            'avg_glucose': round(np.mean(predictions), 1),
            'trend': 'ascendente' if predictions[-1] > predictions[0] else 'descendente',
            'time_in_range': sum(1 for p in predictions if 70 <= p <= 180) / len(predictions) * 100,
            'risk_level': 'alto' if alerts else 'bajo'
        }
        
        logger.info(f"Predicción completada: {summary}")
        
        return PredictionResponse(
            predictions=[round(p, 1) for p in predictions],
            timestamps=timestamps,
            alerts=alerts,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en predicción: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")


@app.get("/model-info")
async def get_model_info():
    """Obtener información del modelo cargado"""
    if model is None or model_config is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado")
    
    return {
        "architecture": "LSTM bidireccional",
        "input_features": model_config['input_size'],
        "hidden_size": model_config['hidden_size'],
        "num_layers": model_config['num_layers'],
        "lookback": model_config['lookback'],
        "feature_columns": model_config['feature_columns'],
        "device": str(device),
        "parameters": sum(p.numel() for p in model.parameters())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
