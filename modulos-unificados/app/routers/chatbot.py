"""
Router para el chatbot educativo de diabetes usando Ollama
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

from app.services.chatbot_service import chatbot_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """
    Endpoint principal del chatbot educativo de diabetes
    
    Args:
        chat_message: Mensaje del usuario y opcionalmente ID de conversación
    
    Returns:
        Respuesta del chatbot con ID de conversación
    """
    try:
        # Obtener o crear ID de conversación
        conv_id = chat_message.conversation_id or str(uuid.uuid4())
        
        # Procesar mensaje
        response_text = await chatbot_manager.process_message(
            message=chat_message.message,
            conversation_id=conv_id
        )
        
        return ChatResponse(
            response=response_text,
            conversation_id=conv_id
        )
        
    except Exception as e:
        logger.error(f"Error en chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar mensaje: {str(e)}"
        )


@router.post("/reset/{conversation_id}")
async def reset_conversation(conversation_id: str):
    """
    Reinicia una conversación específica
    
    Args:
        conversation_id: ID de la conversación a reiniciar
    
    Returns:
        Mensaje de confirmación
    """
    success = chatbot_manager.reset_conversation(conversation_id)
    
    if success:
        return {
            "message": "Conversación reiniciada",
            "conversation_id": conversation_id
        }
    
    return {
        "message": "Conversación no encontrada",
        "conversation_id": conversation_id
    }


@router.get("/chatbot-health")
async def chatbot_health():
    """Estado del servicio de chatbot"""
    return chatbot_manager.get_health_status()


@router.get("/chatbot-info")
async def chatbot_info():
    """Información del chatbot"""
    return {
        "name": "Chatbot Educativo de Diabetes",
        "version": "1.0",
        "model": chatbot_manager.model_name,
        "pdf_loaded": chatbot_manager.pdf_loaded,
        "features": [
            "Información educativa sobre diabetes",
            "Contexto basado en documentación médica",
            "Conversaciones contextuales",
            "Respuestas empáticas y claras"
        ],
        "disclaimer": "No proporciona diagnósticos médicos. Consulta con profesionales de salud para casos específicos."
    }
