# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import logging

from app.database import engine, Base
from app.routers import patients, glucose, analysis, prediction, health, glucose_prediction, chatbot, alimentos
from app.services.prediction import model_manager, startup_event
from app.services.glucose_prediction import glucose_startup_event
from app.services.chatbot_service import chatbot_startup_event
from app.services.alimentos_service import alimentos_startup_event

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Unified Glucose Monitoring & Prediction API",
    description="API completa para monitoreo de glucosa, clustering, predicción de insulina, predicción de glucosa futura, chatbot educativo y gestión de alimentos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(glucose.router, prefix="/glucose", tags=["Glucose"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(prediction.router, prefix="/prediction", tags=["Prediction"])
app.include_router(glucose_prediction.router, prefix="/glucose-prediction", tags=["Glucose Prediction"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(alimentos.router, prefix="/alimentos", tags=["Alimentos"])
app.include_router(health.router, tags=["Health"])

# Crear tablas en la BD
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {
        "message": "Unified Glucose Monitoring & Prediction API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "patients": "/patients",
            "glucose": "/glucose",
            "analysis": "/analysis",
            "insulin_prediction": "/prediction",
            "glucose_prediction": "/glucose-prediction",
            "chatbot": "/chatbot",
            "alimentos": "/alimentos",
            "health": "/health"
        },
        "features": [
            "Monitoreo de glucosa",
            "Análisis y clustering de datos",
            "Predicción de dosis de insulina",
            "Predicción de niveles de glucosa futuros",
            "Chatbot educativo sobre diabetes",
            "Base de datos de alimentos y cálculo de carbohidratos"
        ]
    }

# Evento de startup para cargar los modelos de predicción
@app.on_event("startup")
async def app_startup():
    logger.info("🚀 Iniciando API unificada...")
    await startup_event()  # Cargar modelo de predicción de insulina
    await glucose_startup_event()  # Cargar modelo de predicción de glucosa
    await chatbot_startup_event()  # Cargar servicio de chatbot
    await alimentos_startup_event()  # Cargar servicio de alimentos
    logger.info("✓ API lista")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 API detenida")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)