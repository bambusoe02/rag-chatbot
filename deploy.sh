#!/bin/bash

set -e

echo "🚀 Deploying RAG Chatbot to Kubernetes"

# Configuration
ENVIRONMENT=${1:-dev}
NAMESPACE="rag-chatbot"
REGISTRY=${REGISTRY:-"your-registry.azurecr.io"}
VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Registry: $REGISTRY"

# Build and push images
echo "📦 Building Docker images..."

docker build -t ${REGISTRY}/rag-chatbot-backend:${VERSION} -f Dockerfile.backend .
docker build -t ${REGISTRY}/rag-chatbot-frontend:${VERSION} -f Dockerfile.frontend .

# Tag as latest
docker tag ${REGISTRY}/rag-chatbot-backend:${VERSION} ${REGISTRY}/rag-chatbot-backend:latest
docker tag ${REGISTRY}/rag-chatbot-frontend:${VERSION} ${REGISTRY}/rag-chatbot-frontend:latest

# Push images (skip if REGISTRY contains "your-registry")
if [[ ! "$REGISTRY" == *"your-registry"* ]]; then
    echo "📤 Pushing images to registry..."
    docker push ${REGISTRY}/rag-chatbot-backend:${VERSION}
    docker push ${REGISTRY}/rag-chatbot-backend:latest
    docker push ${REGISTRY}/rag-chatbot-frontend:${VERSION}
    docker push ${REGISTRY}/rag-chatbot-frontend:latest
    echo "✅ Images pushed to registry"
else
    echo "⚠️  Skipping image push (using placeholder registry)"
fi

# Create namespace if not exists
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply kustomization
echo "⚙️  Applying Kubernetes manifests..."

kubectl apply -k k8s/overlays/${ENVIRONMENT}

# Update image tags (if registry is configured)
if [[ ! "$REGISTRY" == *"your-registry"* ]]; then
    echo "🔄 Updating image tags..."
    kubectl set image deployment/backend backend=${REGISTRY}/rag-chatbot-backend:${VERSION} -n ${NAMESPACE} || true
    kubectl set image deployment/frontend frontend=${REGISTRY}/rag-chatbot-frontend:${VERSION} -n ${NAMESPACE} || true
    kubectl set image deployment/celery-worker celery-worker=${REGISTRY}/rag-chatbot-backend:${VERSION} -n ${NAMESPACE} || true
    kubectl set image deployment/celery-beat celery-beat=${REGISTRY}/rag-chatbot-backend:${VERSION} -n ${NAMESPACE} || true
fi

# Wait for rollout
echo "⏳ Waiting for rollout to complete..."

kubectl rollout status deployment/backend -n ${NAMESPACE} --timeout=300s || true
kubectl rollout status deployment/frontend -n ${NAMESPACE} --timeout=300s || true
kubectl rollout status deployment/celery-worker -n ${NAMESPACE} --timeout=300s || true

# Run database migrations (if needed)
echo "🗄️  Running database migrations..."

kubectl run migrations-$(date +%s) --rm -i --restart=Never \
  --image=${REGISTRY}/rag-chatbot-backend:${VERSION} \
  --namespace=${NAMESPACE} \
  -- python init_db.py || echo "⚠️  Migrations skipped or failed"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check status:"
echo "   kubectl get pods -n ${NAMESPACE}"
echo "   kubectl get svc -n ${NAMESPACE}"
echo ""
echo "🌐 Access the application:"
echo "   kubectl port-forward -n ${NAMESPACE} svc/frontend-service 8501:8501"
echo ""
echo "📝 View logs:"
echo "   kubectl logs -f deployment/backend -n ${NAMESPACE}"

