# Azure AKS Deployment for RAG Chatbot

provider "azurerm" {
  features {}
}

# Variables
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

# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "${var.cluster_name}-rg"
  location = var.location
  
  tags = {
    Environment = var.environment
    Project     = "rag-chatbot"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "vnet" {
  name                = "${var.cluster_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = var.cluster_name
  
  kubernetes_version = "1.28"
  
  default_node_pool {
    name       = "general"
    node_count = 3
    vm_size    = "Standard_D4s_v3"
    
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 6
    
    vnet_subnet_id = azurerm_subnet.aks.id
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
  }
  
  tags = {
    Environment = var.environment
  }
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                = "${var.cluster_name}-postgres"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  
  version        = "15"
  administrator_login    = "ragadmin"
  administrator_password = random_password.db_password.result
  
  storage_mb = 32768
  sku_name   = "B_Standard_B1ms"
  
  backup_retention_days = 7
}

resource "azurerm_postgresql_flexible_server_database" "database" {
  name      = "ragchatbot"
  server_id = azurerm_postgresql_flexible_server.postgres.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Storage Account for backups
resource "azurerm_storage_account" "backups" {
  name                     = "${replace(var.cluster_name, "-", "")}backups"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "backups" {
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.backups.name
  container_access_type = "private"
}

# Outputs
output "cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}

output "database_host" {
  value = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "database_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "storage_account_name" {
  value = azurerm_storage_account.backups.name
}

output "configure_kubectl" {
  value = "az aks get-credentials --resource-group ${azurerm_resource_group.rg.name} --name ${azurerm_kubernetes_cluster.aks.name}"
}

