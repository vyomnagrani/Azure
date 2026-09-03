# Azure Container Apps — Skills & Documentation

This repository contains four complementary sets of Azure Container Apps content:

1. **ACA Skill Contributions** (plugin/skills/) — Proposed skill files for [GitHub Copilot for Azure](https://github.com/microsoft/GitHub-Copilot-for-Azure) that improve Container Apps capabilities within the Copilot agent.
2. **ACA Express Documentation** (aca-express-docs/) — Comprehensive documentation for Azure Container Apps Express, covering deployment, configuration, scaling, monitoring, and troubleshooting.
3. **ACA Sandbox Agent 365 Sample** ([aca-sandbox-agent-a365/](aca-sandbox-agent-a365/)) — An offline-first inbox agent that demonstrates Azure Container Apps Sandbox lifecycle management and Microsoft Agent 365 identity, tooling, observability, and governance.
4. **ACA Arc Templates** ([aca-arc-templates/](aca-arc-templates/)) — A local-first "Contoso Edge Store" inventory API and dashboard with conservative first-application scaffolding for an existing Azure Container Apps connected environment on Arc-enabled Kubernetes.

---

## ACA Skill Contributions

Proposed skill contributions organized by contribution area. Each branch represents a focused, independently reviewable PR:

| Branch | Skill Area | Description |
|--------|-----------|-------------|
| `feature/container-apps-k8s-migration` | `azure-cloud-migrate` | Kubernetes (on-prem/other cloud) to Azure Container Apps migration |
| `feature/container-apps-cloudrun-migration` | `azure-cloud-migrate` | GCP Cloud Run to Azure Container Apps migration |
| `feature/container-apps-diagnostics` | `azure-diagnostics` | Expanded troubleshooting: networking, scaling, Dapr, KQL, revisions |
| `feature/container-apps-jobs` | `azure-prepare` | Container Apps Jobs support (manual, scheduled, event-driven) |
| `feature/container-apps-cost-optimization` | `azure-cost-optimization` | Container Apps cost analysis integration |

These files follow the [skill authoring guidelines](https://github.com/microsoft/GitHub-Copilot-for-Azure/blob/main/CONTRIBUTING.md) from the upstream repository:

- SKILL.md files kept under 5000 tokens
- Reference files under 2000 tokens
- Content in `references/` loaded on-demand
- Follows existing patterns in the upstream repo

---

## ACA Express Documentation

Azure Container Apps Express is a simplified, fast, and cost-efficient mode of Azure Container Apps designed for developers who need to deploy HTTP services with minimal configuration.

The `aca-express-docs/` folder contains 8 comprehensive guides:

| Document | Description |
|----------|-------------|
| [Overview](aca-express-docs/local-environment-setup.md) | What ACA Express is, features, comparison vs full Container Apps |
| [Deployment](aca-express-docs/deploy-to-aca-express.md) | Deploy via Portal, CLI, and Bicep; private registries; CI/CD with GitHub Actions |
| [Configuration](aca-express-docs/advanced-configuration.md) | Environment variables, secrets, ingress, custom domains, auth, managed identity |
| [Scaling](aca-express-docs/scaling.md) | Autoscaling with KEDA — HTTP, TCP, queue rules; best practices |
| [Monitoring](aca-express-docs/operations-monitoring.md) | Metrics dashboard, log streaming, KQL queries, Application Insights |
| [Troubleshooting](aca-express-docs/shell-access-troubleshooting.md) | Console access, common issues (startup, image pull, auth, scaling) |
| [Local Development](aca-express-docs/local-development-testing.md) | Docker, Compose, registry push, ACR Build workflow |
| [Samples](aca-express-docs/samples.md) | Quickstarts: Node.js, Python Flask, .NET 8, Nginx static site, auth, custom domain |

---

## ACA Sandbox Agent 365 Sample

The `aca-sandbox-agent-a365/` sample shows how to run an interactive Python
inbox agent in a lifecycle-managed Azure Container Apps Sandbox, register it
with Microsoft Agent 365, and access Work IQ Mail through delegated
on-behalf-of authorization. Start with its fixture-backed offline mode before
enabling any live mailbox permission.

---

## ACA Arc Templates

The `aca-arc-templates/` sample is an initial local-only golden path for Azure
Container Apps on Arc-enabled Kubernetes. It includes a deterministic FastAPI
inventory service, zero-dependency dashboard, unit/API tests, read-only
preflight, defensive cleanup, deployment scaffolding, and an operator-focused
walkthrough.

Start locally without Docker, Azure authentication, or a Kubernetes cluster.
Image build, Azure deployment, and validation against the reserved
Arc-enabled cluster are explicitly deferred.

---

## License

MIT
