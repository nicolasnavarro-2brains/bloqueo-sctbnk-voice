# ☁️ Estrategia de Deployment en Google Cloud Platform (GCP)

## 📋 Resumen Ejecutivo

Este documento presenta la estrategia para desplegar el bot de voz de Scotiabank en **Google Cloud Platform (GCP)** usando Docker y Kubernetes, eliminando la dependencia de equipos locales y ngrok.

---

## 🎯 Objetivos

✅ **Disponibilidad 24/7** - Sin depender de laptops  
✅ **Escalabilidad** - Manejar múltiples llamadas concurrentes  
✅ **Confiabilidad** - Auto-recuperación ante fallos  
✅ **IP Fija** - Eliminar dependencia de ngrok  
✅ **Profesionalismo** - Infraestructura enterprise en GCP  

---

## 📊 Situación Actual vs. Propuesta

### **ANTES (Desarrollo Local)**
```
Laptop + ngrok
  ├── Python scripts corriendo localmente
  ├── ngrok para exponer localhost
  ├── IP cambia cada vez que se reinicia
  └── ❌ Solo funciona si la laptop está encendida
```

**Problemas:**
- ❌ Depende de que alguien tenga su laptop encendida
- ❌ IP cambia constantemente (ngrok gratuito)
- ❌ Sin redundancia
- ❌ No escala
- ❌ No profesional

### **DESPUÉS (GCP)**
```
Google Cloud Platform
  ├── GKE (Google Kubernetes Engine)
  │   ├── 3 pods de Twilio Server (auto-escala)
  │   ├── 2 pods de Rasa (redundancia)
  │   ├── 2 pods de Actions (redundancia)
  │   └── Cloud SQL (MariaDB administrado)
  ├── Cloud Load Balancer con IP fija
  └── ✅ 24/7, auto-escalable, enterprise-grade
```

**Beneficios:**
- ✅ Disponible 24/7 sin intervención humana
- ✅ IP pública fija de GCP
- ✅ Redundancia automática
- ✅ Escala según demanda
- ✅ Infraestructura enterprise

---

## 🏗️ Arquitectura en GCP

```
                    ☁️ GOOGLE CLOUD PLATFORM
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  🌐 Cloud Load Balancer (IP Pública Fija)                │
│     └── https://voicebot.scotiabank.com                  │
│            │                                              │
│            ▼                                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │  GKE - Kubernetes Cluster                       │    │
│  │                                                  │    │
│  │  📞 Twilio Pods (3 réplicas - auto-escala)      │    │
│  │     └─► Audio en RAM (ElevenLabs TTS)           │    │
│  │            │                                     │    │
│  │            ▼                                     │    │
│  │  🤖 Rasa Pods (2 réplicas)                      │    │
│  │     └─► Motor conversacional IA                 │    │
│  │            │                                     │    │
│  │            ▼                                     │    │
│  │  ⚙️ Actions Pods (2 réplicas)                   │    │
│  │     └─► Lógica negocio + Freshdesk              │    │
│  └──────────────────┬───────────────────────────────┘    │
│                     │                                     │
│                     ▼                                     │
│  🗄️ Cloud SQL (MariaDB)                                  │
│     └─► Base de datos administrada                       │
│                                                           │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
            Twilio Voice API
```

---

## 💰 Análisis de Costos (GCP)

### **Opción 1: GKE Standard (Recomendado para Producción)**

| Recurso | Especificación | Costo Mensual |
|---------|----------------|---------------|
| **GKE Cluster** | 3 nodos e2-medium | ~$73 USD |
| **Cloud SQL** | db-n1-standard-1 + 20GB | ~$50 USD |
| **Load Balancer** | 1 IP estática + tráfico | ~$18 USD |
| **Container Registry** | Almacenamiento imágenes | ~$5 USD |
| **Cloud Logging** | Logs y métricas | ~$10 USD |
| **TOTAL** | | **~$156 USD/mes** |

### **Opción 2: Cloud Run (Serverless - Más Económico)**

| Recurso | Especificación | Costo Mensual |
|---------|----------------|---------------|
| **Cloud Run (3 servicios)** | Auto-escala, pay-per-use | ~$15-30 USD |
| **Cloud SQL** | db-f1-micro + 10GB | ~$25 USD |
| **Load Balancer** | HTTPS + certificado | ~$18 USD |
| **Container Registry** | Imágenes Docker | ~$5 USD |
| **Cloud Logging** | Logs básicos | ~$5 USD |
| **TOTAL** | | **~$68-83 USD/mes** |

**✅ Recomendación:** Empezar con **Cloud Run** (serverless) por costo-beneficio

---

## 🚀 Plan de Implementación

### **Fase 1: Preparación (1 semana)**

✅ **Completado:**
- [x] Dockerización del sistema (4 contenedores)
- [x] Kubernetes manifests (k8s/)
- [x] Scripts de deployment
- [x] Documentación técnica

⏳ **Por hacer:**
- [ ] Crear proyecto en GCP
- [ ] Configurar billing account
- [ ] Habilitar APIs necesarias (GKE, Cloud SQL, Container Registry)

### **Fase 2: Setup Inicial GCP (3-5 días)**

**Paso 1: Crear Proyecto GCP**
```bash
gcloud projects create scotiabank-voicebot
gcloud config set project scotiabank-voicebot
```

**Paso 2: Habilitar APIs**
```bash
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

**Paso 3: Crear Cloud SQL (MariaDB)**
```bash
gcloud sql instances create voicebot-db \
    --database-version=MARIADB_10_6 \
    --tier=db-n1-standard-1 \
    --region=us-central1 \
    --root-password=<secure-password>
```

**Paso 4: Crear GKE Cluster**
```bash
gcloud container clusters create voicebot-cluster \
    --zone=us-central1-a \
    --num-nodes=3 \
    --machine-type=e2-medium \
    --enable-autoscaling --min-nodes=2 --max-nodes=10
```

### **Fase 3: Subir Imágenes (1 día)**

```bash
# Tag y push de imágenes a GCR
docker tag bloqueo-sctbnk-voice-rasa gcr.io/scotiabank-voicebot/rasa:v1.0
docker tag bloqueo-sctbnk-voice-actions gcr.io/scotiabank-voicebot/actions:v1.0
docker tag bloqueo-sctbnk-voice-twilio gcr.io/scotiabank-voicebot/twilio:v1.0

docker push gcr.io/scotiabank-voicebot/rasa:v1.0
docker push gcr.io/scotiabank-voicebot/actions:v1.0
docker push gcr.io/scotiabank-voicebot/twilio:v1.0
```

### **Fase 4: Deployment (1 día)**

```bash
# Actualizar k8s/*.yml con rutas de GCR
# Ejemplo en k8s/rasa-deployment.yml:
# image: gcr.io/scotiabank-voicebot/rasa:v1.0

# Deploy a GKE
kubectl apply -f k8s/namespace.yml
kubectl create secret generic sctbnk-secrets --from-env-file=.env -n sctbnk-voice
kubectl apply -f k8s/
```

### **Fase 5: Configuración Final (1 día)**

1. Obtener IP pública del Load Balancer:
```bash
kubectl get service twilio-service -n sctbnk-voice
```

2. Configurar dominio (opcional):
```bash
# En Cloud DNS o tu registrador
voicebot.scotiabank.com → IP_PUBLICA
```

3. Actualizar webhook en Twilio Console:
```
https://IP_PUBLICA/webhook/twilio/voice
o
https://voicebot.scotiabank.com/webhook/twilio/voice
```

4. Cargar datos de prueba:
```bash
kubectl exec -it deployment/twilio -n sctbnk-voice -- python setup_test_data.py
```

### **Fase 6: Testing y Go-Live (2-3 días)**

- [ ] Testing funcional completo
- [ ] Testing de carga (100+ llamadas simultáneas)
- [ ] Validación con equipo de QA
- [ ] Go-live gradual (10% → 50% → 100% tráfico)

---

## 📊 Timeline Completo

```
Semana 1: Preparación + Setup GCP
├─ Día 1-2: Crear proyecto, habilitar APIs
├─ Día 3: Crear Cloud SQL
└─ Día 4-5: Crear GKE cluster

Semana 2: Deployment
├─ Día 1: Subir imágenes a GCR
├─ Día 2: Deploy a Kubernetes
├─ Día 3: Configuración y DNS
└─ Día 4-5: Testing completo

Semana 3: Go-Live
├─ Día 1-2: Testing de carga
├─ Día 3: Validación final
└─ Día 4-5: Go-live gradual
```

**Total: ~3 semanas** (puede ser más rápido con dedicación full-time)

---

## 🔒 Consideraciones de Seguridad

### **1. Secrets Management**
```bash
# Usar Google Secret Manager
gcloud secrets create rasa-pro-license --data-file=license.txt
gcloud secrets create elevenlabs-api-key --data-file=api-key.txt
```

### **2. Network Security**
- ✅ VPC privada para GKE
- ✅ Cloud SQL con IP privada
- ✅ Firewall rules restrictivas
- ✅ HTTPS obligatorio (certificado SSL)

### **3. Access Control**
- ✅ IAM roles granulares
- ✅ Service accounts por servicio
- ✅ Audit logging habilitado

---

## 📈 Monitoreo y Alertas

### **Cloud Logging + Monitoring**

```bash
# Ver logs en tiempo real
gcloud logging read "resource.type=k8s_container AND resource.labels.namespace_name=sctbnk-voice"

# Crear alertas
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Bot Voice Errors" \
    --condition-display-name="High Error Rate" \
    --condition-threshold-value=10
```

### **Métricas Clave a Monitorear:**
- 📞 Llamadas por minuto
- ⏱️ Latencia de respuesta
- ❌ Tasa de errores
- 💾 Uso de CPU/RAM
- 🔄 Rate de auto-scaling

---

## 🎯 KPIs de Éxito

| Métrica | Target | Actual (post-deploy) |
|---------|--------|---------------------|
| **Uptime** | 99.9% | - |
| **Latencia promedio** | < 2 segundos | - |
| **Llamadas concurrentes** | 100+ | - |
| **Tasa de error** | < 1% | - |
| **Costo mensual** | < $100 USD | - |

---

## 🆘 Plan de Rollback

Si algo falla en producción:

```bash
# 1. Revertir a versión anterior
kubectl rollout undo deployment/twilio -n sctbnk-voice

# 2. O volver a ngrok temporalmente
kubectl scale deployment twilio --replicas=0 -n sctbnk-voice
# Lanzar servidor local + ngrok
```

---

## 📞 Soporte y Recursos

### **Documentación GCP:**
- https://cloud.google.com/kubernetes-engine/docs
- https://cloud.google.com/sql/docs
- https://cloud.google.com/run/docs

### **Soporte Interno:**
- **Técnico:** Nicolas Navarro
- **Infraestructura:** Equipo DevOps
- **Negocio:** Product Owner

---

## ✅ Checklist Pre-Deployment

- [ ] Cuenta GCP creada y billing configurado
- [ ] Credenciales de Rasa Pro disponibles
- [ ] Credenciales de ElevenLabs verificadas
- [ ] Credenciales de Twilio y Freshdesk actualizadas
- [ ] Testing local completado exitosamente
- [ ] Modelo de Rasa entrenado y validado
- [ ] Datos de prueba preparados
- [ ] Plan de rollback documentado
- [ ] Equipo capacitado en GCP/Kubernetes
- [ ] Stakeholders informados

---

## 💡 Resumen para Stakeholders

> **"Vamos a migrar el bot de voz desde laptops locales a Google Cloud Platform. Esto nos dará:**
> 
> ✅ **Disponibilidad 24/7** sin depender de equipos locales  
> ✅ **Escalabilidad automática** para manejar picos de llamadas  
> ✅ **Infraestructura profesional** con redundancia y monitoreo  
> ✅ **Costo controlado** (~$70-150 USD/mes según opción)  
> ✅ **Timeline: 3 semanas** desde setup hasta go-live
> 
> **Alternativa serverless (Cloud Run) puede reducir costo a ~$70/mes**"

---

**Estado Actual:** ✅ **Código listo para deployment**  
**Próximo Paso:** Setup de proyecto GCP  
**Timeline Estimado:** 3 semanas hasta producción  

---

*Documento actualizado: Octubre 2025*
