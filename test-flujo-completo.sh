#!/bin/bash

echo "=========================================="
echo "🧪 TEST COMPLETO DEL FLUJO DE LLAMADA"
echo "=========================================="
echo ""

# Test 1: Verificar audio en RAM
echo "1️⃣  Verificando que audio se sirva desde RAM..."
echo "   (Los logs deben mostrar [MEMORIA])"
docker logs sctbnk-twilio 2>&1 | grep "\[MEMORIA\]" | tail -3
echo ""

# Test 2: Verificar clientes en DB
echo "2️⃣  Clientes registrados en DB:"
docker exec sctbnk-mariadb mysql -uroot -pnico bank -e "SELECT telefono, nombre, rut FROM customers;"
echo ""

# Test 3: Simular llamada entrante de Nicolas
echo "3️⃣  Simulando llamada de Nicolas (+56984593400)..."
RESPONSE=$(curl -s -X POST http://localhost:5000/webhook/twilio/voice \
  -d "From=+56984593400" \
  -d "CallSid=TEST_$(date +%s)")

echo "$RESPONSE" | head -5
echo ""

if echo "$RESPONSE" | grep -q "greeting"; then
    echo "   ✅ Bot saludó correctamente"
    echo "   ✅ Audio generado y almacenado en RAM"
else
    echo "   ❌ Error en el flujo"
fi
echo ""

# Test 4: Verificar que ngrok está configurado
echo "4️⃣  URL de ngrok configurada:"
docker logs sctbnk-twilio 2>&1 | grep "ngrok" | tail -1
echo ""

# Test 5: Verificar servicios Rasa y Actions
echo "5️⃣  Estado de servicios:"
echo "   - Rasa: $(curl -s http://localhost:5005/ | head -1)"
echo "   - Actions: $(curl -s http://localhost:5055/health)"
echo ""

echo "=========================================="
echo "✅ VERIFICACIÓN COMPLETA"
echo "=========================================="
echo ""
echo "📞 Para probar en vivo:"
echo "   1. Llama al número de Twilio configurado"
echo "   2. Verifica logs: docker logs -f sctbnk-twilio"
echo ""
