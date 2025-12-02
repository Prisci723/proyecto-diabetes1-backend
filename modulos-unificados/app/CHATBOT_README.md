# Chatbot Educativo de Diabetes - Integración

## Descripción
Se ha integrado un chatbot educativo especializado en diabetes que utiliza Ollama (Llama 3.2) y documentos PDF como contexto para proporcionar información educativa clara y empática.

## Características

- **Modelo de IA**: Llama 3.2 (3B parámetros) vía Ollama
- **Contexto**: Utiliza documentación PDF sobre diabetes
- **Conversaciones**: Mantiene historial de conversación por usuario
- **Educativo**: Proporciona información general, no diagnósticos médicos
- **Multilingüe**: Responde en español de manera clara y concisa

## Requisitos Previos

### 1. Instalar Ollama

```bash
# En Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar servicio
ollama serve
```

### 2. Descargar el modelo

```bash
ollama pull llama3.2:3b
```

### 3. Instalar dependencias Python

```bash
pip install ollama PyPDF2
```

## Nuevos Endpoints

### 1. Chat con el Bot
**POST** `/chatbot/chat`

Envía un mensaje al chatbot y recibe una respuesta educativa.

**Request Body:**
```json
{
  "message": "¿Qué es la diabetes tipo 1?",
  "conversation_id": "opcional-uuid-para-continuar-conversacion"
}
```

**Response:**
```json
{
  "response": "La diabetes tipo 1 es una condición autoinmune donde el páncreas no produce insulina...",
  "conversation_id": "uuid-de-la-conversacion"
}
```

### 2. Reiniciar Conversación
**POST** `/chatbot/reset/{conversation_id}`

Reinicia una conversación específica, borrando su historial.

**Response:**
```json
{
  "message": "Conversación reiniciada",
  "conversation_id": "uuid-de-la-conversacion"
}
```

### 3. Estado del Chatbot
**GET** `/chatbot/chatbot-health`

Verifica el estado del servicio del chatbot.

**Response:**
```json
{
  "status": "online",
  "model": "llama3.2:3b",
  "pdf_loaded": true,
  "pdf_size": 45230,
  "active_conversations": 5
}
```

### 4. Información del Chatbot
**GET** `/chatbot/chatbot-info`

Obtiene información sobre el chatbot y sus características.

**Response:**
```json
{
  "name": "Chatbot Educativo de Diabetes",
  "version": "1.0",
  "model": "llama3.2:3b",
  "pdf_loaded": true,
  "features": [
    "Información educativa sobre diabetes",
    "Contexto basado en documentación médica",
    "Conversaciones contextuales",
    "Respuestas empáticas y claras"
  ],
  "disclaimer": "No proporciona diagnósticos médicos. Consulta con profesionales de salud para casos específicos."
}
```

## Configuración del Documento PDF

### Ubicación del Documento

El chatbot busca el documento PDF en las siguientes ubicaciones (en orden):

1. `backend/documento_diabetes_guia.pdf`
2. `documents/documento_diabetes_guia.pdf`
3. `data/documento_diabetes_guia.pdf`

### Cómo Agregar el Documento

1. **Opción recomendada**: Coloca tu PDF en la carpeta `documents/`

```bash
cp /ruta/a/tu/documento.pdf documents/documento_diabetes_guia.pdf
```

2. El servidor cargará automáticamente el PDF al iniciar
3. Si no encuentra el PDF, el chatbot funcionará sin contexto adicional

### Personalizar la Ruta

Para usar una ruta diferente, edita `services/chatbot_service.py`:

```python
# En __init__ de ChatbotManager
self.pdf_path = Path("tu/ruta/personalizada/documento.pdf")
```

## Estructura de Archivos

```
backend-unificado/
├── routers/
│   └── chatbot.py                  # Router para endpoints del chatbot
├── services/
│   └── chatbot_service.py          # Lógica del chatbot y manejo de Ollama
├── documents/                      # Carpeta para documentos de referencia
│   ├── README.md
│   └── documento_diabetes_guia.pdf # Tu documento PDF (agregar aquí)
└── backend/                        # Carpeta original (alternativa)
    └── documento_diabetes_guia.pdf
```

## Funcionamiento del Sistema

### 1. Carga del Documento
Al iniciar el servidor:
- Lee el PDF y extrae el texto de cada página
- Almacena el contenido en memoria
- Limita el contexto a 6000 caracteres por consulta

### 2. Procesamiento de Mensajes
Para cada mensaje:
1. Crea un prompt con el system prompt + contexto del PDF
2. Incluye los últimos 4 mensajes del historial
3. Envía todo a Ollama para generar respuesta
4. Guarda el intercambio en el historial
5. Mantiene solo los últimos 8 mensajes por conversación

### 3. Gestión de Conversaciones
- Cada usuario tiene un `conversation_id` único
- El historial se mantiene en memoria
- Las conversaciones se pueden reiniciar individualmente

## System Prompt

El chatbot utiliza el siguiente prompt del sistema:

```
Eres un asistente educativo especializado en diabetes. 

IMPORTANTE:
- NO eres médico y NO das diagnósticos médicos
- Recomienda siempre consultar con profesionales de salud para casos específicos
- Proporciona información educativa y general
- Sé empático, claro y amigable
- Si detectas una emergencia médica, indica buscar atención inmediata

Responde de manera clara y concisa en español.
```

## Ejemplos de Uso

### Ejemplo 1: Primera consulta

```python
import requests

url = "http://localhost:8000/chatbot/chat"

# Primera pregunta
response = requests.post(url, json={
    "message": "¿Qué es la diabetes tipo 1?"
})

data = response.json()
print(f"Respuesta: {data['response']}")
print(f"ID de conversación: {data['conversation_id']}")
```

### Ejemplo 2: Continuar conversación

```python
# Seguir la conversación usando el mismo ID
conv_id = data['conversation_id']

response = requests.post(url, json={
    "message": "¿Cómo se trata?",
    "conversation_id": conv_id
})

print(response.json()['response'])
```

### Ejemplo 3: Reiniciar conversación

```python
# Reiniciar cuando se desee empezar de nuevo
reset_url = f"http://localhost:8000/chatbot/reset/{conv_id}"
response = requests.post(reset_url)
print(response.json())
```

### Ejemplo 4: JavaScript/TypeScript (Frontend)

```javascript
// Iniciar nueva conversación
async function askChatbot(message, conversationId = null) {
  const response = await fetch('http://localhost:8000/chatbot/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      conversation_id: conversationId
    })
  });
  
  return await response.json();
}

// Uso
let result = await askChatbot("¿Qué es la diabetes?");
console.log(result.response);
console.log(result.conversation_id);

// Continuar conversación
result = await askChatbot("¿Cuáles son los síntomas?", result.conversation_id);
console.log(result.response);
```

## Configuración Avanzada

### Cambiar el Modelo

Edita `services/chatbot_service.py`:

```python
self.model_name = "llama3.2:1b"  # Modelo más ligero
# o
self.model_name = "llama3.2:3b"  # Modelo por defecto
# o
self.model_name = "llama3:8b"    # Modelo más grande y preciso
```

### Ajustar Parámetros de Generación

En el método `process_message`:

```python
response = ollama.chat(
    model=self.model_name,
    messages=messages,
    options={
        "temperature": 0.7,      # Creatividad (0.0-1.0)
        "num_ctx": 8192,         # Tamaño del contexto
        "top_p": 0.9,            # Nucleus sampling
        "repeat_penalty": 1.1,   # Penalización por repetición
    }
)
```

### Modificar el System Prompt

Edita `services/chatbot_service.py` en `__init__`:

```python
self.system_prompt = """Tu prompt personalizado aquí..."""
```

## Troubleshooting

### Error: "Connection refused" al llamar a Ollama

```bash
# Asegúrate de que Ollama esté corriendo
ollama serve
```

### Error: "Model not found"

```bash
# Descarga el modelo
ollama pull llama3.2:3b

# Verifica modelos disponibles
ollama list
```

### El chatbot responde sin contexto del PDF

1. Verifica que el PDF exista en alguna de las rutas esperadas
2. Revisa los logs del servidor al iniciar
3. Asegúrate de que el PDF tenga texto extraíble (no sea solo imágenes)

### Respuestas muy lentas

- Usa un modelo más pequeño (`llama3.2:1b`)
- Reduce el `num_ctx` en las opciones
- Considera usar GPU si está disponible

## Endpoints del Sistema Completo

| Endpoint | Descripción |
|----------|-------------|
| `/patients` | Gestión de pacientes |
| `/glucose` | Registros de glucosa |
| `/analysis` | Análisis y clustering |
| `/prediction` | Predicción de insulina |
| `/glucose-prediction` | Predicción de glucosa (LSTM) |
| `/chatbot` | **Chatbot educativo (nuevo)** |
| `/health` | Estado general del sistema |

## Consideraciones de Producción

1. **Memoria**: Cada conversación se mantiene en RAM. Considera implementar persistencia o límites de tiempo.

2. **Escalabilidad**: Ollama corre localmente. Para producción, considera:
   - Redis para almacenar conversaciones
   - Cola de mensajes para procesar requests
   - API key para rate limiting

3. **Seguridad**:
   - Implementar autenticación
   - Validar y sanitizar inputs
   - Rate limiting por usuario

4. **Monitoreo**:
   - Logs de todas las conversaciones
   - Métricas de uso y rendimiento
   - Alertas para errores

## Testing

```bash
# Iniciar el servidor
cd "backend-unificado"
python -m uvicorn app.main:app --reload

# Probar endpoint de salud
curl http://localhost:8000/chatbot/chatbot-health

# Probar chat
curl -X POST http://localhost:8000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es la diabetes?"}'

# Ver documentación interactiva
# http://localhost:8000/docs
```

## Limitaciones y Disclaimers

⚠️ **IMPORTANTE**:
- Este chatbot es **solo educativo**
- **NO** proporciona diagnósticos médicos
- **NO** reemplaza la consulta con profesionales de salud
- Siempre recomienda consultar con médicos para casos específicos
- En emergencias, indica buscar atención médica inmediata

## Próximas Mejoras

- [ ] Persistencia de conversaciones en base de datos
- [ ] Integración con datos del paciente
- [ ] Recomendaciones personalizadas basadas en historial
- [ ] Soporte para múltiples idiomas
- [ ] Análisis de sentimiento en las conversaciones
- [ ] Dashboard de métricas de uso
