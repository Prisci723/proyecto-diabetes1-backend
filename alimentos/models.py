from pydantic import BaseModel
from typing import Optional

class Alimento(BaseModel):
    """Modelo para representar un alimento"""
    id: int
    alimento: str
    plato_base: Optional[str] = None
    imagen: Optional[str] = None
    cantidad_sugerida: Optional[float] = None
    unidad: Optional[str] = None
    peso_bruto: Optional[float] = None
    peso_neto: Optional[float] = None
    energia_kcal: Optional[float] = None
    proteina: Optional[float] = None
    lipidos: Optional[float] = None
    hidratos_carbono: Optional[float] = None

class AlimentoSeleccionado(BaseModel):
    """Modelo para alimentos seleccionados por el paciente"""
    categoria: str
    id_alimento: int
    nombre_alimento: str
    hidratos_carbono: float

class ResumenCarbohidratos(BaseModel):
    """Modelo para el resumen de carbohidratos totales"""
    alimentos_seleccionados: list[AlimentoSeleccionado]
    total_carbohidratos: float