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
  default     = 2
  description = "System pool node count. 2 x Standard_D2as_v7 = 4 vCPU total (at the free-trial quota). Two nodes are needed to fit prod + dev environments (each with backend, frontend, and an in-cluster Postgres) plus give per-node disk headroom for the image pulls."
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

# Postgres now runs in-cluster via Helm (see helm/sownia/templates/
# postgres-*.yaml), not as an Azure PaaS resource, so no Postgres-related
# Terraform variables are needed here anymore.
