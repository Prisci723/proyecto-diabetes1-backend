"""
Servicio para predicción de glucosa usando LSTM
"""

import torch
import torch.nn as nn
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import List, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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


class GlucoseModelManager:
    """Gestor del modelo LSTM de predicción de glucosa"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_config = None
        self.device = None
        self.is_loaded = False
        self.model_path = Path("c:/Users/USER/taller/proyecto-diabetes1-backend/glucosa/backend")

    def load_model(self):
        """Cargar modelo, scaler y configuración"""
        try:
            logger.info("Cargando modelo de predicción de glucosa...")
            
            # Detectar device
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Usando device: {self.device}")
            
            # Cargar configuración
            config_path = Path("c:/Users/USER/taller/proyecto-diabetes1-backend/glucosa/backend/model_config.pkl")
            with open(config_path, 'rb') as f:
                self.model_config = pickle.load(f)
            logger.info(f"Configuración cargada: {self.model_config}")
            
            # Cargar scaler
            scaler_path = self.model_path / 'scaler.pkl'
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info("Scaler cargado correctamente")
            
            # Crear y cargar modelo
            self.model = GlucoseLSTM(
                input_size=self.model_config['input_size'],
                hidden_size=self.model_config['hidden_size'],
                num_layers=self.model_config['num_layers'],
                dropout=self.model_config['dropout']
            )

            model_weights_path = Path('c:/Users/USER/taller/proyecto-diabetes1-backend/glucosa/backend/best_glucose_model.pth')
            self.model.load_state_dict(
                torch.load(model_weights_path, map_location=self.device)
            )
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            logger.info("✓ Modelo de glucosa cargado exitosamente")
            
        except Exception as e:
            logger.error(f"Error al cargar modelo de glucosa: {str(e)}")
            self.is_loaded = False
            raise
    
    def add_temporal_features(self, timestamp_str: str) -> dict:
        """Convierte un timestamp en features temporales cíclicos"""
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
    
    def reading_to_features(self, reading) -> np.ndarray:
        """Convierte una lectura de glucosa en vector de features"""
        temporal = self.add_temporal_features(reading.timestamp)
        
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
    
    def predict_next_glucose(self, sequence):
        """Predice el siguiente valor de glucosa"""
        self.model.eval()
        with torch.no_grad():
            sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(self.device)
            prediction = self.model(sequence_tensor).cpu().numpy()
            
            # Manejar dimensiones
            if prediction.ndim == 0:
                prediction = prediction.item()
            else:
                prediction = prediction[0]
            
            # Desnormalizar
            glucose_mean = self.scaler.mean_[0]
            glucose_std = self.scaler.scale_[0]
            prediction_denorm = prediction * glucose_std + glucose_mean
            
        return prediction_denorm
    
    def predict_iterative(self, initial_sequence, user_inputs, n_steps, start_time):
        """Realiza predicción iterativa con timestamps"""
        sequence = initial_sequence.copy()
        predictions = []
        timestamps = []
        
        for step in range(n_steps):
            # Predecir siguiente valor
            next_glucose = self.predict_next_glucose(sequence)
            predictions.append(float(next_glucose))
            
            # Calcular timestamp (cada paso = 5 minutos)
            next_time = start_time + timedelta(minutes=5 * (step + 1))
            timestamps.append(next_time.isoformat())
            
            # Normalizar predicción
            glucose_mean = self.scaler.mean_[0]
            glucose_std = self.scaler.scale_[0]
            next_glucose_norm = (next_glucose - glucose_mean) / glucose_std
            
            # Crear nuevo vector de features
            new_features = sequence[-1].copy()
            new_features[0] = next_glucose_norm
            
            # Aplicar user input si está disponible
            if step < len(user_inputs):
                user_data = user_inputs[step]
                
                # Normalizar carbohidratos
                carbs_norm = (user_data.carbs - self.scaler.mean_[1]) / self.scaler.scale_[1]
                new_features[1] = carbs_norm
                
                # Normalizar bolus
                bolus_norm = (user_data.bolus - self.scaler.mean_[2]) / self.scaler.scale_[2]
                new_features[2] = bolus_norm
                
                # Ejercicio
                if len(new_features) > 9:
                    exercise_int_norm = (user_data.exercise_intensity - self.scaler.mean_[9]) / self.scaler.scale_[9]
                    new_features[9] = exercise_int_norm
                
                if len(new_features) > 10:
                    exercise_dur_norm = (user_data.exercise_duration - self.scaler.mean_[10]) / self.scaler.scale_[10]
                    new_features[10] = exercise_dur_norm
            else:
                # Sin input del usuario: asumir 0
                carbs_norm = (0 - self.scaler.mean_[1]) / self.scaler.scale_[1]
                bolus_norm = (0 - self.scaler.mean_[2]) / self.scaler.scale_[2]
                new_features[1] = carbs_norm
                new_features[2] = bolus_norm
                
                if len(new_features) > 9:
                    new_features[9] = (0 - self.scaler.mean_[9]) / self.scaler.scale_[9]
                if len(new_features) > 10:
                    new_features[10] = (0 - self.scaler.mean_[10]) / self.scaler.scale_[10]
            
            # Actualizar secuencia
            sequence = np.vstack([sequence[1:], new_features])
        
        return predictions, timestamps
    
    def generate_alerts(self, predictions: List[float]) -> List[dict]:
        """Genera alertas basadas en las predicciones"""
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
    
    def predict(self, request):
        """Método principal de predicción"""
        if not self.is_loaded:
            raise Exception("Modelo no cargado")
        
        # Validar que tenemos exactamente 12 lecturas históricas
        if len(request.historical_data) != 12:
            raise ValueError(
                f"Se requieren exactamente 12 lecturas históricas, recibidas: {len(request.historical_data)}"
            )
        
        # Convertir datos históricos a array de features
        historical_features = []
        for reading in request.historical_data:
            features = self.reading_to_features(reading)
            historical_features.append(features)
        
        historical_array = np.array(historical_features)
        logger.info(f"Historical array shape: {historical_array.shape}")
        
        # Normalizar
        historical_normalized = self.scaler.transform(historical_array)
        
        # Obtener timestamp del último dato
        last_timestamp = datetime.fromisoformat(
            request.historical_data[-1].timestamp.replace('Z', '+00:00')
        )
        
        # Hacer predicción iterativa
        predictions, timestamps = self.predict_iterative(
            initial_sequence=historical_normalized,
            user_inputs=request.user_inputs,
            n_steps=request.n_steps,
            start_time=last_timestamp
        )
        
        # Generar alertas
        alerts = self.generate_alerts(predictions)
        
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
        
        return {
            'predictions': [round(p, 1) for p in predictions],
            'timestamps': timestamps,
            'alerts': alerts,
            'summary': summary
        }
    
    def get_model_info(self):
        """Obtener información del modelo"""
        if not self.is_loaded:
            raise Exception("Modelo no cargado")
        
        return {
            "architecture": "LSTM bidireccional",
            "input_features": self.model_config['input_size'],
            "hidden_size": self.model_config['hidden_size'],
            "num_layers": self.model_config['num_layers'],
            "lookback": self.model_config['lookback'],
            "feature_columns": self.model_config['feature_columns'],
            "device": str(self.device),
            "parameters": sum(p.numel() for p in self.model.parameters())
        }


# Instancia global del gestor del modelo
glucose_model_manager = GlucoseModelManager()


async def glucose_startup_event():
    """Evento de startup para cargar el modelo de glucosa"""
    try:
        glucose_model_manager.load_model()
    except Exception as e:
        logger.error(f"Error al cargar modelo de glucosa en startup: {str(e)}")
        # No lanzar excepción para permitir que el servidor inicie
