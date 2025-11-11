#!/bin/bash
echo "=========================================="
echo "📊 LOGS DE CLOUD RUN - TWILIO SERVER"
echo "=========================================="
echo ""
echo "⏳ Esperando logs nuevos..."
echo "   (Llama al +56 2 2914 5014 para generar logs)"
echo ""
echo "=========================================="
echo ""

# Ver logs en bucle cada 5 segundos
while true; do
    clear
    echo "📊 Últimos logs (actualizando cada 5s)..."
    echo "Presiona Ctrl+C para salir"
    echo ""
    gcloud run services logs read twilio-server \
      --region=us-central1 \
      --project=poc-preventa \
      --limit=20
    echo ""
    echo "⏰ $(date '+%H:%M:%S') - Actualizando en 5s..."
    sleep 5
done
