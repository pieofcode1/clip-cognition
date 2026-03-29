metadata description = 'Creates an Azure DocumentDB cluster for vector search with managed identity RBAC.'

param clusterName string
param location string = resourceGroup().location
param tags object = {}

@description('Administrator login name.')
@secure()
param administratorLogin string

@description('Administrator login password.')
@secure()
param administratorLoginPassword string

@description('The compute tier. Defaults to M40.')
@allowed(['Free', 'M25', 'M30', 'M40', 'M50', 'M60', 'M80'])
param sku string = 'M40'

@description('Storage size in GB per shard.')
param storageSizeGb int = 128

@description('Allow access from all Azure services.')
param allowAzureAccess bool = true

@description('Developer public IP address for firewall access. Empty to skip.')
param developerIpAddress string = ''

@description('Principal ID of the user-assigned managed identity for RBAC.')
param appPrincipalId string

@description('Principal ID of the deploying user for RBAC.')
param userPrincipalId string = ''

@description('Type of the user principal.')
param principalType string = 'User'

var databaseName = 'clip-cognition-db'

// Built-in role: Contributor (control-plane management of the cluster)
var contributorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')

module cluster '../core/cosmosdb/mongo-vcore/account.bicep' = {
  name: 'documentdb-cluster'
  params: {
    name: clusterName
    location: location
    tags: tags
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorLoginPassword
    sku: sku
    storageSizeGb: storageSizeGb
    shardCount: 1
    enableHa: false
  }
}

// Allow Azure services (e.g. Container Instances, App Service) to reach the cluster
module azureAccessRule '../core/cosmosdb/mongo-vcore/firewall-rule.bicep' = if (allowAzureAccess) {
  name: 'documentdb-allow-azure'
  params: {
    clusterName: cluster.outputs.name
    ruleName: 'AllowAllAzureServices'
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// RBAC: Assign Contributor role to the managed identity on the cluster
module appRoleAssignment '../core/cosmosdb/mongo-vcore/role-assignment.bicep' = {
  name: 'documentdb-role-app'
  params: {
    clusterName: cluster.outputs.name
    principalId: appPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: contributorRoleId
  }
}

// Firewall: Allow developer public IP
module devIpRule '../core/cosmosdb/mongo-vcore/firewall-rule.bicep' = if (!empty(developerIpAddress)) {
  name: 'documentdb-allow-dev-ip'
  params: {
    clusterName: cluster.outputs.name
    ruleName: 'AllowDeveloperIP'
    startIpAddress: developerIpAddress
    endIpAddress: developerIpAddress
  }
}

// RBAC: Assign Contributor role to the deploying user on the cluster
module userRoleAssignment '../core/cosmosdb/mongo-vcore/role-assignment.bicep' = if (!empty(userPrincipalId)) {
  name: 'documentdb-role-user'
  params: {
    clusterName: cluster.outputs.name
    principalId: userPrincipalId
    principalType: principalType
    roleDefinitionId: contributorRoleId
  }
}

output clusterName string = cluster.outputs.name
// Replace <user> and <password> placeholders in the raw connection string with actual credentials
output connectionString string = replace(replace(cluster.outputs.connectionString, '<user>', administratorLogin), '<password>', administratorLoginPassword)
output databaseName string = databaseName
