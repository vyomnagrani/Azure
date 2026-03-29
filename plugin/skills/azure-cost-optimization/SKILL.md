---
name: azure-cost-optimization
description: "Identify Azure cost savings from usage and spending data. USE FOR: optimize Azure costs, reduce Azure spending/expenses, analyze Azure costs, find cost savings, generate cost optimization report, identify orphaned resources to delete, rightsize VMs, reduce waste, optimize Redis costs, optimize storage costs, AKS cost analysis add-on, namespace cost, cost spike, anomaly, budget alert, AKS cost visibility, optimize Container Apps costs, rightsize Container Apps, Container Apps scale-to-zero savings. DO NOT USE FOR: deploying resources (use azure-deploy), general Azure diagnostics (use azure-diagnostics), security issues (use azure-security)"
license: MIT
metadata:
  author: Microsoft
  version: "1.0.3"
---

# Azure Cost Optimization Skill

Analyze Azure subscriptions to identify cost savings through orphaned resource cleanup, rightsizing, and optimization recommendations based on actual usage data.

## When to Use This Skill

Use this skill when the user asks to:
- Optimize Azure costs or reduce spending
- Analyze Azure subscription for cost savings
- Generate cost optimization report
- Find orphaned or unused resources
- Rightsize Azure VMs, containers, or services
- Identify where they're overspending in Azure
- **Optimize Redis costs specifically** - See [Azure Redis Cost Optimization](./references/azure-redis.md) for Redis-specific analysis
- **Optimize Container Apps costs** - See [Azure Container Apps Cost Optimization](./references/azure-container-apps.md) for ACA-specific analysis

## Instructions

Follow these steps in conversation with the user:

### Step 0: Validate Prerequisites

Before starting, verify these tools and permissions are available:

**Required Tools:**
- Azure CLI installed and authenticated (`az login`)
- Azure CLI extensions: `costmanagement`, `resource-graph`
- Azure Quick Review (azqr) installed - See [Azure Quick Review](./references/azure-quick-review.md) for details

**Required Permissions:**
- Cost Management Reader role
- Monitoring Reader role
- Reader role on subscription/resource group

**Verification commands:**
```powershell
az --version
az account show
az extension show --name costmanagement
azqr version
```

### Step 1: Load Best Practices

Get Azure cost optimization best practices to inform recommendations:

```javascript
// Use Azure MCP best practices tool
mcp_azure_mcp_get_azure_bestpractices({
  intent: "Get cost optimization best practices",
  command: "get_bestpractices",
  parameters: { resource: "cost-optimization", action: "all" }
})
```

### Step 1.5: Redis-Specific Analysis (Conditional)

**If the user specifically requests Redis cost optimization**, use the specialized Redis skill:

📋 **Reference**: [Azure Redis Cost Optimization](./references/azure-redis.md)

**When to use Redis-specific analysis:**
- User mentions "Redis", "Azure Cache for Redis", or "Azure Managed Redis"
- Focus is on Redis resource optimization, not general subscription analysis
- User wants Redis-specific recommendations (SKU downgrade, failed caches, etc.)

> **Note**: For general subscription-wide cost optimization (including Redis), continue with Step 2. For Redis-only focused analysis, follow the instructions in the Redis-specific reference document.

### Step 1.7: AKS-Specific Analysis (Conditional)

**If the user specifically requests AKS cost optimization**, use the specialized AKS reference files:

**When to use AKS-specific analysis:**
- User mentions "AKS", "Kubernetes", "cluster", "node pool", "pod", or "kubectl"
- User wants to enable the AKS cost analysis add-on or namespace cost visibility
- User reports a cost spike, unusual cluster utilization, or wants budget alerts

**Reference files (load only what is needed for the request):**
- [Cost Analysis Add-on](./references/azure-aks-cost-addon.md) — enable namespace-level cost visibility
- [Anomaly Investigation](./references/azure-aks-anomalies.md) — cost spikes, scaling events, budget alerts

> **Note**: For general subscription-wide cost optimization (including AKS resource groups), continue with Step 2. For AKS-focused analysis, follow the instructions in the relevant reference file above.

### Step 1.9: Container Apps-Specific Analysis (Conditional)

**If the user specifically requests Container Apps cost optimization**, use the specialized Container Apps reference:

📋 **Reference**: [Azure Container Apps Cost Optimization](./references/azure-container-apps.md)

**When to use Container Apps-specific analysis:**
- User mentions "Container Apps", "ACA", "container app", or "containerapp"
- User wants to identify over-provisioned replicas or idle environments
- User needs guidance on Consumption vs Dedicated workload profiles
- User wants to optimize Container Apps scaling configuration for cost

**Key capabilities:**
- Discover all Container Apps and environments in a subscription
- Analyze replica counts, CPU/memory allocation, and scaling configuration
- Identify scale-to-zero opportunities for non-production workloads
- Compare Consumption vs Dedicated plan costs
- Detect idle Container Apps environments with no active apps

> **Note**: For general subscription-wide cost optimization (including Container Apps), continue with Step 2. For Container Apps-only focused analysis, follow the instructions in the Container Apps-specific reference document.

### Step 2: Run Azure Quick Review

Run azqr to find orphaned resources (immediate cost savings):

📋 **Reference**: [Azure Quick Review](./references/azure-quick-review.md) - Detailed instructions for running azqr scans

```javascript
// Use Azure MCP extension_azqr tool
extension_azqr({
  subscription: "<SUBSCRIPTION_ID>",
  "resource-group": "<RESOURCE_GROUP>"  // optional
})
```

### Step 3–9: (Unchanged)

Continue with the standard cost optimization workflow: Discover Resources, Query Actual Costs, Validate Pricing, Collect Utilization Metrics, Generate Report, Save Audit Trail, Clean Up.

## References

- [Azure Redis Cost Optimization](./references/azure-redis.md)
- [Azure Container Apps Cost Optimization](./references/azure-container-apps.md)
- [Azure Quick Review](./references/azure-quick-review.md)
- [Azure Resource Graph Queries](./references/azure-resource-graph.md)
