#!/usr/bin/env bash
set -euo pipefail

subscription_id=""
resource_group=""
app_name="contoso-edge-store"
execute=false
confirmation=""

while (($#)); do
  case "$1" in
    --subscription-id) subscription_id="${2:?missing subscription ID}"; shift 2 ;;
    --resource-group) resource_group="${2:?missing resource group}"; shift 2 ;;
    --app-name) app_name="${2:?missing app name}"; shift 2 ;;
    --execute) execute=true; shift ;;
    --confirmation) confirmation="${2:?missing confirmation}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--subscription-id ID --resource-group NAME] [--app-name NAME] [--execute --confirmation DELETE-CONTOSO-EDGE-STORE]"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$subscription_id" || -z "$resource_group" ]]; then
  echo "Dry run: no Azure command will run."
  echo "Potential sample-only target: Container App '$app_name'."
  echo "Provide --subscription-id and --resource-group to print the exact command."
  exit 0
fi
[[ "$app_name" == "contoso-edge-store" ]] || {
  echo "Refusing to delete any target other than the exact sample name 'contoso-edge-store'." >&2
  exit 2
}

echo "Sample-only cleanup command: az containerapp delete --subscription <provided> --resource-group '$resource_group' --name '$app_name'"
echo "This script never deletes clusters, resource groups, registries, or Log Analytics workspaces."
if [[ "$execute" != true ]]; then
  echo "Dry run complete. Add --execute --confirmation DELETE-CONTOSO-EDGE-STORE to proceed."
  exit 0
fi
[[ "$confirmation" == "DELETE-CONTOSO-EDGE-STORE" ]] || {
  echo "Execution requires --confirmation DELETE-CONTOSO-EDGE-STORE." >&2
  exit 2
}
command -v az >/dev/null || { echo "Azure CLI is not installed." >&2; exit 1; }

az containerapp delete --subscription "$subscription_id" \
  --resource-group "$resource_group" --name "$app_name" --yes
