# app/services/prediction.py
import torch
import torch.nn as nn
import numpy as np
from datetime import datetime
import logging
from typing import Optional

from app.models.schemas import PredictionRequest

logger = logging.getLogger(__name__)

class BolusEstimationNetwork(nn.Module):
    def __init__(self, input_dim, hidden_dims=[128, 64, 32], dropout_rate=0.3):
        super(BolusEstimationNetwork, self).__init__()
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[0]),
            nn.BatchNorm1d(hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        self.attention = nn.Sequential(
            nn.Linear(hidden_dims[0], hidden_dims[0] // 2),
            nn.Tanh(),
            nn.Linear(hidden_dims[0] // 2, hidden_dims[0]),
            nn.Softmax(dim=1)
        )
        self.hidden1 = nn.Sequential(
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.BatchNorm1d(hidden_dims[1]),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        self.hidden2 = nn.Sequential(
            nn.Linear(hidden_dims[1], hidden_dims[2]),
            nn.BatchNorm1d(hidden_dims[2]),
            nn.ReLU(),
            nn.Dropout(dropout_rate / 2)
        )
        self.residual_proj = nn.Linear(hidden_dims[0], hidden_dims[2])
        self.output = nn.Sequential(
            nn.Linear(hidden_dims[2], 16),
            nn.ReLU(),
            nn.Linear(16, 1)
        )

    def forward(self, x):
        features = self.feature_extractor(x)
        attention_weights = self.attention(features)
        attended_features = features * attention_weights
        h1 = self.hidden1(attended_features)
        h2 = self.hidden2(h1)
        residual = self.residual_proj(attended_features)
        h2 = h2 + residual
        output = self.output(h2)
        return output.squeeze()

class ModelManager:
    def __init__(self, model_path: str, feature_names_path: Optional[str] = None):
        self.model_path = model_path
        self.feature_names_path = feature_names_path
        self.model = None
        self.feature_names = None
        self.device = torch.device('cpu')
        self.is_loaded = False

    def load_model(self):
        try:
            logger.info(f"Cargando modelo desde: {self.model_path}")
            checkpoint = torch.load(self.model_path, map_location=self.device)
            if 'input_dim' in checkpoint:
                input_dim = checkpoint['input_dim']
            else:
                first_layer_weight = checkpoint['model_state_dict']['feature_extractor.0.weight']
                input_dim = first_layer_weight.shape[1]
            logger.info(f"Dimensión de entrada: {input_dim}")
            self.model = BolusEstimationNetwork(
                input_dim=input_dim,
                hidden_dims=[128, 64, 32],
                dropout_rate=0.3
            ).to(self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            if 'feature_names' in checkpoint:
                self.feature_names = checkpoint['feature_names']
            elif self.feature_names_path:
                import pickle
                with open(self.feature_names_path, 'rb') as f:
                    self.feature_names = pickle.load(f)
            else:
                logger.warning("No se encontraron nombres de features, generando nombres genéricos")
                self.feature_names = [f'feature_{i}' for i in range(input_dim)]
            self.is_loaded = True
            logger.info("✅ Modelo cargado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {str(e)}")
            raise

    def predict(self, request: PredictionRequest) -> dict:
        if not self.is_loaded:
            raise RuntimeError("Modelo no cargado")
        hour_of_day = request.hour_of_day or datetime.now().hour
        day_of_week = request.day_of_week or datetime.now().weekday()
        feature_dict = {name: 0.0 for name in self.feature_names}
        if 'glucose_value' in feature_dict:
            feature_dict['glucose_value'] = request.glucose_value
        if 'carbs_g' in feature_dict:
            feature_dict['carbs_g'] = request.carbs_g
        if 'has_basal_today' in feature_dict:
            feature_dict['has_basal_today'] = float(request.has_basal_today)
        if 'glucose_minutes_before' in feature_dict:
            feature_dict['glucose_minutes_before'] = request.glucose_minutes_before
        if 'hour_of_day' in feature_dict:
            feature_dict['hour_of_day'] = hour_of_day
        if 'day_of_week' in feature_dict:
            feature_dict['day_of_week'] = day_of_week
        meal_feature_name = f'meal_type_{request.meal_type}'
        warnings = []
        if meal_feature_name in feature_dict:
            feature_dict[meal_feature_name] = 1.0
        else:
            warnings.append(f"Tipo de comida '{request.meal_type}' no reconocido en el modelo")
        feature_array = np.array([[feature_dict[name] for name in self.feature_names]])
        feature_tensor = torch.FloatTensor(feature_array).to(self.device)
        with torch.no_grad():
            prediction = self.model(feature_tensor)
        predicted_dose = prediction.cpu().item()
        if 2.0 <= predicted_dose <= 15.0:
            confidence = "high"
        elif 0.0 <= predicted_dose <= 20.0:
            confidence = "medium"
        else:
            confidence = "low"
            warnings.append("Dosis predicha fuera del rango típico")
        if request.glucose_value < 4.0:
            warnings.append("⚠️ GLUCOSA BAJA - Considere consumir carbohidratos antes de insulina")
        elif request.glucose_value > 15.0:
            warnings.append("⚠️ GLUCOSA ALTA - Considere consultar con profesional médico")
        if request.carbs_g > 150:
            warnings.append("Alto contenido de carbohidratos - Verificar dosis cuidadosamente")
        return {
            "predicted_dose": round(predicted_dose, 2),
            "confidence": confidence,
            "input_summary": {
                "glucose": f"{request.glucose_value} mmol/L",
                "carbs": f"{request.carbs_g} g",
                "basal": "Sí" if request.has_basal_today else "No",
                "meal_type": request.meal_type,
                "time": f"{hour_of_day}:00, día {day_of_week}"
            },
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }

# Instancia global
MODEL_PATH = "/home/priscila/Downloads/bolus_estimation_model.pth"  # Ajusta la ruta según sea necesario
model_manager = ModelManager(model_path=MODEL_PATH)

async def startup_event():
    try:
        model_manager.load_model()
        logger.info("🚀 Modelo de predicción cargado")
    except Exception as e:
        logger.error(f"❌ Error cargando modelo de predicción: {str(e)}")