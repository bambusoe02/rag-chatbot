variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "cluster_name" {
  description = "AKS cluster name"
  type        = string
  default     = "rag-chatbot-aks"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "prod"
}

