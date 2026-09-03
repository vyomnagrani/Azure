#!/usr/bin/env bash
set -euo pipefail

inspect_azure=false
inspect_kubernetes=false
subscription_id=""
resource_group=""
connected_environment=""
kube_context=""

usage() {
  cat <<'EOF'
Usage: ./scripts/preflight.sh [options]
  --inspect-azure --subscription-id ID
  [--resource-group NAME --connected-environment NAME]
  --inspect-kubernetes --kube-context CONTEXT
Default behavior checks local tools only. Optional inspections are read-only.
EOF
}

while (($#)); do
  case "$1" in
    --inspect-azure) inspect_azure=true; shift ;;
    --subscription-id) subscription_id="${2:?missing subscription ID}"; shift 2 ;;
    --resource-group) resource_group="${2:?missing resource group}"; shift 2 ;;
    --connected-environment) connected_environment="${2:?missing environment}"; shift 2 ;;
    --inspect-kubernetes) inspect_kubernetes=true; shift ;;
    --kube-context) kube_context="${2:?missing context}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

echo "Contoso Edge Store local preflight (read-only)"
if ! command -v python >/dev/null 2>&1; then
  echo "[missing] Python" >&2
  exit 1
fi
python -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11 or later is required"; print("[found] Python", sys.version.split()[0])'

for tool in az kubectl docker; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "[found] $tool"
  else
    echo "[not found (optional for local tests)] $tool"
  fi
done

if [[ "$inspect_azure" == true ]]; then
  [[ -n "$subscription_id" ]] || { echo "--inspect-azure requires --subscription-id" >&2; exit 2; }
  command -v az >/dev/null || { echo "Azure CLI is not installed" >&2; exit 1; }
  echo "Running explicitly requested read-only Azure queries. This script never signs in."
  az account show --subscription "$subscription_id" --output table
  if [[ -n "$resource_group" && -n "$connected_environment" ]]; then
    az containerapp connected-env show --subscription "$subscription_id" \
      --resource-group "$resource_group" --name "$connected_environment" --output table
  elif [[ -n "$resource_group" || -n "$connected_environment" ]]; then
    echo "Provide both --resource-group and --connected-environment, or neither." >&2
    exit 2
  fi
fi

if [[ "$inspect_kubernetes" == true ]]; then
  [[ -n "$kube_context" ]] || { echo "--inspect-kubernetes requires --kube-context" >&2; exit 2; }
  command -v kubectl >/dev/null || { echo "kubectl is not installed" >&2; exit 1; }
  echo "Running explicitly requested read-only Kubernetes query."
  kubectl --context "$kube_context" get namespaces
fi

echo "Local preflight complete. No cloud or cluster state was changed."

