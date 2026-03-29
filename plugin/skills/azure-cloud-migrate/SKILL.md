---
name: azure-cloud-migrate
description: "Assess and migrate cross-cloud workloads to Azure with migration reports and code conversion guidance. Supports AWS, GCP, Kubernetes, and other providers. WHEN: migrate Lambda to Azure Functions, migrate AWS to Azure, Lambda migration assessment, convert AWS serverless to Azure, migration readiness report, migrate from AWS, migrate from GCP, cross-cloud migration, migrate Kubernetes to Azure Container Apps, migrate K8s to ACA, migrate Cloud Run to ACA, container migration, containerized workload migration."
license: MIT
metadata:
  author: Microsoft
  version: "1.0.2"
---

# Azure Cloud Migrate

> This skill handles **assessment and code migration** of existing cloud workloads to Azure.

## Rules

1. Follow phases sequentially — do not skip
2. Generate assessment before any code migration
3. Load the scenario reference and follow its rules
4. Use `mcp_azure_mcp_get_bestpractices` and `mcp_azure_mcp_documentation` MCP tools
5. Use the latest supported runtime for the target service
6. Destructive actions require `ask_user` — [global-rules](references/services/functions/global-rules.md)

## Migration Scenarios

| Source | Target | Reference |
|--------|--------|-----------|
| AWS Lambda | Azure Functions | [lambda-to-functions.md](references/services/functions/lambda-to-functions.md) |
| Kubernetes (on-prem / other cloud) | Azure Container Apps | [k8s-to-container-apps.md](references/services/container-apps/k8s-to-container-apps.md) |
| GCP Cloud Run | Azure Container Apps | [cloudrun-to-container-apps.md](references/services/container-apps/cloudrun-to-container-apps.md) |

> No matching scenario? Use `mcp_azure_mcp_documentation` and `mcp_azure_mcp_get_bestpractices` tools.

### Container Apps Shared References

All Container Apps migration scenarios share these references:
- **Global rules**: [global-rules.md](references/services/container-apps/global-rules.md) — ACA constraints, limits, unsupported features
- **Assessment**: [assessment.md](references/services/container-apps/assessment.md) — Compatibility analysis framework
- **Code migration**: [code-migration.md](references/services/container-apps/code-migration.md) — Bicep templates, output structure, deployment

Load the scenario-specific reference first, then consult shared references as needed.

## Output Directory

All output goes to `<source-folder>-azure/` at workspace root. Never modify the source directory.

## Steps

1. **Create** `<source-folder>-azure/` at workspace root
2. **Assess** — Analyze source, map services, generate report → `assessment.md`
3. **Migrate** — Convert code using target programming model → `code-migration.md`
4. **Ask User** — "Migration complete. Test locally or deploy to Azure?"
5. **Hand off** to azure-prepare for infrastructure, testing, and deployment

Track progress in `migration-status.md` — see [workflow-details.md](references/workflow-details.md).
