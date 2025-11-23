"""
Servicio para el chatbot educativo de diabetes usando Ollama
"""

import ollama
import PyPDF2
from typing import Dict, List, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ChatbotManager:
    """Gestor del chatbot educativo de diabetes"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
        self.pdf_context: str = ""
        self.pdf_loaded: bool = False
        self.model_name: str = "llama3.2:3b"
        
        # Ruta al PDF (ajustar según sea necesario)
        self.pdf_path = Path(__file__).parent.parent / "backend" / "documento_diabetes_guia.pdf"
        
        self.system_prompt = """Eres un asistente educativo especializado en diabetes. 

IMPORTANTE:
- NO eres médico y NO das diagnósticos médicos
- Recomienda siempre consultar con profesionales de salud para casos específicos
- Proporciona información educativa y general
- Sé empático, claro y amigable
- Si detectas una emergencia médica, indica buscar atención inmediata

Responde de manera clara y concisa en español."""
    
    def load_pdf(self):
        """Carga el PDF cuando se inicializa el servicio"""
        # Intentar múltiples ubicaciones posibles
        possible_paths = [
            self.pdf_path,
            Path(__file__).parent.parent / "documents" / "documento_diabetes_guia.pdf",
            Path(__file__).parent.parent / "data" / "documento_diabetes_guia.pdf",
        ]
        
        pdf_found = None
        for path in possible_paths:
            if path.exists():
                pdf_found = path
                break
        
        if not pdf_found:
            logger.warning(
                f"⚠️  No se encontró el archivo PDF en las ubicaciones esperadas. "
                f"El chatbot funcionará sin contexto del documento."
            )
            return False
        
        try:
            logger.info(f"📄 Cargando PDF: {pdf_found}")
            with open(pdf_found, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_parts.append(f"[Página {page_num + 1}]\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Error en página {page_num + 1}: {e}")
                
                self.pdf_context = "\n\n".join(text_parts)
                
                if self.pdf_context.strip():
                    self.pdf_loaded = True
                    logger.info(f"✅ PDF cargado exitosamente")
                    logger.info(f"   📊 Total páginas: {len(pdf_reader.pages)}")
                    logger.info(f"   📝 Caracteres extraídos: {len(self.pdf_context)}")
                    return True
                else:
                    logger.warning("⚠️  El PDF no contiene texto extraíble")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error al cargar PDF: {e}")
            return False
    
    def create_context_prompt(self, user_message: str) -> str:
        """Crea el prompt con contexto del PDF"""
        if self.pdf_context:
            # Limitar contexto para no sobrepasar límites de tokens
            max_context = 6000  # caracteres
            context = self.pdf_context[:max_context]
            
            if len(self.pdf_context) > max_context:
                context += "\n...(documento continúa)..."
            
            return f"""{self.system_prompt}

DOCUMENTACIÓN DE REFERENCIA:
{context}

Utiliza la información de la documentación anterior cuando sea relevante para responder la pregunta del usuario. Si la información no está en el documento, complementa con tu conocimiento general sobre diabetes."""
        
        return self.system_prompt
    
    async def process_message(self, message: str, conversation_id: str) -> str:
        """
        Procesa un mensaje del usuario y genera respuesta
        
        Args:
            message: Mensaje del usuario
            conversation_id: ID de la conversación
        
        Returns:
            Respuesta del chatbot
        """
        try:
            # Inicializar conversación si no existe
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            # Crear system prompt con contexto
            system_message = self.create_context_prompt(message)
            
            # Preparar mensajes (system + historial + nuevo mensaje)
            messages = [{"role": "system", "content": system_message}]
            
            # Agregar últimos mensajes del historial (máximo 4 mensajes)
            messages.extend(self.conversations[conversation_id][-4:])
            
            # Agregar mensaje actual
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Llamar a Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "num_ctx": 8192,  # Contexto grande para incluir el PDF
                }
            )
            
            assistant_message = response['message']['content']
            
            # Guardar en historial
            self.conversations[conversation_id].append({
                "role": "user",
                "content": message
            })
            self.conversations[conversation_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Mantener solo últimos 8 mensajes en historial
            if len(self.conversations[conversation_id]) > 8:
                self.conversations[conversation_id] = self.conversations[conversation_id][-8:]
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}", exc_info=True)
            raise
    
    def reset_conversation(self, conversation_id: str) -> bool:
        """
        Reinicia una conversación
        
        Args:
            conversation_id: ID de la conversación
        
        Returns:
            True si se encontró y eliminó, False si no existe
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_health_status(self) -> dict:
        """Retorna el estado del servicio"""
        return {
            "status": "online",
            "model": self.model_name,
            "pdf_loaded": self.pdf_loaded,
            "pdf_size": len(self.pdf_context),
            "active_conversations": len(self.conversations)
        }


# Instancia global del gestor del chatbot
chatbot_manager = ChatbotManager()


async def chatbot_startup_event():
    """Evento de startup para cargar el PDF del chatbot"""
    try:
        logger.info("📚 Iniciando servicio de chatbot...")
        chatbot_manager.load_pdf()
        logger.info("✓ Servicio de chatbot listo")
    except Exception as e:
        logger.error(f"Error al inicializar chatbot: {e}")
        # No lanzar excepción para permitir que el servidor inicie
