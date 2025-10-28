#!/bin/bash
# Script para verificar acceso a Rasa Pro imagen

set -e

echo "🔍 =================================================="
echo "   VERIFICANDO ACCESO A RASA PRO"
echo "=================================================="
echo ""

# 1. Verificar .env
if [ ! -f .env ]; then
    echo "❌ No existe archivo .env"
    echo "   Crea uno con: cp env.example .env"
    exit 1
fi

# 2. Verificar si está configurada la key
if ! grep -q "RASA_PRO_LICENSE=" .env || grep -q "RASA_PRO_LICENSE=tu_rasa_pro_license_aqui" .env; then
    echo "❌ RASA_PRO_LICENSE no está configurada en .env"
    echo ""
    echo "Lee: RASA-PRO-SETUP.md para instrucciones"
    exit 1
fi

echo "✅ RASA_PRO_LICENSE encontrada en .env"
echo ""

# 3. Intentar pull de la imagen
echo "🐳 Intentando descargar imagen de Rasa Pro..."
echo "   (Esto puede tardar varios minutos)"
echo ""

if docker pull rasa/rasa-pro:3.14.1; then
    echo ""
    echo "✅ ¡ÉXITO! Puedes usar rasa/rasa-pro:3.14.1"
    echo ""
    echo "Ahora puedes ejecutar:"
    echo "  ./test-docker-local.sh"
else
    echo ""
    echo "❌ No se pudo descargar la imagen"
    echo ""
    echo "OPCIONES:"
    echo ""
    echo "A) Si tienes Rasa Pro:"
    echo "   1. Verifica tu RASA_PRO_LICENSE en .env"
    echo "   2. Puede que necesites login:"
    echo "      docker login rasa.registry.io"
    echo ""
    echo "B) Si NO tienes Rasa Pro:"
    echo "   Usa Rasa Open Source (gratis)"
    echo "   Lee: RASA-PRO-SETUP.md"
    echo ""
    exit 1
fi

