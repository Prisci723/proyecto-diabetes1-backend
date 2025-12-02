# Predicción de Glucosa con LSTM - Integración

## Descripción
Se ha integrado el backend de predicción de glucosa basado en LSTM al sistema principal. Este módulo permite predecir niveles de glucosa futuros usando un modelo LSTM entrenado.

## Nuevos Endpoints

### 1. Predicción de Glucosa
**POST** `/glucose-prediction/predict-glucose`

Realiza predicciones iterativas de niveles de glucosa para los próximos 5-120 minutos (en pasos de 5 minutos).

**Request Body:**
```json
{
  "historical_data": [
    {
      "timestamp": "2024-11-23T14:00:00",
      "glucose": 120.5,
      "carbs": 0,
      "bolus": 0,
      "exercise_intensity": 0,
      "exercise_duration": 0
    },
    // ... 11 lecturas más (total: 12 lecturas = 60 minutos)
  ],
  "user_inputs": [
    {
      "carbs": 50,
      "bolus": 4.5,
      "exercise_intensity": 0,
      "exercise_duration": 0
    },
    // ... más inputs según n_steps
  ],
  "n_steps": 12  // 12 pasos = 60 minutos de predicción
}
```

**Response:**
```json
{
  "predictions": [125.3, 130.1, 135.8, ...],
  "timestamps": ["2024-11-23T14:05:00", "2024-11-23T14:10:00", ...],
  "alerts": [
    {
      "time": "+60 min",
      "type": "HIPERGLUCEMIA",
      "severity": "ADVERTENCIA",
      "glucose": 185.2,
      "message": "Glucosa alta: 185.2 mg/dL. Monitorear y considerar corrección."
    }
  ],
  "summary": {
    "current_glucose": 120.5,
    "final_glucose": 145.8,
    "change": 25.3,
    "min_glucose": 118.2,
    "max_glucose": 185.2,
    "avg_glucose": 142.5,
    "trend": "ascendente",
    "time_in_range": 75.5,
    "risk_level": "bajo"
  }
}
```

### 2. Información del Modelo
**GET** `/glucose-prediction/glucose-model-info`

Retorna información sobre el modelo LSTM cargado.

**Response:**
```json
{
  "architecture": "LSTM bidireccional",
  "input_features": 11,
  "hidden_size": 64,
  "num_layers": 2,
  "lookback": 12,
  "feature_columns": ["glucose", "carbs", "bolus", ...],
  "device": "cpu",
  "parameters": 50432
}
```

### 3. Estado del Servicio
**GET** `/glucose-prediction/glucose-health`

Verifica el estado del servicio de predicción de glucosa.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cpu"
}
```

## Estructura de Archivos Creados

```
backend-unificado/
├── routers/
│   └── glucose_prediction.py          # Nuevo router para predicción de glucosa
├── services/
│   └── glucose_prediction.py          # Lógica del modelo LSTM
├── models/
│   └── schemas.py                     # Schemas actualizados con modelos de glucosa
└── backend2/                          # Archivos del modelo
    ├── best_glucose_model.pth         # Pesos del modelo
    ├── model_config.pkl               # Configuración del modelo
    └── scaler.pkl                     # Scaler para normalización
```

## Features del Modelo

El modelo LSTM utiliza los siguientes features:
1. **glucose**: Nivel de glucosa (mg/dL)
2. **carbs**: Carbohidratos consumidos (g)
3. **bolus**: Dosis de insulina (U)
4. **hour_sin, hour_cos**: Hora del día (cíclico)
5. **day_sin, day_cos**: Día de la semana (cíclico)
6. **time_period**: Período del día (0-3)
7. **is_weekend**: Fin de semana (0/1)
8. **exercise_intensity**: Intensidad del ejercicio (0-10)
9. **exercise_duration**: Duración del ejercicio (min)

## Requisitos de Datos

- **historical_data**: Exactamente 12 lecturas (últimos 60 minutos)
- **user_inputs**: Entre 1 y 24 inputs (5-120 minutos de predicción)
- **n_steps**: Entre 1 y 24 pasos

## Alertas Generadas

El sistema genera alertas automáticas para:
- **HIPOGLUCEMIA CRÍTICA**: < 70 mg/dL
- **GLUCOSA BAJA**: < 80 mg/dL
- **HIPERGLUCEMIA**: > 180 mg/dL
- **HIPERGLUCEMIA CRÍTICA**: > 250 mg/dL

## Uso con el Backend Principal

El servicio está completamente integrado con el backend principal:

```python
# El modelo se carga automáticamente al iniciar el servidor
# Los endpoints están disponibles bajo /glucose-prediction
```

## Endpoints Principales del Sistema

- `/patients` - Gestión de pacientes
- `/glucose` - Registros de glucosa
- `/analysis` - Análisis y clustering
- `/prediction` - Predicción de insulina (modelo anterior)
- `/glucose-prediction` - **Predicción de glucosa (nuevo)**
- `/health` - Estado general del sistema

## Notas Importantes

1. El modelo requiere exactamente 12 lecturas históricas (60 minutos de datos)
2. Cada predicción representa un intervalo de 5 minutos
3. El modelo normaliza automáticamente los datos de entrada
4. Las alertas se generan en base a umbrales clínicos estándar
5. El sistema maneja automáticamente la carga del modelo al iniciar

## Ejemplo de Uso con Python

```python
import requests

url = "http://localhost:8000/glucose-prediction/predict-glucose"

data = {
    "historical_data": [
        {
            "timestamp": f"2024-11-23T14:{i*5:02d}:00",
            "glucose": 120 + i,
            "carbs": 0,
            "bolus": 0,
            "exercise_intensity": 0,
            "exercise_duration": 0
        }
        for i in range(12)
    ],
    "user_inputs": [
        {
            "carbs": 50,
            "bolus": 4.5,
            "exercise_intensity": 0,
            "exercise_duration": 0
        }
    ] * 12,
    "n_steps": 12
}

response = requests.post(url, json=data)
print(response.json())
```

## Testing

Para probar el servicio:

```bash
# Iniciar el servidor
cd "backend-unificado"
python -m uvicorn app.main:app --reload

# Acceder a la documentación interactiva
# http://localhost:8000/docs
```
