# Troubleshooting

| Symptom | Safe checks | Likely boundary |
| --- | --- | --- |
| Python install fails | Confirm Python 3.11+, recreate `.venv`, retry editable install | Local |
| Tests appear stateful | Run tests normally; each test gets a new repository/app | Application |
| Dashboard says unable to load | Check browser network calls and `/api/inventory/summary` | Application/ingress |
| Adjustment returns 422 | Send an integer `quantity_delta` from -1000 to 1000, excluding zero | Client |
| Adjustment returns 409 | Requested removal exceeds available stock | Expected business rule |
| Image does not start | Inspect standard output, port 8080, image architecture, non-root permissions | Image/runtime |
| Probe fails | Request the exact health path from inside the approved diagnostic boundary | Runtime/ingress |
| Image pull fails | Verify immutable reference and platform-managed registry pull access | Platform |
| No public URL | Verify external ingress was approved and configured; inspect DNS/certificate policy | Platform |
| Different replicas show different stock | In-memory state is per process; keep one replica for this milestone | Known limitation |

## Defensive workflow

Do not respond to an app failure by recreating the Arc connection, extension,
custom location, cluster, registry, resource group, or logging workspace.
Collect read-only evidence first and involve the owning persona. Do not paste
tokens, kubeconfig, subscription details, or internal URLs into issues.

## Template problems

If the checked-in YAML is rejected, stop rather than guessing flags or schema.
Check the installed extension version and current official Container Apps YAML
reference, then make a reviewed source change. The YAML is explicitly
unvalidated in this milestone.

