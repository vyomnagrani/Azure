# Troubleshooting

Work from the boundary nearest the symptom. Do not “fix” authorization by adding
broad roles/scopes or bypassing token validation.

## Offline app

| Symptom | Check / resolution |
| --- | --- |
| Import or package error | Use Python 3.11+, activate the intended environment, and run `python -m pip install -e ".[test]"`. Use `".[live,test]"` only for the live adapter. |
| Fixture not found | Start in the sample root or set `OFFLINE_FIXTURE_PATH` to an existing synthetic JSON file. |
| Startup rejects configuration | Confirm `APP_MODE=offline`, remove `send` from `ALLOWED_OPERATIONS`, and use the offline fixture/user/tenant values. |
| Mail send returns an error | Expected. Offline mode never sends. Create and inspect a draft instead. |
| Unexpected results | Offline ask/triage uses deterministic keyword rules, not Foundry. Check `sample-data/inbox.json`. |

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Authentication and OBO

| Symptom | Check / resolution |
| --- | --- |
| Missing access token | The separate SPA/client must sign the human in by authorization code with PKCE and request `api://<blueprint-app-id>/access_as_user`. Agent identities cannot perform browser SSO. Offline calls do not require this token. |
| Invalid issuer/audience/tenant/scope | Confirm issuer, `tid`, JWKS, audience `api://<blueprint-app-id>`, and delegated `access_as_user`. A Graph or Work IQ token is not a valid incoming user assertion. Never disable these checks. |
| Unexpected client | The inbound token's `azp`/`appid` must be an allow-listed SPA/client application ID. Do not use the blueprint or agent identity ID as the browser client. |
| Managed identity assertion fails | Confirm the Sandbox Group UAMI is available inside the sandbox, its client ID is selected, and its federated identity credential on the blueprint has the exact issuer, subject, and audience configured by the supported setup path. |
| Blueprint exchange fails | Confirm the token request authenticates the blueprint with the UAMI assertion, targets `api://AzureADTokenExchange/.default`, and sets `fmi_path` to the child agent identity application ID. Use the approved library/adapter rather than hand-building a variant. |
| OBO exchange fails | Confirm the client ID switches to the agent identity, T1 is the client assertion, the validated SPA token Tc is the user assertion, the requested scope is the approved Work IQ scope, and consent exists in the same tenant. |
| Cross-user data concern | Stop testing. Verify user/tenant binding, token subject/actor, caches, drafts, and tool arguments. Revoke access and follow the incident process if data crossed boundaries. |

Remember: in OBO the human is the subject and the agent identity is the actor.
The UAMI authenticates the blueprint exchange but is not a shortcut for the
human assertion. The current image has no sidecar. Treat sidecar guidance as an
optional alternative for a compatible custom/multi-process image only.

## Agent 365 setup

| Symptom | Check / resolution |
| --- | --- |
| Skills are not found | Run `gh skill add microsoft/agent365-skills`, restart the coding assistant, and list installed skills in the assistant. |
| Setup reports missing tenant prerequisites | Follow `a365-setup` output. Confirm Agent 365 is enabled and the signed-in account/tenant is correct. Do not guess a preview CLI command. |
| Registration forbidden | Use Global Administrator or Agent ID Developer as documented; verify tenant and role activation. |
| Setup waits for consent | An Agent ID Developer cannot complete tenant-wide OAuth grants. Give the generated next steps/URL to a Global Administrator. |
| Work IQ step is skipped | It requires delegated/OBO mode and Microsoft 365 Copilot. It is intentionally skipped for S2S. |
| Tool call is forbidden | Check Global Administrator consent, Work IQ server allow/block state, user license/access, exact delegated scopes, and audience. |
| Generated config differs from docs | Trust the installed skill/current official docs. Preview output evolves. Review and map actual generated values; do not add guessed fields. |

## Observability

| Symptom | Check / resolution |
| --- | --- |
| HTTP success but no telemetry | Confirm the `instrument-observability` journey configured the tenant-authenticated Agent 365 exporter, then confirm at least one user has E7 or Agent 365 assigned; tenant possession alone is insufficient. |
| Defender sees spans but other surfaces do not | Confirm one valid root `invoke_agent` span with tool/inference spans nested beneath it. |
| Content appears in telemetry | Disable the live test, remove prompt/mail/tool payload capture, rotate exposed credentials if any, and follow data incident policy. |
| Wrong actor | Recheck selected OBO mode and distinct human, agent identity, blueprint, and runtime IDs. |

Use the installed validation skill: ask the coding assistant to “validate this
Agent 365 integration.” Availability may be shown as `a365-code-validator` or
Validate & Diagnose.

## Foundry

| Symptom | Check / resolution |
| --- | --- |
| No model deployment / quota | Confirm the `azd` environment's region supports both services and the deployment name matches the actual Foundry output. Request quota or select an approved compatible region/model. |
| Credential unavailable | Confirm managed identity assignment/federation and RBAC. Locally, use an approved developer credential; never add a secret to source. |
| Offline app tries Foundry | Confirm `APP_MODE=offline`. Foundry runtime must only be constructed in live mode. |

## Sandbox lifecycle

| Symptom | Check / resolution |
| --- | --- |
| Data-plane 401/403 | Confirm Entra work account, correct group endpoint, and **Container Apps SandboxGroup Data Owner** at the intended scope. ARM Contributor alone does not grant data-plane access. |
| Wrapper rejects an option | Read the checked-in wrapper and installed dependency versions. Preview contracts change; do not substitute syntax from search results. |
| Exposed endpoint fails | Confirm sandbox is `Running`, correct app port is exposed, FastAPI binds `0.0.0.0`, health endpoint works inside, and network policy allows the route. |
| Resume is unhealthy | Memory-restored network connections might be stale; allow clients to reconnect. Disk suspend restarts processes. Never replay a pending send. |
| Snapshot restore differs | Tier, entrypoint, command, environment, and region come from the snapshot. Create from the disk image if those must change. |
| Costs continue after stop | CPU/memory fees stop, but snapshot/volume/storage and other Azure resources can continue charging. Run full cleanup. |

Inventory the actual scripts:

```powershell
Get-ChildItem .\infra\scripts -File | Sort-Object Name
```

## Confirmation and send

| Symptom | Meaning / action |
| --- | --- |
| Send not allowed | Expected until `send` is explicitly added to the live allow-list after governance approval. |
| Confirmation expired | Re-present the exact current draft and request a new token. |
| Binding mismatch | User, tenant, draft, or action differs. Do not retry with another user's token. |
| Replay rejected | Expected. A confirmation is one-time; obtain a new confirmation for a new attempt after checking provider state. |
| Draft disappears after restart | The sample uses process-local storage. Create a new draft; do not weaken safety. Use an atomic shared store in a scale-out design. |
| Provider timed out during send | Treat outcome as unknown. Query the mailbox/provider with an idempotency strategy before asking the human to confirm another send. |

## Escalation packet

Record timestamps, correlation ID, mode, tenant ID, pseudonymous user/agent IDs,
operation, wrapper name/version, sandbox state, and sanitized error category.
Exclude tokens, consent URLs, mail content, prompts, recipient addresses,
subjects, draft bodies, and secrets. Notify the technical owner and sponsor;
involve security/compliance for possible unauthorized access or disclosure.
