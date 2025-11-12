from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import PyPDF2
from typing import Optional
import uuid
import os

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

# Variables globales
conversations = {}
pdf_context = ""
PDF_PATH = "/home/priscila/Datos/Documentos Universidad/Ingeniería en Ciencias de la Computación/8 Octavo semestre/SHC134 Taller De Especialidad/proyecto_modulos/documentos/documento_diabetes_guia.pdf"  # Cambia por la ruta de tu PDF
OLLAMA_MODEL = "llama3.2:3b"

SYSTEM_PROMPT = """Eres un asistente educativo especializado en diabetes. 

IMPORTANTE:
- NO eres médico y NO das diagnósticos médicos
- Recomienda siempre consultar con profesionales de salud para casos específicos
- Proporciona información educativa y general
- Sé empático, claro y amigable
- Si detectas una emergencia médica, indica buscar atención inmediata

Responde de manera clara y concisa en español."""


def load_pdf_on_startup():
    """Carga el PDF cuando se inicia el servidor"""
    global pdf_context
    
    if not os.path.exists(PDF_PATH):
        print(f"⚠️  ADVERTENCIA: No se encontró el archivo {PDF_PATH}")
        print(f"   Coloca tu PDF en la misma carpeta que este script")
        return False
    
    try:
        print(f"📄 Cargando PDF: {PDF_PATH}")
        with open(PDF_PATH, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"[Página {page_num + 1}]\n{page_text}")
                except Exception as e:
                    print(f"⚠️  Error en página {page_num + 1}: {e}")
            
            pdf_context = "\n\n".join(text_parts)
            
            if pdf_context.strip():
                print(f"✅ PDF cargado exitosamente")
                print(f"   📊 Total páginas: {len(pdf_reader.pages)}")
                print(f"   📝 Caracteres extraídos: {len(pdf_context)}")
                return True
            else:
                print("⚠️  El PDF no contiene texto extraíble")
                return False
                
    except Exception as e:
        print(f"❌ Error al cargar PDF: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Se ejecuta al iniciar el servidor"""
    print("\n" + "="*50)
    print("🚀 Iniciando Chatbot de Diabetes")
    print("="*50)
    load_pdf_on_startup()
    print("="*50 + "\n")


def create_context_prompt(user_message):
    """Crea el prompt con contexto del PDF"""
    if pdf_context:
        # Limitar contexto para no sobrepasar límites de tokens
        max_context = 6000  # caracteres
        context = pdf_context[:max_context]
        
        if len(pdf_context) > max_context:
            context += "\n...(documento continúa)..."
        
        return f"""{SYSTEM_PROMPT}

DOCUMENTACIÓN DE REFERENCIA:
{context}

Utiliza la información de la documentación anterior cuando sea relevante para responder la pregunta del usuario. Si la información no está en el documento, complementa con tu conocimiento general sobre diabetes."""
    
    return SYSTEM_PROMPT


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Endpoint principal del chat"""
    try:
        # Obtener o crear ID de conversación
        conv_id = chat_message.conversation_id or str(uuid.uuid4())
        
        # Inicializar conversación si no existe
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        # Crear system prompt con contexto
        system_message = create_context_prompt(chat_message.message)
        
        # Preparar mensajes (system + historial + nuevo mensaje)
        messages = [{"role": "system", "content": system_message}]
        
        # Agregar últimos mensajes del historial (máximo 4 mensajes)
        messages.extend(conversations[conv_id][-4:])
        
        # Agregar mensaje actual
        messages.append({
            "role": "user",
            "content": chat_message.message
        })
        
        # Llamar a Ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={
                "temperature": 0.7,
                "num_ctx": 8192,  # Contexto grande para incluir el PDF
            }
        )
        
        assistant_message = response['message']['content']
        
        # Guardar en historial
        conversations[conv_id].append({
            "role": "user",
            "content": chat_message.message
        })
        conversations[conv_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Mantener solo últimos 8 mensajes en historial
        if len(conversations[conv_id]) > 8:
            conversations[conv_id] = conversations[conv_id][-8:]
        
        return ChatResponse(
            response=assistant_message,
            conversation_id=conv_id
        )
        
    except Exception as e:
        print(f"❌ Error en chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar mensaje: {str(e)}"
        )


@app.post("/reset/{conversation_id}")
async def reset_conversation(conversation_id: str):
    """Reinicia una conversación"""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"message": "Conversación reiniciada", "conversation_id": conversation_id}
    return {"message": "Conversación no encontrada", "conversation_id": conversation_id}


@app.get("/health")
async def health():
    """Estado del servidor"""
    return {
        "status": "online",
        "model": OLLAMA_MODEL,
        "pdf_loaded": bool(pdf_context),
        "pdf_size": len(pdf_context),
        "active_conversations": len(conversations)
    }


@app.get("/")
async def root():
    """Información de la API"""
    return {
        "message": "API Chatbot de Diabetes",
        "version": "1.0",
        "pdf_loaded": bool(pdf_context),
        "endpoints": {
            "chat": "POST /chat",
            "reset": "POST /reset/{conversation_id}",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("  INSTRUCCIONES:")
    print("="*60)
    print(f"  1. Coloca tu PDF en: {os.path.abspath(PDF_PATH)}")
    print("  2. Asegúrate de que Ollama esté corriendo: ollama serve")
    print(f"  3. Verifica que tengas el modelo: ollama pull {OLLAMA_MODEL}")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)