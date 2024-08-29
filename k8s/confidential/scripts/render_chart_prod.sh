#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# TODO: set this one in values.prod.yaml
AZURE_USER_ASSIGNED_IDENTITY_NAME="${AZURE_USER_ASSIGNED_IDENTITY_NAME:-}"

AZURE_RESOURCE_GROUP="enclaveid-prod"
REGISTRY="mcr.microsoft.com"

AZURE_USER_ASSIGNED_CLIENT_ID="$(az identity show --resource-group "${AZURE_RESOURCE_GROUP}" --name "${AZURE_USER_ASSIGNED_IDENTITY_NAME}" --query 'clientId' -otsv)" \
AZURE_MANAGED_IDENTITY="$(az identity show --resource-group "${AZURE_RESOURCE_GROUP}" --name "${AZURE_USER_ASSIGNED_IDENTITY_NAME}" --query 'id' -otsv)"
KATA_WORKLOAD_MEASUREMENT=$(az confcom katapolicygen -y "${SCRIPT_DIR}/../renders/kata-configs.yaml" --print-policy | base64 --decode | sha256sum | cut -d' ' -f1)

API_IMAGE_DIGEST=$(skopeo inspect "docker://${REGISTRY}/api:${RELEASE_NAME}" --tls-verify=false | jq -r .Digest)

helm template enclaveid "$SCRIPT_DIR"/../helm \
  --set images.api.tag="${API_IMAGE_DIGEST}" \
  --set serviceAccount.name="${AZURE_SERVICE_ACCOUNT_NAME}" \
  --set serviceAccount.annotations."azure\.workload\.identity/client-id"="${AZURE_USER_ASSIGNED_CLIENT_ID}" \
  --set initImages.createSecrets.arguments.managedIdentity="${AZURE_MANAGED_IDENTITY}" \
  --set initImages.createSecrets.arguments.workloadMeasurement="${KATA_WORKLOAD_MEASUREMENT}" \
  -f "${SCRIPT_DIR}/../helm/values.yaml" -f "${SCRIPT_DIR}/../helm/values.prod.yaml" |
  "$SCRIPT_DIR"/split_chart.sh
