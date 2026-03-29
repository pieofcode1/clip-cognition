metadata description = 'Creates an Azure Container Registry.'

param name string
param location string = resourceGroup().location
param tags object = {}

@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'
param adminUserEnabled bool = true

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminUserEnabled
  }
}

output name string = acr.name
output loginServer string = acr.properties.loginServer
output id string = acr.id

#disable-next-line outputs-should-not-contain-secrets
output adminUsername string = acr.listCredentials().username
#disable-next-line outputs-should-not-contain-secrets
output adminPassword string = acr.listCredentials().passwords[0].value
