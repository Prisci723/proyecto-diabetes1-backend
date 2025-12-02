# Módulo de Gestión de Alimentos - Integración

## Descripción
Se ha integrado un módulo completo de gestión de alimentos con información nutricional detallada, diseñado para ayudar a los pacientes con diabetes tipo 1 a calcular carbohidratos en sus comidas.

## Características

- **Base de Datos de Alimentos**: 12 categorías con información nutricional completa
- **Cálculo de Carbohidratos**: Suma automática de carbohidratos de alimentos seleccionados
- **Búsqueda Inteligente**: Buscar alimentos por nombre en todas las categorías
- **Estadísticas**: Información sobre alimentos disponibles por categoría
- **Datos de Ejemplo**: Funciona con datos de ejemplo si no hay conexión a MySQL

## Categorías de Alimentos

1. **Verduras** - Acelgas, brócoli, espinacas, etc.
2. **Frutas** - Manzanas, plátanos, naranjas, etc.
3. **Cereales sin Grasa** - Arroz, pasta, pan, etc.
4. **Cereales con Grasa** - Galletas, pasteles, etc.
5. **Leguminosas** - Frijoles, lentejas, garbanzos, etc.
6. **De Origen Animal** - Carnes, pescado, huevos, etc.
7. **Leche Entera** - Productos lácteos enteros
8. **Leche Descremada** - Productos lácteos bajos en grasa
9. **Leche con Azúcar** - Yogures azucarados, etc.
10. **Aceites y Grasas** - Aceites, mantequilla, aguacate, etc.
11. **Azúcares** - Azúcar, miel, mermeladas, etc.
12. **Platos Preparados** - Comidas completas

## Requisitos

### Base de Datos MySQL (Opcional)

El módulo puede funcionar de dos formas:

1. **Con MySQL**: Conectado a una base de datos real con información completa
2. **Sin MySQL**: Utiliza datos de ejemplo automáticamente

#### Configuración de MySQL

```bash
# Instalar MySQL
sudo apt-get install mysql-server  # Ubuntu/Debian
# o
brew install mysql  # macOS

# Iniciar MySQL
sudo systemctl start mysql

# Crear base de datos
mysql -u root -p
CREATE DATABASE alimentos_db;
USE alimentos_db;

# Crear tablas (ejemplo para verduras)
CREATE TABLE verduras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    alimento VARCHAR(255) NOT NULL,
    plato_base VARCHAR(255),
    imagen VARCHAR(255),
    cantidad_sugerida FLOAT,
    unidad VARCHAR(50),
    peso_bruto FLOAT,
    peso_neto FLOAT,
    energia_kcal FLOAT,
    proteina FLOAT,
    lipidos FLOAT,
    hidratos_carbono FLOAT
);

# Repetir para cada categoría...
```

#### Variables de Entorno

Crear archivo `.env` con:

```bash
# MySQL (opcional)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=alimentos_db
```

## Nuevos Endpoints

### 1. Obtener Categorías
**GET** `/alimentos/categorias`

Obtiene la lista de todas las categorías de alimentos disponibles.

**Response:**
```json
{
  "categorias": [
    {"id": "verduras", "nombre": "Verduras"},
    {"id": "frutas", "nombre": "Frutas"},
    {"id": "cereales_sin_grasa", "nombre": "Cereales sin Grasa"},
    ...
  ]
}
```

### 2. Obtener Alimentos por Categoría
**GET** `/alimentos/alimentos/{categoria}`

Obtiene todos los alimentos de una categoría específica.

**Ejemplo:**
```bash
GET /alimentos/alimentos/frutas
```

**Response:**
```json
[
  {
    "id": 1,
    "alimento": "Manzana",
    "plato_base": null,
    "imagen": null,
    "cantidad_sugerida": 1.0,
    "unidad": "pieza",
    "peso_bruto": 150.0,
    "peso_neto": 130.0,
    "energia_kcal": 60.0,
    "proteina": 0.0,
    "lipidos": 0.0,
    "hidratos_carbono": 15.0
  },
  ...
]
```

### 3. Obtener Detalle de Alimento
**GET** `/alimentos/alimento/{categoria}/{id_alimento}`

Obtiene información detallada de un alimento específico.

**Ejemplo:**
```bash
GET /alimentos/alimento/frutas/1
```

**Response:**
```json
{
  "id": 1,
  "alimento": "Manzana",
  "cantidad_sugerida": 1.0,
  "unidad": "pieza",
  "hidratos_carbono": 15.0,
  ...
}
```

### 4. Calcular Carbohidratos Totales
**POST** `/alimentos/calcular-carbohidratos`

Calcula el total de carbohidratos de los alimentos seleccionados.

**Request Body:**
```json
{
  "alimentos": [
    {
      "categoria": "frutas",
      "id_alimento": 1,
      "nombre_alimento": "Manzana",
      "hidratos_carbono": 15.0
    },
    {
      "categoria": "cereales_sin_grasa",
      "id_alimento": 1,
      "nombre_alimento": "Arroz blanco cocido",
      "hidratos_carbono": 15.0
    }
  ]
}
```

**Response:**
```json
{
  "alimentos_seleccionados": [
    {
      "categoria": "frutas",
      "id_alimento": 1,
      "nombre_alimento": "Manzana",
      "hidratos_carbono": 15.0
    },
    {
      "categoria": "cereales_sin_grasa",
      "id_alimento": 1,
      "nombre_alimento": "Arroz blanco cocido",
      "hidratos_carbono": 15.0
    }
  ],
  "total_carbohidratos": 30.0
}
```

### 5. Buscar Alimentos
**GET** `/alimentos/buscar/{termino}?categoria={categoria}`

Busca alimentos por término en todas las categorías o en una específica.

**Ejemplo:**
```bash
GET /alimentos/buscar/manzana
GET /alimentos/buscar/arroz?categoria=cereales_sin_grasa
```

**Response:**
```json
{
  "termino": "manzana",
  "categoria": null,
  "total_resultados": 3,
  "resultados": [
    {
      "id": 1,
      "alimento": "Manzana",
      "categoria": "frutas",
      "hidratos_carbono": 15.0,
      ...
    }
  ]
}
```

### 6. Estadísticas de Alimentos
**GET** `/alimentos/alimentos-stats`

Obtiene estadísticas sobre los alimentos disponibles.

**Response:**
```json
{
  "total_categorias": 12,
  "categorias": {
    "verduras": 25,
    "frutas": 30,
    "cereales_sin_grasa": 20,
    ...
  },
  "total_alimentos": 250
}
```

## Estructura de Archivos

```
backend-unificado/
├── routers/
│   └── alimentos.py                # 🆕 Router para endpoints de alimentos
├── services/
│   └── alimentos_service.py        # 🆕 Lógica de gestión de alimentos
├── models/
│   └── schemas.py                  # Schemas actualizados con modelos de alimentos
├── alimentos/                      # Carpeta original (referencia)
│   ├── main_alimentos.py
│   ├── models_alimentos.py
│   └── database_alimentos.py
└── .env.example                    # 🆕 Variables de entorno
```

## Información Nutricional Disponible

Cada alimento incluye:

- **Identificación**: ID, nombre, plato base
- **Porción**: Cantidad sugerida, unidad, peso bruto/neto
- **Macronutrientes**:
  - Energía (kcal)
  - Proteínas (g)
  - Lípidos (g)
  - **Hidratos de Carbono (g)** ← Principal para diabetes

## Ejemplos de Uso

### Flujo Completo: Planificar Comida

```python
import requests

BASE = "http://localhost:8000"

# 1. Obtener categorías disponibles
categorias = requests.get(f"{BASE}/alimentos/categorias").json()
print("Categorías:", categorias)

# 2. Ver frutas disponibles
frutas = requests.get(f"{BASE}/alimentos/alimentos/frutas").json()
print(f"Frutas disponibles: {len(frutas)}")

# 3. Buscar alimentos específicos
resultados = requests.get(f"{BASE}/alimentos/buscar/manzana").json()
print(f"Encontrados: {resultados['total_resultados']} alimentos")

# 4. Seleccionar alimentos para una comida
comida = [
    {
        "categoria": "frutas",
        "id_alimento": 1,
        "nombre_alimento": "Manzana",
        "hidratos_carbono": 15.0
    },
    {
        "categoria": "cereales_sin_grasa",
        "id_alimento": 1,
        "nombre_alimento": "Arroz blanco cocido",
        "hidratos_carbono": 15.0
    },
    {
        "categoria": "de_origen_animal",
        "id_alimento": 5,
        "nombre_alimento": "Pechuga de pollo",
        "hidratos_carbono": 0.0
    }
]

# 5. Calcular carbohidratos totales
resumen = requests.post(
    f"{BASE}/alimentos/calcular-carbohidratos",
    json=comida
).json()

print(f"Total de carbohidratos: {resumen['total_carbohidratos']}g")

# 6. Usar este valor para predecir insulina necesaria
insulina = requests.post(f"{BASE}/prediction/", json={
    "glucose_value": 7.0,
    "carbs_g": resumen['total_carbohidratos'],
    "has_basal_today": True,
    "meal_type": "Lunch"
}).json()

print(f"Dosis de insulina sugerida: {insulina['predicted_dose']} U")
```

### Ejemplo Frontend (JavaScript/React)

```javascript
// Componente para seleccionar alimentos
async function obtenerAlimentosPorCategoria(categoria) {
  const response = await fetch(
    `http://localhost:8000/alimentos/alimentos/${categoria}`
  );
  return await response.json();
}

async function calcularCarbohidratos(alimentosSeleccionados) {
  const response = await fetch(
    'http://localhost:8000/alimentos/calcular-carbohidratos',
    {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(alimentosSeleccionados)
    }
  );
  return await response.json();
}

// Uso
const frutas = await obtenerAlimentosPorCategoria('frutas');
const seleccion = [
  {
    categoria: 'frutas',
    id_alimento: 1,
    nombre_alimento: 'Manzana',
    hidratos_carbono: 15.0
  }
];

const resumen = await calcularCarbohidratos(seleccion);
console.log(`Total: ${resumen.total_carbohidratos}g de carbohidratos`);
```

## Integración con Otros Módulos

### Con Predicción de Insulina

```python
# 1. Calcular carbohidratos de la comida
carbohidratos = calcular_carbohidratos(alimentos_seleccionados)

# 2. Predecir dosis de insulina necesaria
prediction = requests.post("/prediction/", json={
    "glucose_value": glucosa_actual,
    "carbs_g": carbohidratos['total_carbohidratos'],
    "has_basal_today": True,
    "meal_type": "Lunch"
})
```

### Con Predicción de Glucosa

```python
# 1. Calcular carbohidratos planificados
carbohidratos_futuros = calcular_carbohidratos(comida_planificada)

# 2. Predecir cómo afectará la glucosa
glucose_prediction = requests.post("/glucose-prediction/predict-glucose", json={
    "historical_data": ultimas_12_lecturas,
    "user_inputs": [{
        "carbs": carbohidratos_futuros['total_carbohidratos'],
        "bolus": dosis_insulina_planificada,
        "exercise_intensity": 0,
        "exercise_duration": 0
    }] * 12,
    "n_steps": 12
})
```

## Modo Sin Conexión a MySQL

Si no hay conexión a MySQL, el sistema funciona automáticamente con datos de ejemplo:

- ✅ Todos los endpoints funcionan
- ✅ Retorna datos de ejemplo para cada categoría
- ✅ Cálculos de carbohidratos funcionan normalmente
- ⚠️ Datos limitados (2-3 alimentos por categoría)

El sistema detecta automáticamente si MySQL está disponible y se adapta.

## Importar Datos a MySQL

Para poblar la base de datos con datos reales:

```sql
-- Ejemplo: Insertar verduras
INSERT INTO verduras (alimento, cantidad_sugerida, unidad, hidratos_carbono) VALUES
('Acelga cocida', 2.0, 'tazas', 10.8),
('Brócoli cocido', 1.5, 'tazas', 10.2),
('Espinaca cocida', 2.0, 'tazas', 11.0);

-- Ejemplo: Insertar frutas
INSERT INTO frutas (alimento, cantidad_sugerida, unidad, hidratos_carbono) VALUES
('Manzana', 1.0, 'pieza', 15.0),
('Plátano', 0.5, 'pieza', 15.0),
('Naranja', 1.0, 'pieza', 15.0);
```

## Troubleshooting

### Error: "Connection refused" (MySQL)
```bash
# Verificar que MySQL esté corriendo
sudo systemctl status mysql

# Iniciar MySQL
sudo systemctl start mysql
```

### Error: "Database not found"
```bash
# Crear la base de datos
mysql -u root -p -e "CREATE DATABASE alimentos_db;"
```

### El servicio funciona con datos de ejemplo
✅ Esto es normal si MySQL no está configurado
✅ El sistema sigue funcionando correctamente
ℹ️ Para usar datos completos, configura MySQL

## Próximas Mejoras

- [ ] Importar base de datos completa de alimentos mexicanos
- [ ] Agregar imágenes de alimentos
- [ ] Sistema de favoritos por usuario
- [ ] Historial de comidas frecuentes
- [ ] Sugerencias inteligentes basadas en patrones
- [ ] Escaneo de código de barras
- [ ] Calculadora de porciones

## Endpoints del Sistema Completo

| Servicio | Endpoint | Descripción |
|----------|----------|-------------|
| **Alimentos** | `GET /alimentos/categorias` | Listar categorías |
| **Alimentos** | `GET /alimentos/alimentos/{cat}` | Alimentos por categoría |
| **Alimentos** | `GET /alimentos/alimento/{cat}/{id}` | Detalle de alimento |
| **Alimentos** | `POST /alimentos/calcular-carbohidratos` | Calcular carbohidratos |
| **Alimentos** | `GET /alimentos/buscar/{termino}` | Buscar alimentos |
| **Alimentos** | `GET /alimentos/alimentos-stats` | Estadísticas |

---

**¡El módulo de alimentos está listo para usar!** 🍎🥗🍞
