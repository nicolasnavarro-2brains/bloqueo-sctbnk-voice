# POC por Voz - Deployment en Nube (GCP)

**De:** Nicolas Navarro  
**Repo GitHub:** [bloqueo-sctbnk-voice](https://github.com/nicolasnavarro-2brains/bloqueo-sctbnk-voice)

---

## 📦 Versiones Necesarias

| Componente | Versión | Notas |
|------------|---------|-------|
| Rasa Pro | 3.13.5 | Motor conversacional |
| Rasa SDK | 3.9.0 | Actions server |
| Python | 3.10.12 | Entorno runtime |
| Docker | Latest | Para build de imágenes |
| Cloud SQL | MySQL 8.0+ | Base de datos |
| Cloud Run | Latest | Serverless containers |

---

## 🚀 Deployment Automatizado (Recomendado)

### Requisitos Previos:
- ✅ Cuenta GCP con proyecto creado
- ✅ gcloud CLI instalado
- ✅ Docker instalado
- ✅ Archivo `.env` configurado

### Pasos:

```bash
# 1. Clonar repositorio
git clone https://github.com/nicolasnavarro-2brains/bloqueo-sctbnk-voice.git
cd bloqueo-sctbnk-voice

# 2. Configurar credenciales
cp env.example .env
nano .env  # Editar con tus API keys

# 3. Autenticar en GCP
gcloud auth login
gcloud config set project poc-preventa  # Cambiar por tu proyecto

# 4. Deployment automatizado (1 COMANDO)
./deploy-gcp.sh
```

**El script automáticamente:**
- ✅ Habilita APIs necesarias
- ✅ Crea Cloud SQL con datos de prueba
- ✅ Build de 3 imágenes Docker
- ✅ Push a Google Container Registry
- ✅ Deploy de Actions Server
- ✅ Deploy de Rasa Server (con licencia Pro)
- ✅ Deploy de Twilio Server (conectado a Cloud SQL)
- ✅ Configura permisos y variables de entorno

**Tiempo estimado:** 15-20 minutos

---

## ⚙️ Variables de Entorno Clave

```bash
# === RASA PRO ===
RASA_PRO_LICENSE="eyJhbGc..."

# === ELEVENLABS TTS ===
ELEVEN_API_KEY="sk-..."
ELEVEN_VOICE_ID="<id_voz_femenina>"
ELEVEN_VOICE_ID2="<id_voz_masculina>"

# === BASE DE DATOS (Cloud SQL) ===
DB_PASSWORD="<password_seguro>"  # Para Cloud SQL
DB_USER="root"
DB_NAME="bank"

# === FRESHDESK ===
FRESHDESK_API_KEY="<tu_api_key>"
FRESHDESK_DOMAIN="<tu_dominio>"

# === GCP (configurar en script) ===
PROJECT_ID="poc-preventa"  # Tu proyecto GCP
REGION="us-central1"
```

---

## 📞 Configurar Twilio (Manual)

### Después del deployment, configurar en Twilio Console:

1. **Ir a:** https://console.twilio.com/
2. **Phone Numbers** → **Manage** → **Active Numbers**
3. **Seleccionar tu número** (ej: `+56 2 2914 5014`)
4. **Voice Configuration:**

| Campo | Valor |
|-------|-------|
| A CALL COMES IN | Webhook |
| URL | `https://twilio-server-XXX.run.app/webhook/twilio/voice` |
| HTTP | POST |

5. **Call Status Changes:**

| Campo | Valor |
|-------|-------|
| Status Callback URL | `https://twilio-server-XXX.run.app/webhook/twilio/status` |
| HTTP | POST |
| Events | ✓ completed, ✓ failed |

6. **Save**

*(La URL exacta te la da el script al finalizar)*

---

## 🧪 Testing

### Verificar Servicios:

```bash
# Ver estado de todos los servicios
gcloud run services list --region=us-central1

# Ver logs en tiempo real
gcloud run services logs tail twilio-server --region=us-central1
```

### Probar Flujo Completo:

**Llamar desde un teléfono de prueba:**

| Nombre | Teléfono | RUT |
|--------|----------|-----|
| Nicolas | +56984593400 | 87654321 |
| Mauricio | +56982079489 | 12345678 |
| María | +56987654321 | 98765432 |
| Carlos | +56955556666 | 55556666 |

**Flujo esperado:**
1. 🎙️ Bot saluda por nombre
2. 📝 Ingresa RUT
3. 🎙️ Bot pregunta: "¿En qué puedo ayudarte?"
4. 🗣️ "Necesito bloquear mi tarjeta"
5. 🎙️ Bot pide últimos 4 dígitos
6. 📝 Ingresa: `1234`
7. 🎙️ Bot confirma: "Encontré tu tarjeta terminada en 1 2 3 4"
8. 🗣️ "Sí"
9. ✅ Tarjeta bloqueada + ticket Freshdesk

---

## 🔧 Comandos Útiles

### Ver Logs:

```bash
# Logs de Twilio Server
gcloud run services logs read twilio-server --region=us-central1 --limit=50

# Logs de Rasa Server
gcloud run services logs read rasa-server --region=us-central1 --limit=50

# Logs de Actions Server
gcloud run services logs read actions-server --region=us-central1 --limit=50
```

### Actualizar Código:

```bash
# 1. Hacer cambios en el código
# 2. Re-ejecutar deployment
./deploy-gcp.sh --update

# O manual:
docker build -f Dockerfile.twilio -t gcr.io/${PROJECT_ID}/twilio:latest .
docker push gcr.io/${PROJECT_ID}/twilio:latest
gcloud run deploy twilio-server --image=gcr.io/${PROJECT_ID}/twilio:latest --region=us-central1
```

### Ver URLs de Servicios:

```bash
# Ver todas las URLs
gcloud run services list --region=us-central1 --format="table(metadata.name,status.url)"
```

---

## 🛠️ Troubleshooting

### Problema: "Número no registrado"

```bash
# Verificar datos en Cloud SQL
gcloud sql connect voicebot-db --user=root --quiet
# Password: <el que configuraste>

USE bank;
SELECT * FROM customers;
```

**Solución:** Si la tabla está vacía, ejecutar:
```bash
./scripts/cargar-datos-cloud-sql.sh
```

---

### Problema: Bot en bucle pidiendo tarjeta

**Causa:** Rasa no conecta con Actions Server

**Solución:**
```bash
# Verificar endpoints.yml
cat endpoints.yml

# Re-deployar Rasa si es necesario
./deploy-gcp.sh --rasa-only
```

---

### Problema: ElevenLabs bloqueado

**Error:** `"detected_unusual_activity"`

**Solución:**
```bash
# Opción A: Comprar plan ElevenLabs ($5 USD/mes)
# Opción B: Usar voz fallback de Twilio
gcloud run services update twilio-server \
  --region=us-central1 \
  --remove-env-vars=ELEVEN_API_KEY,ELEVEN_VOICE_ID,ELEVEN_VOICE_ID2
```

---

## 📊 Arquitectura

```
┌─────────────────────────────────────────────┐
│         Usuario llama a Twilio              │
│              +56 2 2914 5014                │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│      Twilio Server (Cloud Run)              │
│  - Recibe llamada                           │
│  - TTS con ElevenLabs                       │
│  - Audio en RAM                             │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│      Rasa Server (Cloud Run)                │
│  - Motor conversacional                     │
│  - Flows + NLU                              │
│  - Licencia Pro                             │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│      Actions Server (Cloud Run)             │
│  - Custom actions                           │
│  - Lógica de negocio                        │
│  - Integración Freshdesk                    │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│      Cloud SQL (MySQL)                      │
│  - Datos de clientes                        │
│  - RUT y teléfonos                          │
└─────────────────────────────────────────────┘
```

---

## 💰 Costos Estimados (GCP)

| Servicio | Config | Costo Mensual |
|----------|--------|---------------|
| Cloud Run - Twilio | 1 GB RAM | $5 - $15 |
| Cloud Run - Rasa | 2 GB RAM | $15 - $30 |
| Cloud Run - Actions | 512 MB | $3 - $10 |
| Cloud SQL | db-f1-micro | $10 - $20 |
| **TOTAL** | | **$33 - $75 USD** |

*Basado en ~1000 llamadas/mes. Incluye almacenamiento y tráfico.*

---

## 📚 Documentación Completa

- **Arquitectura Técnica:** `ARQUITECTURA-TECNICA.md`
- **Deployment Detallado:** `DEPLOYMENT-GCP.md`
- **Repositorio:** https://github.com/nicolasnavarro-2brains/bloqueo-sctbnk-voice

---

## ✅ Checklist de Deployment

- [ ] Cuenta GCP creada y proyecto configurado
- [ ] gcloud CLI instalado y autenticado
- [ ] Docker instalado localmente
- [ ] Archivo `.env` configurado con credenciales
- [ ] Script `deploy-gcp.sh` ejecutado sin errores
- [ ] URLs de servicios guardadas
- [ ] Webhooks de Twilio configurados
- [ ] Test de llamada exitoso
- [ ] Logs verificados sin errores

---

**🎉 Sistema Listo**  
**24/7 Disponible | Escalable | Sin depender de tu Mac**

**Última actualización:** Noviembre 2025  
**Mantenedor:** Nicolas Navarro

