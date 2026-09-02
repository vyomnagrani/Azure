# Azure Deployment Plan

> **Status:** Ready for Validation

## Project overview

Create a development sample that hosts an interactive inbox-management agent in an Azure Container Apps Sandbox and connects it to Microsoft Agent 365.

**Path:** New project

## Requirements

| Attribute | Value |
| --- | --- |
| Classification | Development sample |
| Scale | One user-operated sandbox |
| Budget | Cost-optimized; suspend when idle |
| Subscription | Selected by the user through `azd` |
| Location | Selected by the user through `azd`; must support ACA Sandboxes and the chosen Foundry model |

## Architecture

- Python FastAPI application using Microsoft Agent Framework.
- Microsoft Agent 365 identity, OBO authentication, Work IQ Mail tooling, and observability.
- Azure Container Apps Sandbox Group and lifecycle-managed sandbox.
- Microsoft Foundry model endpoint.
- Azure Developer CLI with Bicep and post-provision lifecycle scripts.

## Identity and safety

- A signed-in human is the OBO token subject; the registered agent identity is the actor.
- Live mailbox actions use delegated Work IQ Mail permissions.
- Offline fixture mode is the default.
- Reply sending requires a separate, short-lived confirmation.
- Runtime authentication uses managed identity federation. If the Sandbox
  preview cannot expose that identity, live mode remains blocked; this sample
  does not implement a certificate or client-secret runtime path.

## Execution checklist

1. Create the application and offline inbox experience.
2. Add Entra sign-in, OBO, and send confirmation.
3. Register Agent 365 identity and Work IQ tooling.
4. Add privacy-safe Agent 365 observability.
5. Generate Sandbox Group, Foundry, monitoring, identity, and lifecycle artifacts.
6. Document deployment, registration, governance, and sandbox operations.
7. Validate locally, validate infrastructure, and run Agent 365 preflight.

## Files to generate

- `azure.yaml`
- `infra/main.bicep`
- `infra/main.parameters.json`
- `infra/modules/*.bicep`
- `infra/scripts/*`
- `Dockerfile`
- `app/*`
- `tests/*`
- `docs/*`

## Validation gates

- Python tests and static checks pass.
- Container builds and the offline smoke test succeeds.
- Bicep and Azure Developer CLI configuration validate.
- Sandbox lifecycle commands are checked against the installed preview CLI/SDK.
- Agent 365 code validation passes in a configured tenant.

## Notes

- Preview API and package versions must be rechecked during implementation.
- Local tests, source compilation, container build and offline container smoke
  test, Bicep compilation, lifecycle-script parsing, and ACA CLI capability
  checks completed. Tenant registration, consent, live mailbox, exporter
  ingestion, and deployed Sandbox identity/lifecycle checks require the
  customer's licensed test tenant.
- Deployment execution is outside preparation; run Azure validation before any `azd up`.
