metadata description = 'Creates a role based access control definition.'

@description('The name of the role.')
param roleName string

@description('The description of the role.')  
param roleDescription string


@description('The control-plane actions that are allowed for the role.')
param allowedControlPlaneActions string[] = []

@description('The control-plane actions that are not allowed for the role.')
param disallowedControlPlaneActions string[] = []

@description('The data-plane actions that are allowed for the role.')
param allowedDataPlaneActions string[] = []

@description('The data-plane actions that are not allowed for the role.')
param disallowedDataPlaneActions string[] = []

resource definition 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(subscription().id, resourceGroup().id)
  scope: resourceGroup()
  properties: {
    roleName: roleName
    description: roleDescription
    type: 'CustomRole'
    assignableScopes: [
      resourceGroup().id
    ]
    permissions: [
      {
        actions: allowedControlPlaneActions
        notActions: disallowedControlPlaneActions
        dataActions: allowedDataPlaneActions
        notDataActions: disallowedDataPlaneActions
      }
    ]
  }
}

output id string = definition.id
