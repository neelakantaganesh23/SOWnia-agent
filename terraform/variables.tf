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
  description = "Initial node count for system pool"
}

variable "node_vm_size" {
  type        = string
  default     = "Standard_B2s"
  description = "VM size for AKS nodes"
}

variable "tags" {
  type        = map(string)
  default     = {
    Environment = "Production"
    Project     = "SOWnia"
    ManagedBy   = "Terraform"
  }
}
