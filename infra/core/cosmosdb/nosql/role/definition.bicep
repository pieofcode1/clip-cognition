metadata description = 'Creates a role definition for NoSQL cosmosdb database.'

param targetAccountName string

param definitionName string

param allowedDataPlaneActions string[] = []

param deniedDataPlaneActions string[] = []

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = {
  name: targetAccountName
}

resource definition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-11-15' = {
  name: guid('nosql-role-definition', account.id)
  parent: account
  properties: {
    assignableScopes: [
      account.id
    ]
    permissions: [
      {
        dataActions: allowedDataPlaneActions
        notDataActions: deniedDataPlaneActions
      }
    ]
    roleName: definitionName
    type: 'CustomRole'
  }
}

output id string = definition.id
