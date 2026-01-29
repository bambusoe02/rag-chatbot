# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Docker registry access
- Helm 3 (optional, for cert-manager)
- Kustomize (included with kubectl 1.14+)

## Quick Start

```bash
# 1. Configure
export REGISTRY="your-registry.azurecr.io"
export ENVIRONMENT="prod"

# 2. Update secrets
kubectl create secret generic rag-secrets \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=DATABASE_PASSWORD=$(openssl rand -base64 32) \
  -n rag-chatbot

# 3. Deploy
chmod +x deploy.sh
./deploy.sh prod

# 4. Access
kubectl port-forward -n rag-chatbot svc/frontend-service 8501:8501
```

## Architecture

```
┌─────────────────┐
│    Ingress      │ (nginx, with TLS)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼───────┐
│Frontend│ │ Backend  │ (2+ replicas, HPA)
└───┬───┘ └──┬───────┘
    │        │
    │   ┌────┴─────┬──────────┐
    │   │          │          │
┌───▼───▼──┐ ┌────▼────┐ ┌──▼────┐
│  Redis   │ │ Ollama  │ │Celery │
└──────────┘ └─────────┘ └───────┘
```

## Scaling

**Manual scaling:**
```bash
kubectl scale deployment backend --replicas=5 -n rag-chatbot
```

**Auto-scaling (HPA):**
- Backend: 2-10 replicas (CPU 70%, Memory 80%)
- Frontend: 2-5 replicas (CPU 70%)

## Monitoring

```bash
# Pod status
kubectl get pods -n rag-chatbot

# Logs
kubectl logs -f deployment/backend -n rag-chatbot

# Metrics
kubectl top pods -n rag-chatbot

# Events
kubectl get events -n rag-chatbot --sort-by='.lastTimestamp'
```

## Troubleshooting

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n rag-chatbot
kubectl logs <pod-name> -n rag-chatbot
```

**Database issues:**
```bash
# Run migrations manually
kubectl run migrations --rm -i --restart=Never \
  --image=your-registry/rag-chatbot-backend:latest \
  --namespace=rag-chatbot \
  -- python init_db.py
```

**Storage issues:**
```bash
kubectl get pvc -n rag-chatbot
kubectl describe pvc rag-data-pvc -n rag-chatbot
```

## Security

- Network policies restrict pod-to-pod communication
- Non-root containers (UID 1000)
- Read-only root filesystem (where possible)
- Resource limits prevent DoS
- TLS/HTTPS enforced
- Secrets encrypted at rest

## Backup

```bash
# Backup persistent volumes
kubectl exec -n rag-chatbot deployment/backend -- \
  tar czf /tmp/backup.tar.gz /app/data

kubectl cp rag-chatbot/backend-pod:/tmp/backup.tar.gz ./backup.tar.gz
```

## Cleanup

```bash
kubectl delete namespace rag-chatbot
```

## Environments

**Development:**
```bash
./deploy.sh dev
```

**Production:**
```bash
./deploy.sh prod
```

## Resource Requirements

**Minimum cluster:**
- 4 CPU cores
- 16GB RAM
- 100GB storage

**Recommended (production):**
- 8+ CPU cores
- 32GB+ RAM
- 200GB+ storage
- GPU nodes (optional, for Ollama)

