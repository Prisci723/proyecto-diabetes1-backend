"""
Router para gestión de alimentos y cálculo de carbohidratos
"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from app.models.schemas import Alimento, AlimentoSeleccionado, ResumenCarbohidratos
from app.services.alimentos_service import alimentos_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Categorías de alimentos disponibles
CATEGORIAS = [
    {"id": "verduras", "nombre": "Verduras"},
    {"id": "frutas", "nombre": "Frutas"},
    {"id": "cereales_sin_grasa", "nombre": "Cereales sin Grasa"},
    {"id": "cereales_con_grasa", "nombre": "Cereales con Grasa"},
    {"id": "leguminosas", "nombre": "Leguminosas"},
    {"id": "de_origen_animal", "nombre": "De Origen Animal"},
    {"id": "leche_entera", "nombre": "Leche Entera"},
    {"id": "leche_descremada", "nombre": "Leche Descremada"},
    {"id": "leche_con_azucar", "nombre": "Leche con Azúcar"},
    {"id": "aceites_grasas", "nombre": "Aceites y Grasas"},
    {"id": "azucares", "nombre": "Azúcares"},
    {"id": "platos_preparados", "nombre": "Platos Preparados"}
]


@router.get("/categorias")
async def obtener_categorias():
    """
    Obtener lista de todas las categorías de alimentos disponibles
    
    Returns:
        Lista de categorías con ID y nombre
    """
    return {"categorias": CATEGORIAS}


@router.get("/alimentos/{categoria}", response_model=List[Alimento])
async def obtener_alimentos_por_categoria(categoria: str):
    """
    Obtener todos los alimentos de una categoría específica
    
    Args:
        categoria: Nombre de la categoría (verduras, frutas, etc.)
    
    Returns:
        Lista de alimentos de la categoría con información nutricional
    """
    try:
        alimentos = await alimentos_manager.obtener_alimentos_por_categoria(categoria)
        return alimentos
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener alimentos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener alimentos: {str(e)}")


@router.get("/alimento/{categoria}/{id_alimento}", response_model=Alimento)
async def obtener_alimento_detalle(categoria: str, id_alimento: int):
    """
    Obtener información detallada de un alimento específico
    
    Args:
        categoria: Nombre de la categoría
        id_alimento: ID del alimento
    
    Returns:
        Información completa del alimento incluyendo valores nutricionales
    """
    try:
        alimento = await alimentos_manager.obtener_alimento_detalle(categoria, id_alimento)
        return alimento
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener alimento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener alimento: {str(e)}")


@router.post("/calcular-carbohidratos", response_model=ResumenCarbohidratos)
async def calcular_carbohidratos_totales(alimentos: List[AlimentoSeleccionado]):
    """
    Calcular la suma total de carbohidratos de los alimentos seleccionados
    
    Args:
        alimentos: Lista de alimentos seleccionados por el paciente
    
    Returns:
        Resumen con alimentos seleccionados y total de carbohidratos
    """
    try:
        resumen = alimentos_manager.calcular_carbohidratos(alimentos)
        return resumen
    except Exception as e:
        logger.error(f"Error al calcular carbohidratos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al calcular: {str(e)}")


@router.get("/buscar/{termino}")
async def buscar_alimentos(termino: str, categoria: str = None):
    """
    Buscar alimentos por término en todas las categorías o en una específica
    
    Args:
        termino: Término de búsqueda
        categoria: Categoría específica (opcional)
    
    Returns:
        Lista de alimentos que coinciden con la búsqueda
    """
    try:
        resultados = await alimentos_manager.buscar_alimentos(termino, categoria)
        return {
            "termino": termino,
            "categoria": categoria,
            "total_resultados": len(resultados),
            "resultados": resultados
        }
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


@router.get("/alimentos-stats")
async def obtener_estadisticas():
    """
    Obtener estadísticas generales sobre los alimentos disponibles
    
    Returns:
        Estadísticas de alimentos por categoría
    """
    try:
        stats = await alimentos_manager.obtener_estadisticas()
        return stats
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")
