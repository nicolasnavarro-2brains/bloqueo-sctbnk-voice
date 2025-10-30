#!/bin/bash
# Script helper para deployment a GCP

PROJECT_ID="scotiabank-voicebot"
REGION="us-central1"

echo "🚀 GCP Deployment Helper"
echo ""
echo "Asegúrate de haber:"
echo "  1. Creado cuenta GCP"
echo "  2. Instalado gcloud CLI"
echo "  3. Autenticado con: gcloud auth login"
echo ""
read -p "¿Continuar? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Configurar proyecto
echo "📦 Configurando proyecto..."
gcloud config set project $PROJECT_ID

# Habilitar APIs
echo "🔧 Habilitando APIs necesarias..."
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com

# Tag y push de imágenes
echo "🐳 Subiendo imágenes a GCR..."
docker tag bloqueo-sctbnk-voice-rasa gcr.io/$PROJECT_ID/rasa:v1.0
docker tag bloqueo-sctbnk-voice-actions gcr.io/$PROJECT_ID/actions:v1.0
docker tag bloqueo-sctbnk-voice-twilio gcr.io/$PROJECT_ID/twilio:v1.0

echo "⏳ Pushing (esto tarda 5-10 min)..."
docker push gcr.io/$PROJECT_ID/rasa:v1.0 &
docker push gcr.io/$PROJECT_ID/actions:v1.0 &
docker push gcr.io/$PROJECT_ID/twilio:v1.0 &
wait

echo ""
echo "✅ Imágenes subidas!"
echo ""
echo "📋 Próximo paso:"
echo "   Crear Cloud SQL con:"
echo "   ./create-cloudsql.sh"
echo ""
