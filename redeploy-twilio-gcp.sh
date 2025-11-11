#!/bin/bash

PROJECT_ID="poc-preventa"
REGION="us-central1"
SERVICE_NAME="twilio-server"
IMAGE_NAME="gcr.io/${PROJECT_ID}/twilio:latest"

echo "=========================================="
echo "🚀 RE-DEPLOY TWILIO SERVER A GCP"
echo "=========================================="
echo ""

echo "1️⃣  Construyendo imagen Docker..."
docker build -f Dockerfile.twilio -t $IMAGE_NAME .

echo ""
echo "2️⃣  Subiendo imagen a GCR..."
docker push $IMAGE_NAME

echo ""
echo "3️⃣  Deployando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --platform=managed \
  --allow-unauthenticated \
  --set-cloudsql-instances=poc-preventa:us-central1:voicebot-db

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETADO"
echo "=========================================="
echo ""
echo "🧪 Prueba llamando al: +56 2 2914 5014"
