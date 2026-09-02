#!/usr/bin/env bash

set -euo pipefail

ACTION="${1:-preflight}"
if [[ $# -gt 0 ]]; then shift; fi

SUBSCRIPTION="${AZURE_SUBSCRIPTION_ID:-}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-}"
GROUP="${ACA_SANDBOX_GROUP:-}"
REGION="${ACA_SANDBOX_REGION:-${AZURE_LOCATION:-}}"
IDENTITY_RESOURCE_ID="${AZURE_MANAGED_IDENTITY_RESOURCE_ID:-}"
REGISTRY="${AZURE_CONTAINER_REGISTRY_NAME:-}"
SANDBOX_ID=""
DISK="ubuntu"
DISK_ID=""
SNAPSHOT=""
NAME=""
IMAGE=""
REPOSITORY="aca-sandbox-agent-a365"
TAG="dev"
BUILD_CONTEXT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT="8000"
EXECUTE=0
CONFIRM_DELETE=""
ALLOW_HOSTS=()
ENVIRONMENT=()
ENTRYPOINT=""

usage() {
  cat <<'EOF'
Usage: sandbox.sh [action] [options]

Actions (default: preflight):
  preflight       Check tools, Azure context, sandbox identity, and CLI capabilities.
  build-image     Build the project container image in ACR.
  create          Create a default-deny sandbox from a public disk or snapshot.
  image           Build a private sandbox disk image from an OCI image.
  port            Expose a sandbox TCP port anonymously and print its HTTPS URL.
  port-remove     Remove a previously exposed sandbox port.
  endpoint        Show sandbox details used to rediscover exposed endpoints.
  egress          Replace egress policy with default-deny plus --allow-host rules.
  stop            Stop a sandbox while retaining disk state.
  snapshot        Capture a named snapshot.
  resume          Resume a stopped sandbox.
  identity-check  Verify managed-identity environment capability inside a sandbox.
  delete          Delete a sandbox; additionally requires --confirm-delete <id>.

Context options:
  --subscription ID  --resource-group NAME  --group NAME  --region NAME
Operation options:
  --id UUID  --disk NAME  --disk-id UUID  --snapshot NAME  --name NAME
  --image OCI_URL  --env KEY=VALUE (repeatable)  --entrypoint COMMAND
  --port NUMBER  --allow-host PATTERN (repeatable)  --identity RESOURCE_ID
  --registry NAME  --repository NAME  --tag TAG  --context PATH
  --execute  --confirm-delete UUID

All mutating actions require --execute. Context can instead come from the azd
outputs AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, ACA_SANDBOX_GROUP,
ACA_SANDBOX_REGION, and AZURE_MANAGED_IDENTITY_RESOURCE_ID.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription) SUBSCRIPTION="$2"; shift 2 ;;
    --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
    --group) GROUP="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --identity) IDENTITY_RESOURCE_ID="$2"; shift 2 ;;
    --registry) REGISTRY="$2"; shift 2 ;;
    --id) SANDBOX_ID="$2"; shift 2 ;;
    --disk) DISK="$2"; shift 2 ;;
    --disk-id) DISK_ID="$2"; shift 2 ;;
    --snapshot) SNAPSHOT="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --repository) REPOSITORY="$2"; shift 2 ;;
    --tag) TAG="$2"; shift 2 ;;
    --context) BUILD_CONTEXT="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --allow-host) ALLOW_HOSTS+=("$2"); shift 2 ;;
    --env) ENVIRONMENT+=("$2"); shift 2 ;;
    --entrypoint) ENTRYPOINT="$2"; shift 2 ;;
    --execute) EXECUTE=1; shift ;;
    --confirm-delete) CONFIRM_DELETE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

identity_gate() {
  cat <<'EOF'

Agent identity gate:
  Do not enable live Agent 365 mode until identity-check succeeds for a sandbox.
  The group-level UAMI is the intended credential; no secret is emitted here.

This sample does not implement a certificate runtime path. If the identity
probe fails, keep live mode disabled rather than adding a client secret.
EOF
}

have() { command -v "$1" >/dev/null 2>&1; }

require_az() {
  if ! have az; then
    echo "Missing prerequisite: az (https://learn.microsoft.com/cli/azure/install-azure-cli)" >&2
    exit 3
  fi
  az account show --output none >/dev/null 2>&1 || {
    echo "Azure CLI is not signed in. Run: az login" >&2
    exit 3
  }
}

require_tools() {
  require_az
  if ! have aca; then
    echo "Missing prerequisite: aca (https://aka.ms/aca-cli-install)" >&2
    exit 3
  fi
}

require_context() {
  local missing=()
  [[ -n "$SUBSCRIPTION" ]] || missing+=("--subscription/AZURE_SUBSCRIPTION_ID")
  [[ -n "$RESOURCE_GROUP" ]] || missing+=("--resource-group/AZURE_RESOURCE_GROUP")
  [[ -n "$GROUP" ]] || missing+=("--group/ACA_SANDBOX_GROUP")
  [[ -n "$REGION" ]] || missing+=("--region/ACA_SANDBOX_REGION")
  if [[ ${#missing[@]} -gt 0 ]]; then
    printf 'Missing context: %s\n' "${missing[*]}" >&2
    exit 2
  fi
}

require_id() {
  [[ -n "$SANDBOX_ID" ]] || { echo "--id is required for $ACTION" >&2; exit 2; }
}

require_execute() {
  [[ "$EXECUTE" == "1" ]] || {
    echo "Dry stop: '$ACTION' changes Azure state. Re-run with --execute." >&2
    exit 2
  }
}

common=( )
set_common() {
  common=(-s "$SUBSCRIPTION" -g "$RESOURCE_GROUP" --group "$GROUP" --region "$REGION")
}

case "$ACTION" in
  preflight)
    echo "ACA Sandbox infrastructure preflight"
    echo "Preview assumptions: Microsoft.App/sandboxGroups@2026-02-01-preview; aca CLI command surface is checked at runtime."
    if ! have az; then
      echo "WARN: Azure CLI is not installed; install from https://learn.microsoft.com/cli/azure/install-azure-cli"
    elif ! az account show --output none >/dev/null 2>&1; then
      echo "WARN: Azure CLI is installed but not signed in; run az login."
    else
      echo "OK: Azure CLI authenticated."
    fi
    if ! have aca; then
      echo "WARN: ACA CLI preview is not installed; install with: curl -fsSL https://aka.ms/aca-cli-install | sh"
    else
      echo "OK: $(aca --version 2>&1 | head -n 1)"
      for cmd in \
        "sandbox create" "sandboxgroup disk create" "sandbox port add" \
        "sandbox egress set" "sandbox stop" "sandbox snapshot" \
        "sandbox resume" "sandbox delete" "sandboxgroup identity show"; do
        if aca $cmd --help >/dev/null 2>&1; then
          echo "OK: aca $cmd"
        else
          echo "WARN: installed preview CLI does not advertise 'aca $cmd'."
        fi
      done
    fi
    if [[ -n "$SUBSCRIPTION" && -n "$RESOURCE_GROUP" && -n "$GROUP" ]] && have az && az account show --output none >/dev/null 2>&1; then
      resource_id="/subscriptions/${SUBSCRIPTION}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/sandboxGroups/${GROUP}"
      identity_type="$(az resource show --ids "$resource_id" --api-version 2026-02-01-preview --query identity.type -o tsv 2>/dev/null || true)"
      if [[ "$identity_type" == *UserAssigned* ]]; then
        echo "OK: sandbox group has a user-assigned managed identity."
      else
        echo "WARN: sandbox group was not found or does not report UserAssigned identity."
      fi
      echo "Operator prerequisite: assign Container Apps SandboxGroup Data Owner to the signed-in user at the group scope."
      echo "  aca sandboxgroup role create --group '$GROUP' --role 'Container Apps SandboxGroup Data Owner' --principal-id <SIGNED_IN_USER_OBJECT_ID>"
    else
      echo "INFO: Azure context is incomplete; ARM identity verification was skipped."
    fi
    identity_gate
    ;;
  create)
    require_tools; require_context; require_execute; set_common
    args=(sandbox create "${common[@]}" --label sample=aca-sandbox-agent-a365 --egress-default Deny --traffic-inspection Full)
    if [[ -n "$SNAPSHOT" ]]; then
      args+=(--snapshot "$SNAPSHOT")
    elif [[ -n "$DISK_ID" ]]; then
      args+=(--disk-id "$DISK_ID")
    else
      args+=(--disk "$DISK")
    fi
    [[ -z "$ENTRYPOINT" ]] || args+=(--entrypoint "$ENTRYPOINT")
    for setting in "${ENVIRONMENT[@]}"; do args+=(--env "$setting"); done
    for host in "${ALLOW_HOSTS[@]}"; do args+=(--egress-rule "${host}:Allow"); done
    aca "${args[@]}"
    ;;
  build-image)
    require_az; require_context; require_execute
    [[ -n "$REGISTRY" ]] || { echo "--registry or AZURE_CONTAINER_REGISTRY_NAME is required for build-image" >&2; exit 2; }
    [[ -f "$BUILD_CONTEXT/Dockerfile" ]] || { echo "Dockerfile not found under --context: $BUILD_CONTEXT" >&2; exit 2; }
    az acr build --subscription "$SUBSCRIPTION" --registry "$REGISTRY" \
      --image "${REPOSITORY}:${TAG}" --file "$BUILD_CONTEXT/Dockerfile" "$BUILD_CONTEXT"
    echo "OCI image: ${REGISTRY}.azurecr.io/${REPOSITORY}:${TAG}"
    ;;
  image)
    require_tools; require_context; require_execute; set_common
    [[ -n "$IMAGE" && -n "$NAME" ]] || { echo "--image and --name are required for image" >&2; exit 2; }
    args=(sandboxgroup disk create "${common[@]}" --image "$IMAGE" --name "$NAME")
    if [[ "$IMAGE" == *".azurecr.io/"* ]]; then
      [[ -n "$IDENTITY_RESOURCE_ID" ]] || { echo "Private ACR image requires --identity RESOURCE_ID." >&2; exit 2; }
      help_text="$(aca sandboxgroup disk create --help 2>&1)"
      if grep -Eq '^[[:space:]]+--registry-identity([[:space:]]|<)' <<<"$help_text"; then
        args+=(--registry-identity "$IDENTITY_RESOURCE_ID")
      elif grep -Eq '^[[:space:]]+--identity([[:space:]]|<)' <<<"$help_text"; then
        args+=(--identity "$IDENTITY_RESOURCE_ID")
      else
        echo "Installed aca CLI cannot safely express private-registry identity. Use current CLI help or the portal; no credential fallback is attempted." >&2
        exit 4
      fi
    fi
    aca "${args[@]}"
    ;;
  port)
    require_tools; require_context; require_id; require_execute; set_common
    echo "WARNING: this creates an anonymous public HTTPS endpoint."
    aca sandbox port add "${common[@]}" --id "$SANDBOX_ID" --port "$PORT" --anonymous -o json
    ;;
  port-remove)
    require_tools; require_context; require_id; require_execute; set_common
    aca sandbox port remove "${common[@]}" --id "$SANDBOX_ID" --port "$PORT"
    ;;
  endpoint)
    require_tools; require_context; require_id; set_common
    echo "Inspect the ports/endpoints fields in this response:"
    aca sandbox get "${common[@]}" --id "$SANDBOX_ID" -o json
    ;;
  egress)
    require_tools; require_context; require_id; require_execute; set_common
    args=(sandbox egress set "${common[@]}" --id "$SANDBOX_ID" --default Deny --traffic-inspection Full)
    for host in "${ALLOW_HOSTS[@]}"; do args+=(--rule "${host}:Allow"); done
    aca "${args[@]}"
    ;;
  stop)
    require_tools; require_context; require_id; require_execute; set_common
    aca sandbox stop "${common[@]}" --id "$SANDBOX_ID"
    ;;
  snapshot)
    require_tools; require_context; require_id; require_execute; set_common
    [[ -n "$NAME" ]] || { echo "--name is required for snapshot" >&2; exit 2; }
    aca sandbox snapshot "${common[@]}" --id "$SANDBOX_ID" --name "$NAME"
    ;;
  resume)
    require_tools; require_context; require_id; require_execute; set_common
    echo "WARNING: resume restarts compute billing."
    aca sandbox resume "${common[@]}" --id "$SANDBOX_ID"
    ;;
  identity-check)
    require_tools; require_context; require_id; require_execute; set_common
    echo "Checking only for identity endpoint/header presence; no token is requested or printed."
    if aca sandbox exec "${common[@]}" --id "$SANDBOX_ID" -c \
      'test -n "${IDENTITY_ENDPOINT:-}" && { test -n "${IDENTITY_HEADER:-}" || test -n "${MSI_ENDPOINT:-}"; }'; then
      echo "PASS: managed-identity runtime capability is present."
    else
      echo "FAIL: managed-identity runtime capability was not detected."
      identity_gate
      exit 5
    fi
    ;;
  delete)
    require_tools; require_context; require_id; require_execute; set_common
    [[ "$CONFIRM_DELETE" == "$SANDBOX_ID" ]] || {
      echo "Deletion refused. Pass --confirm-delete with the exact sandbox id." >&2
      exit 2
    }
    aca sandbox delete "${common[@]}" --id "$SANDBOX_ID" --yes
    ;;
  *)
    echo "Unknown action: $ACTION" >&2
    usage >&2
    exit 2
    ;;
esac
