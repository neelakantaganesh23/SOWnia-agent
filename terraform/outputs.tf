output "resource_group_name" {
  value = data.azurerm_resource_group.sownia_rg.name
}

output "acr_login_server" {
  value = azurerm_container_registry.sownia_acr.login_server
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.sownia_aks.name
}

output "aks_cluster_fqdn" {
  value = azurerm_kubernetes_cluster.sownia_aks.fqdn
}
