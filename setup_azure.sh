#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-sejfa-rg}"
LOCATION="${LOCATION:-swedencentral}"
ACR_NAME="${ACR_NAME:-sejfaacr}"
ENVIRONMENT_NAME="${ENVIRONMENT_NAME:-sejfa-env}"
APP_NAME="${APP_NAME:-sejfa-app}"
GITHUB_ORG="${GITHUB_ORG:-itsimonfredlingjack}"
GITHUB_REPO="${GITHUB_REPO:-grupp-ett-github}"

echo "Creating resource group: ${RESOURCE_GROUP} (${LOCATION})"
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" 1>/dev/null

echo "Creating Azure Container Registry: ${ACR_NAME}"
az acr create \
  --name "${ACR_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --sku Basic \
  --admin-enabled true \
  1>/dev/null

echo "Creating Container Apps environment: ${ENVIRONMENT_NAME}"
az containerapp env create \
  --name "${ENVIRONMENT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  1>/dev/null

echo "Creating Container App: ${APP_NAME}"
az containerapp create \
  --name "${APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --environment "${ENVIRONMENT_NAME}" \
  --image "mcr.microsoft.com/hello-world:latest" \
  --target-port 5000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  1>/dev/null

echo "Creating Azure AD app registration for GitHub Actions OIDC"
read -r AZURE_CLIENT_ID AZURE_APP_OBJECT_ID < <(
  az ad app create \
    --display-name "sejfa-github-actions" \
    --query "[appId,id]" \
    --output tsv
)

echo "Creating service principal"
az ad sp create --id "${AZURE_CLIENT_ID}" 1>/dev/null

RG_SCOPE="$(az group show --name "${RESOURCE_GROUP}" --query id --output tsv)"
ACR_SCOPE="$(az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" --query id --output tsv)"

echo "Assigning Contributor role on resource group"
az role assignment create \
  --assignee "${AZURE_CLIENT_ID}" \
  --role Contributor \
  --scope "${RG_SCOPE}" \
  1>/dev/null

echo "Assigning AcrPush role on ACR"
az role assignment create \
  --assignee "${AZURE_CLIENT_ID}" \
  --role AcrPush \
  --scope "${ACR_SCOPE}" \
  1>/dev/null

FEDERATED_CREDENTIAL_FILE="$(mktemp)"
cat > "${FEDERATED_CREDENTIAL_FILE}" <<EOF
{
  "name": "github-actions-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main",
  "description": "OIDC trust for GitHub Actions main branch deploys",
  "audiences": [
    "api://AzureADTokenExchange"
  ]
}
EOF

echo "Creating federated credential"
az ad app federated-credential create \
  --id "${AZURE_APP_OBJECT_ID}" \
  --parameters "${FEDERATED_CREDENTIAL_FILE}" \
  1>/dev/null

rm -f "${FEDERATED_CREDENTIAL_FILE}"

AZURE_TENANT_ID="$(az account show --query tenantId --output tsv)"
AZURE_SUBSCRIPTION_ID="$(az account show --query id --output tsv)"

echo
echo "Add the following values as GitHub Repository Secrets:"
echo "AZURE_CLIENT_ID=${AZURE_CLIENT_ID}"
echo "AZURE_TENANT_ID=${AZURE_TENANT_ID}"
echo "AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}"
echo "ACR_NAME=${ACR_NAME}"
echo "APP_NAME=${APP_NAME}"
echo "RESOURCE_GROUP=${RESOURCE_GROUP}"
