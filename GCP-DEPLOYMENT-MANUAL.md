# 🌍 Guía Paso a Paso: Deployment Manual en GCP

**Objetivo:** Llevar el bot de voz a producción en Google Cloud Platform  
**Tiempo estimado:** 2-3 horas (primera vez)  
**Nivel:** Beginner-friendly con explicaciones detalladas

---

## 📋 ¿Qué Vamos a Hacer?

Esta guía te lleva de la mano para:
1. Crear cuenta en GCP (gratis por 90 días)
2. Instalar herramientas necesarias
3. Subir el código a la nube
4. Crear base de datos en la nube
5. Configurar 3 servicios (Rasa, Actions, Twilio)
6. Conectar todo
7. Probar que funcione

**Al final tendrás:** Un bot funcionando 24/7 sin necesidad de tu computadora prendida.

---

## ✅ Prerrequisitos

Antes de empezar, asegúrate de tener:

- [ ] Tarjeta de crédito/débito (para GCP - **no te cobran**, solo verificación)
- [ ] Cuenta de Gmail
- [ ] Bot funcionando localmente (haber ejecutado `./deploy-local.sh`)
- [ ] Archivo `.env` configurado con tus credenciales

---

## 🚀 PARTE 1: Crear Cuenta y Proyecto GCP

**⏱️ Tiempo:** 30 minutos

---

### **Paso 1.1: Crear Cuenta GCP**

1. Abre tu navegador y ve a: **https://cloud.google.com/**

2. Click en el botón **"Comenzar gratis"** (o "Get started for free")

3. **Inicia sesión** con tu cuenta de Gmail

4. **Acepta** términos y condiciones

5. Completa el formulario:
   - **País:** Chile
   - **Tipo de cuenta:** Empresa (si es para Scotiabank)
   - **Nombre:** Tu nombre o nombre de la empresa
   - **Dirección:** Tu dirección

6. **Ingresa datos de la tarjeta:**
   - ⚠️ **IMPORTANTE:** No te cobrarán nada
   - ⚠️ Es solo para verificación
   - ✅ Recibes **$300 USD gratis** por 90 días

7. Click en **"Comenzar mi prueba gratuita"**

✅ **¡Cuenta creada!** Deberías ver el Dashboard de GCP.

---

### **Paso 1.2: Crear Proyecto**

Los proyectos en GCP son como "carpetas" que organizan tus recursos.

1. En la **barra superior**, busca el selector de proyecto (dice "My First Project" o similar)

2. Click en el selector → Se abre un modal

3. Click en **"Nuevo Proyecto"** (arriba a la derecha)

4. **Nombre del proyecto:** `poc-preventa` (o el que prefieras)
   - Usa solo minúsculas, números y guiones
   - Ejemplo: `scotiabank-voicebot`

5. **Organización:** Dejar vacío (a menos que tengas una)

6. Click en **"Crear"**

7. **Espera 30-60 segundos** mientras se crea

8. Verás una notificación cuando esté listo

9. **Selecciona el proyecto** desde el selector

✅ **Proyecto creado y seleccionado**

---

### **Paso 1.3: Habilitar Facturación**

Aunque no te cobran (tienes $300 gratis), necesitas vincular la facturación.

1. Menú lateral (☰) → **Facturación**

2. Si dice "Este proyecto no tiene cuenta de facturación":
   - Click en **"Vincular cuenta de facturación"**
   - Selecciona tu cuenta (la que creaste en Paso 1.1)
   - Click en **"Establecer cuenta"**

3. Deberías ver: **"Facturación habilitada"** ✅

✅ **Billing configurado**

---

## 🔧 PARTE 2: Instalar Google Cloud CLI

**⏱️ Tiempo:** 15 minutos

El CLI (Command Line Interface) te permite controlar GCP desde tu terminal.

---

### **Paso 2.1: Instalar gcloud CLI**

**En tu Mac**, abre la Terminal y ejecuta:

```bash
# Descargar e instalar
curl https://sdk.cloud.google.com | bash

# Espera 2-3 minutos mientras se instala
```

**Durante la instalación te preguntará:**
- ¿Modificar tu PATH? → **Y** (yes)
- ¿Enviar estadísticas? → Como prefieras (recomiendo **N**)

**Reiniciar la terminal:**

```bash
exec -l $SHELL
```

**Verificar instalación:**

```bash
gcloud --version
```

Deberías ver algo como:
```
Google Cloud SDK 450.0.0
```

✅ **gcloud CLI instalado**

**Si no funciona:** Descarga el instalador desde https://cloud.google.com/sdk/docs/install

---

### **Paso 2.2: Autenticar en GCP**

```bash
# Iniciar sesión
gcloud auth login
```

**Lo que pasa:**
1. Se abre tu navegador
2. Te pide elegir tu cuenta de Gmail
3. Click en **"Permitir"**
4. Verás: "You are now authenticated"
5. Cierra la pestaña del navegador

**En la terminal verás:**
```
You are now logged in as [tu-email@gmail.com]
```

✅ **Autenticado**

---

### **Paso 2.3: Configurar Proyecto por Defecto**

```bash
# Configurar tu proyecto (usa el nombre que creaste)
gcloud config set project poc-preventa

# Verificar
gcloud config list
```

**Deberías ver:**
```
[core]
account = tu-email@gmail.com
project = poc-preventa
```

✅ **CLI configurado y listo**

---

## 🐳 PARTE 3: Subir Imágenes Docker a GCP

**⏱️ Tiempo:** 20-30 minutos

Vamos a subir las 3 imágenes Docker (Rasa, Actions, Twilio) a Google Container Registry.

---

### **Paso 3.1: Habilitar APIs Necesarias**

```bash
# Habilitar Container Registry
gcloud services enable containerregistry.googleapis.com

# Habilitar Artifact Registry  
gcloud services enable artifactregistry.googleapis.com

# Esto tarda 1-2 minutos
```

**Configurar Docker para GCR:**

```bash
gcloud auth configure-docker gcr.io
```

Deberías ver: `Docker configuration file updated.`

✅ **APIs habilitadas**

---

### **Paso 3.2: Ir a Tu Proyecto**

```bash
cd ~/Documents/bloqueo-sctbnk-voice
```

---

### **Paso 3.3: Construir Imágenes Docker**

Si no las has construido recientemente:

```bash
# Construir las 3 imágenes
docker build -f Dockerfile.rasa -t rasa-local .
docker build -f Dockerfile.actions -t actions-local .
docker build -f Dockerfile.twilio -t twilio-local .

# Esto tarda 10-15 minutos
```

**Mientras esperas:** Puedes ir preparando un café ☕

---

### **Paso 3.4: Tagear Imágenes para GCR**

```bash
# Define tu PROJECT_ID (el que creaste)
PROJECT_ID="poc-preventa"

# Tag las imágenes para GCR
docker tag rasa-local gcr.io/$PROJECT_ID/rasa:latest
docker tag actions-local gcr.io/$PROJECT_ID/actions:latest
docker tag twilio-local gcr.io/$PROJECT_ID/twilio:latest
```

**Verificar:**
```bash
docker images | grep gcr.io
```

Deberías ver 3 imágenes con `gcr.io/poc-preventa/`

---

### **Paso 3.5: Push a Google Container Registry**

```bash
# Push de las 3 imágenes (tarda 5-10 minutos)
docker push gcr.io/$PROJECT_ID/rasa:latest
docker push gcr.io/$PROJECT_ID/actions:latest
docker push gcr.io/$PROJECT_ID/twilio:latest
```

**Verás barras de progreso:**
```
latest: digest: sha256:abc123... size: 4567
```

**Verificar en GCP Console:**
1. Ve a: https://console.cloud.google.com/gcr
2. Deberías ver 3 imágenes: `rasa`, `actions`, `twilio`

✅ **Imágenes subidas a GCR**

---

## 🗄️ PARTE 4: Crear Base de Datos (Cloud SQL)

**⏱️ Tiempo:** 30 minutos

Vamos a crear una base de datos MySQL en la nube y cargar los datos de prueba.

---

### **Paso 4.1: Habilitar Cloud SQL API**

```bash
gcloud services enable sqladmin.googleapis.com
```

---

### **Paso 4.2: Crear Instancia MySQL**

```bash
# Crear instancia (tarda 5-10 minutos)
gcloud sql instances create voicebot-db \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=MiPasswordSeguro123

# Reemplaza "MiPasswordSeguro123" con tu password
# ⚠️ GUARDA ESTE PASSWORD - lo necesitarás después
```

**Qué significa cada cosa:**
- `voicebot-db` → Nombre de tu base de datos
- `MYSQL_8_0` → Versión de MySQL
- `db-f1-micro` → Tamaño (el más pequeño y barato)
- `us-central1` → Región (USA central)
- `root-password` → Password del usuario root

**Mientras se crea (5-10 min):** Puedes seguir con el próximo paso en paralelo.

✅ **Instancia creándose...**

---

### **Paso 4.3: Crear Database**

Una vez que la instancia esté lista (puedes verificar en https://console.cloud.google.com/sql):

```bash
# Crear database "bank"
gcloud sql databases create bank --instance=voicebot-db
```

✅ **Database creada**

---

### **Paso 4.4: Cargar Datos de Prueba**

Ahora vamos a conectarnos y cargar los clientes de prueba.

```bash
# Conectar a Cloud SQL
gcloud sql connect voicebot-db --user=root --quiet
```

Te pedirá el password que configuraste en el Paso 4.2.

**Una vez dentro de MySQL, ejecuta:**

```sql
USE bank;

CREATE TABLE customers (
    id VARCHAR(36) PRIMARY KEY,
    rut VARCHAR(9) NOT NULL UNIQUE,
    nombre VARCHAR(64) NOT NULL,
    nombre_completo VARCHAR(128) NOT NULL,
    telefono VARCHAR(12) NOT NULL UNIQUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customers (id, rut, nombre, nombre_completo, telefono) VALUES
(UUID(), '87654321', 'Nicolas', 'Nicolas Navarro Aravena', '+56984593400'),
(UUID(), '12345678', 'Mauricio', 'Mauricio González López', '+56982079489'),
(UUID(), '98765432', 'María', 'María Fernández Silva', '+56987654321'),
(UUID(), '55556666', 'Carlos', 'Carlos Rodríguez Pérez', '+56955556666');

-- Verificar que se cargaron
SELECT telefono, nombre, rut FROM customers;
```

Deberías ver los 4 clientes.

**Para salir de MySQL:**
```sql
EXIT;
```

✅ **Datos de prueba cargados**

---

## ☁️ PARTE 5: Deploy de Servicios en Cloud Run

**⏱️ Tiempo:** 30 minutos

Vamos a desplegar los 3 servicios: Actions, Rasa y Twilio.

---

### **Paso 5.1: Habilitar Cloud Run**

```bash
gcloud services enable run.googleapis.com
```

---

### **Paso 5.2: Deploy Actions Server**

```bash
PROJECT_ID="poc-preventa"

gcloud run deploy actions-server \
    --image=gcr.io/$PROJECT_ID/actions:latest \
    --region=us-central1 \
    --platform=managed \
    --memory=512Mi \
    --cpu=1 \
    --allow-unauthenticated
```

**Te preguntará:** `Allow unauthenticated invocations?` → **y** (yes)

**Guarda la URL que te da** (ejemplo):
```
Service URL: https://actions-server-abc123.us-central1.run.app
```

```bash
# Guardar en variable
ACTIONS_URL="https://actions-server-abc123.us-central1.run.app"
```

✅ **Actions Server deployado**

---

### **Paso 5.3: Deploy Rasa Server**

Necesitas tu licencia de Rasa Pro (desde tu .env):

```bash
# Cargar .env
source .env

gcloud run deploy rasa-server \
    --image=gcr.io/$PROJECT_ID/rasa:latest \
    --region=us-central1 \
    --platform=managed \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --allow-unauthenticated \
    --set-env-vars RASA_PRO_LICENSE="$RASA_PRO_LICENSE",ACTION_SERVER_URL="$ACTIONS_URL/webhook"
```

**Guarda la URL:**
```bash
RASA_URL="https://rasa-server-xyz789.us-central1.run.app"
```

✅ **Rasa Server deployado**

---

### **Paso 5.4: Deploy Twilio Server**

Este es el más importante, conecta con Cloud SQL:

```bash
# Obtener connection name de Cloud SQL
SQL_CONNECTION=$(gcloud sql instances describe voicebot-db --format="value(connectionName)")

echo "SQL Connection: $SQL_CONNECTION"
# Ejemplo: poc-preventa:us-central1:voicebot-db

gcloud run deploy twilio-server \
    --image=gcr.io/$PROJECT_ID/twilio:latest \
    --region=us-central1 \
    --platform=managed \
    --memory=1Gi \
    --cpu=1 \
    --allow-unauthenticated \
    --add-cloudsql-instances=$SQL_CONNECTION \
    --set-env-vars \
BASE_URL="TBD",\
RASA_URL="$RASA_URL/webhooks/rest/webhook",\
DB_HOST="/cloudsql/$SQL_CONNECTION",\
DB_PORT="3306",\
DB_USER="root",\
DB_PASSWORD="MiPasswordSeguro123",\
DB_NAME="bank",\
ELEVEN_API_KEY="$ELEVEN_API_KEY",\
ELEVEN_VOICE_ID="$ELEVEN_VOICE_ID",\
ELEVEN_VOICE_ID2="$ELEVEN_VOICE_ID2",\
FRESHDESK_API_KEY="$FRESHDESK_API_KEY",\
FRESHDESK_DOMAIN="$FRESHDESK_DOMAIN"
```

**⚠️ Importante:** Reemplaza `MiPasswordSeguro123` con el password que usaste en el Paso 4.2.

**Guarda la URL:**
```bash
TWILIO_URL="https://twilio-server-def456.us-central1.run.app"
```

**Actualizar BASE_URL:**
```bash
gcloud run services update twilio-server \
    --region=us-central1 \
    --update-env-vars BASE_URL="$TWILIO_URL"
```

✅ **Twilio Server deployado**

---

### **Paso 5.5: Configurar Permisos de Cloud SQL**

Para que Twilio Server pueda conectarse a Cloud SQL:

```bash
# Obtener service account
SERVICE_ACCOUNT=$(gcloud run services describe twilio-server \
    --region=us-central1 \
    --format='value(spec.template.spec.serviceAccountName)')

# Si está vacío, usar el default
if [ -z "$SERVICE_ACCOUNT" ]; then
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
    SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi

# Dar permisos
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudsql.client"
```

✅ **Permisos configurados**

---

## 📞 PARTE 6: Configurar Twilio

**⏱️ Tiempo:** 10 minutos

Ahora vamos a conectar tu número de Twilio con el servidor en GCP.

---

### **Paso 6.1: Actualizar Webhook de Voz**

1. Ve a: **https://console.twilio.com/**

2. Menú lateral → **Phone Numbers** → **Manage** → **Active Numbers**

3. **Click en tu número** (ejemplo: +56 2 2914 5014)

4. Scroll hasta **"Voice Configuration"**

5. En **"A CALL COMES IN":**
   - Selecciona: **Webhook**
   - URL: `[TU_TWILIO_URL]/webhook/twilio/voice`
   - Ejemplo: `https://twilio-server-def456.us-central1.run.app/webhook/twilio/voice`
   - HTTP: **POST**

6. Click en **"Save"** (abajo de la página)

✅ **Webhook de voz configurado**

---

### **Paso 6.2: Configurar Status Callback**

En la misma página del número:

1. Scroll hasta **"Call Status Changes"**

2. **Status Callback URL:**
   - URL: `[TU_TWILIO_URL]/webhook/twilio/status`
   - Ejemplo: `https://twilio-server-def456.us-central1.run.app/webhook/twilio/status`
   - HTTP: **POST**

3. **Events:** Marca las casillas:
   - ☑️ `completed`
   - ☑️ `failed`

4. Click en **"Save"**

✅ **Status callback configurado**

---

## 🧪 PARTE 7: Testing

**⏱️ Tiempo:** 15 minutos

Vamos a probar que todo funcione.

---

### **Paso 7.1: Verificar Servicios**

```bash
# Test Rasa (debe responder "Hello from Rasa")
curl https://rasa-server-xyz789.us-central1.run.app

# Test Actions (debe responder JSON con status: ok)
curl https://actions-server-abc123.us-central1.run.app/health

# Test Twilio (debe responder HTML)
curl https://twilio-server-def456.us-central1.run.app
```

✅ **Servicios responden**

---

### **Paso 7.2: Test Completo del Flujo**

```bash
# Test conversación con Rasa
curl -X POST https://rasa-server-xyz789.us-central1.run.app/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "hola"}'
```

Deberías ver una respuesta JSON con el mensaje del bot.

✅ **Rasa funcionando**

---

### **Paso 7.3: Llamada de Prueba Real**

1. **Llama** al número de Twilio desde uno de los teléfonos registrados:
   - +56984593400 (Nicolas)
   - +56982079489 (Mauricio)

2. **Flujo esperado:**
   - 🎙️ Bot te saluda por nombre
   - 📝 Pide tu RUT → Ingresas: `87654321`
   - 🎙️ Pregunta: "¿En qué puedo ayudarte?"
   - 🗣️ Dices: "Necesito bloquear mi tarjeta"
   - 🎙️ Pide últimos 4 dígitos → Ingresas: `1234`
   - 🎙️ Confirma: "Encontré tu tarjeta terminada en 1 2 3 4"
   - 🗣️ Dices: "Sí"
   - ✅ Tarjeta bloqueada

✅ **¡FUNCIONA!** 🎉

---

### **Paso 7.4: Ver Logs**

Si algo no funciona, revisa los logs:

```bash
# Logs de Twilio Server (el más importante)
gcloud run services logs read twilio-server --region=us-central1 --limit=50

# Logs de Rasa
gcloud run services logs read rasa-server --region=us-central1 --limit=50

# Logs de Actions
gcloud run services logs read actions-server --region=us-central1 --limit=50
```

---

## 💰 PARTE 8: Monitoreo de Costos

**⏱️ Tiempo:** 5 minutos

---

### **Ver Costos Actuales**

1. Ve a: **https://console.cloud.google.com/billing**

2. Click en tu cuenta de facturación

3. **"Informes"** → Ver gráficos de uso

**Costos estimados:**
- Cloud Run (3 servicios): $5-20/mes
- Cloud SQL (db-f1-micro): $10-20/mes
- Container Registry: $2-5/mes
- **TOTAL:** ~$17-45 USD/mes

**Con los $300 gratis:** Tienes ~6-17 meses sin pagar nada.

---

## 📋 Checklist Final

Verifica que hayas completado todo:

- [ ] Cuenta GCP creada con $300 gratis
- [ ] Proyecto creado y configurado
- [ ] gcloud CLI instalado y autenticado
- [ ] 3 imágenes Docker subidas a GCR
- [ ] Cloud SQL creado con 4 clientes de prueba
- [ ] Actions Server deployado
- [ ] Rasa Server deployado
- [ ] Twilio Server deployado y conectado a Cloud SQL
- [ ] Permisos de Cloud SQL configurados
- [ ] Webhook de Twilio actualizado
- [ ] Status callback configurado
- [ ] Llamada de prueba exitosa
- [ ] Logs sin errores

✅ **¡Todo completo!**

---

## 🆘 Troubleshooting

### **Problema: "Permission denied"**

```bash
# Reiniciar autenticación
gcloud auth login
gcloud auth application-default login
```

---

### **Problema: "Service unavailable" en Cloud Run**

```bash
# Ver logs para identificar el error
gcloud run services logs read [SERVICE_NAME] --region=us-central1 --tail

# Verificar que las env vars estén configuradas
gcloud run services describe [SERVICE_NAME] --region=us-central1
```

---

### **Problema: Bot dice "número no registrado"**

**Causa:** Cloud SQL no tiene datos o no conecta.

**Solución:**
```bash
# Verificar datos en Cloud SQL
gcloud sql connect voicebot-db --user=root

# Dentro de MySQL:
USE bank;
SELECT * FROM customers;

# Si no hay datos, cargar de nuevo (Paso 4.4)
```

---

### **Problema: Bot se queda en bucle pidiendo tarjeta**

**Causa:** Rasa no conecta con Actions Server.

**Solución:**
```bash
# Verificar que ACTIONS_URL esté correcta
gcloud run services describe rasa-server --region=us-central1 \
  --format='value(spec.template.spec.containers[0].env)'

# Debe aparecer ACTION_SERVER_URL
```

---

### **Problema: ElevenLabs da error "unusual activity"**

**Causa:** Cuenta free tier bloqueada.

**Solución:**
- Comprar plan pagado en https://elevenlabs.io ($5/mes)
- O remover voces de ElevenLabs (usará Polly de Twilio):

```bash
gcloud run services update twilio-server \
  --region=us-central1 \
  --remove-env-vars ELEVEN_API_KEY,ELEVEN_VOICE_ID,ELEVEN_VOICE_ID2
```

---

## 🎉 ¡FELICITACIONES!

Tu bot está en producción:
- ✅ Disponible 24/7
- ✅ No necesitas tu Mac prendida
- ✅ IP fija (adiós ngrok)
- ✅ Auto-escalable
- ✅ Costos predecibles (~$20-40/mes)

---

## 📞 Próximos Pasos (Opcional)

1. **Monitoreo avanzado:**
   - Configurar alertas por email
   - Dashboard de métricas

2. **Seguridad:**
   - Usar Secret Manager para passwords
   - Restringir acceso por IP

3. **CI/CD:**
   - Deploy automático desde Git

---

## 📚 Recursos Adicionales

- **Documentación GCP:** https://cloud.google.com/docs
- **Rasa Docs:** https://rasa.com/docs/
- **Twilio Docs:** https://www.twilio.com/docs

---

**Última actualización:** Noviembre 2025  
**Mantenedor:** Nicolas Navarro  
**Repositorio:** https://github.com/nicolasnavarro-2brains/bloqueo-sctbnk-voice

