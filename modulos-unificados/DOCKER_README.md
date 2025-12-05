# Docker Setup - API Unificada de Diabetes

## 📋 Requisitos Previos

- Docker Desktop instalado ([Descargar aquí](https://www.docker.com/products/docker-desktop))
- Docker Compose (incluido en Docker Desktop)

## 🚀 Inicio Rápido

### 1. Construir y ejecutar todos los servicios

```bash
# Desde el directorio modulos-unificados/
docker-compose up --build
```

### 2. Acceder a la aplicación

- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **MySQL**: localhost:3306

## 🛠️ Comandos Útiles

### Ejecutar en segundo plano (detached mode)
```bash
docker-compose up -d
```

### Ver logs
```bash
# Todos los servicios
docker-compose logs -f

# Solo la API
docker-compose logs -f api

# Solo PostgreSQL
docker-compose logs -f postgres
```

### Detener servicios
```bash
docker-compose down
```

### Detener y eliminar volúmenes (⚠️ elimina datos)
```bash
docker-compose down -v
```

### Reconstruir solo la API
```bash
docker-compose up --build api
```

### Ejecutar comandos dentro del contenedor
```bash
# Acceder al shell de la API
docker exec -it diabetes-api bash

# Acceder a PostgreSQL
docker exec -it diabetes-postgres psql -U diabetes_user -d glucose_db

# Acceder a MySQL
docker exec -it diabetes-mysql mysql -u alimentos_user -palimentos_password alimentos_db
```

## 📦 Estructura de Servicios

### API (FastAPI)
- **Puerto**: 8000
- **Imagen**: Construida desde Dockerfile local
- **Variables de entorno**: Configuradas en docker-compose.yml

### PostgreSQL
- **Puerto**: 5432
- **Base de datos**: glucose_db
- **Usuario**: diabetes_user
- **Password**: diabetes_password
- **Inicialización**: `init_glucose.sql`

### MySQL
- **Puerto**: 3306
- **Base de datos**: alimentos_db
- **Usuario**: alimentos_user
- **Password**: alimentos_password
- **Inicialización**: `init.sql` y `agregar_datos.sql`

## 🔧 Configuración Avanzada

### Usar Ollama para el Chatbot

1. Descomentar el servicio `ollama` en `docker-compose.yml`
2. Descomentar la variable `OLLAMA_HOST` en el servicio `api`
3. Reiniciar los servicios:

```bash
docker-compose down
docker-compose up -d
```

4. Descargar el modelo LLaMA:
```bash
docker exec -it diabetes-ollama ollama pull llama3.2
```

### Hot Reload para Desarrollo

Descomentar en `docker-compose.yml` la línea:
```yaml
volumes:
  - ./app:/app
```

Y modificar el comando de la API para usar `--reload`:
```yaml
command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Cambiar Puertos

Edita el `docker-compose.yml` y cambia el mapeo de puertos:
```yaml
ports:
  - "PUERTO_HOST:PUERTO_CONTENEDOR"
```

## 🔐 Seguridad en Producción

⚠️ **IMPORTANTE**: Antes de desplegar en producción:

1. Cambia todas las contraseñas en `docker-compose.yml`
2. Genera una `SECRET_KEY` segura
3. Configura `ALLOWED_ORIGINS` con dominios específicos
4. Establece `DEBUG: "False"`
5. Usa variables de entorno en lugar de hardcodear valores sensibles

Ejemplo usando `.env`:
```bash
# Crear archivo .env
cat > .env << EOF
POSTGRES_PASSWORD=secure_password_here
MYSQL_PASSWORD=another_secure_password
SECRET_KEY=$(openssl rand -hex 32)
EOF

# Referenciar en docker-compose.yml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

## 📊 Verificar Estado de Servicios

```bash
# Ver servicios en ejecución
docker-compose ps

# Verificar health checks
docker inspect diabetes-postgres | grep -A 10 Health
docker inspect diabetes-mysql | grep -A 10 Health
```

## 🐛 Troubleshooting

### La API no puede conectarse a las bases de datos

Verifica que los health checks estén pasando:
```bash
docker-compose ps
```

### Error de permisos en volúmenes

```bash
sudo chown -R $USER:$USER postgres_data mysql_data
```

### Puertos ya en uso

Cambia los puertos en `docker-compose.yml` o detén los servicios que usan esos puertos:
```bash
# Ver qué usa el puerto 8000
sudo lsof -i :8000
```

### Reconstruir desde cero

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## 📝 Notas

- Los datos persisten en volúmenes Docker (`postgres_data`, `mysql_data`)
- El directorio `app/documents` se monta para el chatbot
- Los modelos de ML (`.pth`) se copian dentro de la imagen
- Los archivos de inicialización SQL se ejecutan automáticamente

## 🤝 Desarrollo en Equipo

Para compartir la configuración:

1. Commitea: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
2. NO commitees: archivos `.env` con credenciales reales
3. Sí commitea: `.env.example` con valores de ejemplo
