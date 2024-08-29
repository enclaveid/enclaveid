#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
K8S_CONFIG_DIR="${SCRIPT_DIR}/../renders/kata-configs.yaml"

# This adds an initContainer to the guacamole pod that will
# wait for postgres to be ready before starting up.
SELECTOR='select(.kind == "Deployment" and .spec.template.metadata.labels."app.kubernetes.io/name" == "guacamole-guacamole").spec.template.spec.initContainers'
INIT_CONTAINER='[{"name": "wait-for-pg", "image": "busybox", "command": ["sh", "-c", "until nc -z enclaveid-postgresql.default.svc.cluster.local 5432; do echo waiting for postgresql; sleep 2; done;"]}]'

yq e "$SELECTOR |= $INIT_CONTAINER + ." -i "$K8S_CONFIG_DIR"

# Make guacd print debug logs rather than just info
yq e 'select(.kind == "Deployment" and .metadata.name == "enclaveid-guacamole-guacd").spec.template.spec.containers[] |= (select(.name == "guacamole") | .["command"] = ["/opt/guacamole/sbin/guacd", "-b", "0.0.0.0", "-L", "debug", "-f"])' -i "$K8S_CONFIG_DIR"
