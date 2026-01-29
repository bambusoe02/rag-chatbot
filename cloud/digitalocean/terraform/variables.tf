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

