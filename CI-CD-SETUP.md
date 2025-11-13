# 🔄 Configuración de CI/CD con Cloud Build

**Objetivo:** Automatizar deployment cuando se hace push a Git  
**Tiempo estimado:** 30 minutos  
**Resultado:** Push a `main` → Deploy automático en 10-15 minutos

---

## 📋 ¿Qué es CI/CD?

**CI/CD** = Continuous Integration / Continuous Deployment

**Flujo automático:**
```
Desarrollador hace: git push origin main
    ↓
Cloud Build detecta el cambio
    ↓
Build automático de imágenes Docker
    ↓
Deploy automático a Cloud Run
    ↓
Sistema actualizado sin intervención manual
```

**Ventajas:**
- ✅ No necesitas ejecutar scripts manualmente
- ✅ Deployment consistente cada vez
- ✅ Historial de todos los deployments
- ✅ Rollback fácil si algo falla

---

## 🚀 PARTE 1: Configurar Secret Manager

**⏱️ Tiempo:** 10 minutos

Cloud Build necesita acceso a credenciales (passwords, API keys). Las guardamos en Secret Manager.

---

### **Paso 1.1: Habilitar Secret Manager API**

```bash
gcloud services enable secretmanager.googleapis.com
```

---

### **Paso 1.2: Crear Secrets**

Crea un secret por cada credencial sensible:

```bash
PROJECT_ID="poc-preventa"  # Cambiar por tu proyecto

# Cargar .env
source .env

# Crear secrets
echo -n "$RASA_PRO_LICENSE" | gcloud secrets create rasa-pro-license \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$DB_PASSWORD" | gcloud secrets create db-password \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$ELEVEN_API_KEY" | gcloud secrets create eleven-api-key \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$ELEVEN_VOICE_ID" | gcloud secrets create eleven-voice-id \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$ELEVEN_VOICE_ID2" | gcloud secrets create eleven-voice-id2 \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$FRESHDESK_API_KEY" | gcloud secrets create freshdesk-api-key \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$FRESHDESK_DOMAIN" | gcloud secrets create freshdesk-domain \
  --data-file=- \
  --replication-policy="automatic"
```

**Verificar:**
```bash
gcloud secrets list
```

Deberías ver los 7 secrets creados.

✅ **Secrets creados**

---

### **Paso 1.3: Dar Permisos a Cloud Build**

Cloud Build necesita acceso a los secrets:

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Dar permisos a Cloud Build service account
gcloud secrets add-iam-policy-binding rasa-pro-license \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding eleven-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding eleven-voice-id \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding eleven-voice-id2 \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding freshdesk-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding freshdesk-domain \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

✅ **Permisos configurados**

---

## 🔗 PARTE 2: Conectar GitHub con Cloud Build

**⏱️ Tiempo:** 15 minutos

---

### **Paso 2.1: Habilitar Cloud Build API**

```bash
gcloud services enable cloudbuild.googleapis.com
```

---

### **Paso 2.2: Conectar Repositorio GitHub**

**Opción A: Desde GCP Console (Más Fácil)**

1. Ve a: **https://console.cloud.google.com/cloud-build/triggers**

2. Click en **"Conectar repositorio"**

3. Selecciona **"GitHub (Cloud Build GitHub App)"**

4. **Autoriza** Cloud Build a acceder a tu GitHub

5. Selecciona tu repositorio: `nicolasnavarro-2brains/bloqueo-sctbnk-voice`

6. Click en **"Conectar"**

✅ **Repositorio conectado**

---

### **Paso 2.3: Crear Trigger**

1. En la misma página, click en **"Crear trigger"**

2. **Configuración básica:**
   - **Nombre:** `deploy-production`
   - **Descripción:** `Deploy automático cuando se hace push a main`

3. **Evento:**
   - **Tipo de evento:** Push a una rama
   - **Rama:** `^main$` (solo main)

4. **Configuración:**
   - **Tipo:** Archivo de configuración de Cloud Build
   - **Ubicación:** `cloudbuild.yaml`

5. **Opciones avanzadas:**
   - **Máquina de compilación:** `e2-highcpu-8` (más rápida)
   - **Timeout:** `1800s` (30 minutos)

6. Click en **"Crear"**

✅ **Trigger creado**

---

### **Paso 2.4: Dar Permisos a Cloud Build y Cloud Run**

Cloud Build necesita permisos para deployar a Cloud Run y acceder a Secret Manager:

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
CLOUD_RUN_SA="${PROJECT_ID}@appspot.gserviceaccount.com"

# Permisos para Cloud Build
# 1. Secret Manager a nivel de proyecto
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/secretmanager.secretAccessor"

# 2. Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/run.admin"

# 3. Service Account User
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"

# Permisos para Cloud Run Service Account (necesarios para --set-secrets)
# 1. Secret Manager a nivel de proyecto
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_RUN_SA}" \
  --role="roles/secretmanager.secretAccessor"

# 2. Permisos en secrets específicos
for secret in rasa-pro-license db-password eleven-api-key eleven-voice-id eleven-voice-id2 freshdesk-api-key freshdesk-domain; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor"
done
```

✅ **Permisos configurados**

> **Nota:** Estos permisos son necesarios porque Cloud Run accede directamente a Secret Manager cuando usamos `--set-secrets` en lugar de `--set-env-vars`.

---

## 🧪 PARTE 3: Probar CI/CD

**⏱️ Tiempo:** 5 minutos

---

### **Paso 3.1: Hacer un Cambio y Push**

```bash
# Hacer un cambio pequeño (ej: actualizar README)
echo "# Test CI/CD" >> README.md

# Commit y push
git add README.md
git commit -m "Test: CI/CD deployment"
git push origin main
```

---

### **Paso 3.2: Ver Build en Progreso**

1. Ve a: **https://console.cloud.google.com/cloud-build/builds**

2. Deberías ver un build **"EN PROGRESO"**

3. Click en el build para ver logs en tiempo real

**El build hará:**
- ✅ Build de 3 imágenes Docker
- ✅ Push a Container Registry
- ✅ Deploy de Actions Server
- ✅ Deploy de Rasa Server
- ✅ Deploy de Twilio Server

**⏱️ Tiempo:** 10-15 minutos

---

### **Paso 3.3: Verificar Deployment**

Una vez que el build termine con ✅:

```bash
# Ver servicios actualizados
gcloud run services list --region=us-central1

# Ver logs del último deployment
gcloud run services describe twilio-server --region=us-central1
```

✅ **CI/CD funcionando**

---

## 📊 Monitoreo de Builds

### **Ver Historial de Builds:**

1. Ve a: **https://console.cloud.google.com/cloud-build/builds**

2. Verás todos los builds con:
   - ✅ Éxito
   - ❌ Fallido
   - ⏳ En progreso

### **Ver Logs Detallados:**

Click en cualquier build para ver:
- Tiempo de cada paso
- Logs de Docker build
- Logs de deployment
- Errores si los hay

---

## 🔄 Actualizar Secrets

Si cambias alguna credencial:

```bash
# Actualizar secret
echo -n "nuevo_valor" | gcloud secrets versions add db-password \
  --data-file=-

# El próximo build usará el nuevo valor automáticamente
```

---

## 🛠️ Troubleshooting

### **Problema: Build falla con "Permission denied"**

```bash
# Verificar permisos de Cloud Build
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
```

---

### **Problema: "Secret not found"**

```bash
# Verificar que los secrets existan
gcloud secrets list

# Verificar permisos
gcloud secrets get-iam-policy rasa-pro-license
```

---

### **Problema: Build tarda mucho**

**Solución:** Ya está configurado con `E2_HIGHCPU_8` (máquina rápida).  
Si quieres más velocidad, puedes usar `E2_HIGHCPU_32` (más caro).

---

## 📋 Checklist de Configuración

- [ ] Secret Manager API habilitado
- [ ] 7 secrets creados (Rasa, DB, ElevenLabs, Freshdesk)
- [ ] Permisos de secrets a Cloud Build
- [ ] Cloud Build API habilitado
- [ ] Repositorio GitHub conectado
- [ ] Trigger creado para rama `main`
- [ ] Permisos de Cloud Run a Cloud Build
- [ ] Test de push exitoso
- [ ] Build completado sin errores
- [ ] Servicios actualizados correctamente

---

## 🎯 Flujo Completo

```
1. Desarrollador hace cambios
   git add .
   git commit -m "Nueva feature"
   git push origin main

2. GitHub notifica a Cloud Build
   (automático)

3. Cloud Build ejecuta cloudbuild.yaml
   - Build imágenes Docker
   - Push a GCR
   - Deploy a Cloud Run
   (10-15 minutos)

4. Sistema actualizado automáticamente
   ✅ Sin intervención manual
```

---

## 🔧 Troubleshooting

### **Problema 1: Build falla con "Permission denied" para Secret Manager**

**Error:**
```
Permission 'secretmanager.versions.access' denied
```

**Solución:**
```bash
PROJECT_ID="tu-proyecto"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
CLOUD_RUN_SA="${PROJECT_ID}@appspot.gserviceaccount.com"

# Dar permisos a nivel de proyecto
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_RUN_SA}" \
  --role="roles/secretmanager.secretAccessor"

# Dar permisos en secrets específicos
for secret in rasa-pro-license db-password eleven-api-key eleven-voice-id eleven-voice-id2 freshdesk-api-key freshdesk-domain; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor"
  
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor"
done
```

---

### **Problema 2: Build falla en step "deploy-rasa" o "deploy-twilio"**

**Error:**
```
Build step failed: step exited with non-zero status: 1
```

**Solución:**
1. Verificar que los secrets existan:
   ```bash
   gcloud secrets list
   ```

2. Verificar que tengan versiones:
   ```bash
   gcloud secrets versions list rasa-pro-license
   ```

3. Verificar permisos (ver Problema 1)

4. Revisar logs del build:
   ```bash
   gcloud builds log [BUILD_ID]
   ```

---

### **Problema 3: Error de sintaxis YAML en cloudbuild.yaml**

**Error:**
```
yaml: line X: could not find expected ':'
```

**Solución:**
- Verificar que no haya problemas de indentación
- Validar YAML:
  ```bash
  python3 -c "import yaml; yaml.safe_load(open('cloudbuild.yaml'))"
  ```

---

### **Problema 4: Build funciona pero servicios no responden**

**Solución:**
1. Verificar que los servicios estén desplegados:
   ```bash
   gcloud run services list --region=us-central1
   ```

2. Verificar logs de Cloud Run:
   ```bash
   gcloud run services logs read twilio-server --region=us-central1
   ```

3. Verificar que las URLs estén configuradas en Twilio

---

### **Problema 5: Build tarda mucho tiempo**

**Normal:**
- Build completo: 20-30 minutos (entrena modelo Rasa)
- Build sin entrenar: 10-15 minutos

**Si tarda más:**
- Verificar que no haya builds en cola
- Considerar usar máquinas más potentes en `cloudbuild.yaml`:
  ```yaml
  options:
    machineType: 'E2_HIGHCPU_8'
  ```

---

## 💰 Costos

**Cloud Build:**
- $0.003 por minuto de build
- Build típico: 10-15 minutos = **$0.03 - $0.045 por deployment**

**Con 10 deployments/mes:** ~$0.50 USD/mes

---

## 📚 Recursos

- **Cloud Build Docs:** https://cloud.google.com/build/docs
- **Secret Manager:** https://cloud.google.com/secret-manager/docs
- **Cloud Build Triggers:** https://cloud.google.com/build/docs/triggers

---

**Última actualización:** Noviembre 2025  
**Mantenedor:** Nicolas Navarro

