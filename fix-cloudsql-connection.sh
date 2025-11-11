#!/bin/bash

PROJECT_ID="poc-preventa"
REGION="us-central1"
SERVICE_NAME="twilio-server"

echo "=========================================="
echo "🔧 ARREGLANDO CONEXIÓN A CLOUD SQL"
echo "=========================================="
echo ""

# 1. Obtener el service account de Cloud Run
echo "1️⃣  Obteniendo Service Account..."
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(spec.template.spec.serviceAccountName)')

if [ -z "$SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
  echo "   Usando default: $SERVICE_ACCOUNT"
else
  echo "   Service Account: $SERVICE_ACCOUNT"
fi

# 2. Dar permisos de Cloud SQL Client
echo ""
echo "2️⃣  Dando permisos de Cloud SQL Client..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudsql.client" \
  --quiet

echo ""
echo "3️⃣  Verificando conexión de Cloud SQL..."
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(spec.template.metadata.annotations."run.googleapis.com/cloudsql-instances")'

echo ""
echo "=========================================="
echo "✅ Permisos actualizados"
echo "=========================================="
echo ""
echo "Ahora necesitas RE-DEPLOYAR el servicio:"
echo ""
echo "gcloud run services update $SERVICE_NAME \\"
echo "  --region=$REGION \\"
echo "  --project=$PROJECT_ID \\"
echo "  --clear-cloudsql-instances \\"
echo "  --add-cloudsql-instances=poc-preventa:us-central1:voicebot-db"
echo ""
