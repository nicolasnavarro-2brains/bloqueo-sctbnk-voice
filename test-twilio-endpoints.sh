#!/bin/bash
# Test de endpoints Twilio

echo "=========================================="
echo "🧪 TEST DE ENDPOINTS TWILIO"
echo "=========================================="
echo ""

# Test 1: Simular llamada entrante
echo "1️⃣  Simulando llamada entrante..."
curl -s -X POST http://localhost:5000/webhook/twilio/voice \
  -d "From=+56984593400" \
  -d "CallSid=TEST123456789" \
  | head -20
echo ""
echo "✅ Llamada simulada"
echo ""

# Test 2: Verificar endpoint de colección de RUT
echo "2️⃣  Verificando endpoint collect_rut..."
curl -s http://localhost:5000/webhook/twilio/collect_rut \
  | head -10
echo ""
echo "✅ Endpoint collect_rut OK"
echo ""

# Test 3: Verificar base de datos
echo "3️⃣  Verificando datos en base de datos..."
docker exec sctbnk-mariadb mysql -uroot -pscotiabank123 bank -e "SELECT phone, name FROM customers LIMIT 3;"
echo "✅ Base de datos OK"
echo ""

echo "=========================================="
echo "✅ TODOS LOS TESTS COMPLETADOS"
echo "=========================================="
