#!/bin/bash

echo ""
echo "=========================================="
echo "🧪 PRUEBA 1: TARJETA VÁLIDA + CONFIRMAR"
echo "=========================================="
echo ""

echo "👤 Usuario dice: 'quiero bloquear mi tarjeta'"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_valid_confirm", "message": "quiero bloquear mi tarjeta"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: '1234' (válida)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_valid_confirm", "message": "1234"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: 'sí' (confirmar bloqueo)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_valid_confirm", "message": "sí"}'
echo ""
echo ""

sleep 3

echo "=========================================="
echo "🧪 PRUEBA 2: TARJETA VÁLIDA + CANCELAR"
echo "=========================================="
echo ""

echo "👤 Usuario dice: 'Quiero bloquear mi tarjeta'"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_valid_cancel", "message": "Quiero bloquear mi tarjeta"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: '5678' (válida)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_valid_cancel", "message": "5678"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: 'no' (cancelar bloqueo)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_valid_cancel", "message": "no"}'
echo ""
echo ""

sleep 3

echo "=========================================="
echo "🧪 PRUEBA 3: TARJETA INVÁLIDA (1er intento) + CONFIRMAR"
echo "=========================================="
echo ""

echo "👤 Usuario dice: 'quiero bloquear mi tarjeta'"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_invalid_once", "message": "quiero bloquear mi tarjeta"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: '1111' (inválida - 1er intento)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_invalid_once", "message": "11"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: '1234' (válida - retry)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_invalid_once", "message": "1234"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: 'sí' (confirmar bloqueo)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_invalid_once", "message": "sí"}'
echo ""
echo ""

sleep 3

echo "=========================================="
echo "🧪 PRUEBA 4: TARJETA INVÁLIDA (2 intentos) → Transferir"
echo "=========================================="
echo ""

echo "👤 Usuario dice: 'quiero bloquear mi tarjeta'"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_invalid_twice", "message": "quiero bloquear mi tarjeta"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: '1111' (inválida - 1er intento)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_invalid_twice", "message": "1111"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: '2222' (inválida - 2do intento)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_invalid_twice", "message": "2222"}'
echo ""
echo ""

sleep 3

echo "=========================================="
echo "🧪 PRUEBA 5: CANCELAR con diferentes palabras"
echo "=========================================="
echo ""

echo "👤 Usuario dice: 'quiero bloquear mi tarjeta'"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_cancel_words", "message": "quiero bloquear mi tarjeta"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: '9999' (válida)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_cancel_words", "message": "9999"}'
echo ""
echo ""

sleep 2

echo "👤 Usuario dice: 'cancelar' (cancelar bloqueo)"
curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_cancel_words", "message": "cancelar"}'
echo ""
echo ""

sleep 3

echo ""
echo "=========================================="
echo "✅ TODAS LAS PRUEBAS COMPLETADAS"
echo "=========================================="
echo ""
echo "📊 Resumen de pruebas:"
echo "  1. ✅ Tarjeta válida + Confirmar bloqueo"
echo "  2. ❌ Tarjeta válida + Cancelar bloqueo"
echo "  3. ✅ Tarjeta inválida (1 intento) + Confirmar"
echo "  4. 📞 Tarjeta inválida (2 intentos) → Transferir"
echo "  5. ❌ Cancelar con palabra 'cancelar'"
echo ""
