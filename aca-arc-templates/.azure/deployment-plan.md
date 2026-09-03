# ACA Arc Templates Deployment Plan

## Status

Local validation complete; deployment validation deferred

## Scope

Prepare the local-only "Contoso Edge Store" golden path and deferred deployment
scaffolding for Azure Container Apps on an existing Arc-enabled Kubernetes
environment. No Azure authentication, cloud/cluster commands, deployment,
Docker build, commit, or push is in scope.

## Decisions

- Modify the repository with one self-contained content set.
- Use Python 3.11+, FastAPI, Pydantic, Uvicorn, plain static assets, and a
  thread-safe in-memory repository.
- Package the `app` module with Hatchling and test isolated ASGI apps with
  pytest and HTTPX.
- Target an existing connected environment only through parameterized,
  unvalidated first-application YAML.
- Keep platform setup with the platform persona and code/image/app operation
  with the application persona.
- Keep scripts local/read-only by default and cleanup sample-only and dry-run.
- Defer Azure context, authentication, platform setup, image build/push,
  deployment, cluster validation, event processing, KEDA, Jobs, Dapr,
  production hardening, and multi-location.

## Artifacts

- `app`, `tests`, `scripts`, `deploy`, and `docs`
- `pyproject.toml`, `Dockerfile`, and local configuration examples
- `.github/workflows/aca-arc-templates-ci.yml`
- Repository README entry and section

## Acceptance criteria

- Tests cover health, deterministic data, adjustment outcomes, summary changes,
  and the dashboard with isolation.
- Python compiles and Bash/PowerShell scripts parse.
- No checked-in real Azure IDs, resource names, or secrets.
- Documentation distinguishes implemented behavior, deployment scaffolding,
  and deferred live validation.
- Later cluster validation covers revision health, ingress/API behavior,
  adjustment semantics, logs, and safe sample-only cleanup.

## Validation constraints

Only Python tests, compilation, shell/parser syntax, and safe static checks are
allowed now. Azure, Kubernetes, Docker, and live deployment validation are
explicitly deferred.

## Validation proof

Executed locally on 2026-09-02:

- `python -m pytest` - 11 tests passed.
- `python -m compileall -q app tests` - passed.
- `bash -n scripts/preflight.sh scripts/smoke-test.sh scripts/cleanup.sh` -
  passed.
- PowerShell parser validation for all `scripts/*.ps1` - passed.
- Default Bash cleanup dry-run - passed without invoking Azure.
- Static GUID, Docker tag/user, and deployment-placeholder checks - passed.

The Dockerfile was not built. Azure CLI and kubectl live modes were not run.
The Container App YAML was not submitted or cluster-validated.
