"""
Router para el chatbot educativo de diabetes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

from app.services.chatbot_service import chatbot_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


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
    
    Example:
        ```json
        {
            "message": "¿Qué es la hipoglucemia?",
            "conversation_id": "optional-id"
        }
        ```
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
            "message": "Conversación reiniciada exitosamente",
            "conversation_id": conversation_id
        }
    
    return {
        "message": "La conversación no existía",
        "conversation_id": conversation_id
    }


@router.get("/health")
async def chatbot_health():
    """
    Verifica el estado del servicio de chatbot
    
    Returns:
        Estado actual del servicio incluyendo:
        - status: online/loading
        - model: nombre del modelo
        - pdf_loaded: si el PDF está cargado
        - pdf_chunks: cantidad de fragmentos del PDF
        - active_conversations: conversaciones activas
    """
    return chatbot_manager.get_health_status()


@router.get("/info")
async def chatbot_info():
    """
    Información general del chatbot
    
    Returns:
        Información sobre capacidades y características del chatbot
    """
    return {
        "name": "DiaBot - Chatbot Educativo de Diabetes Tipo 1",
        "version": "2.0",
        "model": chatbot_manager.model_name,
        "pdf_loaded": chatbot_manager.pdf_loaded,
        "features": [
            "Información educativa sobre diabetes tipo 1",
            "Contexto basado en documentación médica oficial",
            "Conversaciones contextuales con memoria",
            "Respuestas empáticas y claras",
            "Validación de relevancia de preguntas",
            "Agente inteligente con LangChain"
        ],
        "capabilities": [
            "Responder preguntas sobre diabetes tipo 1",
            "Explicar conceptos de glucosa, insulina y manejo",
            "Proporcionar información sobre alimentación",
            "Ayudar con dudas sobre ejercicio y diabetes",
            "Explicar síntomas y complicaciones",
            "Informar sobre tecnología para diabetes"
        ],
        "limitations": [
            "Solo responde sobre diabetes tipo 1",
            "No proporciona diagnósticos médicos",
            "No da dosis específicas de medicamentos",
            "Rechaza temas no relacionados con diabetes"
        ],
        "disclaimer": "⚠️ Este chatbot NO reemplaza la consulta médica. No proporciona diagnósticos ni dosis personalizadas. Siempre consulta con tu médico tratante para decisiones importantes sobre tu salud."
    }


@router.get("/stats")
async def chatbot_stats():
    """
    Estadísticas del chatbot
    
    Returns:
        Estadísticas de uso del chatbot
    """
    health = chatbot_manager.get_health_status()
    
    return {
        "active_conversations": health["active_conversations"],
        "total_messages": sum(
            len(conv) for conv in chatbot_manager.conversations.values()
        ),
        "pdf_loaded": health["pdf_loaded"],
        "pdf_chunks": health["pdf_chunks"],
        "model": health["model"],
        "status": health["status"]
    }