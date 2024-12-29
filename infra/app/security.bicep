metadata description = 'Creates Role definition and assignment resources'

@description('Database Account Name')
param databaseAccountName string

@description('Id of the service principals to assign database and app roles')
param appPrincipalId string

@description('Id of the user assigned identity to assign database and app roles')
param userPrincipalId string

@description('Type of the principal')
param principalType string

resource database 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = {
  name: databaseAccountName
}

module nosqlDefinition '../core/cosmosdb/nosql/role/definition.bicep' = {
  name: 'nosql-definition-app'
  params: {
    targetAccountName: database.name
    definitionName: 'nosql-role-definition'
    allowedDataPlaneActions: [
      'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
      'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
      'Microsoft.DocumentDB/databaseAccounts/readMetadata'
    ]
  }
}

module nosqlAppAssignment '../core/cosmosdb/nosql/role/assignment.bicep' = if (!empty(appPrincipalId)) {
  name: 'nosql-role-assignment-app'
  params: {
    targetAccountName: database.name
    roleDefinitionId: nosqlDefinition.outputs.id
    principalId: appPrincipalId
    principalType: principalType
  }
}

module nosqlUserAssignment '../core/cosmosdb/nosql/role/assignment.bicep' = if (!empty(userPrincipalId)) {
  name: 'nosql-role-assignment-user'
  params: {
    targetAccountName: databaseAccountName
    roleDefinitionId: nosqlDefinition.outputs.id
    principalId: userPrincipalId ?? ''
    principalType: principalType
  }
}

module openaiAppAssignment '../core/security/role/assignment.bicep' = if (!empty(appPrincipalId)) {
  name: 'openai-role-assignment-read-app'
  params: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User built-in role
    principalId: appPrincipalId
    principalType: 'ServicePrincipal' // Specify the principal type 
  }
}

module openaiUserAssignment '../core/security/role/assignment.bicep' = if (!empty(userPrincipalId)) {
  name: 'openai-role-assignment-read-user'
  params: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User built-in role
    principalId: userPrincipalId ?? ''
    principalType: !empty(principalType) ? principalType : 'User' // Principal type or current deployment user
  }
}

output roleDefinitions object = {
  nosql: nosqlDefinition.outputs.id
}

output roleAssignments array = union(
  !empty(appPrincipalId) ? [nosqlAppAssignment.outputs.id, openaiAppAssignment.outputs.id] : [],
  !empty(userPrincipalId) ? [nosqlUserAssignment.outputs.id, openaiUserAssignment.outputs.id] : []
)
