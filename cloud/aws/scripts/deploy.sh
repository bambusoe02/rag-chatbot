#!/bin/bash

set -e

echo "🚀 Deploying RAG Chatbot to AWS EKS"

# Variables
REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME="rag-chatbot-eks"
ENVIRONMENT=${ENVIRONMENT:-prod}

# Step 1: Initialize Terraform
echo "📦 Initializing Terraform..."
cd cloud/aws/terraform
terraform init

# Step 2: Plan infrastructure
echo "📋 Planning infrastructure..."
terraform plan -out=tfplan

# Step 3: Apply infrastructure
echo "⚙️  Creating AWS resources..."
read -p "Apply Terraform plan? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

terraform apply tfplan

# Step 4: Configure kubectl
echo "🔧 Configuring kubectl..."
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

# Step 5: Install AWS Load Balancer Controller
echo "📦 Installing AWS Load Balancer Controller..."
helm repo add eks https://aws.github.io/eks-charts
helm repo update

kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds?ref=master"

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Step 6: Install cert-manager (for SSL)
echo "🔐 Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s

# Step 7: Install metrics-server
echo "📊 Installing metrics-server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Step 8: Create namespace and secrets
echo "🔐 Creating namespace and secrets..."
kubectl create namespace rag-chatbot --dry-run=client -o yaml | kubectl apply -f -

# Get database password from Terraform output
DB_PASSWORD=$(terraform output -raw database_password)
SECRET_KEY=$(openssl rand -hex 32)

kubectl create secret generic rag-secrets \
  --from-literal=SECRET_KEY=$SECRET_KEY \
  --from-literal=DATABASE_PASSWORD=$DB_PASSWORD \
  --namespace=rag-chatbot \
  --dry-run=client -o yaml | kubectl apply -f -

# Step 9: Deploy application
echo "🚀 Deploying application..."
cd ../../../
kubectl apply -k k8s/overlays/$ENVIRONMENT

# Step 10: Wait for deployment
echo "⏳ Waiting for deployment to complete..."
kubectl wait --for=condition=available deployment --all -n rag-chatbot --timeout=600s

# Step 11: Get Load Balancer URL
echo "✅ Deployment complete!"
echo ""
echo "📊 Status:"
kubectl get pods -n rag-chatbot
echo ""
echo "🌐 Access URL:"
kubectl get ingress -n rag-chatbot -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' || echo "Ingress not ready yet"
echo ""
echo "📝 View logs:"
echo "  kubectl logs -f deployment/backend -n rag-chatbot"

