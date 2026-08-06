variable "resource_group_name" {
  type        = string
  default     = "rg-sownia-aks-prod"
  description = "Name of the Azure Resource Group"
}

variable "location" {
  type        = string
  default     = "eastus"
  description = "Azure region for resources"
}

variable "acr_name" {
  type        = string
  default     = "acrsowniaaksprod"
  description = "Globally unique name for Azure Container Registry"
}

variable "aks_cluster_name" {
  type        = string
  default     = "aks-sownia-prod"
  description = "Name of the AKS cluster"
}

variable "aks_dns_prefix" {
  type        = string
  default     = "sownia-k8s"
  description = "DNS prefix for AKS cluster"
}

variable "node_count" {
  type        = number
  default     = 1
  description = "Initial node count for system pool. 1 x Standard_B2s = 2 vCPU, safely under the free-trial 4-vCPU regional quota."
}

variable "node_vm_size" {
  type        = string
  default     = "Standard_D2as_v7"
  description = "VM size for AKS nodes. B-series is not allowed in this subscription; D2as_v7 (2 vCPU, 8 GB) is the smallest allowed SKU and stays within the 4-vCPU quota at 1 node."
}

variable "tags" {
  type        = map(string)
  default     = {
    Environment = "Production"
    Project     = "SOWnia"
    ManagedBy   = "Terraform"
  }
}

# --- Postgres (auth + per-user data) ---------------------------------------

variable "pg_server_name" {
  type        = string
  default     = "psql-sownia-prod"
  description = "Globally unique name for the Postgres Flexible Server"
}

variable "pg_location" {
  type        = string
  default     = "eastus2"
  description = "Region for the Postgres Flexible Server. Kept independent from var.location: eastus returns an empty allowed-version list on this free-trial subscription (zero Flexible Server capacity/quota there), which surfaces as a confusing 'Version should be in: []' error rather than a clear quota message. Postgres connects over its public endpoint, not a VNet, so it does not need to share a region with AKS."
}

variable "pg_admin_username" {
  type        = string
  default     = "sowniaadmin"
  description = "Postgres server admin username"
}

variable "pg_admin_password" {
  type        = string
  sensitive   = true
  description = "Postgres server admin password. Supplied via TF_VAR_pg_admin_password from a pipeline secret; never committed."
}

variable "pg_sku_name" {
  type        = string
  default     = "B_Standard_B1ms"
  description = "Cheapest Burstable tier. A separate PaaS SKU - does not consume AKS node vCPU quota."
}

variable "pg_database_name" {
  type        = string
  default     = "sownia"
  description = "Prod database name"
}

variable "pg_dev_database_name" {
  type        = string
  default     = "sownia_dev"
  description = "Dev database name, same server as prod (shared compute, isolated catalog)"
}

variable "dev_client_ip" {
  type        = string
  default     = ""
  description = "Optional developer IP for psql access via firewall rule; leave blank to skip"
}
