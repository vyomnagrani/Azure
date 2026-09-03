# 03 - First application

**Implemented:** local app and API tests.  
**Deployment scaffold:** image and Container App configuration.  
**Deferred validation:** build, push, create/update, ingress, and cluster checks.

## 1. Validate locally

Follow the root sample README. The expected seed has four SKUs and 18 total
units. Successful test execution is required before producing an image.

## 2. Prepare an image later

The `Dockerfile` uses a pinned Python 3.12 slim tag, a non-root numeric user,
port 8080, and a liveness health check. Docker Desktop is not available for
this milestone, so the file has not been built.

At the later validation window, choose either an approved local engine or a
registry build service. Use an immutable, unique tag; never use `latest`.
An ACR operator may choose the public Azure CLI pattern below after verifying
the current CLI help and replacing all placeholders:

```console
az acr build --registry <registry-name> --image contoso-edge-store:<unique-tag> .
```

This is a documented scaffold, not a command run by this project.

## 3. Render and review the app YAML

Copy `deploy/config.example.env` to an ignored operator file. Replace every
`${...}` token in `deploy/containerapp.yaml`; do not submit unresolved tokens.
The YAML targets one replica because in-memory state is not shared.

Before deployment, compare the YAML schema with the output/help supported by
the installed `az containerapp` extension. The checked-in file has not been
submitted to Azure. A later operator may use the current documented
`az containerapp create --yaml` workflow, but must derive the exact command
from current Microsoft Learn/CLI help and the approved connected environment.

## 4. Validate the application later

Once the app reports a healthy revision and an ingress URL is approved:

```powershell
.\scripts\smoke-test.ps1 -BaseUrl "https://<approved-fqdn>"
```

```bash
bash ./scripts/smoke-test.sh "https://<approved-fqdn>"
```

The smoke test is read-only and does not adjust inventory.

## Later cluster acceptance criteria

- The deployment uses the approved connected environment and immutable image.
- Exactly one healthy revision receives traffic and one replica is requested.
- Liveness and readiness probes succeed on port 8080.
- HTTPS ingress returns the dashboard, four deterministic items, and matching
  summary counts.
- A controlled positive adjustment changes item and summary values.
- A below-zero adjustment returns 409 and leaves quantity unchanged.
- An unknown SKU returns 404 and invalid input returns 422.
- Application logs show startup and request access without credentials.
- Restarting the replica demonstrably resets data, confirming the documented
  in-memory limitation.
- Dry-run cleanup identifies only the sample app; approved cleanup removes only
  that app and leaves shared platform resources intact.
