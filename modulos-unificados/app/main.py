# app/main.py
"""
Unified Glucose Monitoring & Prediction API
API completa para monitoreo de diabetes tipo 1
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import logging

from app.database import engine, Base
from app.routers import (
    patients, 
    glucose, 
    analysis, 
    prediction, 
    health, 
    glucose_prediction, 
    chatbot, 
    alimentos,
    users
)
from app.services.prediction import startup_event as insulin_startup
from app.services.glucose_prediction import glucose_startup_event
from app.services.chatbot_service import chatbot_startup_event
from app.services.alimentos_service import alimentos_startup_event

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Unified Glucose Monitoring & Prediction API",
    description="""
    API completa para monitoreo y gestión de diabetes tipo 1.
    
    ## Características principales:
    
    * **Gestión de Pacientes**: Registro y administración de pacientes
    * **Monitoreo de Glucosa**: Registro de lecturas y análisis
    * **Clustering Inteligente**: Clasificación de pacientes según perfil glucémico
    * **Predicción de Insulina**: Recomendaciones de dosis basadas en ML
    * **Predicción de Glucosa**: Pronóstico de niveles futuros
    * **Chatbot Educativo**: Asistente especializado en diabetes tipo 1
    * **Base de Alimentos**: Gestión de carbohidratos y macronutrientes
    
    ## Modelos utilizados:
    
    * KMeans para clustering de perfiles
    * Random Forest para predicción de insulina
    * LSTM/Prophet para predicción de glucosa futura
    * LLaMA 3.2 para chatbot con RAG
    """,
    version="1.0.0",
    contact={
        "name": "Equipo de Desarrollo",
        "email": "support@diabetesapi.com"
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3000",
        # "http://localhost:5173",
        # "http://127.0.0.1:3000",
        # "http://127.0.0.1:5173",
        "*"  # En producción, especificar dominios permitidos
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== INCLUIR ROUTERS ====================

# Gestión de pacientes
app.include_router(
    patients.router,
    prefix="/patients",
    tags=["Patients"],
    responses={404: {"description": "Paciente no encontrado"}}
)

# Lecturas de glucosa
app.include_router(
    glucose.router,
    prefix="/glucose",
    tags=["Glucose"],
    responses={404: {"description": "Recurso no encontrado"}}
)

# Análisis y clustering
app.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis & Clustering"],
    responses={400: {"description": "Datos insuficientes para análisis"}}
)

# Predicción de insulina
app.include_router(
    prediction.router,
    prefix="/prediction",
    tags=["Insulin Prediction"],
    responses={503: {"description": "Modelo no disponible"}}
)

# Predicción de glucosa futura
app.include_router(
    glucose_prediction.router,
    prefix="/glucose-prediction",
    tags=["Glucose Prediction"],
    responses={503: {"description": "Modelo no disponible"}}
)

# Chatbot educativo
app.include_router(
    chatbot.router,
    prefix="/chatbot",
    tags=["Chatbot"],
    responses={500: {"description": "Error en el chatbot"}}
)

# Base de datos de alimentos
app.include_router(
    alimentos.router,
    prefix="/alimentos",
    tags=["Food Database"],
    responses={404: {"description": "Alimento no encontrado"}}
)

# Gestión de usuarios
app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Usuario no encontrado"}}
)

# Health checks y utilidades
app.include_router(
    health.router,
    tags=["Health & Utilities"]
)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)
logger.info("✅ Tablas de base de datos creadas/verificadas")


# ==================== ENDPOINTS RAÍZ ====================

@app.get("/")
async def root():
    """
    Endpoint raíz - Información general de la API
    """
    return {
        "message": "Unified Glucose Monitoring & Prediction API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "documentation": {
            "interactive_docs": "/docs",
            "openapi_schema": "/openapi.json",
            "redoc": "/redoc"
        },
        "endpoints": {
            "patients": {
                "base": "/patients",
                "description": "Gestión de pacientes",
                "methods": ["GET", "POST", "PUT", "DELETE"]
            },
            "glucose": {
                "base": "/glucose",
                "description": "Lecturas de glucosa",
                "methods": ["GET", "POST"]
            },
            "analysis": {
                "base": "/analysis",
                "description": "Análisis y clustering",
                "methods": ["GET"]
            },
            "insulin_prediction": {
                "base": "/prediction",
                "description": "Predicción de dosis de insulina",
                "methods": ["POST"]
            },
            "glucose_prediction": {
                "base": "/glucose-prediction",
                "description": "Predicción de niveles futuros",
                "methods": ["POST"]
            },
            "chatbot": {
                "base": "/chatbot",
                "description": "Chatbot educativo",
                "methods": ["GET", "POST"]
            },
            "alimentos": {
                "base": "/alimentos",
                "description": "Base de datos de alimentos",
                "methods": ["GET", "POST", "PUT", "DELETE"]
            },
            "health": {
                "base": "/health",
                "description": "Estado del sistema",
                "methods": ["GET"]
            }
        },
        "features": [
            "Monitoreo continuo de glucosa",
            "Clustering de perfiles glucémicos",
            "Predicción de dosis de insulina con ML",
            "Predicción de glucosa futura",
            "Chatbot educativo con LLM y RAG",
            "Base de datos de alimentos y carbohidratos",
            "Análisis de métricas clínicas (TIR, CV, GMI)",
            "Recomendaciones personalizadas"
        ],
        "clinical_metrics": [
            "TIR (Time in Range)",
            "CV (Coefficient of Variation)",
            "GMI (Glucose Management Indicator)",
            "TBR (Time Below Range)",
            "TAR (Time Above Range)"
        ]
    }


@app.get("/api-info")
async def api_info():
    """
    Información detallada sobre la API y sus capacidades
    """
    return {
        "api_name": "Unified Glucose Monitoring & Prediction API",
        "version": "1.0.0",
        "description": "Sistema completo para gestión de diabetes tipo 1",
        "technology_stack": {
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "ml_framework": "Scikit-learn",
            "deep_learning": "TensorFlow/PyTorch",
            "llm": "LLaMA 3.2 (Ollama)",
            "clustering": "KMeans",
            "prediction_models": [
                "Random Forest (Insulina)",
                "LSTM/Prophet (Glucosa)"
            ]
        },
        "clinical_standards": {
            "tir_target": ">70%",
            "cv_target": "<36%",
            "tbr_target": "<4%",
            "tar_target": "<25%",
            "glucose_range": "3.9-10.0 mmol/L",
            "severe_hypo": "<3.0 mmol/L",
            "severe_hyper": ">13.9 mmol/L"
        },
        "cluster_profiles": {
            0: "Control Excelente",
            1: "Control Moderado",
            2: "Alta Variabilidad",
            3: "Riesgo Hipoglucemia",
            4: "Control Subóptimo"
        },
        "data_requirements": {
            "daily_metrics": "Mínimo 10 lecturas/día",
            "analysis": "Mínimo 7 días de datos",
            "clustering": "Mínimo 7 días con 10+ lecturas/día"
        }
    }


# ==================== EVENTOS DE STARTUP ====================

@app.on_event("startup")
async def app_startup():
    """
    Evento de inicio: Carga todos los modelos y servicios
    """
    logger.info("=" * 70)
    logger.info("🚀 INICIANDO UNIFIED GLUCOSE MONITORING & PREDICTION API")
    logger.info("=" * 70)
    
    try:
        # 1. Cargar modelo de predicción de insulina
        logger.info("📊 Cargando modelo de predicción de insulina...")
        await insulin_startup()
        
        # 2. Cargar modelo de predicción de glucosa
        logger.info("📈 Cargando modelo de predicción de glucosa...")
        await glucose_startup_event()
        
        # 3. Inicializar chatbot educativo
        logger.info("🤖 Inicializando chatbot educativo...")
        await chatbot_startup_event()
        
        # 4. Cargar base de datos de alimentos
        logger.info("🍽️  Cargando base de datos de alimentos...")
        await alimentos_startup_event()
        
        logger.info("=" * 70)
        logger.info("✅ API LISTA Y OPERACIONAL")
        logger.info("=" * 70)
        logger.info("📚 Documentación interactiva: http://localhost:8000/docs")
        logger.info("🔍 ReDoc: http://localhost:8000/redoc")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"❌ ERROR DURANTE EL INICIO: {e}")
        logger.error("=" * 70)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento de apagado: Limpieza de recursos
    """
    logger.info("=" * 70)
    logger.info("🛑 DETENIENDO API")
    logger.info("=" * 70)
    logger.info("✓ Recursos liberados")
    logger.info("✓ Conexiones cerradas")
    logger.info("=" * 70)


# ==================== MANEJO DE ERRORES GLOBAL ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handler personalizado para 404"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Recurso no encontrado",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "El recurso solicitado no existe",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handler personalizado para errores 500"""
    logger.error(f"Error interno: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detail": "Ha ocurrido un error inesperado. Por favor contacte al administrador.",
            "path": str(request.url)
        }
    )


# ==================== MAIN ====================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Solo para desarrollo
        log_level="info"
    )