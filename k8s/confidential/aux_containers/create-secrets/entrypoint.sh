#!/bin/bash

set -euo pipefail

# See https://github.com/microsoft/confidential-container-demos/blob/main/kafka/setup-key.sh

if [ $# != 2 ] && [ $# != 6 ]; then
  echo "Usage: $0 <ENVIRONMENT> <KEY_NAME> [<KV_STORE_NAME>] [<MANAGED_IDENTITY>] [<MAA_ENDPOINT>] [<WORKLOAD_MEASUREMENT>]"
  exit 1
fi

ENVIRONMENT=$1
KEY_NAME=$2

KV_STORE_NAME=$3
MANAGED_IDENTITY=$4
MAA_ENDPOINT=$5
WORKLOAD_MEASUREMENT=$6

# We tmpfs to store sensitive data since the disk is not yet encrypted
TMPFS_DIR="/tmp"
cd "$TMPFS_DIR" || exit

# Generate master secret
openssl genrsa -out "$KEY_NAME.pem" 3072
echo "......Generated master secret"

# Derive intermediate secret from master secret
SEED=$(openssl rsa -in "$KEY_NAME.pem" -outform DER | openssl dgst -sha256 -binary | xxd -p | tr -d '\n')
certtool --generate-privkey --key-type=rsa --to-rsa --sec-param=high --seed="$SEED" --provable --outfile intermediate-secret.pem
echo "......Generated intermediate secret"

# Generate CA from intermediate secret
openssl req -new -x509 -days 3650 -key intermediate-secret.pem -out ca-cert.pem -config /ca.cnf
echo "......Generated CA from intermediate secret"

# Upload secret and CA to key vault
if [ "$ENVIRONMENT" = "microk8s" ]; then

  # Use the unencrypted shared storage to store the secrets
  # as we would do in AKV
  cp "$KEY_NAME.pem" /mnt/unencrypted-shared-storage/
  cp ca-cert.pem /mnt/unencrypted-shared-storage/

elif [ "$ENVIRONMENT" = "aks" ]; then

  # TODO: Create mHSM and throw away the secrets
  # TODO: Check that the retention period == key valdity period AND purge protection is enabled (which is immutable)

  AZURE_AKV_RESOURCE_ENDPOINT="$KV_STORE_NAME.managedhsm.azure.net"
  AZURE_KV_TYPE="managedHSM"

  key_vault_name=$(echo "$AZURE_AKV_RESOURCE_ENDPOINT" | cut -d. -f1)
  echo "Key vault name is ${key_vault_name}"

  if [[ $(az keyvault list -o json | grep "Microsoft.KeyVault/${AZURE_KV_TYPE}s/${key_vault_name}") ]] 2>/dev/null; then
    echo "AKV endpoint OK"
  else
    echo "Azure akv resource endpoint doesn't exist. Please refer to documentation instructions to set it up first:"
    exit 1
  fi

  policy_file_name="/key-release-policy.json"

  # Update the policy file with the workload measurement
  jq --arg equalsValue "${WORKLOAD_MEASUREMENT}" '
            .anyOf[] |= (.allOf |= map(if .claim == "x-ms-sevsnpvm-hostdata" then .equals = $equalsValue else . end))
    ' "${policy_file_name}" >tmp.$$.json

  mv tmp.$$.json "${policy_file_name}"

  # Update the policy file with the MAA endpoint
  jq --arg equalsValue "${MAA_ENDPOINT}" '.anyOf[] |= (.authority = $equalsValue)' "${policy_file_name}" >tmp.$$.json

  mv tmp.$$.json "${policy_file_name}"

  echo "......Creating RSA key in ${AZURE_AKV_RESOURCE_ENDPOINT} with HSM"
  az keyvault key create --id https://$AZURE_AKV_RESOURCE_ENDPOINT/keys/${KEY_NAME} --ops \
    wrapKey unwrapKey encrypt decrypt --kty RSA-HSM --size 3072 --exportable \
    --policy ${policy_file_name}
  echo "......Created RSA key in ${AZURE_AKV_RESOURCE_ENDPOINT}"

  # Upload CA to AKV
  az keyvault secret set --vault-name "$KV_STORE_NAME" --name $CA_CERT_NAME --file your-ca-cert.pem
  echo "......Uploaded CA to AKV"
else
  echo "Unknown environment $ENVIRONMENT. Exiting."
  exit 1
fi
