# AKS cluster setup

## Requirements

Install the `azure-cli`, enable `aks-preview` extension and the feature flags.

```bash
# Install azure-cli and login
az login

# Install aks-preview extension
az extension add --name aks-preview
az extension update --name aks-preview

# Install confcom extension
az extension add --name confcom
az extension update --name confcom

# Register Kata CoCo feature flag
az feature register --namespace "Microsoft.ContainerService" --name "KataCcIsolationPreview"

# Register AKS GPU image feature flag
az feature register --namespace "Microsoft.ContainerService" --name "GPUDedicatedVHDPreview"

# Verify registration status and refresh registration status in resource provider
az feature show --namespace "Microsoft.ContainerService" --name "KataCcIsolationPreview"
az feature show --namespace "Microsoft.ContainerService" --name "GPUDedicatedVHDPreview"

az provider register --namespace "Microsoft.ContainerService"
```

## (staging) Configure the cluster without CC

```bash
AZURE_RESOURCE_GROUP=enclaveid-staging
AZURE_CLUSTER_NAME=enclaveid-cluster-staging
AZURE_NODE_VM_SIZE=Standard_D4_v5 # Confidential VMs are not available eastus2 but we have the GPU quota here
AZURE_REGION=eastus2
```

## (prod) Configure the cluster with CC

```bash
AZURE_RESOURCE_GROUP=enclaveid-prod
AZURE_CLUSTER_NAME=enclaveid-cluster-prod
AZURE_NODE_VM_SIZE=Standard_DC4as_cc_v5 # Confidential VMs
AZURE_REGION=westeurope
AZURE_SERVICE_ACCOUNT_NAME=enclaveid-cluster-identity-sa
AZURE_SUBSCRIPTION=$(az account show --query id --output tsv)
AZURE_USER_ASSIGNED_IDENTITY_NAME=enclaveid-cluster-identity
AZURE_FEDERATED_IDENTITY_CREDENTIAL_NAME=enclaveid-cluster-identity-credential
MAA_ENDPOINT="sharedeus.eus.attest.azure.net"
```

## Create the cluster and the GPU nodepool

We need to create a cluster with one system node and two nodepools, one for CPU workloads (API, Guacamole, Dagster) and another for GPU workloads (Dagster ML jobs).
We configure the cluster autoscaler on the GPU pool to minimize costs.

```bash
# Create the cluster with one system node (need the same CVM type bc of kata)
az aks create --tier standard --location "${AZURE_REGION}" --resource-group "${AZURE_RESOURCE_GROUP}" --name "${AZURE_CLUSTER_NAME}" --kubernetes-version 1.29 --os-sku AzureLinux --node-vm-size "${AZURE_NODE_VM_SIZE}" --node-count 1 --enable-oidc-issuer --enable-workload-identity --generate-ssh-keys  --enable-cluster-autoscaler

# Get cluster credentials
az aks get-credentials --resource-group "${AZURE_RESOURCE_GROUP}" --name "${AZURE_CLUSTER_NAME}" --overwrite-existing

# Add nodepools for GPU workloads
# We also add a taint to make sure only GPU workloads are scheduled here

# standard_nc24ads_a100_v4 for single gpu workloads
az aks nodepool add --resource-group "${AZURE_RESOURCE_GROUP}" --name gpupool1 --cluster-name "${AZURE_CLUSTER_NAME}" --node-count 0 --labels sku=gpu gpu-count=1 --node-taints sku=gpu:NoSchedule --node-vm-size standard_nc24ads_a100_v4 --min-count 0 --max-count 4 --enable-cluster-autoscaler --aks-custom-headers UseGPUDedicatedVHD=true --priority Spot --eviction-policy Delete  --spot-max-price -1

# for big llms
az aks nodepool add --resource-group "${AZURE_RESOURCE_GROUP}" --name gpupool2 --cluster-name "${AZURE_CLUSTER_NAME}" --node-count 0 --labels sku=gpu gpu-count=2 --node-taints sku=gpu:NoSchedule --node-vm-size standard_nc48ads_a100_v4 --min-count 0 --max-count 2 --enable-cluster-autoscaler --aks-custom-headers UseGPUDedicatedVHD=true --priority Spot --eviction-policy Delete  --spot-max-price -1

# for image generation
az aks nodepool add --resource-group "${AZURE_RESOURCE_GROUP}" --name gpupool3 --cluster-name "${AZURE_CLUSTER_NAME}" --node-count 0 --labels sku=gpu gpu-count=4 --node-taints sku=gpu:NoSchedule --node-vm-size standard_nc96ads_a100_v4 --min-count 0 --max-count 1 --enable-cluster-autoscaler --aks-custom-headers UseGPUDedicatedVHD=true --priority Spot --eviction-policy Delete  --spot-max-price -1


# Configure the autoscaler for the gpu workloads
az aks update --resource-group "${AZURE_RESOURCE_GROUP}" --name "${AZURE_CLUSTER_NAME}" --cluster-autoscaler-profile skip-nodes-with-system-pods=false scale-down-unneeded-time=1m
```

## (staging) Add a non-CC nodepool

```bash
az aks nodepool add --resource-group "${AZURE_RESOURCE_GROUP}" --name cpupool --cluster-name "${AZURE_CLUSTER_NAME}" --node-count 2 --os-sku AzureLinux --node-vm-size "${AZURE_NODE_VM_SIZE}" --min-count 0 --max-count 4 --enable-cluster-autoscaler
```

## (prod) Add a CC nodepool

```bash
# IMPORTANT: Autoscaling is not supported for confidential computing nodes.
# Configuring the autoscaler for this pool will make austoscaling fail for the whole cluster.
az aks nodepool add --resource-group "${AZURE_RESOURCE_GROUP}" --name cpupool --cluster-name "${AZURE_CLUSTER_NAME}" --node-count 2 --os-sku AzureLinux --node-vm-size "${AZURE_NODE_VM_SIZE}" --workload-runtime KataCcIsolation
```

## Tear down the cluster

```bash
az group delete --name "${AZURE_RESOURCE_GROUP}" --yes
```

<!-- In order to deploy to AKS in production, there are a bunch of things to configure.

Set up a resource group in Azure: `enclaveid-prod`

Reference: <https://learn.microsoft.com/en-us/azure/aks/deploy-confidential-containers-default-policy>


Setup Federated Identity

```bash
# Get the OIDC issuer
AKS_OIDC_ISSUER="$(az aks show -n "${AZURE_CLUSTER_NAME}" -g "${AZURE_RESOURCE_GROUP}" --query "oidcIssuerProfile.issuerUrl" -otsv)"

# Create a managed identity for the cluster
az identity create --name "${AZURE_USER_ASSIGNED_IDENTITY_NAME}" --resource-group "${AZURE_RESOURCE_GROUP}" --location "${AZURE_REGION}" --subscription "${AZURE_SUBSCRIPTION}"

# With the setup complete, we can now use MANAGED_IDENTITY in the initContainer
# and USER_ASSIGNED_CLIENT_ID in the ServiceAccount config
```

Deploy the Kata-agnostic portion of the Helm chart:

```bash
# Render the chart
make helm-chart DEPLOYMENT=aks AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP AZURE_USER_ASSIGNED_IDENTITY_NAME=$AZURE_USER_ASSIGNED_IDENTITY_NAME

kubectl apply –f k8s/renders/k8s-configs.yaml
```

Create the federated identity credential between the managed identity, service account issuer, and subject:

```bash
az identity federated-credential create --name ${AZURE_FEDERATED_IDENTITY_CREDENTIAL_NAME} --identity-name ${AZURE_USER_ASSIGNED_IDENTITY_NAME} --resource-group ${AZURE_RESOURCE_GROUP} --issuer ${AKS_OIDC_ISSUER} --subject system:serviceaccount:default:${AZURE_SERVICE_ACCOUNT_NAME}
```

Set up the KV with the right roles:

```bash

```

Deploy the Kata portion of the Helm chart:

```bash
kubectl apply –f k8s/renders/kata-configs.yaml
```

- Run `az login` on host
- Create service principal: `az ad sp create-for-rbac --name enclaveid-dev`
- Create keyvault
- Assign role to keyvault: `az keyvault set-policy --name enclaveid-dev --spn 1c79e8e8-67d1-4dd8-a15a-d2d34f5902ec --key-permissions all`

Create a .env file in `/createSecrets` with the service principal credentials -->
