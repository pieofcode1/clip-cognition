metadata description = 'Storage account RBAC role assignment resource.'

@description('Storage account name')
param accountName string

@description('Id of the service principals to assign database and app roles')
param principalId string

@description('Id of the user assigned identity to assign database and app roles')
param roleDefinitionId string

@description('Type of the principal')
param principalType string


resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: accountName
}

resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, resourceGroup().id, principalId, roleDefinitionId)
  scope: storageAccount
  properties: {
    principalId: principalId
    roleDefinitionId: roleDefinitionId
    principalType: principalType
  }
}

output id string = storageRoleAssignment.id

