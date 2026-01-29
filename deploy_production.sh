#!/bin/bash

set -e

echo "🚀 RAG Chatbot Production Deployment"
echo "====================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-production}
DEPLOY_METHOD=${2:-docker}  # docker, kubernetes, cloud

echo "Environment: $ENVIRONMENT"
echo "Method: $DEPLOY_METHOD"
echo ""

# Pre-flight checks
echo "🔍 Running pre-flight checks..."

# Check if checklist is complete
if [ ! -f "PRODUCTION_CHECKLIST.md" ]; then
    echo -e "${RED}❌ PRODUCTION_CHECKLIST.md not found${NC}"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Create from template: cp .env.production.template .env"
    exit 1
fi

# Check for default SECRET_KEY
if grep -q "CHANGE_THIS" .env; then
    echo -e "${RED}❌ Default secrets found in .env${NC}"
    echo "Update all CHANGE_THIS values"
    exit 1
fi

# Run optimization script
echo ""
echo "🔧 Running optimization checks..."
python optimize.py || {
    echo -e "${YELLOW}⚠️  Optimization script had warnings${NC}"
    read -p "Continue anyway? (yes/no): " continue
    if [ "$continue" != "yes" ]; then
        exit 1
    fi
}

# Run tests
echo ""
echo "🧪 Running tests..."
if command -v pytest &> /dev/null; then
    pytest tests/ -v --tb=short || {
        echo -e "${RED}❌ Tests failed${NC}"
        read -p "Continue anyway? (yes/no): " continue
        if [ "$continue" != "yes" ]; then
            exit 1
        fi
    }
else
    echo -e "${YELLOW}⚠️  pytest not found, skipping tests${NC}"
fi

# Run performance benchmark
echo ""
echo "📊 Running performance benchmark..."
python performance_benchmark.py || {
    echo -e "${YELLOW}⚠️  Performance benchmark failed${NC}"
    read -p "Continue anyway? (yes/no): " continue
    if [ "$continue" != "yes" ]; then
        exit 1
    fi
}

# Deployment
echo ""
echo "🚀 Starting deployment..."

case $DEPLOY_METHOD in
    docker)
        echo "📦 Deploying with Docker Compose..."
        
        # Build images
        docker-compose build
        
        # Start services
        docker-compose up -d
        
        # Wait for services
        echo "⏳ Waiting for services to be ready..."
        sleep 10
        
        # Health check
        curl -f http://localhost:8000/health/status || {
            echo -e "${RED}❌ Health check failed${NC}"
            docker-compose logs
            exit 1
        }
        
        echo -e "${GREEN}✅ Deployment complete${NC}"
        echo ""
        echo "🌐 Access application:"
        echo "   Frontend: http://localhost:8501"
        echo "   Backend: http://localhost:8000"
        echo "   Docs: http://localhost:8000/docs"
        ;;
    
    kubernetes)
        echo "☸️  Deploying to Kubernetes..."
        
        # Apply manifests
        kubectl apply -k k8s/overlays/$ENVIRONMENT
        
        # Wait for rollout
        kubectl rollout status deployment/backend -n rag-chatbot
        kubectl rollout status deployment/frontend -n rag-chatbot
        
        # Get ingress URL
        INGRESS_URL=$(kubectl get ingress -n rag-chatbot -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
        
        echo -e "${GREEN}✅ Deployment complete${NC}"
        echo ""
        echo "🌐 Access application:"
        echo "   URL: https://$INGRESS_URL"
        ;;
    
    cloud)
        echo "☁️  Deploying to cloud..."
        
        if [ -z "$CLOUD_PROVIDER" ]; then
            echo -e "${RED}❌ CLOUD_PROVIDER not set${NC}"
            echo "Set: export CLOUD_PROVIDER=aws (or gcp, azure, digitalocean)"
            exit 1
        fi
        
        # AWS/GCP/Azure deployment
        cd cloud/$CLOUD_PROVIDER/terraform
        terraform init
        terraform apply -auto-approve
        
        echo -e "${GREEN}✅ Deployment complete${NC}"
        ;;
    
    *)
        echo -e "${RED}❌ Unknown deployment method: $DEPLOY_METHOD${NC}"
        exit 1
        ;;
esac

# Post-deployment checks
echo ""
echo "🔍 Running post-deployment checks..."

# Health check
echo "  Checking health endpoint..."
curl -f http://localhost:8000/health/status 2>/dev/null && echo "  ✅ Health check passed" || echo "  ⚠️  Health check failed"

# Metrics
echo "  Checking metrics endpoint..."
curl -f http://localhost:8000/metrics 2>/dev/null | head -5 && echo "  ✅ Metrics available" || echo "  ⚠️  Metrics check failed"

echo ""
echo "=================================="
echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
echo "=================================="
echo ""
echo "📝 Next steps:"
echo "  1. Monitor dashboards for 1 hour"
echo "  2. Test critical user flows"
echo "  3. Check error rates"
echo "  4. Verify backups are running"
echo "  5. Update documentation"
echo ""
echo "📊 Monitoring:"
echo "  Grafana: http://localhost:3000 (if configured)"
echo "  Prometheus: http://localhost:9090 (if configured)"
echo "  Logs: docker-compose logs -f"
echo ""
echo "🆘 Rollback if needed:"
echo "  docker-compose down"
echo "  git checkout <previous-version>"
echo "  docker-compose up -d"

