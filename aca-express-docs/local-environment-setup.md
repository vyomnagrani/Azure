# Overview: Azure Container Apps Express

Azure Container Apps Express is a simplified, fast, and cost-efficient mode of Azure Container Apps designed for developers who want to deploy HTTP services with minimal configuration. It targets the common use case of "deploy my container and scale it based on traffic" without the complexity of full Container Apps.

## What is ACA Express?

ACA Express is a new `environmentMode` for Azure Container Apps. When you create an environment with `environmentMode=Express`, you get:

- **Faster deployments** — apps deploy in ~30 seconds instead of 2–5 minutes
- **Scale to zero** — no charges when your app has no traffic
- **Simplified model** — one app per environment, single container, HTTP only
- **Automatic auth** — one-click Microsoft Entra ID authentication setup
- **Built-in monitoring** — metrics, log streaming, and console access in the portal

## Who is ACA Express for?

ACA Express is ideal for:

- Web APIs and HTTP microservices
- Single-page application backends
- Webhooks and lightweight services
- Development and testing workloads
- Prototypes and demos that need quick deployment

## Key features

| Feature | Description |
|---------|-------------|
| **Container deployment** | Deploy any container image from ACR, Docker Hub, or other registries |
| **HTTP ingress** | HTTP/1.1, HTTP/2, and WebSocket support with external access |
| **Autoscaling** | Horizontal scaling from 0 to 10 replicas based on HTTP traffic or custom rules |
| **Environment variables & secrets** | Configure your app with key-value pairs and secure secrets |
| **Custom domains** | Bring your own domain with automatic TLS certificate management |
| **Authentication** | One-click Microsoft Entra ID or GitHub auth with auto app registration |
| **Metrics & logs** | CPU, memory, request count, latency metrics; real-time log streaming |
| **Console access** | Interactive shell into running containers for debugging |

## ACA Express vs. full Container Apps

| Capability | ACA Express | Full Container Apps |
|-----------|-------------|-------------------|
| Apps per environment | 1 | Multiple |
| Active revisions | 1 (single revision) | Multiple with traffic splitting |
| Networking | External HTTP only | External + internal, service discovery |
| Containers per app | 1 | Multiple + sidecars |
| Protocols | HTTP/1.1, HTTP/2, WebSocket | HTTP + gRPC + TCP/UDP |
| Dapr | Not available | Available |
| VNet integration | Not available | Available |
| Volume mounts | Not available | Available |
| Auth setup | Automated (one-click) | Manual Entra configuration |
| Deploy time | ~30 seconds | ~2–5 minutes |

## Resource model

```
Subscription
  └── Resource Group
        └── Managed Environment (environmentMode: "Express")
              └── Container App
                    ├── Container configuration (image, CPU, memory, port)
                    ├── Scaling rules (min/max replicas, HTTP/custom rules)
                    ├── Ingress (external access, custom domain, CORS, IP restrictions)
                    ├── Auth (Microsoft Entra ID, GitHub)
                    └── Monitoring (metrics, logs, console)
```

In Express mode, each environment hosts a single app. This simplifies networking, scaling, and management.

## How to get started

You can create and manage ACA Express apps using:

- **Azure Portal** — guided creation wizard with visual management
- **Azure CLI** — `az containerapp` commands for scripting and automation
- **ARM templates / Bicep** — infrastructure-as-code deployments
- **Terraform** — third-party IaC support

See [Deploying your app](deploy-to-aca-express.md) for step-by-step instructions.

## Next steps

- [Deploy your first app](deploy-to-aca-express.md)
- [Configure your app](advanced-configuration.md)
- [Set up autoscaling](scaling.md)
- [Monitor with metrics and logs](operations-monitoring.md)
- [Debug with console access](shell-access-troubleshooting.md)
