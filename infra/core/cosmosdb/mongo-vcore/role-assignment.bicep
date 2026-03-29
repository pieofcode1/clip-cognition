metadata description = 'Creates an Azure RBAC role assignment scoped to a DocumentDB cluster.'

@description('The name of the DocumentDB cluster.')
param clusterName string

@description('The principal ID to assign the role to.')
param principalId string

@description('The type of the principal.')
@allowed(['ServicePrincipal', 'User', 'Group'])
param principalType string = 'ServicePrincipal'

@description('The built-in role definition ID to assign.')
param roleDefinitionId string

resource cluster 'Microsoft.DocumentDB/mongoClusters@2024-07-01' existing = {
  name: clusterName
}

resource assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, resourceGroup().id, clusterName, principalId, roleDefinitionId)
  scope: cluster
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: roleDefinitionId
  }
}

output id string = assignment.id
