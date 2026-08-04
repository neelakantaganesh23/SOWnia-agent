terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0"
    }
  }
}

provider "azurerm" {
  skip_provider_registration = true
  features {}
}

# 1. Azure Container Registry (ACR)
resource "azurerm_container_registry" "sownia_acr" {
  name                = var.acr_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Standard"
  admin_enabled       = true
  tags                = var.tags
}

# 2. Azure Kubernetes Service (AKS) Cluster
resource "azurerm_kubernetes_cluster" "sownia_aks" {
  name                = var.aks_cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
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
