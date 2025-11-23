"""
Servicio para gestión de alimentos y cálculo de carbohidratos
"""

import mysql.connector
from mysql.connector import Error
import os
from typing import List, Optional, Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AlimentosManager:
    """Gestor de alimentos y base de datos MySQL"""
    
    def __init__(self):
        self.connection = None
        self.categorias_validas = [
            "verduras", "frutas", "cereales_sin_grasa", "cereales_con_grasa",
            "leguminosas", "de_origen_animal", "leche_entera", "leche_descremada",
            "leche_con_azucar", "aceites_grasas", "azucares", "platos_preparados"
        ]
    
    def conectar(self):
        """Crear conexión a la base de datos MySQL"""
        try:
            # Intentar cargar variables de entorno
            from dotenv import load_dotenv
            load_dotenv()
            
            self.connection = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'alimentos_db')
            )
            
            if self.connection.is_connected():
                logger.info("✓ Conectado a MySQL - Base de datos de alimentos")
                return True
            return False
            
        except Error as e:
            logger.warning(f"No se pudo conectar a MySQL: {e}")
            logger.info("El módulo de alimentos funcionará con datos de ejemplo")
            return False
        except Exception as e:
            logger.warning(f"Error al conectar: {e}")
            return False
    
    def desconectar(self):
        """Cerrar conexión a la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión a MySQL cerrada")
    
    async def obtener_alimentos_por_categoria(self, categoria: str) -> List[Dict]:
        """
        Obtener todos los alimentos de una categoría
        
        Args:
            categoria: Nombre de la categoría
        
        Returns:
            Lista de alimentos
        """
        if categoria not in self.categorias_validas:
            raise ValueError(f"Categoría '{categoria}' no encontrada")
        
        # Si no hay conexión, retornar datos de ejemplo
        if not self.connection or not self.connection.is_connected():
            logger.info(f"Retornando datos de ejemplo para categoría: {categoria}")
            return self._obtener_datos_ejemplo(categoria)
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM {categoria}"
            cursor.execute(query)
            alimentos = cursor.fetchall()
            cursor.close()
            return alimentos
        except Exception as e:
            logger.error(f"Error al consultar BD: {e}")
            return self._obtener_datos_ejemplo(categoria)
    
    async def obtener_alimento_detalle(self, categoria: str, id_alimento: int) -> Dict:
        """
        Obtener información detallada de un alimento específico
        
        Args:
            categoria: Nombre de la categoría
            id_alimento: ID del alimento
        
        Returns:
            Información del alimento
        """
        if categoria not in self.categorias_validas:
            raise ValueError(f"Categoría '{categoria}' no encontrada")
        
        # Si no hay conexión, retornar datos de ejemplo
        if not self.connection or not self.connection.is_connected():
            alimentos = self._obtener_datos_ejemplo(categoria)
            for alimento in alimentos:
                if alimento['id'] == id_alimento:
                    return alimento
            raise ValueError("Alimento no encontrado")
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM {categoria} WHERE id = %s"
            cursor.execute(query, (id_alimento,))
            alimento = cursor.fetchone()
            cursor.close()
            
            if not alimento:
                raise ValueError("Alimento no encontrado")
            
            return alimento
        except Exception as e:
            logger.error(f"Error al consultar BD: {e}")
            raise ValueError("Error al obtener alimento")
    
    def calcular_carbohidratos(self, alimentos_seleccionados: List) -> Dict:
        """
        Calcular el total de carbohidratos de alimentos seleccionados
        
        Args:
            alimentos_seleccionados: Lista de alimentos con carbohidratos
        
        Returns:
            Resumen con total de carbohidratos
        """
        total_carbohidratos = sum(
            float(alimento.hidratos_carbono) for alimento in alimentos_seleccionados
        )
        
        return {
            "alimentos_seleccionados": [
                {
                    "categoria": a.categoria,
                    "id_alimento": a.id_alimento,
                    "nombre_alimento": a.nombre_alimento,
                    "hidratos_carbono": a.hidratos_carbono
                }
                for a in alimentos_seleccionados
            ],
            "total_carbohidratos": round(total_carbohidratos, 2)
        }
    
    async def buscar_alimentos(self, termino: str, categoria: Optional[str] = None) -> List[Dict]:
        """
        Buscar alimentos por término
        
        Args:
            termino: Término de búsqueda
            categoria: Categoría específica (opcional)
        
        Returns:
            Lista de alimentos que coinciden
        """
        categorias_buscar = [categoria] if categoria else self.categorias_validas
        resultados = []
        
        for cat in categorias_buscar:
            try:
                alimentos = await self.obtener_alimentos_por_categoria(cat)
                for alimento in alimentos:
                    if termino.lower() in alimento['alimento'].lower():
                        alimento['categoria'] = cat
                        resultados.append(alimento)
            except Exception as e:
                logger.error(f"Error al buscar en {cat}: {e}")
        
        return resultados
    
    async def obtener_estadisticas(self) -> Dict:
        """
        Obtener estadísticas de alimentos
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            "total_categorias": len(self.categorias_validas),
            "categorias": {},
            "total_alimentos": 0
        }
        
        for categoria in self.categorias_validas:
            try:
                alimentos = await self.obtener_alimentos_por_categoria(categoria)
                count = len(alimentos)
                stats["categorias"][categoria] = count
                stats["total_alimentos"] += count
            except Exception as e:
                logger.error(f"Error al obtener stats de {categoria}: {e}")
                stats["categorias"][categoria] = 0
        
        return stats
    
    def _obtener_datos_ejemplo(self, categoria: str) -> List[Dict]:
        """Retornar datos de ejemplo cuando no hay conexión a BD"""
        datos_ejemplo = {
            "verduras": [
                {
                    "id": 1,
                    "alimento": "Acelga cocida",
                    "plato_base": None,
                    "imagen": None,
                    "cantidad_sugerida": 2.0,
                    "unidad": "tazas",
                    "peso_bruto": 360.0,
                    "peso_neto": 360.0,
                    "energia_kcal": 72.0,
                    "proteina": 7.2,
                    "lipidos": 0.0,
                    "hidratos_carbono": 10.8
                },
                {
                    "id": 2,
                    "alimento": "Brócoli cocido",
                    "plato_base": None,
                    "imagen": None,
                    "cantidad_sugerida": 1.5,
                    "unidad": "tazas",
                    "peso_bruto": 270.0,
                    "peso_neto": 270.0,
                    "energia_kcal": 68.0,
                    "proteina": 6.8,
                    "lipidos": 0.0,
                    "hidratos_carbono": 10.2
                }
            ],
            "frutas": [
                {
                    "id": 1,
                    "alimento": "Manzana",
                    "plato_base": None,
                    "imagen": None,
                    "cantidad_sugerida": 1.0,
                    "unidad": "pieza",
                    "peso_bruto": 150.0,
                    "peso_neto": 130.0,
                    "energia_kcal": 60.0,
                    "proteina": 0.0,
                    "lipidos": 0.0,
                    "hidratos_carbono": 15.0
                },
                {
                    "id": 2,
                    "alimento": "Plátano",
                    "plato_base": None,
                    "imagen": None,
                    "cantidad_sugerida": 0.5,
                    "unidad": "pieza",
                    "peso_bruto": 80.0,
                    "peso_neto": 60.0,
                    "energia_kcal": 60.0,
                    "proteina": 0.0,
                    "lipidos": 0.0,
                    "hidratos_carbono": 15.0
                }
            ],
            "cereales_sin_grasa": [
                {
                    "id": 1,
                    "alimento": "Arroz blanco cocido",
                    "plato_base": None,
                    "imagen": None,
                    "cantidad_sugerida": 0.5,
                    "unidad": "taza",
                    "peso_bruto": 90.0,
                    "peso_neto": 90.0,
                    "energia_kcal": 70.0,
                    "proteina": 2.0,
                    "lipidos": 0.0,
                    "hidratos_carbono": 15.0
                }
            ]
        }
        
        return datos_ejemplo.get(categoria, [])


# Instancia global del gestor de alimentos
alimentos_manager = AlimentosManager()


async def alimentos_startup_event():
    """Evento de startup para conectar a la base de datos de alimentos"""
    try:
        logger.info("🍎 Iniciando servicio de alimentos...")
        alimentos_manager.conectar()
        # No es crítico si falla, funcionará con datos de ejemplo
    except Exception as e:
        logger.warning(f"Servicio de alimentos iniciado con datos de ejemplo: {e}")
