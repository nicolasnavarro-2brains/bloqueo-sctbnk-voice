#!/bin/bash

# ============================================================
# SCRIPT DE CONFIGURACIÓN DE CI/CD
# ============================================================
# Este script configura Cloud Build y Secret Manager
# para CI/CD automático
# ============================================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "============================================================"
echo "  🔄 CONFIGURACIÓN DE CI/CD CON CLOUD BUILD"
echo "============================================================"
echo ""

# Verificar .env
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

source .env

# Obtener PROJECT_ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No hay proyecto GCP configurado"
    echo "Ejecutar: gcloud config set project TU_PROYECTO"
    exit 1
fi

echo -e "${BLUE}[INFO]${NC} Proyecto: $PROJECT_ID"
echo ""

# Confirmar
read -p "¿Continuar con la configuración de CI/CD? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelado"
    exit 0
fi

# ============================================================
# PASO 1: Habilitar APIs
# ============================================================

echo -e "${BLUE}[1/5]${NC} Habilitando APIs..."

gcloud services enable secretmanager.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet

echo -e "${GREEN}✓${NC} APIs habilitadas"
echo ""

# ============================================================
# PASO 2: Crear Secrets
# ============================================================

echo -e "${BLUE}[2/5]${NC} Creando secrets en Secret Manager..."

# Función para crear o actualizar secret
create_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if gcloud secrets describe $secret_name --quiet 2>/dev/null; then
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --quiet
        echo "  ✓ $secret_name (actualizado)"
    else
        echo -n "$secret_value" | gcloud secrets create $secret_name \
            --data-file=- \
            --replication-policy="automatic" \
            --quiet
        echo "  ✓ $secret_name (creado)"
    fi
}

# Crear todos los secrets
create_secret "rasa-pro-license" "$RASA_PRO_LICENSE"
create_secret "db-password" "${DB_PASSWORD:-nico}"
create_secret "eleven-api-key" "$ELEVEN_API_KEY"
create_secret "eleven-voice-id" "$ELEVEN_VOICE_ID"
create_secret "eleven-voice-id2" "$ELEVEN_VOICE_ID2"
create_secret "freshdesk-api-key" "$FRESHDESK_API_KEY"
create_secret "freshdesk-domain" "$FRESHDESK_DOMAIN"

echo -e "${GREEN}✓${NC} Secrets creados"
echo ""

# ============================================================
# PASO 3: Dar Permisos a Cloud Build
# ============================================================

echo -e "${BLUE}[3/5]${NC} Configurando permisos..."

PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Permisos para Secret Manager (a nivel de proyecto y en secrets específicos)
echo "  - Permisos de Secret Manager para Cloud Build..."
# Permisos a nivel de proyecto
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet > /dev/null 2>&1

# Permisos en secrets específicos
for secret in rasa-pro-license db-password eleven-api-key eleven-voice-id eleven-voice-id2 freshdesk-api-key freshdesk-domain; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:${CLOUD_BUILD_SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet > /dev/null 2>&1
done

# Permisos para Cloud Run
echo "  - Permisos de Cloud Run..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" \
    --quiet > /dev/null 2>&1

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" \
    --quiet > /dev/null 2>&1

# Permisos de Secret Manager para Cloud Run Service Account
echo "  - Permisos de Secret Manager para Cloud Run..."
CLOUD_RUN_SA="${PROJECT_ID}@appspot.gserviceaccount.com"
# Permisos a nivel de proyecto
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet > /dev/null 2>&1

# Permisos en secrets específicos (necesarios para --set-secrets)
for secret in rasa-pro-license db-password eleven-api-key eleven-voice-id eleven-voice-id2 freshdesk-api-key freshdesk-domain; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:${CLOUD_RUN_SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet > /dev/null 2>&1
done

echo -e "${GREEN}✓${NC} Permisos configurados"
echo ""

# ============================================================
# PASO 4: Verificar cloudbuild.yaml
# ============================================================

echo -e "${BLUE}[4/5]${NC} Verificando cloudbuild.yaml..."

if [ ! -f cloudbuild.yaml ]; then
    echo -e "${YELLOW}⚠${NC}  cloudbuild.yaml no encontrado"
    echo "   Crear el archivo antes de continuar"
    exit 1
fi

echo -e "${GREEN}✓${NC} cloudbuild.yaml encontrado"
echo ""

# ============================================================
# PASO 5: Instrucciones Finales
# ============================================================

echo -e "${BLUE}[5/5]${NC} Configuración completada"
echo ""
echo "============================================================"
echo "  ✅ CI/CD CONFIGURADO"
echo "============================================================"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo ""
echo "1. Conectar GitHub con Cloud Build:"
echo "   https://console.cloud.google.com/cloud-build/triggers"
echo ""
echo "2. Click en 'Conectar repositorio'"
echo ""
echo "3. Seleccionar: GitHub (Cloud Build GitHub App)"
echo ""
echo "4. Autorizar y seleccionar tu repo"
echo ""
echo "5. Crear trigger:"
echo "   - Nombre: deploy-production"
echo "   - Evento: Push a rama 'main'"
echo "   - Config: cloudbuild.yaml"
echo ""
echo "6. Hacer push a main para probar:"
echo "   git push origin main"
echo ""
echo "============================================================"
echo ""
echo "📚 Documentación completa: CI-CD-SETUP.md"
echo ""

