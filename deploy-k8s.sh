#!/bin/bash
# Script para deployment a Kubernetes

set -e

echo "☸️  =============================================="
echo "   DEPLOYMENT K8S - Scotiabank Voice Bot"
echo "=============================================="
echo ""

# Verificar kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl no está instalado"
    echo "   Instala desde: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

echo "✅ kubectl instalado"
echo ""

# Verificar conexión al cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ No hay conexión con un cluster de Kubernetes"
    echo "   Opciones:"
    echo "   1. Minikube local: minikube start"
    echo "   2. GKE: gcloud container clusters get-credentials CLUSTER-NAME"
    echo "   3. EKS: aws eks update-kubeconfig --name CLUSTER-NAME"
    echo "   4. DigitalOcean: doctl kubernetes cluster kubeconfig save CLUSTER-NAME"
    exit 1
fi

echo "✅ Conectado al cluster"
kubectl cluster-info
echo ""

# Namespace
echo "📦 Creando namespace..."
kubectl apply -f k8s/namespace.yml
echo ""

# Secrets
echo "🔐 Configurando secrets..."
if kubectl get secret sctbnk-secrets -n sctbnk-voice &> /dev/null; then
    echo "⚠️  Secret 'sctbnk-secrets' ya existe"
    read -p "¿Quieres recrearlo? (s/n): " respuesta
    if [ "$respuesta" = "s" ]; then
        kubectl delete secret sctbnk-secrets -n sctbnk-voice
        kubectl create secret generic sctbnk-secrets --from-env-file=.env -n sctbnk-voice
        echo "✅ Secret recreado"
    fi
else
    kubectl create secret generic sctbnk-secrets --from-env-file=.env -n sctbnk-voice
    echo "✅ Secret creado"
fi
echo ""

# MariaDB
echo "🗄️  Desplegando MariaDB..."
kubectl apply -f k8s/mariadb-deployment.yml
echo "⏳ Esperando a que MariaDB esté listo..."
kubectl wait --for=condition=ready pod -l app=mariadb -n sctbnk-voice --timeout=300s || true
echo ""

# Actions
echo "⚙️  Desplegando Actions..."
kubectl apply -f k8s/actions-deployment.yml
echo "⏳ Esperando a que Actions esté listo..."
kubectl wait --for=condition=ready pod -l app=actions -n sctbnk-voice --timeout=180s || true
echo ""

# Rasa
echo "🤖 Desplegando Rasa..."
kubectl apply -f k8s/rasa-deployment.yml
echo "⏳ Esperando a que Rasa esté listo..."
kubectl wait --for=condition=ready pod -l app=rasa -n sctbnk-voice --timeout=180s || true
echo ""

# Twilio
echo "📞 Desplegando Twilio Server..."
kubectl apply -f k8s/twilio-deployment.yml
echo "⏳ Esperando a que Twilio esté listo..."
kubectl wait --for=condition=ready pod -l app=twilio -n sctbnk-voice --timeout=180s || true
echo ""

echo "✅ Deployment completado!"
echo ""
echo "📊 Estado de los pods:"
kubectl get pods -n sctbnk-voice
echo ""

echo "🌐 Servicios:"
kubectl get services -n sctbnk-voice
echo ""

echo "📡 Obteniendo IP pública del LoadBalancer..."
sleep 5
EXTERNAL_IP=$(kubectl get service twilio-service -n sctbnk-voice -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
EXTERNAL_HOSTNAME=$(kubectl get service twilio-service -n sctbnk-voice -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

if [ -n "$EXTERNAL_IP" ]; then
    echo "✅ IP Pública: $EXTERNAL_IP"
    echo ""
    echo "📱 Configurar en Twilio Console:"
    echo "   Webhook URL: https://$EXTERNAL_IP/webhook/twilio/voice"
elif [ -n "$EXTERNAL_HOSTNAME" ]; then
    echo "✅ Hostname Público: $EXTERNAL_HOSTNAME"
    echo ""
    echo "📱 Configurar en Twilio Console:"
    echo "   Webhook URL: https://$EXTERNAL_HOSTNAME/webhook/twilio/voice"
else
    echo "⏳ LoadBalancer aún no tiene IP asignada"
    echo "   Ejecuta: kubectl get service twilio-service -n sctbnk-voice -w"
fi

echo ""
echo "📋 Comandos útiles:"
echo "   Ver pods:        kubectl get pods -n sctbnk-voice"
echo "   Ver logs:        kubectl logs -f -l app=twilio -n sctbnk-voice"
echo "   Ver servicios:   kubectl get services -n sctbnk-voice"
echo "   Escalar:         kubectl scale deployment twilio --replicas=5 -n sctbnk-voice"
echo ""
echo "🎉 ¡Deployment exitoso!"

