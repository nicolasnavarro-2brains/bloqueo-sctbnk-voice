# 🌍 Guía Paso a Paso: Subir Bot a Google Cloud Platform

**Objetivo:** Llevar el bot de voz desde tu máquina local a producción en GCP

**Tiempo estimado:** 2-3 horas (primera vez)

---

## 📋 Prerrequisitos

- ✅ Tarjeta de crédito/débito (para GCP - hay $300 gratis por 90 días)
- ✅ Bot funcionando localmente con Docker
- ✅ Cuenta de Gmail

---

## 🚀 PARTE 1: Crear Cuenta y Proyecto GCP (30 min)

### **Paso 1.1: Crear Cuenta GCP**

1. Ve a: https://cloud.google.com/
2. Click en **"Comenzar gratis"** o **"Get started for free"**
3. Inicia sesión con tu cuenta de Gmail
4. Acepta términos y condiciones
5. Selecciona tu país: **Chile**
6. Tipo de cuenta: **Empresa** (si es para Scotiabank)
7. Ingresa datos de la tarjeta
   - ⚠️ **No te cobrarán** - solo para verificación
   - ⚠️ Recibes **$300 USD gratis** por 90 días

✅ **Cuenta creada**

---

### **Paso 1.2: Crear Proyecto**

1. En la consola de GCP: https://console.cloud.google.com/
2. Click en el selector de proyecto (arriba a la izquierda)
3. Click en **"Nuevo Proyecto"**
4. Nombre del proyecto: `scotiabank-voicebot`
5. Organización: Dejar vacío (o seleccionar tu empresa)
6. Click en **"Crear"**
7. Espera 30 segundos

✅ **Proyecto creado**

---

### **Paso 1.3: Habilitar Billing**

1. Menú lateral → **Facturación**
2. Selecciona tu cuenta de facturación
3. Vincúlala al proyecto `scotiabank-voicebot`

✅ **Billing configurado**

---

## 🔧 PARTE 2: Instalar Google Cloud CLI (15 min)

### **Paso 2.1: Instalar gcloud CLI**

**En tu Mac:**

```bash
# Descargar e instalar
curl https://sdk.cloud.google.com | bash

# Reiniciar la terminal
exec -l $SHELL

# Verificar instalación
gcloud --version
```

Si no funciona, descarga desde: https://cloud.google.com/sdk/docs/install

---

### **Paso 2.2: Autenticar**

```bash
# Iniciar sesión
gcloud auth login

# Se abrirá tu navegador → Inicia sesión con tu Gmail
# Autoriza el acceso
```

✅ **Autenticado**

---

### **Paso 2.3: Configurar Proyecto**

```bash
# Configurar proyecto por defecto
gcloud config set project scotiabank-voicebot

# Verificar
gcloud config list
```

✅ **CLI configurado**

---

## 🐳 PARTE 3: Subir Imágenes Docker a GCP (20 min)

### **Paso 3.1: Habilitar Container Registry**

```bash
# Habilitar API
gcloud services enable containerregistry.googleapis.com

# Configurar Docker para usar GCR
gcloud auth configure-docker
```

---

### **Paso 3.2: Tag y Push de Imágenes**

```bash
# Ir a tu proyecto
cd ~/Documents/bloqueo-sctbnk-voice

# Asegurarte que las imágenes estén construidas
docker-compose build

# Tag para GCR (usa tu PROJECT_ID)
PROJECT_ID="poc-preventa"

docker tag bloqueo-sctbnk-voice-rasa gcr.io/$PROJECT_ID/rasa:v1.0
docker tag bloqueo-sctbnk-voice-actions gcr.io/$PROJECT_ID/actions:v1.0
docker tag bloqueo-sctbnk-voice-twilio gcr.io/$PROJECT_ID/twilio:v1.0

# Push a GCR (esto tarda 5-10 min)
docker push gcr.io/$PROJECT_ID/rasa:v1.0
docker push gcr.io/$PROJECT_ID/actions:v1.0
docker push gcr.io/$PROJECT_ID/twilio:v1.0
```

**Verificar en GCP Console:**
- Ve a: https://console.cloud.google.com/gcr
- Deberías ver 3 imágenes: `rasa`, `actions`, `twilio`

✅ **Imágenes subidas**

---

## 🗄️ PARTE 4: Crear Base de Datos (Cloud SQL) (30 min)

### **Paso 4.1: Habilitar API**

```bash
gcloud services enable sqladmin.googleapis.com
```

---

### **Paso 4.2: Crear Instancia MariaDB**

```bash
# Crear instancia (tarda 5-10 min)
gcloud sql instances create voicebot-db \
    --database-version=MARIADB_10_6 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=nico \
    --storage-size=10GB \
    --storage-type=SSD \
    --backup \
    --backup-start-time=03:00

# Crear base de datos
gcloud sql databases create bank --instance=voicebot-db

# Crear usuario
gcloud sql users create nico \
    --instance=voicebot-db \
    --password=nico
```

✅ **Base de datos creada**

---

### **Paso 4.3: Cargar Datos de Prueba**

```bash
# Obtener IP de la instancia
gcloud sql instances describe voicebot-db --format="value(ipAddresses[0].ipAddress)"

# Ejemplo: 34.123.45.67

# Autorizar tu IP para conectar
MY_IP=$(curl -s ifconfig.me)
gcloud sql instances patch voicebot-db --authorized-networks=$MY_IP

# Conectar y cargar datos
gcloud sql connect voicebot-db --user=root

# Una vez dentro de MySQL:
# USE bank;
# Copia el SQL de crear tabla desde setup_test_data.py
# INSERT los 4 clientes de prueba
```

Alternativamente, usa Cloud Shell (más fácil):
https://console.cloud.google.com/sql/instances/voicebot-db/overview

✅ **Datos cargados**

---

## ☁️ PARTE 5: Deploy con Cloud Run (Serverless - Recomendado) (30 min)

### **Paso 5.1: Habilitar Cloud Run**

```bash
gcloud services enable run.googleapis.com
```

---

### **Paso 5.2: Deploy Rasa Server**

```bash
PROJECT_ID="poc-preventa"

gcloud run deploy rasa-server \
    --image=gcr.io/$PROJECT_ID/rasa:v1.0 \
    --platform=managed \
    --region=us-central1 \
    --memory=2Gi \
    --cpu=2 \
    --port=5005 \
    --allow-unauthenticated \
    --set-env-vars="RASA_HOME=/app,RASA_PRO_LICENSE=$RASA_PRO_LICENSE"

# Guarda la URL que te da (ejemplo: https://rasa-server-xxxxx.run.app)
RASA_URL="https://rasa-server-813030270163.us-central1.run.app"
```

---

### **Paso 5.3: Deploy Actions Server**

```bash
# Obtener IP de Cloud SQL
SQL_CONNECTION=$(gcloud sql instances describe voicebot-db --format="value(connectionName)")

gcloud run deploy actions-server \
    --image=gcr.io/$PROJECT_ID/actions:v1.0 \
    --platform=managed \
    --region=us-central1 \
    --memory=512Mi \
    --port=5055 \
    --allow-unauthenticated \
    --set-env-vars="DB_HOST=voicebot-db,DB_USER=nico,DB_PASSWORD=nico,DB_NAME=bank"

# Guarda la URL
ACTIONS_URL="https://actions-server-813030270163.us-central1.run.app"
```

---

### **Paso 5.4: Deploy Twilio Server**

```bash
gcloud run deploy twilio-server \
    --image=gcr.io/$PROJECT_ID/twilio:v1.0 \
    --platform=managed \
    --region=us-central1 \
    --memory=512Mi \
    --port=5000 \
    --allow-unauthenticated \
    --set-env-vars="RASA_URL=$RASA_URL/webhooks/rest/webhook,\
DB_HOST=voicebot-db,DB_USER=nico,DB_PASSWORD=TU_PASSWORD,DB_NAME=bank,\
ELEVEN_API_KEY=$ELEVEN_API_KEY,ELEVEN_VOICE_ID=$ELEVEN_VOICE_ID,\
ELEVEN_VOICE_ID2=$ELEVEN_VOICE_ID2,FRESHDESK_API_KEY=$FRESHDESK_API_KEY,\
FRESHDESK_DOMAIN=$FRESHDESK_DOMAIN"

# ⭐ GUARDA ESTA URL - Es la que usarás en Twilio
TWILIO_URL="https://twilio-server-813030270163.us-central1.run.app"
```

✅ **Servicios desplegados**

---

## 🔗 PARTE 6: Conectar Cloud Run con Cloud SQL (15 min)

Los servicios de Cloud Run necesitan conectarse a Cloud SQL:

```bash
# Agregar conexión a Cloud SQL para cada servicio
SQL_CONNECTION=$(gcloud sql instances describe voicebot-db --format="value(connectionName)")

# Actions
gcloud run services update actions-server \
    --add-cloudsql-instances=$SQL_CONNECTION \
    --region=us-central1

# Twilio
gcloud run services update twilio-server \
    --add-cloudsql-instances=$SQL_CONNECTION \
    --region=us-central1
```

✅ **Cloud SQL conectado**

---

## 📞 PARTE 7: Configurar Twilio (10 min)

### **Paso 7.1: Actualizar Webhook**

1. Ve a: https://console.twilio.com/
2. Phone Numbers → Manage → Active Numbers
3. Selecciona tu número
4. Scroll a **Voice Configuration**
5. En **A CALL COMES IN**:
   - Webhook: `https://twilio-server-813030270163.us-central1.run.app/webhook/twilio/voice`
   - HTTP POST
6. Click **Save**

✅ **Twilio configurado**

---

### **Paso 7.2: Configurar Status Callback**

En el mismo número de Twilio:

1. Scroll a **Call Status Changes**
2. Status Callback URL: `https://twilio-server-813030270163.us-central1.run.app/webhook/twilio/status`
3. HTTP POST
4. Events: `completed`, `failed`
5. Click **Save**

✅ **Callbacks configurados**

---

## 🧪 PARTE 8: Testing (15 min)

### **Paso 8.1: Verificar Servicios**

```bash
# Verificar Rasa
curl https://rasa-server-813030270163.us-central1.run.app

# Verificar Actions
curl https://actions-server-813030270163.us-central1.run.app/health

# Verificar Twilio
curl https://twilio-server-813030270163.us-central1.run.app
```

---

### **Paso 8.2: Llamada de Prueba**

1. Llama al número de Twilio desde uno de los teléfonos registrados:
   - +56982079489 (Mauricio)
   - +56984593400 (Nicolas)

2. El bot debería:
   ✅ Saludarte por nombre
   ✅ Pedirte el RUT
   ✅ Procesar el bloqueo

---

### **Paso 8.3: Ver Logs**

```bash
# Ver logs en tiempo real
gcloud run services logs read twilio-server --region=us-central1 --tail

# Ver logs de Rasa
gcloud run services logs read rasa-server --region=us-central1 --tail

# Ver logs de Actions
gcloud run services logs read actions-server --region=us-central1 --tail
```

✅ **Sistema funcionando en producción**

---

## 💰 PARTE 9: Monitoreo de Costos

### **Ver Costos Actuales:**

1. Ve a: https://console.cloud.google.com/billing
2. **Informes** → Ver uso actual
3. Deberías ver:
   - Cloud Run: ~$5-20/mes
   - Cloud SQL: ~$25/mes
   - Container Registry: ~$5/mes
   - **TOTAL: ~$35-50/mes** (con free tier)

---

## 🔒 PARTE 10: Seguridad (Opcional pero Recomendado)

### **Usar Secret Manager para Credenciales:**

```bash
# Habilitar API
gcloud services enable secretmanager.googleapis.com

# Crear secrets
echo -n "$RASA_PRO_LICENSE" | gcloud secrets create rasa-license --data-file=-
echo -n "$ELEVEN_API_KEY" | gcloud secrets create elevenlabs-key --data-file=-
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-

# Dar acceso a Cloud Run
gcloud secrets add-iam-policy-binding rasa-license \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## 📋 Checklist Final

- [ ] Cuenta GCP creada
- [ ] Proyecto `scotiabank-voicebot` creado
- [ ] gcloud CLI instalado y autenticado
- [ ] 3 imágenes Docker subidas a GCR
- [ ] Cloud SQL (MariaDB) creado y con datos
- [ ] 3 servicios de Cloud Run desplegados
- [ ] Cloud SQL conectado a Cloud Run
- [ ] Webhook de Twilio actualizado
- [ ] Llamada de prueba exitosa
- [ ] Logs funcionando correctamente

---

## 🆘 Troubleshooting

### **Error: "Permission denied"**
```bash
# Reiniciar autenticación
gcloud auth login
gcloud auth application-default login
```

### **Error: "Service unavailable"**
```bash
# Ver logs
gcloud run services logs read twilio-server --region=us-central1 --tail
```

### **Error: "Can't connect to database"**
```bash
# Verificar conexión Cloud SQL
gcloud sql instances describe voicebot-db
# Asegurarse que add-cloudsql-instances esté configurado
```

### **Bot no responde en llamada**
1. Ver logs de Twilio Server
2. Verificar que RASA_URL esté correcta
3. Verificar que todas las env vars estén configuradas

---

## 🎉 ¡LISTO!

Tu bot está en producción:
- ✅ Disponible 24/7
- ✅ IP fija (no más ngrok)
- ✅ Auto-escalable
- ✅ Costo: ~$35-50 USD/mes

---

## 📞 Próximos Pasos

1. **Dominio personalizado** (opcional):
   - Comprar dominio: `voicebot.scotiabank.cl`
   - Configurar en Cloud Run

2. **Monitoring avanzado**:
   - Configurar alertas
   - Dashboard de métricas

3. **CI/CD**:
   - Deploy automático desde Git

---

**¿Dudas?** Revisa los logs o contacta al equipo técnico.

---

*Última actualización: Octubre 2025*

