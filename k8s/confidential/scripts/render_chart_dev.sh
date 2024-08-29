#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

REGISTRY="docker.io"

# TODO: should use release name instead
API_IMAGE_DIGEST=$(skopeo inspect "docker://${REGISTRY}/enclaveid/api:master" --tls-verify=false | jq -r .Digest)
GUACAMOLE_TUNNEL_IMAGE_DIGEST=$(skopeo inspect "docker://${REGISTRY}/enclaveid/guacamole-tunnel:master" --tls-verify=false | jq -r .Digest)

CREATE_SECRETS_IMAGE_DIGEST=$(skopeo inspect "docker://${REGISTRY}/enclaveid/create-secrets:latest" --tls-verify=false | jq -r .Digest)
LOAD_SECRETS_IMAGE_DIGEST=$(skopeo inspect "docker://${REGISTRY}/enclaveid/load-secrets:latest" --tls-verify=false | jq -r .Digest)

helm template enclaveid "$SCRIPT_DIR"/../helm \
  --set secrets.dagster.token="${DAGSTER_TOKEN}" \
  --set containers.api.image="${REGISTRY}/enclaveid/api@${API_IMAGE_DIGEST}" \
  --set containers.guacamoleTunnel.image="${REGISTRY}/enclaveid/guacamole-tunnel@${GUACAMOLE_TUNNEL_IMAGE_DIGEST}" \
  --set initContainers.createSecrets.image="${REGISTRY}/enclaveid/create-secrets@${CREATE_SECRETS_IMAGE_DIGEST}" \
  --set initContainers.loadSecrets.image="${REGISTRY}/enclaveid/load-secrets@${LOAD_SECRETS_IMAGE_DIGEST}" \
  -f "${SCRIPT_DIR}/../helm/values.yaml" -f "${SCRIPT_DIR}/../helm/values.dev.yaml" --debug |
  "$SCRIPT_DIR"/split_chart.sh
