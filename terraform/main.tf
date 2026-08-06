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

  # Remote state in Azure Storage so state PERSISTS across pipeline runs.
  # Without this, the ephemeral build agent loses state each run and
  # Terraform re-tries to create resources that already exist ("already
  # exists - needs to be imported"). The storage account/container are
  # created ONCE by the owner (see DEPLOYMENT.md §1a). Values must be
  # literals here; auth comes from the ARM_* env vars set in the pipeline.
  backend "azurerm" {
    resource_group_name  = "rg-sownia-aks-prod"
    storage_account_name = "stsowniatfstate01"
    container_name       = "tfstate"
    key                  = "sownia.aks.tfstate"
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

  # The live cluster has the OIDC issuer enabled (Azure default / cannot be
  # disabled once on). Declare it so Terraform doesn't try to turn it off,
  # which Azure rejects with OIDCIssuerFeatureCannotBeDisabled.
  oidc_issuer_enabled = true

  default_node_pool {
    name       = "systempool"
    node_count = var.node_count
    vm_size    = var.node_vm_size
    # 64 GB: the 3.1 GB backend image plus per-deploy image churn overflows a
    # 32 GB disk and triggers DiskPressure pod evictions. NOTE: changing this
    # recreates the node pool (brief workload downtime; the LoadBalancer IP and
    # HF-dataset storage persist).
    os_disk_size_gb = 64
    # Required whenever certain node-pool properties (os_disk_size_gb, vm_size,
    # etc.) change in place: Azure spins up a temporary pool under this name,
    # migrates workloads, then deletes it - avoids the provider's
    # "temporary_name_for_rotation must be specified" error.
    temporary_name_for_rotation = "temppool"
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

# NOTE: Azure Database for PostgreSQL Flexible Server was removed - this
# free-trial subscription has zero Flexible Server capacity in every region
# tried (the API reports an empty allowed-version list). Postgres now runs
# IN-CLUSTER as a StatefulSet on a PersistentVolume, deployed via the Helm
# chart (helm/sownia/templates/postgres-*.yaml) - no Azure PaaS quota needed,
# each namespace gets its own isolated database.
