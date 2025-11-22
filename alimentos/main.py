from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from models import Alimento, AlimentoSeleccionado, ResumenCarbohidratos
from database import get_db_connection, close_db_connection

app = FastAPI(title="Asistente Inteligente para Diabetes Tipo 1")

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominio exacto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Categorías disponibles
CATEGORIAS = [
    "verduras",
    "frutas",
    "cereales_sin_grasa",
    "cereales_con_grasa",
    "leguminosas",
    "de_origen_animal",
    "leche_entera",
    "leche_descremada",
    "leche_con_azucar",
    "aceites_grasas",
    "azucares",
    "platos_preparados"
]

@app.get("/")
def read_root():
    """Endpoint raíz"""
    return {
        "mensaje": "API del Asistente Inteligente para Diabetes Tipo 1",
        "version": "1.0"
    }

@app.get("/categorias")
def obtener_categorias():
    """Obtener lista de todas las categorías de alimentos"""
    return {
        "categorias": [
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
    }

@app.get("/alimentos/{categoria}", response_model=List[Alimento])
def obtener_alimentos_por_categoria(categoria: str):
    """
    Obtener todos los alimentos de una categoría específica
    
    Args:
        categoria: Nombre de la categoría (verduras, frutas, etc.)
    
    Returns:
        Lista de alimentos de la categoría
    """
    if categoria not in CATEGORIAS:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM {categoria}"
        cursor.execute(query)
        alimentos = cursor.fetchall()
        cursor.close()
        
        return alimentos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener alimentos: {str(e)}")
    finally:
        close_db_connection(connection)

@app.post("/calcular-carbohidratos", response_model=ResumenCarbohidratos)
def calcular_carbohidratos_totales(alimentos: List[AlimentoSeleccionado]):
    """
    Calcular la suma total de carbohidratos de los alimentos seleccionados
    
    Args:
        alimentos: Lista de alimentos seleccionados por el paciente
    
    Returns:
        Resumen con alimentos seleccionados y total de carbohidratos
    """
    total_carbohidratos = sum(alimento.hidratos_carbono for alimento in alimentos)
    
    return ResumenCarbohidratos(
        alimentos_seleccionados=alimentos,
        total_carbohidratos=round(total_carbohidratos, 2)
    )

@app.get("/alimento/{categoria}/{id_alimento}", response_model=Alimento)
def obtener_alimento_detalle(categoria: str, id_alimento: int):
    """
    Obtener información detallada de un alimento específico
    
    Args:
        categoria: Nombre de la categoría
        id_alimento: ID del alimento
    
    Returns:
        Información completa del alimento
    """
    if categoria not in CATEGORIAS:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM {categoria} WHERE id = %s"
        cursor.execute(query, (id_alimento,))
        alimento = cursor.fetchone()
        cursor.close()
        
        if not alimento:
            raise HTTPException(status_code=404, detail="Alimento no encontrado")
        
        return alimento
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener alimento: {str(e)}")
    finally:
        close_db_connection(connection)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)