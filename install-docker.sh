#!/bin/bash

echo "🐳 =============================================="
echo "   INSTALACIÓN DE DOCKER DESKTOP"
echo "=============================================="
echo ""

# Verificar sistema operativo
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ Sistema: macOS detectado"
    echo ""
    
    # Verificar arquitectura
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        echo "💻 Arquitectura: Apple Silicon (M1/M2/M3)"
        URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
    else
        echo "💻 Arquitectura: Intel"
        URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
    fi
    
    echo ""
    echo "📥 Opciones de instalación:"
    echo ""
    echo "OPCIÓN 1: Instalación Automática con Homebrew (Recomendado)"
    echo "   brew install --cask docker"
    echo ""
    echo "OPCIÓN 2: Instalación Manual"
    echo "   1. Visita: https://www.docker.com/products/docker-desktop"
    echo "   2. Descarga Docker Desktop para Mac"
    echo "   3. Arrastra Docker.app a Applications"
    echo "   4. Abre Docker.app"
    echo "   5. Espera a que inicie (icono de ballena en la barra superior)"
    echo ""
    
    # Verificar si Homebrew está instalado
    if command -v brew &> /dev/null; then
        echo "✅ Homebrew detectado"
        echo ""
        read -p "¿Quieres instalar Docker con Homebrew ahora? (s/n): " respuesta
        if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
            echo ""
            echo "📦 Instalando Docker Desktop..."
            brew install --cask docker
            echo ""
            echo "✅ Docker Desktop instalado"
            echo ""
            echo "⚠️  IMPORTANTE: Abre Docker Desktop desde Applications para completar la instalación"
            open -a Docker
        fi
    else
        echo "⚠️  Homebrew no está instalado"
        echo "   Descarga manualmente desde:"
        echo "   👉 https://www.docker.com/products/docker-desktop"
    fi
    
else
    echo "❌ Este script es para macOS"
    echo "   Para Linux: apt-get install docker.io docker-compose"
    echo "   Para Windows: https://www.docker.com/products/docker-desktop"
fi

echo ""
echo "📚 Después de instalar:"
echo "   1. Abre Docker Desktop"
echo "   2. Espera a que esté 'running'"
echo "   3. Ejecuta: docker --version"
echo "   4. Ejecuta: ./deploy-local.sh"

