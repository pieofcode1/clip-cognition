metadata description = 'Creates a role assignment for a user assigned identity.'

@description('Target Database Account Name')
param targetAccountName string

@description('The id of the role definition.')
param roleDefinitionId string

@description('The id of the user assigned identity.')
param principalId string

@description('The type of the principal.')
param principalType string

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = {
  name: targetAccountName
}

resource assignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  name: guid(roleDefinitionId, principalId, account.id)
  parent: account
  properties: {
    principalId: principalId
    roleDefinitionId: roleDefinitionId
    scope: account.id
  }
}

output id string = assignment.id
