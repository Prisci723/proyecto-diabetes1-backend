# 🏥 Backend Unificado - Sistema de Gestión de Diabetes Tipo 1

## 🎯 Descripción General

Sistema completo e integrado para el manejo de diabetes tipo 1 que combina monitoreo de glucosa, predicciones con inteligencia artificial, asistencia educativa y gestión nutricional.

## ✨ Características Principales

### 🩺 Monitoreo y Análisis
- Gestión de pacientes con diabetes tipo 1
- Registro y seguimiento de niveles de glucosa
- Análisis de patrones mediante clustering
- Métricas de control glucémico (TIR, CV, GMI)
- Recomendaciones personalizadas

### 🤖 Inteligencia Artificial
- **Predicción de Insulina**: Modelo ML para calcular dosis de insulina basado en glucosa actual y carbohidratos
- **Predicción de Glucosa**: Modelo LSTM que predice niveles de glucosa futuros (5-120 minutos)
- **Alertas Inteligentes**: Sistema de alertas de hipo/hiperglucemia

### 💬 Asistencia Educativa
- **Chatbot con IA**: Asistente educativo basado en Llama 3.2
- Respuestas contextuales sobre diabetes
- Información basada en documentación médica
- Conversaciones naturales y empáticas

### 🍎 Gestión Nutricional
- Base de datos de alimentos (12 categorías)
- Información nutricional detallada
- Cálculo automático de carbohidratos
- Búsqueda de alimentos
- Integración con predicción de insulina

## 🚀 Inicio Rápido

### Requisitos
- Python 3.8+
- PostgreSQL (base de datos principal)
- Ollama + Llama 3.2 (para chatbot)
- MySQL (opcional, para alimentos)

### Instalación

```bash
# 1. Clonar e instalar dependencias
cd backend-unificado
pip install -r requirements.txt

# 2. Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.2:3b

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 4. Iniciar el servidor
python -m uvicorn app.main:app --reload
```

### Acceso Rápido
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Estado**: http://localhost:8000/health

## 📚 Documentación Detallada

- **[QUICKSTART.md](QUICKSTART.md)** - Guía de inicio paso a paso
- **[GLUCOSE_PREDICTION_README.md](GLUCOSE_PREDICTION_README.md)** - Predicción de glucosa con LSTM
- **[CHATBOT_README.md](CHATBOT_README.md)** - Chatbot educativo
- **[ALIMENTOS_README.md](ALIMENTOS_README.md)** - Gestión de alimentos
- **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Resumen de integración

## 🌐 Endpoints Principales

| Categoría | Endpoint | Descripción |
|-----------|----------|-------------|
| **Sistema** | `GET /` | Información general |
| **Sistema** | `GET /health` | Estado del sistema |
| **Pacientes** | `POST /patients` | Crear paciente |
| **Glucosa** | `POST /glucose/readings` | Registrar lectura |
| **Análisis** | `POST /analysis/patient/{id}` | Analizar paciente |
| **Insulina** | `POST /prediction/` | Predecir dosis |
| **Glucosa** | `POST /glucose-prediction/predict-glucose` | Predecir glucosa |
| **Chatbot** | `POST /chatbot/chat` | Chat educativo |
| **Alimentos** | `GET /alimentos/categorias` | Listar categorías |
| **Alimentos** | `POST /alimentos/calcular-carbohidratos` | Calcular carbohidratos |

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│         Frontend (React/Vue)             │
└──────────────┬──────────────────────────┘
               │ REST API
┌──────────────▼──────────────────────────┐
│      FastAPI Backend Unificado           │
│  ┌────────────────────────────────────┐ │
│  │  Routers (8 módulos)               │ │
│  ├────────────────────────────────────┤ │
│  │  Services (Lógica de negocio)      │ │
│  ├────────────────────────────────────┤ │
│  │  Models (Schemas + DB Models)      │ │
│  └────────────────────────────────────┘ │
└──────┬────────┬────────┬───────┬────────┘
       │        │        │       │
   ┌───▼──┐ ┌──▼───┐ ┌──▼──┐ ┌─▼────┐
   │ Post │ │ LSTM │ │Ollama│ │MySQL │
   │ greSQL│ │Model │ │ LLM  │ │(opt) │
   └──────┘ └──────┘ └──────┘ └──────┘
```

## 📊 Módulos Integrados

### 1️⃣ Módulo de Monitoreo
- Gestión de pacientes
- Registro de glucosa
- Análisis y clustering
- Sistema de recomendaciones

### 2️⃣ Módulo de Predicción de Insulina
- Modelo ML entrenado
- Predicción basada en múltiples factores
- Advertencias de seguridad

### 3️⃣ Módulo de Predicción de Glucosa
- Modelo LSTM para series temporales
- Predicciones iterativas
- Alertas automáticas
- Análisis de tendencias

### 4️⃣ Módulo de Chatbot
- IA con Llama 3.2
- Contexto de documentos médicos
- Conversaciones naturales
- Información educativa

### 5️⃣ Módulo de Alimentos
- 12 categorías de alimentos
- Información nutricional
- Cálculo de carbohidratos
- Búsqueda inteligente

## 🔧 Tecnologías

- **Backend**: FastAPI, Python 3.8+
- **Bases de Datos**: PostgreSQL, MySQL (opcional)
- **ML/AI**: PyTorch, scikit-learn, Ollama
- **IA Generativa**: Llama 3.2 (3B parámetros)
- **Validación**: Pydantic
- **ORM**: SQLAlchemy
- **Documentación**: Swagger/OpenAPI

## 📦 Estructura del Proyecto

```
backend-unificado/
├── main.py                      # Aplicación principal
├── routers/                     # Endpoints organizados
│   ├── patients.py
│   ├── glucose.py
│   ├── analysis.py
│   ├── prediction.py
│   ├── glucose_prediction.py
│   ├── chatbot.py
│   ├── alimentos.py
│   └── health.py
├── services/                    # Lógica de negocio
│   ├── clustering.py
│   ├── metrics.py
│   ├── prediction.py
│   ├── glucose_prediction.py
│   ├── chatbot_service.py
│   └── alimentos_service.py
├── models/                      # Modelos de datos
│   ├── db_models.py
│   └── schemas.py
├── backend2/                    # Modelo LSTM
│   ├── best_glucose_model.pth
│   ├── model_config.pkl
│   └── scaler.pkl
├── documents/                   # Documentos para chatbot
│   └── documento_diabetes_guia.pdf
└── *.md                        # Documentación
```

## 🧪 Testing

```bash
# Verificar estado del sistema
curl http://localhost:8000/health

# Probar chatbot
curl -X POST http://localhost:8000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es la diabetes tipo 1?"}'

# Probar predicción de glucosa
curl -X POST http://localhost:8000/glucose-prediction/predict-glucose \
  -H "Content-Type: application/json" \
  -d @ejemplo_prediccion.json

# Ver documentación interactiva
# Abrir: http://localhost:8000/docs
```

## 🔐 Seguridad

⚠️ **Importante para Producción**:
- [ ] Configurar autenticación JWT
- [ ] Implementar rate limiting
- [ ] Usar HTTPS/TLS
- [ ] Validar todas las entradas
- [ ] Configurar CORS específicos
- [ ] Implementar logging de auditoría
- [ ] Cifrar datos sensibles
- [ ] Backup regular de bases de datos

## ⚠️ Disclaimers

- **Uso Médico**: Este sistema es educativo y de apoyo. NO reemplaza la consulta médica profesional.
- **Diagnósticos**: No proporciona diagnósticos médicos.
- **Tratamiento**: Cualquier ajuste en tratamiento debe ser supervisado por profesionales de salud.
- **Emergencias**: En caso de emergencia médica, contactar servicios de emergencia inmediatamente.

## 📈 Estado del Proyecto

- ✅ Integración completa de 4 backends
- ✅ 8 routers funcionales
- ✅ 30+ endpoints disponibles
- ✅ Documentación completa
- ✅ Modelos ML listos
- ⚠️ En desarrollo - no para uso médico real sin supervisión

## 🤝 Contribuir

Este es un proyecto educativo/académico. Para contribuir:
1. Seguir las mejores prácticas de código
2. Documentar cambios
3. Incluir tests
4. Respetar la estructura del proyecto

## 📞 Soporte

Para dudas sobre el sistema:
- Revisar la documentación en `/docs`
- Consultar archivos README específicos
- Verificar el estado con `/health`

## 📜 Licencia

Proyecto educativo - Taller de Especialidad SHC134

---

**Desarrollado con 💙 para mejorar la calidad de vida de personas con diabetes tipo 1**

🚀 **¡Sistema listo para desarrollo!**
