# app/models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class GlucoseReadingCreate(BaseModel):
    patient_id: str
    timestamp: datetime
    value: float = Field(..., ge=2.0, le=25.0)

    @validator('value')
    def validate_glucose(cls, v):
        if not 2.0 <= v <= 25.0:
            raise ValueError('Glucosa debe estar entre 2.0 y 25.0 mmol/L')
        return v

class GlucoseReadingBulk(BaseModel):
    patient_id: str
    readings: List[Dict[str, Any]]

class PatientCreate(BaseModel):
    id: str
    name: str
    age: int = Field(..., ge=1, le=120)
    diabetes_type: str = Field(..., pattern="^(Type 1|Type 2)$")
    diagnosis_date: datetime

class DailyMetricsResponse(BaseModel):
    date: datetime
    mean_glucose: float
    cv: float
    tir: float
    tbr: float
    tar: float
    gmi: float
    n_readings: int

    class Config:
        orm_mode = True

class ClusterInfo(BaseModel):
    cluster_id: int
    cluster_name: str
    confidence_score: float
    assigned_at: datetime
    metrics: Dict[str, float]

class RecommendationLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INFO = "info"

class Recommendation(BaseModel):
    level: RecommendationLevel
    category: str
    title: str
    description: str
    priority: int

class PatientAnalysisResponse(BaseModel):
    patient_id: str
    analysis_date: datetime
    cluster_info: Optional[ClusterInfo]
    current_metrics: DailyMetricsResponse
    recommendations: List[Recommendation]
    trend: str
    risk_score: float

class PredictionRequest(BaseModel):
    glucose_value: float = Field(..., ge=2.0, le=30.0)
    carbs_g: float = Field(..., ge=0.0, le=300.0)
    has_basal_today: bool
    meal_type: str = 'meal_Lunch'
    hour_of_day: Optional[int] = Field(None, ge=0, le=23)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    glucose_minutes_before: float = Field(10.0, ge=0.0, le=120.0)

    @validator('meal_type')
    def validate_meal_type(cls, v):
        valid_meals = ['meal_Breakfast', 'meal_Lunch', 'meal_Dinner', 'meal_Snack', 'meal_Pre-meal', 'meal_Post-meal', 'meal_Dinner', 'meal_Supper']
        if v not in valid_meals:
            raise ValueError(f'meal_type debe ser uno de: {valid_meals}')
        return v

class PredictionResponse(BaseModel):
    predicted_dose: float
    confidence: str
    input_summary: dict
    warnings: List[str]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    timestamp: str

# ============================================================================
# SCHEMAS PARA PREDICCIÓN DE GLUCOSA (LSTM)
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


class GlucosePredictionRequest(BaseModel):
    """Request para hacer predicción de glucosa"""
    historical_data: List[GlucoseReading] = Field(..., min_items=12, max_items=12, 
                                                   description="Últimas 12 lecturas (60 min)")
    user_inputs: List[UserInput] = Field(..., min_items=1, max_items=24,
                                          description="Inputs del usuario para cada paso futuro")
    n_steps: int = Field(default=12, ge=1, le=24, description="Número de pasos a predecir (5 min cada uno)")


class GlucosePredictionResponse(BaseModel):
    """Response con las predicciones de glucosa"""
    predictions: List[float] = Field(..., description="Predicciones de glucosa en mg/dL")
    timestamps: List[str] = Field(..., description="Timestamps de cada predicción")
    alerts: List[dict] = Field(..., description="Alertas de hipo/hiperglucemia")
    summary: dict = Field(..., description="Resumen de la predicción")

# ============================================================================
# SCHEMAS PARA GESTIÓN DE ALIMENTOS
# ============================================================================

class Alimento(BaseModel):
    """Modelo para representar un alimento con información nutricional"""
    id: int
    alimento: str
    plato_base: Optional[str] = None
    imagen: Optional[str] = None
    cantidad_sugerida: Optional[float] = None
    unidad: Optional[str] = None
    peso_bruto: Optional[float] = None
    peso_neto: Optional[float] = None
    energia_kcal: Optional[float] = None
    proteina: Optional[float] = None
    lipidos: Optional[float] = None
    hidratos_carbono: Optional[float] = None


class AlimentoSeleccionado(BaseModel):
    """Modelo para alimentos seleccionados por el paciente"""
    categoria: str
    id_alimento: int
    nombre_alimento: str
    hidratos_carbono: float


class ResumenCarbohidratos(BaseModel):
    """Modelo para el resumen de carbohidratos totales"""
    alimentos_seleccionados: List[AlimentoSeleccionado]
    total_carbohidratos: float