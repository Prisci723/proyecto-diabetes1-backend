# 🚀 Guía de Inicio Rápido - Backend Unificado

## Sistema Completo de Monitoreo y Predicción de Glucosa

Este backend unificado incluye:
- ✅ Monitoreo de glucosa y gestión de pacientes
- ✅ Análisis y clustering de datos
- ✅ Predicción de dosis de insulina
- ✅ Predicción de niveles de glucosa futuros (LSTM)
- ✅ Chatbot educativo sobre diabetes (Ollama + Llama 3.2)
- ✅ Base de datos de alimentos y cálculo de carbohidratos

---

## 📋 Requisitos Previos

### 1. Python 3.8+
```bash
python --version  # Verificar versión
```

### 2. PostgreSQL (para base de datos)
```bash
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
# o
brew install postgresql  # macOS
```

### 3. Ollama (para el chatbot)
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar servicio
ollama serve

# En otra terminal, descargar el modelo
ollama pull llama3.2:3b
```

### 4. MySQL (opcional, para módulo de alimentos)
```bash
sudo apt-get install mysql-server  # Ubuntu/Debian
# o
brew install mysql  # macOS

# Crear base de datos (opcional)
mysql -u root -p
CREATE DATABASE alimentos_db;
```

---

## ⚡ Instalación Rápida

### Paso 1: Clonar e instalar dependencias
```bash
cd "backend-unificado"

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar Base de Datos
```bash
# Crear base de datos PostgreSQL
sudo -u postgres psql
CREATE DATABASE glucose_db;
CREATE USER glucose_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE glucose_db TO glucose_user;
\q

# Crear archivo .env
cat > .env << EOF
DATABASE_URL=postgresql://glucose_user:tu_password@localhost:5432/glucose_db
EOF
```

### Paso 3: Verificar archivos del modelo
```bash
# Verificar que existan los archivos del modelo LSTM
ls -l backend2/
# Debe mostrar:
# - best_glucose_model.pth
# - model_config.pkl
# - scaler.pkl

# Verificar que exista el PDF del chatbot
ls -l documents/
# Debe mostrar:
# - documento_diabetes_guia.pdf
```

### Paso 4: Iniciar el servidor
```bash
# Asegúrate de que Ollama esté corriendo
ollama serve  # En una terminal separada

# Iniciar el servidor FastAPI
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Verificar Instalación

### 1. Verificar que el servidor esté corriendo
```bash
curl http://localhost:8000/
```

Deberías ver:
```json
{
  "message": "Unified Glucose Monitoring & Prediction API",
  "status": "operational",
  "endpoints": {...}
}
```

### 2. Verificar estado de los servicios
```bash
# Estado general
curl http://localhost:8000/health

# Estado del modelo de predicción de insulina
curl http://localhost:8000/prediction/model-info

# Estado del modelo de predicción de glucosa
curl http://localhost:8000/glucose-prediction/glucose-model-info

# Estado del chatbot
curl http://localhost:8000/chatbot/chatbot-health
```

### 3. Probar el chatbot
```bash
curl -X POST http://localhost:8000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es la diabetes tipo 1?"}'
```

---

## 📚 Documentación Interactiva

Una vez que el servidor esté corriendo, visita:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Aquí podrás:
- Ver todos los endpoints disponibles
- Probar las APIs interactivamente
- Ver los esquemas de datos

---

## 🎯 Endpoints Principales

| Servicio | Endpoint | Descripción |
|----------|----------|-------------|
| **General** | `GET /` | Información del sistema |
| **Salud** | `GET /health` | Estado de todos los servicios |
| **Pacientes** | `GET /patients` | Listar pacientes |
| **Pacientes** | `POST /patients` | Crear paciente |
| **Glucosa** | `POST /glucose/readings` | Registrar lecturas |
| **Análisis** | `POST /analysis/patient/{id}` | Analizar paciente |
| **Insulina** | `POST /prediction/` | Predecir dosis de insulina |
| **Glucosa** | `POST /glucose-prediction/predict-glucose` | Predecir glucosa futura |
| **Chatbot** | `POST /chatbot/chat` | Chat educativo |
| **Alimentos** | `GET /alimentos/categorias` | Categorías de alimentos |
| **Alimentos** | `POST /alimentos/calcular-carbohidratos` | Calcular carbohidratos |

---

## 🔧 Configuración Adicional

### Cambiar Puerto
```bash
python -m uvicorn app.main:app --reload --port 8080
```

### Modo Producción (sin reload)
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Variables de Entorno (.env)
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db_name
SECRET_KEY=tu-secreto-aqui
DEBUG=False
OLLAMA_HOST=http://localhost:11434
```

---

## 🐛 Solución de Problemas

### Error: "Model not found" (Chatbot)
```bash
# Descargar el modelo de Ollama
ollama pull llama3.2:3b

# Verificar modelos instalados
ollama list
```

### Error: "Connection refused" (Ollama)
```bash
# Iniciar Ollama
ollama serve
```

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Error de Base de Datos
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar conexión
psql -U glucose_user -d glucose_db -h localhost
```

### Error: "Model file not found" (LSTM)
```bash
# Verificar que los archivos existan
ls -l backend2/best_glucose_model.pth
ls -l backend2/model_config.pkl
ls -l backend2/scaler.pkl
```

### PDF no cargado en el chatbot
```bash
# Verificar que el PDF exista
ls -l documents/documento_diabetes_guia.pdf

# Si no está, cópialo
cp /ruta/al/documento.pdf documents/documento_diabetes_guia.pdf
```

---

## 📖 Documentación Detallada

- **Predicción de Glucosa LSTM**: Ver `GLUCOSE_PREDICTION_README.md`
- **Chatbot Educativo**: Ver `CHATBOT_README.md`
- **API General**: Ver documentación en `/docs` cuando el servidor esté corriendo

---

## 🧪 Ejemplo de Uso Completo

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Verificar estado
health = requests.get(f"{BASE_URL}/health").json()
print("Estado:", health)

# 2. Crear paciente
patient = requests.post(f"{BASE_URL}/patients", json={
    "id": "PAT001",
    "name": "Juan Pérez",
    "age": 35,
    "diabetes_type": "Type 1",
    "diagnosis_date": "2020-01-01T00:00:00"
}).json()

# 3. Registrar lectura de glucosa
reading = requests.post(f"{BASE_URL}/glucose/readings", json={
    "patient_id": "PAT001",
    "timestamp": "2024-11-23T14:30:00",
    "value": 6.5  # mmol/L
}).json()

# 4. Predecir dosis de insulina
insulin_pred = requests.post(f"{BASE_URL}/prediction/", json={
    "glucose_value": 6.5,
    "carbs_g": 60,
    "has_basal_today": True,
    "meal_type": "Lunch"
}).json()

# 5. Preguntar al chatbot
chat_response = requests.post(f"{BASE_URL}/chatbot/chat", json={
    "message": "¿Cómo manejo la hipoglucemia?"
}).json()

print("Respuesta del chatbot:", chat_response['response'])
```

---

## 🚀 Siguiente Pasos

1. ✅ Verificar que todos los servicios estén funcionando
2. ✅ Probar cada endpoint en `/docs`
3. ✅ Integrar con tu frontend
4. ✅ Configurar base de datos de producción
5. ✅ Implementar autenticación y autorización
6. ✅ Configurar logging y monitoreo

---

## 📞 Soporte

Para más información, consulta los archivos README específicos:
- `GLUCOSE_PREDICTION_README.md` - Predicción de glucosa
- `CHATBOT_README.md` - Chatbot educativo
- `ALIMENTOS_README.md` - Gestión de alimentos

---

## ⚠️ Avisos Importantes

- **Desarrollo**: Esta aplicación está en desarrollo
- **Uso Médico**: No usar para diagnósticos o tratamientos sin supervisión médica
- **Seguridad**: Implementar autenticación antes de producción
- **Datos**: Los datos son sensibles, asegurar cumplimiento de normativas (HIPAA, GDPR, etc.)
