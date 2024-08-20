# Deployment

## Set up the cluster

- [Microk8s](microk8s.md)
- [AKS](aks.md)

## Build and deploy

Set `AZURE_CLUSTER_NAME` to be one of:

- `microk8s`
- `enclaveid-cluster-staging`
- `enclaveid-cluster`

Depending on which environment you want to deploy to.

```bash
# Build the containers
bun nx run @enclaveid/enclaveid:containers
bun nx run @enclaveid/enclaveid:aux-containers

# Render the Helm chart
CONTEXT=$AZURE_CLUSTER_NAME bun nx run @enclaveid/enclaveid:helm-chart

# Apply the chart
CONTEXT=$AZURE_CLUSTER_NAME bun nx run @enclaveid/enclaveid:deploy
```

## Secrets management

Static secrets are managed in GitHub Secrets. Dynamic secrets are managed in Dagster.
