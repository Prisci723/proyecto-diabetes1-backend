#!/bin/bash

# ========================================
# Script de utilidades para el backend unificado
# ========================================

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Backend Unificado - Sistema de Diabetes Tipo 1       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Función para verificar servicios
check_services() {
    echo "🔍 Verificando servicios..."
    echo ""
    
    # PostgreSQL
    if command -v psql &> /dev/null; then
        echo "  ✅ PostgreSQL instalado"
    else
        echo "  ❌ PostgreSQL NO instalado"
    fi
    
    # MySQL
    if command -v mysql &> /dev/null; then
        echo "  ✅ MySQL instalado"
    else
        echo "  ⚠️  MySQL NO instalado (opcional)"
    fi
    
    # Ollama
    if command -v ollama &> /dev/null; then
        echo "  ✅ Ollama instalado"
        if ollama list | grep -q "llama3.2:3b"; then
            echo "     ✅ Modelo llama3.2:3b disponible"
        else
            echo "     ❌ Modelo llama3.2:3b NO disponible"
            echo "        Ejecutar: ollama pull llama3.2:3b"
        fi
    else
        echo "  ❌ Ollama NO instalado"
    fi
    
    # Python
    if command -v python3 &> /dev/null; then
        echo "  ✅ Python $(python3 --version | cut -d' ' -f2)"
    else
        echo "  ❌ Python NO instalado"
    fi
    
    echo ""
}

# Función para verificar archivos del modelo
check_model_files() {
    echo "📦 Verificando archivos del modelo..."
    echo ""
    
    if [ -f "backend2/best_glucose_model.pth" ]; then
        echo "  ✅ best_glucose_model.pth"
    else
        echo "  ❌ best_glucose_model.pth NO encontrado"
    fi
    
    if [ -f "backend2/model_config.pkl" ]; then
        echo "  ✅ model_config.pkl"
    else
        echo "  ❌ model_config.pkl NO encontrado"
    fi
    
    if [ -f "backend2/scaler.pkl" ]; then
        echo "  ✅ scaler.pkl"
    else
        echo "  ❌ scaler.pkl NO encontrado"
    fi
    
    if [ -f "documents/documento_diabetes_guia.pdf" ]; then
        echo "  ✅ documento_diabetes_guia.pdf"
    else
        echo "  ⚠️  documento_diabetes_guia.pdf NO encontrado (opcional)"
    fi
    
    echo ""
}

# Función para instalar dependencias
install_deps() {
    echo "📥 Instalando dependencias..."
    pip install -r requirements.txt
    echo "✅ Dependencias instaladas"
    echo ""
}

# Función para iniciar Ollama
start_ollama() {
    echo "🚀 Iniciando Ollama..."
    if command -v ollama &> /dev/null; then
        ollama serve &
        echo "✅ Ollama iniciado en background"
        echo "   PID: $!"
    else
        echo "❌ Ollama no está instalado"
    fi
    echo ""
}

# Función para iniciar el servidor
start_server() {
    echo "🚀 Iniciando servidor FastAPI..."
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Función para verificar salud del sistema
check_health() {
    echo "🏥 Verificando salud del sistema..."
    echo ""
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✅ Servidor respondiendo"
        curl -s http://localhost:8000/health | python -m json.tool
    else
        echo "  ❌ Servidor NO responde"
        echo "     ¿Está el servidor iniciado?"
    fi
    echo ""
}

# Función para mostrar documentación
show_docs() {
    echo "📚 Documentación disponible:"
    echo ""
    ls -1 *.md | sed 's/^/  📄 /'
    echo ""
    echo "Ver en línea: http://localhost:8000/docs"
    echo ""
}

# Menú principal
show_menu() {
    echo "Selecciona una opción:"
    echo ""
    echo "  1) Verificar servicios"
    echo "  2) Verificar archivos del modelo"
    echo "  3) Instalar dependencias"
    echo "  4) Iniciar Ollama"
    echo "  5) Iniciar servidor"
    echo "  6) Verificar salud del sistema"
    echo "  7) Mostrar documentación"
    echo "  8) Todo (verificar + iniciar)"
    echo "  9) Salir"
    echo ""
    read -p "Opción: " option
    
    case $option in
        1) check_services ;;
        2) check_model_files ;;
        3) install_deps ;;
        4) start_ollama ;;
        5) start_server ;;
        6) check_health ;;
        7) show_docs ;;
        8)
            check_services
            check_model_files
            read -p "¿Iniciar Ollama? (s/n): " start_ollama_choice
            if [ "$start_ollama_choice" = "s" ]; then
                start_ollama
                sleep 2
            fi
            start_server
            ;;
        9) exit 0 ;;
        *) echo "Opción inválida" ;;
    esac
}

# Si se ejecuta sin argumentos, mostrar menú
if [ $# -eq 0 ]; then
    show_menu
else
    # Si se pasa argumento, ejecutar directamente
    case $1 in
        check) check_services && check_model_files ;;
        install) install_deps ;;
        start) start_server ;;
        health) check_health ;;
        docs) show_docs ;;
        *) echo "Uso: $0 [check|install|start|health|docs]" ;;
    esac
fi
