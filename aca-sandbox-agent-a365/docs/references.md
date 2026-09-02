# Official references and source samples

Links and statements were checked against official sources on **2026-09-01**.
Preview documentation and product contracts can change; recheck before a live
deployment.

## Agent 365 and Work IQ

- [Microsoft Agent 365 overview](https://learn.microsoft.com/microsoft-agent-365/overview)
- [Quickstart: Connect an existing agent to Agent 365](https://learn.microsoft.com/microsoft-agent-365/developer/get-started)
- [Agent 365 Skills](https://learn.microsoft.com/microsoft-agent-365/developer/agent-365-skills)
- [Agent 365 identity](https://learn.microsoft.com/microsoft-agent-365/developer/identity)
- [Set up an agent blueprint](https://learn.microsoft.com/microsoft-agent-365/developer/registration)
- [Work IQ MCP overview (preview)](https://learn.microsoft.com/microsoft-agent-365/tooling-servers-overview)
- [Microsoft 365 Copilot licensing](https://learn.microsoft.com/copilot/microsoft-365/microsoft-365-copilot-licensing)
- [Frontier previews for Agent 365](https://learn.microsoft.com/microsoft-agent-365/frontier)
- [Agent 365 service description](https://learn.microsoft.com/office365/servicedescriptions/microsoft-agent-365/microsoft-agent-365)

## Identity and authentication

- [Agent identities in Microsoft Entra Agent ID](https://learn.microsoft.com/entra/agent-id/agent-identities)
- [Agent identity blueprints](https://learn.microsoft.com/entra/agent-id/agent-blueprint)
- [Agent OBO OAuth flow](https://learn.microsoft.com/entra/agent-id/agent-on-behalf-of-oauth-flow)
- [Interactive agent authentication and OBO](https://learn.microsoft.com/entra/agent-id/interactive-agent-authentication-authorization-flow)
- [Agent tokens](https://learn.microsoft.com/entra/agent-id/agent-tokens)
- [Agent token claims](https://learn.microsoft.com/entra/agent-id/agent-token-claims)
- [Owners, sponsors, and managers](https://learn.microsoft.com/entra/agent-id/agent-owners-sponsors-managers)
- [Govern agent identities](https://learn.microsoft.com/entra/id-governance/agent-id-governance-overview)
- [Federate an application with an Azure managed identity](https://learn.microsoft.com/entra/workload-id/workload-identity-federation-config-app-trust-managed-identity)
- [Authorization code flow with PKCE](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-auth-code-flow)

## Container Apps Sandboxes and Foundry

- [Azure Container Apps Sandboxes overview (preview)](https://learn.microsoft.com/azure/container-apps/sandboxes-overview)
- [Snapshots and state management](https://learn.microsoft.com/azure/container-apps/sandboxes-snapshots-state-management)
- [Sandbox group with Bicep](https://learn.microsoft.com/azure/container-apps/sandboxes-quickstart-bicep)
- [Microsoft Foundry overview](https://learn.microsoft.com/azure/ai-foundry/what-is-azure-ai-foundry)
- [Managed identities for Azure resources](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview)

## Governance, security, and compliance

- [Agent 365 registry and lifecycle actions](https://learn.microsoft.com/microsoft-365/admin/manage/agent-actions?view=o365-worldwide)
- [Defender support for Agent 365](https://learn.microsoft.com/microsoft-agent-365/guidance/defender-agent-365)
- [Purview support for Agent 365](https://learn.microsoft.com/microsoft-agent-365/guidance/purview-agent-365)
- [Purview data security and compliance for AI agents](https://learn.microsoft.com/purview/ai-agent-365)

## Official source samples

- [Agent 365 Skills source](https://github.com/microsoft/agent365-skills)
- [Agent 365 Python Agent Framework sample](https://github.com/microsoft/Agent365-Samples/tree/main/python/agent-framework/sample-agent)
- [Agent 365 samples](https://github.com/microsoft/Agent365-Samples)
- [Azure Container Apps Sandboxes samples](https://github.com/Azure-Samples/azure-container-apps-sandboxes)
- [Sandbox full-lifecycle lab](https://github.com/Azure-Samples/azure-container-apps-sandboxes/blob/main/python/labs/01-getting-started.ipynb)
- [Sandbox agents samples](https://github.com/Azure-Samples/azure-container-apps-sandboxes/tree/main/python/samples/08-sandbox-agents)

Source samples demonstrate product APIs and patterns; they are not automatically
the version pinned by this repository. For executable sandbox operations, use
this sample's `infra/scripts/`.
