#!/bin/bash

PROJECT_ID="poc-preventa"
REGION="us-central1"
SERVICE_NAME="rasa-server"
IMAGE_NAME="gcr.io/${PROJECT_ID}/rasa:latest"
ACTIONS_URL="https://actions-server-refdqiiupa-uc.a.run.app/webhook"

echo "=========================================="
echo "🚀 RE-DEPLOY RASA SERVER A GCP"
echo "=========================================="
echo ""

echo "1️⃣  Construyendo imagen Docker de Rasa..."
docker build -f Dockerfile.rasa -t $IMAGE_NAME .

echo ""
echo "2️⃣  Subiendo imagen a GCR..."
docker push $IMAGE_NAME

echo ""
echo "3️⃣  Deployando a Cloud Run con Actions URL..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars ACTION_SERVER_URL=$ACTIONS_URL

echo ""
echo "=========================================="
echo "✅ RASA DEPLOYMENT COMPLETADO"
echo "=========================================="
echo ""
echo "Actions Server: $ACTIONS_URL"
