metadata description = 'Creates a role assignment for a user assigned identity.'

@description('The id of the role definition.')
param roleDefinitionId string

@description('The id of the user assigned identity.')
param principalId string

@description('The type of the principal.')
param principalType string

resource assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, resourceGroup().id, principalId, roleDefinitionId)
  properties: {
    principalId: principalId
    principalType: !empty(principalType) ? principalType : null
    roleDefinitionId: roleDefinitionId
  }
}

output id string = assignment.id
