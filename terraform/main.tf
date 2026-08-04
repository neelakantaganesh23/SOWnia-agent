terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      # Pinned to 3.x: uses `skip_provider_registration` and does not
      # require an explicit subscription_id, which keeps free-trial
      # service-connection auth simple. Avoids the moving 4.x target.
      version = "~> 3.116.0"
    }
  }
}

provider "azurerm" {
  features {}

  # The free-trial service principal usually only has Contributor on the
  # resource group, NOT the subscription, so it cannot register resource
  # providers (that needs subscription scope) and would 403. Providers must
  # be pre-registered ONCE by the subscription owner (see README/DEPLOY notes).
  skip_provider_registration = true
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

  # Free control-plane tier — no cost for the managed Kubernetes API server.
  sku_tier = "Free"

  default_node_pool {
    name            = "systempool"
    node_count      = var.node_count
    vm_size         = var.node_vm_size
    os_disk_size_gb = 32
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
