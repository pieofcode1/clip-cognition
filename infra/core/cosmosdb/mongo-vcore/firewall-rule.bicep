metadata description = 'Creates a firewall rule for an Azure DocumentDB cluster.'

param clusterName string

@description('Name of the firewall rule.')
param ruleName string

@description('Start IP address of the allowed range.')
param startIpAddress string

@description('End IP address of the allowed range.')
param endIpAddress string

resource cluster 'Microsoft.DocumentDB/mongoClusters@2024-07-01' existing = {
  name: clusterName
}

resource firewallRule 'Microsoft.DocumentDB/mongoClusters/firewallRules@2024-07-01' = {
  name: ruleName
  parent: cluster
  properties: {
    startIpAddress: startIpAddress
    endIpAddress: endIpAddress
  }
}

output name string = firewallRule.name
