#!/bin/bash

# Script para probar la conversación completa del bot de bloqueo de tarjetas
# Genera call_sid únicos automáticamente para evitar conflictos de contexto
# Formatea el XML para mejor legibilidad
# Incluye testing de identificación de clientes por número de teléfono
clear
# Función para mostrar uso del script
show_usage() {
    echo "Uso: $0 [phone_number]"
    echo ""
    echo "Ejemplos:"
    echo "  $0                    # Sin número específico (usará +56982221070)"
    echo "  $0 +56982221070      # Con número específico"
    echo "  $0 +56912345678      # Con otro número para probar cliente no encontrado"
    echo ""
}

# Función para formatear XML de manera legible
pretty_print() {
    local xml_content="$1"
    
    # Intentar usar xmllint para formatear
    if command -v xmllint >/dev/null 2>&1; then
        echo "$xml_content" | xmllint --format - 2>/dev/null || echo "$xml_content"
    else
        # Fallback: usar Python para formatear básicamente
        echo "$xml_content" | python3 -c "
import xml.dom.minidom
import sys
try:
    xml_str = sys.stdin.read()
    dom = xml.dom.minidom.parseString(xml_str)
    print(dom.toprettyxml(indent='  '))
except:
    print(xml_str)
" 2>/dev/null || echo "$xml_content"
    fi
}

# Procesar argumentos
PHONE_NUMBER=${1:-"+56982221070"}

# Generar call_sid único basado en timestamp y número aleatorio
TIMESTAMP=$(date +%s)
RANDOM_NUM=$((RANDOM % 1000))
CALL_SID="TEST_${TIMESTAMP}_${RANDOM_NUM}"

echo "🎯 Iniciando prueba con call_sid único: ${CALL_SID}"
echo "📱 Número de teléfono: ${PHONE_NUMBER}"
echo "⏰ Timestamp: $(date)"
echo ""

# 1. Llamada inicial
echo "📞 1. Llamada inicial..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s -X POST "http://localhost:5000/webhook/twilio/voice" \
  -d "CallSid=${CALL_SID}&From=${PHONE_NUMBER}&To=+1234567890" \
  -H "Content-Type: application/x-www-form-urlencoded")
pretty_print "$RESPONSE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "⏳ Esperando 3 segundos..."
sleep 3
echo ""

# 2. Usuario dice: quiero bloquear mi tarjeta
echo "🎤 2. Usuario dice: quiero bloquear mi tarjeta..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s -X POST "http://localhost:5000/webhook/twilio/speech?call_sid=${CALL_SID}" \
  -d "SpeechResult=quiero bloquear mi tarjeta&Confidence=0.95" \
  -H "Content-Type: application/x-www-form-urlencoded")
pretty_print "$RESPONSE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "⏳ Esperando 3 segundos..."
sleep 3
echo ""

# 3. Usuario dice: 1234
echo "🎤 3. Usuario dice: 1234..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s -X POST "http://localhost:5000/webhook/twilio/speech?call_sid=${CALL_SID}" \
  -d "SpeechResult=1234&Confidence=0.90" \
  -H "Content-Type: application/x-www-form-urlencoded")
pretty_print "$RESPONSE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "⏳ Esperando 3 segundos..."
sleep 3
echo ""

# 4. Usuario confirma: sí
echo "🎤 4. Usuario confirma: sí..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s -X POST "http://localhost:5000/webhook/twilio/speech?call_sid=${CALL_SID}" \
  -d "SpeechResult=sí&Confidence=0.95" \
  -H "Content-Type: application/x-www-form-urlencoded")
pretty_print "$RESPONSE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ables de entorno (no incluyo keys hardcodeadas). Estos archivos incluyen:

generación de audio con ElevenLabs (archivos .mp3 únicos por call_sid + uuid),


echo ""
echo "✅ Prueba de conversación completada!"
echo "🎯 Call SID utilizado: ${CALL_SID}"
echo "📱 Número de teléfono: ${PHONE_NUMBER}"
echo "⏰ Finalizado: $(date)"
echo ""
echo "💡 Para probar con diferentes números:"
echo "   ./test_conversation.sh +56982221070  # Cliente conocido"
echo "   ./test_conversation.sh +56912345678  # Cliente no encontrado"
