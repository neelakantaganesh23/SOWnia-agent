terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0"
    }
  }
  backend "azurerm" {
    # Configure Azure Blob Storage backend for Terraform state in production
  }
}

provider "azurerm" {
  features {}
}

# 1. Resource Group
resource "azurerm_resource_group" "sownia_rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# 2. Azure Container Registry (ACR)
resource "azurerm_container_registry" "sownia_acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.sownia_rg.name
  location            = azurerm_resource_group.sownia_rg.location
  sku                 = "Standard"
  admin_enabled       = true
  tags                = var.tags
}

# 3. Azure Kubernetes Service (AKS) Cluster
resource "azurerm_kubernetes_cluster" "sownia_aks" {
  name                = var.aks_cluster_name
  location            = azurerm_resource_group.sownia_rg.location
  resource_group_name = azurerm_resource_group.sownia_rg.name
  dns_prefix          = var.aks_dns_prefix
  tags                = var.tags

  default_node_pool {
    name       = "systempool"
    node_count = var.node_count
    vm_size    = var.node_vm_size
    os_disk_size_gb = 50
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "kubenet"
    load_balancer_sku = "standard"
  }
}

# 4. Attach ACR to AKS (Allow AKS to pull images from ACR without secrets)
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.sownia_aks.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.sownia_acr.id
  skip_service_principal_aad_check = true
}
