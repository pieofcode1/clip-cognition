metadata description = 'Creates Role definition and assignment resources'

@description('Database Account Name')
param databaseAccountName string

@description('storage account name')
param storageAccountName string

@description('Id of the service principals to assign database and app roles')
param appPrincipalId string

@description('Id of the user assigned identity to assign database and app roles')
param userPrincipalId string

@description('Type of the principal')
param principalType string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

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

module storageAccountRoleAssignmentUser '../core/storage/role-assignment.bicep' = {
  name: 'storage-account-user-role-assignment'
  params: {
    accountName: storageAccount.name
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor built-in role
    principalType: !empty(principalType) ? principalType : 'User' // Principal type or current deployment user
  }
}

module storageAccountRoleAssignmentApp '../core/storage/role-assignment.bicep' = {
  name: 'storage-account-app-role-assignment'
  params: {
    accountName: storageAccount.name
    principalId: appPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor built-in role
    principalType: 'ServicePrincipal' // Specify the principal type
  }
}

output roleDefinitions object = {
  nosql: nosqlDefinition.outputs.id
}

output roleAssignments array = union(
  !empty(appPrincipalId) ? [nosqlAppAssignment.?outputs.?id ?? '', openaiAppAssignment.?outputs.?id ?? ''] : [],
  !empty(userPrincipalId) ? [nosqlUserAssignment.?outputs.?id ?? '', openaiUserAssignment.?outputs.?id ?? ''] : []
)
