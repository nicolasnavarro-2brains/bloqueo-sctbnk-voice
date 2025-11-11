#!/bin/bash

# ============================================================
# SCRIPT DE DEPLOYMENT AUTOMATIZADO A GCP
# ============================================================
# Este script automatiza el deployment completo del bot a GCP
# Incluye: Cloud SQL, Cloud Run (3 servicios), permisos
# ============================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Banner
echo ""
echo "============================================================"
echo "  🚀 DEPLOYMENT AUTOMATIZADO A GCP - Bot por Voz"
echo "============================================================"
echo ""

# ============================================================
# PASO 0: Verificar requisitos
# ============================================================

print_info "Verificando requisitos previos..."

# Verificar gcloud
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI no está instalado"
    echo "Instalar desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
print_success "gcloud CLI instalado"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado"
    echo "Instalar desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_success "Docker instalado"

# Verificar .env
if [ ! -f .env ]; then
    print_error "Archivo .env no encontrado"
    echo "Crear .env desde env.example y configurar credenciales"
    exit 1
fi
print_success "Archivo .env encontrado"

# Cargar variables de .env
source .env

# Verificar variables críticas
if [ -z "$RASA_PRO_LICENSE" ]; then
    print_error "RASA_PRO_LICENSE no configurada en .env"
    exit 1
fi
print_success "Variables de entorno cargadas"

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Obtener PROJECT_ID actual
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    print_error "No hay proyecto GCP configurado"
    echo "Ejecutar: gcloud config set project TU_PROYECTO"
    exit 1
fi

REGION="us-central1"
DB_INSTANCE="voicebot-db"
DB_NAME="bank"
DB_USER="root"

print_info "Proyecto GCP: $PROJECT_ID"
print_info "Región: $REGION"
echo ""

# Confirmar
read -p "¿Continuar con el deployment? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelado"
    exit 0
fi

# ============================================================
# PASO 1: Habilitar APIs
# ============================================================

print_info "Habilitando APIs necesarias..."

gcloud services enable run.googleapis.com --quiet
gcloud services enable sqladmin.googleapis.com --quiet
gcloud services enable containerregistry.googleapis.com --quiet
gcloud services enable artifactregistry.googleapis.com --quiet

print_success "APIs habilitadas"
echo ""

# ============================================================
# PASO 2: Crear Cloud SQL (si no existe)
# ============================================================

print_info "Verificando Cloud SQL..."

if gcloud sql instances describe $DB_INSTANCE --quiet 2>/dev/null; then
    print_warning "Cloud SQL '$DB_INSTANCE' ya existe, omitiendo creación"
else
    print_info "Creando Cloud SQL (esto toma 5-10 minutos)..."
    
    # Pedir password si no está en .env
    if [ -z "$DB_PASSWORD" ]; then
        read -sp "Ingresa password para Cloud SQL: " DB_PASSWORD
        echo ""
    fi
    
    gcloud sql instances create $DB_INSTANCE \
        --database-version=MYSQL_8_0 \
        --tier=db-f1-micro \
        --region=$REGION \
        --root-password="$DB_PASSWORD" \
        --quiet
    
    print_success "Cloud SQL creado"
    
    # Crear database
    print_info "Creando database '$DB_NAME'..."
    gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE --quiet
    print_success "Database creado"
    
    # Cargar datos
    print_info "Cargando datos de prueba..."
    
    # Crear archivo SQL temporal
    cat > /tmp/setup_db.sql << 'EOF'
USE bank;

CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(36) PRIMARY KEY,
    rut VARCHAR(9) NOT NULL UNIQUE,
    nombre VARCHAR(64) NOT NULL,
    nombre_completo VARCHAR(128) NOT NULL,
    telefono VARCHAR(12) NOT NULL UNIQUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO customers (id, rut, nombre, nombre_completo, telefono) VALUES
(UUID(), '87654321', 'Nicolas', 'Nicolas Navarro Aravena', '+56984593400'),
(UUID(), '12345678', 'Mauricio', 'Mauricio González López', '+56982079489'),
(UUID(), '98765432', 'María', 'María Fernández Silva', '+56987654321'),
(UUID(), '55556666', 'Carlos', 'Carlos Rodríguez Pérez', '+56955556666');
EOF
    
    gcloud sql connect $DB_INSTANCE --user=root --quiet < /tmp/setup_db.sql
    rm /tmp/setup_db.sql
    
    print_success "Datos de prueba cargados"
fi

echo ""

# ============================================================
# PASO 3: Build y Push Docker Images
# ============================================================

print_info "Configurando Docker para GCR..."
gcloud auth configure-docker gcr.io --quiet
print_success "Docker configurado"
echo ""

print_info "Construyendo imágenes Docker (esto toma 10-15 minutos)..."

# Build Actions
print_info "[1/3] Building Actions Server..."
docker build -f Dockerfile.actions -t gcr.io/${PROJECT_ID}/actions:latest . --quiet
print_success "Actions image built"

# Build Twilio
print_info "[2/3] Building Twilio Server..."
docker build -f Dockerfile.twilio -t gcr.io/${PROJECT_ID}/twilio:latest . --quiet
print_success "Twilio image built"

# Build Rasa (el más lento)
print_info "[3/3] Building Rasa Server (esto toma ~10 minutos)..."
docker build -f Dockerfile.rasa -t gcr.io/${PROJECT_ID}/rasa:latest .
print_success "Rasa image built"

echo ""
print_info "Subiendo imágenes a GCR..."

docker push gcr.io/${PROJECT_ID}/actions:latest &
docker push gcr.io/${PROJECT_ID}/twilio:latest &
docker push gcr.io/${PROJECT_ID}/rasa:latest &

wait  # Esperar a que terminen todos los push

print_success "Imágenes subidas a GCR"
echo ""

# ============================================================
# PASO 4: Deploy Actions Server
# ============================================================

print_info "Deployando Actions Server..."

gcloud run deploy actions-server \
  --image=gcr.io/${PROJECT_ID}/actions:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --quiet

ACTIONS_URL=$(gcloud run services describe actions-server \
  --region=$REGION \
  --format='value(status.url)')

print_success "Actions Server deployado: $ACTIONS_URL"
echo ""

# ============================================================
# PASO 5: Deploy Rasa Server
# ============================================================

print_info "Deployando Rasa Server..."

gcloud run deploy rasa-server \
  --image=gcr.io/${PROJECT_ID}/rasa:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --set-env-vars RASA_PRO_LICENSE="${RASA_PRO_LICENSE}" \
  --set-env-vars ACTION_SERVER_URL="${ACTIONS_URL}/webhook" \
  --quiet

RASA_URL=$(gcloud run services describe rasa-server \
  --region=$REGION \
  --format='value(status.url)')

print_success "Rasa Server deployado: $RASA_URL"
echo ""

# ============================================================
# PASO 6: Deploy Twilio Server
# ============================================================

print_info "Deployando Twilio Server..."

gcloud run deploy twilio-server \
  --image=gcr.io/${PROJECT_ID}/twilio:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --set-cloudsql-instances=${PROJECT_ID}:${REGION}:${DB_INSTANCE} \
  --set-env-vars BASE_URL="TBD" \
  --set-env-vars RASA_URL="${RASA_URL}/webhooks/rest/webhook" \
  --set-env-vars DB_HOST="/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE}" \
  --set-env-vars DB_PORT="3306" \
  --set-env-vars DB_USER="${DB_USER}" \
  --set-env-vars DB_PASSWORD="${DB_PASSWORD}" \
  --set-env-vars DB_NAME="${DB_NAME}" \
  --set-env-vars ELEVEN_API_KEY="${ELEVEN_API_KEY}" \
  --set-env-vars ELEVEN_VOICE_ID="${ELEVEN_VOICE_ID}" \
  --set-env-vars ELEVEN_VOICE_ID2="${ELEVEN_VOICE_ID2}" \
  --set-env-vars FRESHDESK_API_KEY="${FRESHDESK_API_KEY}" \
  --set-env-vars FRESHDESK_DOMAIN="${FRESHDESK_DOMAIN}" \
  --quiet

TWILIO_URL=$(gcloud run services describe twilio-server \
  --region=$REGION \
  --format='value(status.url)')

# Actualizar BASE_URL
print_info "Actualizando BASE_URL..."
gcloud run services update twilio-server \
  --region=$REGION \
  --update-env-vars BASE_URL="${TWILIO_URL}" \
  --quiet

print_success "Twilio Server deployado: $TWILIO_URL"
echo ""

# ============================================================
# PASO 7: Configurar Permisos
# ============================================================

print_info "Configurando permisos de Cloud SQL..."

SERVICE_ACCOUNT=$(gcloud run services describe twilio-server \
  --region=$REGION \
  --format='value(spec.template.spec.serviceAccountName)')

if [ -z "$SERVICE_ACCOUNT" ]; then
    SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
fi

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudsql.client" \
  --quiet > /dev/null

print_success "Permisos configurados"
echo ""

# ============================================================
# PASO 8: Testing
# ============================================================

print_info "Ejecutando tests de verificación..."

# Test Rasa
echo -n "  - Rasa Server... "
RASA_TEST=$(curl -s -X POST ${RASA_URL}/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "hola"}')

if [ -n "$RASA_TEST" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test Actions
echo -n "  - Actions Server... "
ACTIONS_TEST=$(curl -s ${ACTIONS_URL}/webhook)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test Twilio
echo -n "  - Twilio Server... "
TWILIO_TEST=$(curl -s ${TWILIO_URL}/)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""

# ============================================================
# RESUMEN FINAL
# ============================================================

echo ""
echo "============================================================"
echo "  ✅ DEPLOYMENT COMPLETADO EXITOSAMENTE"
echo "============================================================"
echo ""
echo "📝 URLs de Servicios:"
echo ""
echo "  Twilio Server:  $TWILIO_URL"
echo "  Rasa Server:    $RASA_URL"
echo "  Actions Server: $ACTIONS_URL"
echo ""
echo "============================================================"
echo "📞 CONFIGURAR EN TWILIO CONSOLE:"
echo "============================================================"
echo ""
echo "1. Ir a: https://console.twilio.com/"
echo "2. Phone Numbers → Active Numbers → [Tu número]"
echo ""
echo "3. Voice Configuration:"
echo "   - A CALL COMES IN:"
echo "     URL: ${TWILIO_URL}/webhook/twilio/voice"
echo "     HTTP: POST"
echo ""
echo "4. Call Status Changes:"
echo "   - Status Callback URL:"
echo "     ${TWILIO_URL}/webhook/twilio/status"
echo "     HTTP: POST"
echo "     Events: ✓ completed, ✓ failed"
echo ""
echo "5. Save"
echo ""
echo "============================================================"
echo "🧪 TESTING:"
echo "============================================================"
echo ""
echo "Llamar desde:"
echo "  - +56984593400 (Nicolas, RUT: 87654321)"
echo "  - +56982079489 (Mauricio, RUT: 12345678)"
echo ""
echo "Ver logs:"
echo "  gcloud run services logs tail twilio-server --region=$REGION"
echo ""
echo "============================================================"
echo ""
print_success "Deployment finalizado. ¡Sistema listo en producción! 🎉"
echo ""

