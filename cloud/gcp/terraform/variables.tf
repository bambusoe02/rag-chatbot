variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "rag-chatbot-gke"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "prod"
}

