#!/bin/bash
# Script simplificado para testing local

set -e

echo "🧪 =============================================="
echo "   TESTING LOCAL CON DOCKER"
echo "=============================================="
echo ""

# 1. Verificar Docker
echo "1️⃣  Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado o no está en el PATH"
    echo ""
    echo "Por favor:"
    echo "  1. Abre Docker Desktop"
    echo "  2. Espera a que diga 'Engine running'"
    echo "  3. Vuelve a ejecutar este script"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Docker no está corriendo"
    echo ""
    echo "Por favor:"
    echo "  1. Abre Docker Desktop"
    echo "  2. Espera a que diga 'Engine running'"
    echo "  3. Vuelve a ejecutar este script"
    exit 1
fi

echo "✅ Docker está corriendo"
echo ""

# 2. Verificar .env
echo "2️⃣  Verificando configuración..."
if [ ! -f .env ]; then
    echo "⚠️  Creando .env desde env.example..."
    cp env.example .env
    echo "✅ .env creado"
fi

# Verificar Rasa Pro License
if grep -q "RASA_PRO_LICENSE=tu_rasa_pro_license_aqui" .env 2>/dev/null || ! grep -q "RASA_PRO_LICENSE=" .env 2>/dev/null; then
    echo ""
    echo "⚠️  RASA_PRO_LICENSE no configurada"
    echo "   Para usar Rasa Pro 3.13.5, lee: RASA-PRO-SETUP.md"
    echo "   (Puedes continuar, pero Rasa puede fallar)"
fi
echo ""

# 3. Verificar modelo de Rasa
echo "3️⃣  Verificando modelo de Rasa..."
if [ ! -d "models" ] || [ -z "$(ls -A models/*.tar.gz 2>/dev/null)" ]; then
    echo "⚠️  No hay modelo de Rasa"
    echo "   Para un testing rápido, continuaremos sin él"
    echo "   (Rasa puede fallar, pero los otros servicios funcionarán)"
else
    echo "✅ Modelo de Rasa encontrado"
fi
echo ""

# 4. Build
echo "4️⃣  Construyendo imágenes Docker..."
echo "   (Esto puede tardar 5-10 minutos la primera vez)"
echo ""
docker-compose build

echo ""
echo "✅ Imágenes construidas"
echo ""

# 5. Iniciar servicios
echo "5️⃣  Iniciando servicios..."
docker-compose up -d

echo ""
echo "⏳ Esperando a que los servicios inicien (30 segundos)..."
sleep 30

echo ""
echo "6️⃣  Estado de los servicios:"
docker-compose ps

echo ""
echo "7️⃣  Verificando endpoints..."
echo ""

# Verificar cada servicio
check_service() {
    local name=$1
    local url=$2
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name: $url"
        return 0
    else
        echo "❌ $name no responde: $url"
        return 1
    fi
}

check_service "MariaDB" "localhost:3306" || true
check_service "Twilio Server" "http://localhost:5000" || true
check_service "Rasa" "http://localhost:5005" || true
check_service "Actions" "http://localhost:5055/health" || true

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  ✅ TESTING LOCAL COMPLETADO                      ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "📊 Ver logs en tiempo real:"
echo "   docker-compose logs -f"
echo ""
echo "📊 Ver logs de un servicio específico:"
echo "   docker-compose logs -f twilio"
echo "   docker-compose logs -f rasa"
echo ""
echo "🔄 Reiniciar un servicio:"
echo "   docker-compose restart twilio"
echo ""
echo "🛑 Detener todo:"
echo "   docker-compose down"
echo ""
echo "📱 Para probar con Twilio (en otra terminal):"
echo "   ngrok http 5000"
echo "   Luego configura la URL en Twilio Console"
echo ""
echo "🎉 ¡Listo para desarrollar!"

