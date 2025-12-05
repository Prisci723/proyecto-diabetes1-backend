#!/bin/bash
# Script para verificar dependencias antes de construir Docker

echo "🔍 Verificando compatibilidad de dependencias..."

# Crear entorno virtual temporal
python3 -m venv /tmp/test_env
source /tmp/test_env/bin/activate

# Intentar instalar dependencias
cd "$(dirname "$0")/app"
pip install --upgrade pip > /dev/null 2>&1

echo "📦 Instalando dependencias..."
if pip install -r requirements.txt --dry-run 2>&1 | grep -q "ERROR"; then
    echo "❌ Error: Conflicto de dependencias detectado"
    pip install -r requirements.txt --dry-run
    deactivate
    rm -rf /tmp/test_env
    exit 1
else
    echo "✅ Todas las dependencias son compatibles"
    deactivate
    rm -rf /tmp/test_env
    exit 0
fi
