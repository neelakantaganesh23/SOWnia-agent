output "resource_group_name" {
  value = var.resource_group_name
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

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.sownia_pg.fqdn
}

output "postgres_database_name" {
  value = azurerm_postgresql_flexible_server_database.sownia_db.name
}

output "postgres_dev_database_name" {
  value = azurerm_postgresql_flexible_server_database.sownia_dev_db.name
}
