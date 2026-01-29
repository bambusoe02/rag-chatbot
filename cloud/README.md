# Cloud Deployment Guide

Complete guide for deploying RAG Chatbot to major cloud providers.

## Quick Comparison

| Provider | Best For | Cost (est.) | Setup Time | GPU Support |
|----------|----------|-------------|------------|-------------|
| **AWS EKS** | Enterprise, flexibility | $150-500/mo | 30-45 min | ✅ Excellent |
| **Google Cloud GKE** | ML/AI workloads, automation | $120-450/mo | 25-40 min | ✅ Excellent |
| **Azure AKS** | Microsoft integration | $140-480/mo | 30-45 min | ✅ Good |
| **DigitalOcean** | Simplicity, cost | $80-300/mo | 15-30 min | ❌ Limited |

## Prerequisites

All providers require:
- Cloud account with billing enabled
- CLI tools installed
- Terraform 1.0+
- kubectl
- Docker (for building images)

---

## 🟠 AWS EKS Deployment

### 1. Install AWS CLI
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure
aws configure
```

### 2. Deploy Infrastructure
```bash
cd cloud/aws/terraform

# Initialize Terraform
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name rag-chatbot-eks
```

### 3. Deploy Application
```bash
# Run deployment script
./scripts/deploy.sh

# Or manually:
kubectl apply -k ../../k8s/overlays/prod
```

### 4. Get Access URL
```bash
kubectl get ingress -n rag-chatbot
```

### Cost Optimization
- Use Spot instances for Celery workers
- Enable cluster autoscaler
- Use S3 lifecycle policies
- Reserved instances for production

**Estimated cost:** $150-500/month
- EKS: $73/month
- EC2 (3x t3.large): ~$150/month
- RDS (db.t3.micro): ~$15/month
- Data transfer: ~$20/month

---

## 🔵 Google Cloud GKE Deployment

### 1. Install gcloud CLI
```bash
# Install
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize
gcloud init

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable APIs
```bash
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sql-component.googleapis.com
```

### 3. Deploy Infrastructure
```bash
cd cloud/gcp/terraform

# Initialize
terraform init

# Apply
terraform apply

# Configure kubectl
gcloud container clusters get-credentials rag-chatbot-gke --region us-central1
```

### 4. Deploy Application
```bash
kubectl apply -k ../../../k8s/overlays/prod
```

### Cost Optimization
- Use Preemptible VMs for workers
- Regional clusters (cheaper than zonal)
- Committed use discounts
- Cloud SQL autoscaling

**Estimated cost:** $120-450/month
- GKE: Free (cluster management)
- Compute (3x e2-standard-4): ~$180/month
- Cloud SQL (db-f1-micro): ~$10/month
- Cloud Storage: ~$5/month

---

## 🔷 Azure AKS Deployment

### 1. Install Azure CLI
```bash
# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login
```

### 2. Deploy Infrastructure
```bash
cd cloud/azure/terraform

terraform init
terraform apply

# Configure kubectl
az aks get-credentials --resource-group rag-chatbot-aks-rg --name rag-chatbot-aks
```

### 3. Deploy Application
```bash
kubectl apply -k ../../../k8s/overlays/prod
```

### Cost Optimization
- Use Azure Spot VMs
- Reserved VM instances
- Azure Hybrid Benefit
- Auto-shutdown schedules

**Estimated cost:** $140-480/month
- AKS: Free (cluster management)
- VMs (3x Standard_D4s_v3): ~$200/month
- PostgreSQL (Basic): ~$20/month
- Storage: ~$10/month

---

## 🌊 DigitalOcean Deployment

### Option A: App Platform (Easiest)

1. **Fork repository**
2. **Create app:**
```bash
   doctl apps create --spec cloud/digitalocean/app.yaml
```
3. **Wait for deployment** (15-20 min)
4. **Access app:**
```bash
   doctl apps list
```

**Cost:** $80-200/month (all-inclusive)

### Option B: Kubernetes (More control)
```bash
# Install doctl
brew install doctl  # macOS
snap install doctl  # Linux

# Authenticate
doctl auth init

# Deploy
cd cloud/digitalocean/terraform
terraform init
terraform apply

# Configure kubectl
doctl kubernetes cluster kubeconfig save rag-chatbot-k8s

# Deploy app
kubectl apply -k ../../../k8s/overlays/prod
```

**Cost:** $100-300/month

---

## 🔧 Post-Deployment

### 1. Verify Deployment
```bash
kubectl get pods -n rag-chatbot
kubectl get svc -n rag-chatbot
kubectl get ingress -n rag-chatbot
```

### 2. Configure DNS
Point your domain to the Load Balancer IP/hostname.

### 3. Enable SSL
```bash
# Cert-manager (already installed)
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 4. Setup Monitoring
```bash
# Install Prometheus + Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Login: admin / prom-operator
```

### 5. Setup Backups
```bash
# Edit cron schedule
kubectl edit cronjob backup-job -n rag-chatbot

# Manual backup
kubectl create job --from=cronjob/backup-job manual-backup-1 -n rag-chatbot
```

---

## 📊 Monitoring & Logs
```bash
# View logs
kubectl logs -f deployment/backend -n rag-chatbot

# View metrics
kubectl top pods -n rag-chatbot

# Events
kubectl get events -n rag-chatbot --sort-by='.lastTimestamp'

# Port-forward to local
kubectl port-forward -n rag-chatbot svc/frontend-service 8501:8501
```

---

## 🆘 Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n rag-chatbot
kubectl logs <pod-name> -n rag-chatbot
```

### Connection issues
```bash
# Test internal connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Inside pod:
wget -O- http://backend-service:8000/health/live
```

### Out of resources
```bash
# Check node resources
kubectl top nodes

# Scale down
kubectl scale deployment backend --replicas=1 -n rag-chatbot
```

---

## 💰 Cost Management

### Monitor spending
- AWS: Cost Explorer
- GCP: Cloud Billing Reports
- Azure: Cost Management
- DigitalOcean: Billing dashboard

### Reduce costs
1. Use smaller instance types
2. Enable autoscaling (scale to zero when idle)
3. Use spot/preemptible instances
4. Delete unused resources
5. Set up budget alerts

---

## 🗑️ Cleanup
```bash
# AWS
cd cloud/aws/terraform
terraform destroy

# GCP
cd cloud/gcp/terraform
terraform destroy

# Azure
cd cloud/azure/terraform
terraform destroy

# DigitalOcean
doctl kubernetes cluster delete rag-chatbot-k8s
```

---

## 📚 Further Reading

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [AWS EKS Workshop](https://www.eksworkshop.com/)
- [GKE Tutorials](https://cloud.google.com/kubernetes-engine/docs/tutorials)
- [Azure AKS Best Practices](https://docs.microsoft.com/en-us/azure/aks/best-practices)

