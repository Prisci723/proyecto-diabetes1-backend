"""
Servicio para el chatbot educativo de diabetes usando LangChain + Ollama
"""

import os
import uuid
import logging
from typing import Dict, List, Optional
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


class ChatbotManager:
    """Gestor del chatbot educativo de diabetes con agentes"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
        self.pdf_chunks: List[str] = []
        self.llm: Optional[ChatOllama] = None
        self.chain = None
        self.pdf_loaded: bool = False
        self.model_name: str = "llama3.2:3b"
        
        # Configurar rutas posibles del PDF
        self.possible_pdf_paths = [
            Path(__file__).parent.parent / "documents" / "documento_diabetes_guia.pdf",
            Path("/app/documents/documento_diabetes_guia.pdf"),
            Path("documents/documento_diabetes_guia.pdf"),
        ]
    
    def es_pregunta_sobre_diabetes(self, pregunta: str) -> bool:
        """
        Verifica si una pregunta está relacionada con diabetes tipo 1.
        """
        pregunta_lower = pregunta.lower()
        
        # Palabras clave relacionadas con diabetes y alimentación para diabéticos
        keywords_diabetes = [
            # Enfermedad
            'diabetes', 'diabético', 'diabética', 'diabéticos', 'diabéticas',
            'prediabetes', 'hiperglucemia', 'hipoglucemia', 'hiperglucemias', 'hipoglucemias',

            # Sustancias y mediciones
            'glucosa', 'glucosas', 'azúcar', 'azucares', 'azucar', 'insulina', 'insulinas',
            'carbohidrato', 'carbohidratos', 'carb', 'carbs', 'ketona', 'cetona', 'cetonas',
            'hba1c', 'hemoglobina', 'hemoglobinas', 'hemoglobina glicosilada',

            # Equipos médicos
            'glucómetro', 'glucometro', 'glucómetros', 'glucometros',
            'sensor', 'sensores',
            'bomba', 'bombas', 'bomba de insulina', 'bombas de insulina',
            'monitor', 'monitores', 'monitoreo', 'monitorización',

            # Órganos y especialistas
            'páncreas', 'pancreas', 'endocrinólogo', 'endocrinologa',
            'endocrinólogos', 'endocrinólogas', 'endocrino', 'endocrinos',

            # Condición clínica
            'cetoacidosis', 'cetoacidosis diabética',
            'resistencia a la insulina',

            # Tipos de diabetes
            'tipo 1', 'tipo I', 't1d', 't1', 'diabetes tipo 1',
            'tipo 2', 'tipo II', 't2d', 't2', 'diabetes tipo 2',
            'gestacional', 'diabetes gestacional',
            'autoimmune', 'autoinmune',

            # Alimentación y comidas
            'desayuno', 'desayunos',
            'almuerzo', 'almuerzos',
            'comida', 'comidas',
            'cena', 'cenas',
            'alimentación', 'alimentaciones',
            'dieta', 'dietas',
            'nutrición', 'nutricional', 'nutricion',
            'hidrato', 'hidratos',
            'snack', 'snacks',
            'alimento', 'alimentos',
            'comer', 'comiendo',
            'menú', 'menu', 'menus',
            'receta', 'recetas',

            # Actividad física
            'ejercicio', 'ejercicios',
            'actividad física', 'actividades físicas',

            # Manejo y tratamiento
            'tratamiento', 'tratamientos',
            'control', 'controles',
            'dosis', 'dosis (plural igual)',
            'inyección', 'inyectarse', 'inyecciones',
            'aplicación de insulina', 'bolo', 'basal',
            'cronómetro', 'registro', 'diario de glucosa',

            # Síntomas
            'síntoma', 'síntomas', 'sintoma', 'sintomas',
            'dolor', 'dolores',
            'sed', 'mucha sed', 'polidipsia',
            'hambre', 'mucha hambre', 'polifagia',
            'cansancio', 'fatiga', 'agotamiento',
            'visión', 'visiones', 'visión borrosa',
            'orina', 'orinar', 'orinas', 'poliuria',
            'náusea', 'náuseas', 'nausea', 'nauseas',
            'vómito', 'vómitos', 'vomito', 'vomitos',
            'pérdida de peso', 'perdida de peso',

            # Otros términos médicos
            'glucógeno', 'glucogeno',
            'metabolismo', 'metabólico', 'metabolico',
            'glucagón', 'glucagon',
            'insulinoresistencia', 'hipo', 'hiper',

            # Recomendaciones
            'recomendar', 'recomendarías', 'recomiendas', 'sugerir', 'sugieres',
            'complicación', 'complicaciones',
            'ayudar', 'ayuda', 'ayudame', 'ayúdame'
        ]

        # Palabras prohibidas MUY ESPECÍFICAS que indican claramente temas NO relacionados
        keywords_prohibidas = [
            # PROGRAMACIÓN Y CÓDIGO
            'python', 'java', 'javascript', 'código fuente', 'programar un',
            'script de', 'algoritmo de búsqueda', 'función lambda',
            'sintaxis de', 'backend api', 'frontend react',

            # MATEMÁTICA PURA
            'ecuación diferencial', 'integral definida', 'derivada parcial',
            'teorema de', 'demostración matemática',

            # DEPORTES PROFESIONALES
            'champions league', 'copa mundial', 'liga española',
            'gol de messi', 'partido de fútbol',

            # CINE / SERIES / MÚSICA
            'película de marvel', 'serie de netflix',
            'canción de', 'álbum de',

            # POLÍTICA
            'elecciones presidenciales', 'partido político',
            'congreso nacional', 'senado de',

            # HISTORIA / GUERRA
            'segunda guerra mundial', 'revolución francesa',
            'batalla de', 'imperio romano'
        ]

        # PRIMERO: Verificar si tiene palabras clave de diabetes (PRIORIDAD ALTA)
        if any(keyword in pregunta_lower for keyword in keywords_diabetes):
            # Si tiene palabras de diabetes, verificar que NO sea un tema prohibido MUY ESPECÍFICO
            if not any(keyword in pregunta_lower for keyword in keywords_prohibidas):
                return True
        
        # SEGUNDO: Verificar contexto de alimentación para diabéticos
        palabras_alimentacion = ['desayuno', 'almuerzo', 'cena', 'merienda', 'comida', 'alimento', 'comer', 'menú', 'receta']
        palabras_contexto_diabetes = ['diabético', 'diabetes', 'diabéticos', 'diabética', 'glucosa', 'azúcar', 'carbohidrato']
        
        tiene_alimentacion = any(palabra in pregunta_lower for palabra in palabras_alimentacion)
        tiene_contexto_diabetes = any(palabra in pregunta_lower for palabra in palabras_contexto_diabetes)
        
        # Si menciona alimentación Y diabetes en la misma pregunta, es válido
        if tiene_alimentacion and tiene_contexto_diabetes:
            return True
        
        # Si menciona "ayudar" o "recomendar" junto con alimentación, asumir contexto diabético
        if tiene_alimentacion and any(palabra in pregunta_lower for palabra in ['ayudar', 'ayuda', 'recomendar', 'sugerir']):
            return True
        
        return True
    
    def buscar_en_pdf(self, query: str) -> str:
        """Busca fragmentos relevantes del PDF usando coincidencia de palabras clave."""
        if not self.pdf_chunks:
            return "El PDF no está cargado."

        query_words = [word.lower() for word in query.split() if len(word) > 2]
        scored = []

        for chunk in self.pdf_chunks:
            chunk_lower = chunk.lower()
            matches = sum(1 for word in query_words if word in chunk_lower)
            if matches > 0:
                score = matches / max(1, len(query_words))
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for score, chunk in scored[:5]]

        if not top_chunks:
            return "No encontré información relevante en el PDF para esta pregunta."

        return "Información relevante del PDF:\n\n" + "\n\n---\n\n".join(top_chunks)
    
    def load_pdf(self):
        """Carga el PDF y crea los chunks"""
        pdf_found = None
        for path in self.possible_pdf_paths:
            if path.exists():
                pdf_found = path
                break
        
        if not pdf_found:
            logger.warning("⚠️  No se encontró el PDF. El bot funcionará sin documento de referencia.")
            return False
        
        try:
            logger.info(f"📄 Cargando PDF: {pdf_found}")
            loader = PyPDFLoader(str(pdf_found))
            docs = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks_docs = splitter.split_documents(docs)
            self.pdf_chunks = [doc.page_content for doc in chunks_docs]

            logger.info(f"✅ PDF cargado: {len(self.pdf_chunks)} fragmentos")
            self.pdf_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al cargar PDF: {str(e)}")
            self.pdf_loaded = False
            return False
    
    def initialize_agent(self):
        """Inicializa el chatbot con LangChain"""
        try:
            # Crear modelo LLM
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=0.3,
                num_ctx=32768,
                repeat_penalty=1.1,
                top_p=0.9
            )
            logger.info(f"✅ Modelo {self.model_name} conectado")
            
            # Crear prompt del chatbot
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres DiaBot, un asistente especializado ÚNICAMENTE en diabetes tipo 1.

ANÁLISIS DE RELEVANCIA - Responde SOLO si la pregunta está relacionada con:
✅ Diabetes tipo 1 directamente
✅ Glucosa, insulina, monitoreo glucémico
✅ Alimentación para diabéticos (dietas, carbohidratos, índice glucémico)
✅ Ejercicio y diabetes
✅ Hipoglucemia o hiperglucemia
✅ Complicaciones de diabetes tipo 1
✅ Manejo diario, conteo de carbohidratos, dosis de insulina
✅ Tecnología para diabetes (bombas, sensores, glucómetros)
✅ Síntomas, diagnóstico, tratamiento de diabetes tipo 1

❌ NO respondas preguntas sobre:
- Programación, matemáticas, ciencia general
- Otros tipos de diabetes (tipo 2, gestacional) a menos que se compare con tipo 1
- Temas médicos no relacionados con diabetes
- Entretenimiento, cultura, tecnología no relacionada con diabetes

REGLAS ESTRICTAS:
1. Si la pregunta NO está relacionada con diabetes tipo 1:
   → Responde EXACTAMENTE: "Lo siento, solo puedo ayudarte con temas de diabetes tipo 1. ¿En qué relacionado con tu diabetes te puedo asistir hoy?"

2. Si SÍ está relacionada con diabetes tipo 1:
   → Responde de forma clara, empática y basada en evidencia
   → Usa la información del contexto proporcionado cuando esté disponible

3. Responsabilidad médica:
   → Nunca des consejos médicos personalizados o dosis específicas
   → Siempre recomienda consultar al médico tratante para decisiones importantes
   → Admite cuando no tienes información suficiente

Responde SIEMPRE en español con un tono profesional, empático y educativo.

{context}"""),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])
            
            # Crear chain
            self.chain = self.prompt | self.llm
            
            logger.info("✅ Chatbot inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al inicializar chatbot: {str(e)}")
            return False
    
    async def process_message(self, message: str, conversation_id: str) -> str:
        """
        Procesa un mensaje del usuario y genera respuesta
        """
        if self.llm is None:
            raise Exception("Chatbot no inicializado")
        
        # Pre-validación
        if not self.es_pregunta_sobre_diabetes(message):
            logger.info(f"❌ Pregunta rechazada (pre-validación): {message[:50]}...")
            return "Lo siento, solo puedo ayudarte con temas de diabetes tipo 1. ¿En qué relacionado con tu diabetes te puedo asistir hoy?"
        
        # Crear o recuperar conversación
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # Construir historial (máx 12 mensajes)
        chat_history = []
        for msg in self.conversations[conversation_id][-12:]:
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            else:
                chat_history.append(AIMessage(content=msg["content"]))
        
        # Buscar información relevante del PDF
        context = ""
        if self.pdf_loaded:
            pdf_info = self.buscar_en_pdf(message)
            context = f"\n\nInformación del documento:\n{pdf_info}\n"
        
        # Ejecutar chain
        try:
            result = self.chain.invoke({
                "input": message,
                "chat_history": chat_history,
                "context": context
            })
            
            # Extraer contenido de la respuesta
            if hasattr(result, 'content'):
                response_text = result.content
            else:
                response_text = str(result)
            
            # Post-validación
            forbidden_keywords = [
                'python', 'programación', 'código', 'suma', 'matemática',
                'fútbol', 'deporte', 'mundial', 'película', 'música',
                'política', 'historia', 'geografía'
            ]
            
            response_lower = response_text.lower()
            is_rejection = "solo puedo ayudarte con temas de diabetes tipo 1" in response_lower
            
            if not is_rejection and any(keyword in response_lower for keyword in forbidden_keywords):
                logger.warning("⚠️ Respuesta fuera de tema detectada. Forzando rechazo.")
                response_text = "Lo siento, solo puedo ayudarte con temas de diabetes tipo 1. ¿En qué relacionado con tu diabetes te puedo asistir hoy?"
            
        except Exception as e:
            logger.error(f"Error en ejecución del chatbot: {str(e)}")
            response_text = "Lo siento, tuve un problema al procesar tu mensaje. ¿Podrías reformular tu pregunta?"
        
        # Guardar en historial
        self.conversations[conversation_id].append({"role": "user", "content": message})
        self.conversations[conversation_id].append({"role": "assistant", "content": response_text})
        
        # Limitar historial
        if len(self.conversations[conversation_id]) > 40:
            self.conversations[conversation_id] = self.conversations[conversation_id][-40:]
        
        return response_text
    
    def reset_conversation(self, conversation_id: str) -> bool:
        """Reinicia una conversación"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_health_status(self) -> dict:
        """Retorna el estado del servicio"""
        return {
            "status": "online" if self.llm is not None else "loading",
            "model": self.model_name,
            "pdf_loaded": self.pdf_loaded,
            "pdf_chunks": len(self.pdf_chunks),
            "active_conversations": len(self.conversations)
        }


# Instancia global
chatbot_manager = ChatbotManager()


async def chatbot_startup_event():
    """Evento de startup para inicializar el chatbot"""
    try:
        logger.info("📚 Iniciando servicio de chatbot...")
        chatbot_manager.load_pdf()
        chatbot_manager.initialize_agent()
        logger.info("✅ Servicio de chatbot listo")
    except Exception as e:
        logger.error(f"❌ Error al inicializar chatbot: {e}")
        raise