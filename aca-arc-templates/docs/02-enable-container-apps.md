# 02 - Container Apps platform setup scaffold

**Deployment scaffold only. No platform commands have been run or
cluster-validated.**

This walkthrough begins with one already Arc-enabled AKS cluster and ends with
the platform persona handing an existing connected environment resource ID to
the application persona. It intentionally does not automate extension or
custom-location creation.

## Platform handoff checklist

Using the current Microsoft Learn guidance for Azure Container Apps on
Azure Arc-enabled Kubernetes, the platform persona must verify:

1. The reserved cluster is connected to Azure Arc and is in a supported region
   and Kubernetes configuration.
2. Required Azure resource providers and supported CLI extensions are
   registered/installed under the organization's change process.
3. The Container Apps extension is healthy and its version is supported.
4. The custom location and connected environment refer to this cluster.
5. Registry pull identity/credentials, outbound connectivity, ingress, DNS,
   certificates, and log collection satisfy the test plan.
6. The application operator has least-privilege access to inspect the
   environment and manage only the sample Container App.

Do not copy old preview commands from blogs. Product syntax and supported
versions can change. Use the current official procedures at execution time and
record their versions in the validation notes.

## Required private handoff values

- Subscription ID
- Resource group
- Azure location
- Connected environment name and full resource ID
- Approved registry hostname and immutable image reference
- Expected ingress exposure and DNS behavior
- Log access procedure

Store these values in an ignored local file based on
`deploy/config.example.env`. They are not secrets by definition, but they can
identify internal resources and do not belong in this sample.

## Exit criteria

- Platform health is green before the app is introduced.
- The connected environment is readable through an explicit preflight.
- Registry pull access is approved.
- Ownership, cost boundary, rollback owner, and validation window are recorded.
- No cluster, resource group, registry, or workspace is considered disposable.

