# 🚀 Guía de Deployment - Scotiabank Voice Bot

Esta guía te llevará desde desarrollo local hasta producción en la nube con Docker y Kubernetes.

---

## 📋 Tabla de Contenidos

1. [Testing Local con Docker](#testing-local-con-docker)
2. [Deployment a Kubernetes](#deployment-a-kubernetes)
3. [Proveedores Cloud](#proveedores-cloud)
4. [Configuración de Twilio](#configuración-de-twilio)
5. [Monitoreo y Logs](#monitoreo-y-logs)
6. [Troubleshooting](#troubleshooting)

---

## 🐳 Testing Local con Docker

### Prerequisitos

```bash
# Instalar Docker Desktop
# https://www.docker.com/products/docker-desktop

# Verificar instalación
docker --version
docker-compose --version
```

### Paso 1: Configurar Variables de Entorno

```bash
# Copiar .env.example a .env
cp env.example .env

# Editar .env con tus credenciales
nano .env
```

### Paso 2: Entrenar el Modelo de Rasa

```bash
# Activar entorno virtual
source venv/bin/activate

# Entrenar modelo
rasa train

# Verificar que se creó models/*.tar.gz
ls -lh models/
```

### Paso 3: Build de las Imágenes Docker

```bash
# Build de todas las imágenes
docker-compose build

# O build individual
docker build -f Dockerfile.rasa -t sctbnk-rasa .
docker build -f Dockerfile.actions -t sctbnk-actions .
docker build -f Dockerfile.twilio -t sctbnk-twilio .
```

### Paso 4: Iniciar los Servicios

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Ver solo logs de un servicio
docker-compose logs -f twilio
```

### Paso 5: Verificar que Todo Funciona

```bash
# Verificar servicios corriendo
docker-compose ps

# Probar endpoints
curl http://localhost:5005  # Rasa
curl http://localhost:5055/health  # Actions
curl http://localhost:5000  # Twilio

# Ejecutar tests
./test_all_scenarios.sh
```

### Paso 6: Exponer con ngrok (para testing con Twilio)

```bash
# En otra terminal
ngrok http 5000

# Copiar la URL https://xxxxx.ngrok.io
# Configurarla en Twilio Console
```

### Detener Servicios

```bash
# Detener todo
docker-compose down

# Detener y borrar volúmenes (¡cuidado con la BD!)
docker-compose down -v
```

---

## ☸️ Deployment a Kubernetes

### Prerequisitos

```bash
# Instalar kubectl
# https://kubernetes.io/docs/tasks/tools/

# Verificar instalación
kubectl version --client
```

### Opción 1: Testing Local con Minikube

```bash
# Instalar minikube
# https://minikube.sigs.k8s.io/docs/start/

# Iniciar cluster local
minikube start --cpus 4 --memory 8192

# Habilitar ingress
minikube addons enable ingress

# Verificar
kubectl cluster-info
```

### Opción 2: Cluster en la Nube

Ver sección [Proveedores Cloud](#proveedores-cloud)

---

## 📦 Build y Push de Imágenes

### 1. Configurar Docker Registry

**Docker Hub:**
```bash
# Login
docker login

# Tag images
docker tag sctbnk-rasa tu-usuario/sctbnk-rasa:latest
docker tag sctbnk-actions tu-usuario/sctbnk-actions:latest
docker tag sctbnk-twilio tu-usuario/sctbnk-twilio:latest

# Push
docker push tu-usuario/sctbnk-rasa:latest
docker push tu-usuario/sctbnk-actions:latest
docker push tu-usuario/sctbnk-twilio:latest
```

**AWS ECR:**
```bash
# Login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin tu-cuenta.dkr.ecr.us-east-1.amazonaws.com

# Tag y push
docker tag sctbnk-rasa:latest tu-cuenta.dkr.ecr.us-east-1.amazonaws.com/sctbnk-rasa:latest
docker push tu-cuenta.dkr.ecr.us-east-1.amazonaws.com/sctbnk-rasa:latest
```

### 2. Actualizar Manifiestos K8s

Editar `k8s/*-deployment.yml` y cambiar:
```yaml
image: tu-registry/sctbnk-rasa:latest
```

---

## 🚀 Deployment a Kubernetes

### Paso 1: Crear Namespace

```bash
kubectl apply -f k8s/namespace.yml
```

### Paso 2: Configurar Secrets

```bash
# Opción A: Desde archivo .env
kubectl create secret generic sctbnk-secrets \
  --from-env-file=.env \
  --namespace=sctbnk-voice

# Opción B: Desde manifiesto
# Editar k8s/secrets.yml con tus valores
kubectl apply -f k8s/secrets.yml
```

### Paso 3: Deploy de MariaDB

```bash
kubectl apply -f k8s/mariadb-deployment.yml

# Esperar a que esté listo
kubectl wait --for=condition=ready pod -l app=mariadb -n sctbnk-voice --timeout=300s
```

### Paso 4: Inicializar Base de Datos

```bash
# Copiar script de setup
kubectl cp setup_test_data.py sctbnk-voice/$(kubectl get pod -l app=mariadb -n sctbnk-voice -o jsonpath='{.items[0].metadata.name}'):/tmp/

# Ejecutar en el pod
kubectl exec -it -n sctbnk-voice $(kubectl get pod -l app=mariadb -n sctbnk-voice -o jsonpath='{.items[0].metadata.name}') -- bash

# Dentro del pod
apt-get update && apt-get install -y python3 python3-pip
pip3 install pymysql python-dotenv
python3 /tmp/setup_test_data.py
exit
```

### Paso 5: Deploy de Actions

```bash
kubectl apply -f k8s/actions-deployment.yml

# Verificar
kubectl get pods -n sctbnk-voice -l app=actions
kubectl logs -f -n sctbnk-voice -l app=actions
```

### Paso 6: Deploy de Rasa

```bash
kubectl apply -f k8s/rasa-deployment.yml

# Verificar
kubectl get pods -n sctbnk-voice -l app=rasa
kubectl logs -f -n sctbnk-voice -l app=rasa
```

### Paso 7: Deploy de Twilio Server

```bash
kubectl apply -f k8s/twilio-deployment.yml

# Verificar
kubectl get pods -n sctbnk-voice -l app=twilio
```

### Paso 8: Obtener IP Pública

```bash
# Ver servicios
kubectl get services -n sctbnk-voice

# Obtener IP pública del LoadBalancer
kubectl get service twilio-service -n sctbnk-voice -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# O si es hostname (AWS)
kubectl get service twilio-service -n sctbnk-voice -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

---

## ☁️ Proveedores Cloud

### DigitalOcean (Recomendado para empezar)

**Ventajas:**
- ✅ Más barato (~$40/mes)
- ✅ Interfaz simple
- ✅ Kubernetes managed
- ✅ Documentación clara

**Pasos:**
```bash
# 1. Crear cuenta en DigitalOcean
# 2. Crear Kubernetes cluster (3 nodos, $12 cada uno)
# 3. Descargar kubeconfig
doctl kubernetes cluster kubeconfig save tu-cluster

# 4. Verificar conexión
kubectl get nodes

# 5. Deploy (usar los comandos de arriba)
```

### Google Cloud (GKE)

**Ventajas:**
- ✅ Excelente performance
- ✅ Autoescalado
- ✅ $300 créditos gratis

**Pasos:**
```bash
# 1. Crear proyecto en GCP
# 2. Habilitar Kubernetes Engine API
# 3. Crear cluster
gcloud container clusters create sctbnk-cluster \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --zone=us-central1-a

# 4. Obtener credenciales
gcloud container clusters get-credentials sctbnk-cluster --zone=us-central1-a

# 5. Deploy
kubectl apply -f k8s/
```

### AWS (EKS)

**Ventajas:**
- ✅ Integración con otros servicios AWS
- ✅ Muy robusto

**Pasos:**
```bash
# 1. Instalar eksctl
# 2. Crear cluster
eksctl create cluster \
  --name sctbnk-cluster \
  --region us-east-1 \
  --nodes 3 \
  --node-type t3.medium

# 3. Verificar
kubectl get nodes

# 4. Deploy
kubectl apply -f k8s/
```

---

## 📱 Configuración de Twilio

### 1. Obtener IP Pública

```bash
# Obtener IP/hostname del LoadBalancer
kubectl get service twilio-service -n sctbnk-voice
```

### 2. Configurar Webhook en Twilio Console

1. Ir a https://console.twilio.com/
2. Phone Numbers → Active Numbers
3. Seleccionar tu número
4. Configurar webhook:
   ```
   https://TU-IP-PUBLICA/webhook/twilio/voice
   ```
5. Method: HTTP POST
6. Save

### 3. Configurar Status Callback (Opcional)

Para limpieza automática del caché:
```
https://TU-IP-PUBLICA/webhook/twilio/status
```

---

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real

```bash
# Todos los pods
kubectl logs -f -n sctbnk-voice --all-containers=true

# Por servicio
kubectl logs -f -n sctbnk-voice -l app=twilio
kubectl logs -f -n sctbnk-voice -l app=rasa
kubectl logs -f -n sctbnk-voice -l app=actions

# Pod específico
kubectl logs -f -n sctbnk-voice nombre-del-pod
```

### Verificar Estado de Pods

```bash
# Ver todos los pods
kubectl get pods -n sctbnk-voice

# Ver detalle de un pod
kubectl describe pod nombre-del-pod -n sctbnk-voice

# Ver recursos consumidos
kubectl top pods -n sctbnk-voice
kubectl top nodes
```

### Acceder a un Pod

```bash
# Shell interactivo
kubectl exec -it -n sctbnk-voice nombre-del-pod -- /bin/bash

# Ejecutar comando
kubectl exec -n sctbnk-voice nombre-del-pod -- ls -la
```

---

## 🐛 Troubleshooting

### Pod no inicia

```bash
# Ver eventos
kubectl describe pod nombre-del-pod -n sctbnk-voice

# Ver logs
kubectl logs nombre-del-pod -n sctbnk-voice

# Problemas comunes:
# 1. Imagen no encontrada → verificar registry
# 2. Secrets no configurados → kubectl get secrets -n sctbnk-voice
# 3. Falta recursos → kubectl describe nodes
```

### Base de datos no conecta

```bash
# Verificar servicio de BD
kubectl get service mariadb-service -n sctbnk-voice

# Probar conexión desde otro pod
kubectl run -it --rm debug --image=mysql:8 --restart=Never -- mysql -h mariadb-service.sctbnk-voice -u nico -p
```

### LoadBalancer sin IP

```bash
# Verificar evento del servicio
kubectl describe service twilio-service -n sctbnk-voice

# Si tu proveedor no soporta LoadBalancer, usa NodePort:
# Editar k8s/twilio-deployment.yml: type: NodePort

# Obtener puerto
kubectl get service twilio-service -n sctbnk-voice
# Usar: http://NODE-IP:NODE-PORT
```

### Rasa no responde

```bash
# Verificar que el modelo existe
kubectl exec -n sctbnk-voice -l app=rasa -- ls -la /app/models/

# Si no hay modelo, copiarlo:
kubectl cp models/tu-modelo.tar.gz sctbnk-voice/nombre-pod-rasa:/app/models/

# Reiniciar pods de Rasa
kubectl rollout restart deployment/rasa -n sctbnk-voice
```

---

## 🔄 Actualizar el Sistema

### Actualizar Código

```bash
# 1. Build nueva imagen
docker build -f Dockerfile.twilio -t tu-registry/sctbnk-twilio:v2 .

# 2. Push
docker push tu-registry/sctbnk-twilio:v2

# 3. Actualizar deployment
kubectl set image deployment/twilio twilio=tu-registry/sctbnk-twilio:v2 -n sctbnk-voice

# 4. Ver progreso
kubectl rollout status deployment/twilio -n sctbnk-voice
```

### Rollback

```bash
# Ver historial
kubectl rollout history deployment/twilio -n sctbnk-voice

# Volver a versión anterior
kubectl rollout undo deployment/twilio -n sctbnk-voice
```

---

## 💰 Costos Estimados

| Proveedor | Configuración | Costo Mensual |
|-----------|--------------|---------------|
| **DigitalOcean** | 3 nodos (2vCPU, 4GB RAM) | ~$36/mes |
| **DigitalOcean** | 3 nodos (2vCPU, 4GB RAM) + LB | ~$42/mes |
| **GCP (GKE)** | 3 nodos (e2-medium) | ~$75/mes |
| **AWS (EKS)** | 3 nodos (t3.medium) | ~$80/mes + $75 (EKS) = $155/mes |

**Recomendación:** Empezar con DigitalOcean, migrar a GCP/AWS si necesitas escalar.

---

## ✅ Checklist de Deployment

- [ ] Docker images construidas y pusheadas
- [ ] Secrets configurados en Kubernetes
- [ ] MariaDB desplegado y inicializado
- [ ] Actions desplegado y conectado a BD
- [ ] Rasa desplegado con modelo entrenado
- [ ] Twilio server desplegado
- [ ] LoadBalancer con IP pública asignada
- [ ] Twilio webhook configurado
- [ ] Prueba de llamada exitosa
- [ ] Monitoreo configurado
- [ ] Backups de BD configurados

---

## 📞 Soporte

Si tienes problemas, revisa:
1. Logs de Kubernetes
2. Esta guía de troubleshooting
3. Documentación de tu proveedor cloud
4. Issues en GitHub del proyecto

**¡Buena suerte con el deployment! 🚀**

