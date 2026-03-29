# Container Apps Cost Optimization

Analyze Azure Container Apps resources for cost savings opportunities.

## When to Use

Use this reference when the user asks about:
- Container Apps cost optimization or spending reduction
- Right-sizing container app CPU/memory allocations
- Identifying idle or over-provisioned Container Apps environments
- Choosing between Consumption and Dedicated workload profiles

## Analysis Steps

### 1. Discover Container Apps Resources

```bash
# List all Container Apps in subscription
az containerapp list --subscription SUB_ID \
  --query "[].{name:name,rg:resourceGroup,env:properties.environmentId}" -o table

# List Container Apps environments
az containerapp env list --subscription SUB_ID -o table
```

### 2. Check Replica and Scaling Configuration

```bash
# For each app, check scaling config
az containerapp show --name APP -g RG \
  --query "{min:properties.template.scale.minReplicas,max:properties.template.scale.maxReplicas,rules:properties.template.scale.rules[].name}"

# Check current replica count
az containerapp replica list --name APP -g RG --revision REV -o table
```

### 3. Analyze Resource Allocation

```bash
# Check CPU/memory per container
az containerapp show --name APP -g RG \
  --query "properties.template.containers[].{name:name,cpu:resources.cpu,memory:resources.memory}"

# Check utilization metrics (last 7 days)
az monitor metrics list --resource RESOURCE_ID \
  --metric "UsageNanoCores,WorkingSetBytes" \
  --interval PT1H --aggregation Average \
  --start-time START --end-time END
```

## Common Optimization Opportunities

### Scale-to-Zero for Non-Production

**Impact: High** — Apps with `minReplicas: 1` that receive no traffic during off-hours.

**Detection:**
```bash
az containerapp show --name APP -g RG \
  --query "properties.template.scale.minReplicas"
```

**Fix:** Set `minReplicas: 0` for dev/test apps and non-latency-sensitive workloads:
```bash
az containerapp update --name APP -g RG --min-replicas 0
```

### Right-Size CPU and Memory

**Impact: Medium** — Apps allocated more CPU/memory than they use.

Check utilization against allocation. If average CPU < 25% of allocated, consider downsizing:

| Allocation | Monthly Cost (Consumption, approx) |
|-----------|-----------------------------------|
| 0.25 vCPU / 0.5 GiB | ~$15/mo per always-on replica |
| 0.5 vCPU / 1 GiB | ~$30/mo per always-on replica |
| 1 vCPU / 2 GiB | ~$60/mo per always-on replica |
| 2 vCPU / 4 GiB | ~$120/mo per always-on replica |

### Consumption vs Dedicated Plan

| Factor | Consumption | Dedicated |
|--------|------------|-----------|
| Best for | Variable/bursty traffic | Steady-state workloads |
| Billing | Per-request + per-second active | Reserved profile capacity |
| Scale to zero | Yes | Yes (but profile stays running) |
| Cost advantage | Low/variable traffic | High-utilization workloads |

**Recommendation:** Use Consumption unless apps consistently use >60% of a Dedicated profile's capacity.

### Idle Environments

**Impact: Low-Medium** — Container Apps environments with no active apps still incur minor platform costs.

```bash
# Find environments with zero apps
az containerapp list --subscription SUB_ID \
  --query "[].properties.environmentId" -o tsv | sort -u > envs_with_apps.txt
az containerapp env list --subscription SUB_ID \
  --query "[].id" -o tsv | sort > all_envs.txt
comm -23 all_envs.txt envs_with_apps.txt
```

### Optimize Dapr Component Costs

If using Dapr with Azure services, ensure state store and pub/sub use the cheapest tier meeting throughput needs.

## Report Template

```markdown
# Container Apps Cost Optimization Report

## Summary
- **Total Container Apps**: <count>
- **Total Environments**: <count>
- **Estimated Monthly Savings**: $<amount>

## Findings

| # | App | Issue | Savings | Action |
|---|-----|-------|---------|--------|
| 1 | | Over-provisioned CPU | $X/mo | Reduce to 0.25 vCPU |
| 2 | | minReplicas=1 (dev) | $X/mo | Set minReplicas=0 |
```
