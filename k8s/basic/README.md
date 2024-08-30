# v0

This chart only has the bare minimum required to run the API and the Dagster agent.

## Configure ingress in AKS

```bash
az aks approuting enable --resource-group enclaveid-prod --name enclaveid-cluster-prod
```

## Add dns zone to networking addon
  
https://learn.microsoft.com/en-us/azure/aks/app-routing-dns-ssl#attach-azure-dns-zone-to-the-application-routing-add-on

