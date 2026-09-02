# Agent 365 setup

This sample uses the **standard agent + OBO** path. It does not need an agent's
user account, mailbox, UPN, or Teams presence. Do not choose the AI teammate or
Agentic-User path for this sample.

## Preview and licensing checkpoint

Status as of **2026-09-01**:

| Capability | Status / requirement |
| --- | --- |
| Agent 365 | Generally available for commercial tenants since 2026-05-01; per-user licensing. At least one user needs a qualifying license. Microsoft recommends E5 as the base. |
| Agent 365 identity registration | No additional capability license in the developer quickstart, but Agent 365 must be enabled in the tenant. |
| Observability | At least one user must have Microsoft 365 E7 or Microsoft Agent 365 **assigned**. A SKU merely present in the tenant is insufficient; telemetry can otherwise be silently dropped. |
| Work IQ MCP | Preview, subject to supplemental preview terms, and requires Microsoft 365 Copilot. Availability and admin controls can vary by region. |
| AI teammate / agent's user account | Frontier preview only and out of scope. Frontier requires tenant enrollment and Global Administrator enablement. |
| Entra ID Governance for agents | Microsoft 365 E7, or Microsoft Agent 365 paired with at least Entra P1 or Microsoft 365 E3. |
| Container Apps Sandboxes | Preview; API/SDK/CLI can change, and preview sandboxes might need recreation. |
| Defender / Purview features | Entitlements vary by plan. Verify the service descriptions for the exact monitoring, DLP, audit, and eDiscovery features you intend to use. |

Also budget for Azure sandbox/snapshot/storage usage and Foundry model
consumption. Preview means no assumption of production SLA or compatibility.

## Roles and people

Identify these people before setup:

- **Sponsor:** accountable business representative for both blueprint and agent.
- **Developer:** Global Administrator or Agent ID Developer for registration.
- **Global Administrator:** reviews and grants tenant-wide OAuth consent. Required
  if the developer cannot grant the listed permissions.
- **Azure owner/operator:** can deploy and grant the sandbox data-plane role.
- **Security/compliance reviewers:** approve telemetry, Work IQ scopes, DLP, and
  retention.

Use separate test users and non-sensitive mail during validation.

## Guided setup with official skills

Install from the official repository:

```console
gh skill add microsoft/agent365-skills
```

Restart the coding assistant. Run it from this sample directory and state the
outcomes below. The text in quotation marks is a prompt, not a shell command.

### 1. Detect and route: `a365-setup`

> “Set up this project for Agent 365 as a standard OBO agent.”

Review its detected stack (Python / Microsoft Agent Framework), tenant,
subscription, standard-agent choice, OBO mode, and proposed capabilities.
`a365-setup` installs or updates the Agent 365 CLI, validates Azure
prerequisites, and delegates registration.

### 2. Register: `make-a365-agent`

> “Register this standard OBO agent with Agent 365. Use the approved sponsor.”

Review the resulting blueprint, one agent identity, sponsor assignments,
credential plan, declared permissions, and generated configuration. One
blueprint can create many identities and shares its credentials across them;
use a separate blueprint when the credential or baseline-permission boundary
must differ.

Register a **separate SPA/client application** for human sign-in. Configure
authorization code with PKCE and the SPA's own redirect URI. The blueprint
exposes the delegated scope
`api://<blueprint-app-id>/access_as_user`; preauthorize/consent it as required
and allow-list the SPA client ID in the API configuration. Agent identities and
blueprints cannot initiate browser `/authorize` SSO, so do not configure either
as if it were the SPA. A public SPA never has a client secret.

The skill may create local generated files. Treat IDs as configuration and any
secret values as secrets. Follow `.gitignore`; do not commit
`a365.generated.config.json`, local detection caches, certificates, tokens, or
consent URLs unless repository policy explicitly identifies a sanitized file.

### 3. Observe: `instrument-observability`

> “Add Agent 365 observability using OBO authentication. Do not record message
> content, prompts, recipient addresses, subjects, bodies, tokens, or draft text.”

The checked-in `app/observability.py` creates content-free `invoke_agent`,
inference, and tool scopes plus a metadata-only audit record. Use the skill to
configure the tenant-authenticated exporter and verify that any Agent Framework
auto-instrumentation does not duplicate those child spans. Do not treat console
or Application Insights output alone as proof that Agent 365 ingestion is
enabled.
Pseudonymous IDs are still data: restrict access and retention.

### 4. Connect mail: `add-workiq-tools`

> “Add only Work IQ Mail tools with delegated OBO permissions. Keep send
> disabled in the application allow-list.”

Do not request Calendar, Word, Teams, SharePoint, or application permissions.
The skill is the source of current tool server configuration; do not copy the
illustrative values from `ToolingManifest.example.json` into production.

### 5. Validate

> “Validate this Agent 365 integration without changing behavior.”

This routes to the installed validator capability (internally described as
`a365-code-validator` when available). Also run the repository tests. Confirm
offline behavior before and after onboarding is identical.

## Global Administrator consent

Blueprint permission declaration and admin consent are different steps. When
an Agent ID Developer performs setup, the tool completes what it can and prints
the next steps and a consent URL.

1. Developer records the tenant, blueprint, agent identity, sponsor, exact
   resources/scopes, and intended test users.
2. Developer sends the **fresh tool-generated** URL and review packet to the
   Global Administrator over an approved channel.
3. Global Administrator signs into the same tenant, reads the consent screen,
   compares every permission with the approval, and accepts only if they match.
4. Operator verifies the grant in Entra and reruns validation.
5. Keep `send` disabled until its delegated permission and control review are
   separately approved.

Do not paste consent URLs into issues or logs, manufacture a URL, grant broad
Graph permissions “for convenience,” or assume green setup output proves
consent.

## Runtime credential

Federate the blueprint to the Sandbox Group user-assigned managed identity
created by the infrastructure. This is the primary credential path and keeps
long-lived secrets out of the single image. At runtime:

1. the UAMI authenticates the blueprint for an Azure AD token exchange, with
   the child agent identity application ID in `fmi_path`;
2. the returned blueprint exchange token becomes the agent identity's client
   assertion in the OBO request; and
3. that OBO request includes the validated SPA user token and the approved Work
   IQ scope.

If managed-identity federation is unavailable, keep live mode disabled. This
sample intentionally does not implement a certificate or client-secret runtime
path; adding one requires a separate threat model, secret-store integration,
rotation procedure, and governance review.

The current architecture does not deploy a sidecar. A sidecar is an optional
alternative only for a compatible custom/multi-process image that installs and
runs it on loopback. Do not configure a localhost broker URL for the single
image.

### Live configuration map

Use the IDs emitted by the checked-in infrastructure and Agent 365 setup. The
names in `.env.example` are configuration contracts, not permission to invent
IDs.

| Setting | Source and purpose |
| --- | --- |
| `ENTRA_TENANT_ID` | Tenant that contains the SPA, blueprint, and agent identity. |
| `ENTRA_SPA_CLIENT_ID` | Separate public client registration used for browser authorization code with PKCE. |
| `ENTRA_ALLOWED_CLIENT_IDS` | Comma-separated API callers; include the SPA ID. The API compares this with token `azp`/`appid`. |
| `ENTRA_AUDIENCE` | Exactly `api://<blueprint-app-id>` for inbound token validation. |
| `ENTRA_API_SCOPE` | Exactly the blueprint's exposed `api://<blueprint-app-id>/access_as_user` scope requested by the SPA. |
| `ENTRA_BLUEPRINT_APP_ID` | Parent blueprint application/client ID used in the first server-side exchange. |
| `ENTRA_AGENT_IDENTITY_APP_ID` | Child agent identity application/client ID used as `fmi_path`, then as the OBO client ID. |
| `AZURE_CLIENT_ID` | Sandbox Group UAMI client ID. `DirectFmiOBOBroker` uses it for the managed-identity assertion; Foundry uses the same UAMI by default. |
| `OBO_BROKER_MODE` | Keep the implemented default, `direct_fmi`, for this single image. |
| `A365_MAILTOOLS_URL` | Tenant-approved Work IQ Mail MCP endpoint. |
| `A365_MAILTOOLS_AUDIENCE` | Work IQ Mail tools resource audience from approved setup output. |
| `A365_MAILTOOLS_SCOPE` | The configured tools audience plus `/.default`, as validated by the app. |

`OBO_BROKER_URL` is unused in `direct_fmi` mode. It is present only for the
optional `sidecar` mode and is valid only when a compatible image separately
installs and runs that sidecar on loopback. Do not add a localhost value to make
the primary path “look configured.”

## Readiness evidence

- Agent appears in the Agent 365 registry with owner/sponsor.
- Blueprint and agent identity are distinct and tenant-local values are correct.
- SPA/client registration is distinct, uses PKCE, requests only
  `api://<blueprint-app-id>/access_as_user`, and is allow-listed by client ID.
- UAMI federation, `fmi_path` binding, and the subsequent OBO exchange are
  validated without logging Tc, T1, or the downstream token.
- Consent shows only approved delegated Mail tooling.
- Live list/read/draft works as the signed-in test user; another user cannot
  access the first user's drafts.
- Send remains denied without both allow-list enablement and a valid
  confirmation.
- An invocation produces a root span and content-free metadata in the approved
  admin/security surface.
- Sponsor, expiry/review date, cleanup owner, and incident contact are recorded.
