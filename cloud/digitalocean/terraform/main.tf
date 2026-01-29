# DigitalOcean Kubernetes for RAG Chatbot

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "cluster_name" {
  description = "Cluster name"
  type        = string
  default     = "rag-chatbot-k8s"
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

# Kubernetes Cluster
resource "digitalocean_kubernetes_cluster" "cluster" {
  name    = var.cluster_name
  region  = var.region
  version = "1.28.2-do.0"
  
  node_pool {
    name       = "general-pool"
    size       = "s-4vcpu-8gb"
    auto_scale = true
    min_nodes  = 2
    max_nodes  = 5
  }
}

# Database
resource "digitalocean_database_cluster" "postgres" {
  name       = "${var.cluster_name}-postgres"
  engine     = "pg"
  version    = "15"
  size       = "db-s-1vcpu-1gb"
  region     = var.region
  node_count = 1
}

resource "digitalocean_database_db" "database" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "ragchatbot"
}

resource "digitalocean_database_user" "user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "ragadmin"
}

# Redis
resource "digitalocean_database_cluster" "redis" {
  name       = "${var.cluster_name}-redis"
  engine     = "redis"
  version    = "7"
  size       = "db-s-1vcpu-1gb"
  region     = var.region
  node_count = 1
}

# Spaces (S3-compatible storage) for backups
resource "digitalocean_spaces_bucket" "backups" {
  name   = "${var.cluster_name}-backups"
  region = var.region
  
  lifecycle_rule {
    enabled = true
    expiration {
      days = 30
    }
  }
}

# Outputs
output "cluster_endpoint" {
  value = digitalocean_kubernetes_cluster.cluster.endpoint
}

output "cluster_id" {
  value = digitalocean_kubernetes_cluster.cluster.id
}

output "database_host" {
  value = digitalocean_database_cluster.postgres.host
}

output "database_port" {
  value = digitalocean_database_cluster.postgres.port
}

output "database_user" {
  value = digitalocean_database_user.user.name
}

output "database_password" {
  value     = digitalocean_database_user.user.password
  sensitive = true
}

output "redis_host" {
  value = digitalocean_database_cluster.redis.host
}

output "configure_kubectl" {
  value = "doctl kubernetes cluster kubeconfig save ${digitalocean_kubernetes_cluster.cluster.id}"
}

