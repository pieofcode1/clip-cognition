metadata description = 'App service plan resource.'

param name string
param location string = resourceGroup().location
param tags object = {}

@allowed([
  'F1'
  'D1'
  'B1'
  'B2'
  'B3'
  'S1'
  'S2'
  'S3'
])
@description('The SKU of the app service plan.')
param sku string = 'F1'

@allowed([
  'linux'
])
@description('The OS of the app service plan.')
param kind string = 'linux'

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: kind
  properties: {
    reserved: kind == 'linux' ? true : null
  }
}

output name string = plan.name
