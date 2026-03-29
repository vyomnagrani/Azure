# Azure Container Apps Skill Contributions

Proposed skill contributions for [GitHub Copilot for Azure](https://github.com/microsoft/GitHub-Copilot-for-Azure) to improve Azure Container Apps capabilities.

## Overview

This repository contains skill files organized by contribution area. Each branch represents a focused, independently reviewable PR:

| Branch | Skill Area | Description |
|--------|-----------|-------------|
| `feature/container-apps-k8s-migration` | `azure-cloud-migrate` | Kubernetes (on-prem/other cloud) to Azure Container Apps migration |
| `feature/container-apps-cloudrun-migration` | `azure-cloud-migrate` | GCP Cloud Run to Azure Container Apps migration |
| `feature/container-apps-diagnostics` | `azure-diagnostics` | Expanded troubleshooting: networking, scaling, Dapr, KQL, revisions |
| `feature/container-apps-jobs` | `azure-prepare` | Container Apps Jobs support (manual, scheduled, event-driven) |
| `feature/container-apps-cost-optimization` | `azure-cost-optimization` | Container Apps cost analysis integration |

## Contributing

These files follow the [skill authoring guidelines](https://github.com/microsoft/GitHub-Copilot-for-Azure/blob/main/CONTRIBUTING.md) from the upstream repository:

- SKILL.md files kept under 5000 tokens
- Reference files under 2000 tokens
- Content in `references/` loaded on-demand
- Follows existing patterns in the upstream repo

## License

MIT
