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

# 5. Postgres Flexible Server — backs the auth system + per-user data.
# Burstable B1ms is a separate PaaS SKU and does NOT count against the
# AKS node vCPU quota, so it fits the free-trial 4-vCPU constraint.
resource "azurerm_postgresql_flexible_server" "sownia_pg" {
  name                = var.pg_server_name
  resource_group_name = var.resource_group_name
  # Deliberately NOT var.location - eastus has zero Postgres Flexible Server
  # capacity/quota on this free-trial subscription (see variables.tf).
  location = var.pg_location
  version  = "14"

  administrator_login    = var.pg_admin_username
  administrator_password = var.pg_admin_password

  sku_name   = var.pg_sku_name
  storage_mb = 32768 # 32GB minimum tier

  backup_retention_days        = 7
  public_network_access_enabled = true

  tags = var.tags
}

# One server, two databases: prod and dev share compute (avoids doubling
# recurring cost on a free trial) but stay fully isolated as separate
# database catalogs, so a bad dev migration/test can never touch prod data.
resource "azurerm_postgresql_flexible_server_database" "sownia_db" {
  name      = var.pg_database_name
  server_id = azurerm_postgresql_flexible_server.sownia_pg.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_database" "sownia_dev_db" {
  name      = var.pg_dev_database_name
  server_id = azurerm_postgresql_flexible_server.sownia_pg.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Allow AKS pods to reach Postgres. The cluster uses kubenet + a standard
# LB with no static/pinned egress IP configured, so per-IP rules aren't
# practical here; this is Azure's documented "allow all Azure resources"
# rule (broader than a VNet-scoped rule — acceptable for this free-trial
# setup, can be tightened later with VNet integration).
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.sownia_pg.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Optional: a developer's own IP for direct psql debugging.
resource "azurerm_postgresql_flexible_server_firewall_rule" "dev_client" {
  count            = var.dev_client_ip != "" ? 1 : 0
  name             = "AllowDevClient"
  server_id        = azurerm_postgresql_flexible_server.sownia_pg.id
  start_ip_address = var.dev_client_ip
  end_ip_address   = var.dev_client_ip
}
