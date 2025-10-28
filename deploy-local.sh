#!/bin/bash
# Script para deployment local con Docker Compose

set -e

echo "🚀 =============================================="
echo "   DEPLOYMENT LOCAL - Scotiabank Voice Bot"
echo "=============================================="
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    echo "   Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose no está instalado"
    exit 1
fi

echo "✅ Docker instalado"
echo ""

# Verificar .env
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "   Copiando env.example a .env..."
    cp env.example .env
    echo "   ⚠️  IMPORTANTE: Edita .env con tus credenciales"
    echo ""
    read -p "¿Quieres editar .env ahora? (s/n): " respuesta
    if [ "$respuesta" = "s" ]; then
        ${EDITOR:-nano} .env
    fi
fi

echo "✅ Archivo .env configurado"
echo ""

# Verificar modelo de Rasa
if [ ! -d "models" ] || [ -z "$(ls -A models/*.tar.gz 2>/dev/null)" ]; then
    echo "⚠️  No hay modelo de Rasa entrenado"
    echo "   Entrenando modelo..."
    source venv/bin/activate 2>/dev/null || true
    rasa train
    echo "✅ Modelo entrenado"
else
    echo "✅ Modelo de Rasa encontrado"
fi

echo ""
echo "📦 Building imágenes Docker..."
docker-compose build

echo ""
echo "🚀 Iniciando servicios..."
docker-compose up -d

echo ""
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

echo ""
echo "✅ Servicios iniciados!"
echo ""
echo "📊 Estado de los servicios:"
docker-compose ps

echo ""
echo "🔍 Verificando endpoints:"
echo ""

# Verificar Rasa
if curl -s http://localhost:5005 > /dev/null; then
    echo "✅ Rasa: http://localhost:5005"
else
    echo "❌ Rasa no responde"
fi

# Verificar Actions
if curl -s http://localhost:5055/health > /dev/null; then
    echo "✅ Actions: http://localhost:5055/health"
else
    echo "❌ Actions no responde"
fi

# Verificar Twilio
if curl -s http://localhost:5000 > /dev/null; then
    echo "✅ Twilio: http://localhost:5000"
else
    echo "❌ Twilio no responde"
fi

echo ""
echo "📱 Para probar con Twilio:"
echo "   1. Ejecuta en otra terminal: ngrok http 5000"
echo "   2. Copia la URL https://xxxxx.ngrok.io"
echo "   3. Configúrala en Twilio Console"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs:        docker-compose logs -f"
echo "   Ver un servicio: docker-compose logs -f twilio"
echo "   Detener:         docker-compose down"
echo "   Reiniciar:       docker-compose restart"
echo ""
echo "✅ Deployment local completado!"

