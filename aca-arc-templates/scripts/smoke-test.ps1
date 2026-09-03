[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8080"
)

$ErrorActionPreference = "Stop"
$base = $BaseUrl.TrimEnd("/")

$live = Invoke-RestMethod -Uri "$base/health/live"
if ($live.status -ne "ok") { throw "Liveness check failed." }

$ready = Invoke-RestMethod -Uri "$base/health/ready"
if ($ready.status -ne "ready") { throw "Readiness check failed." }

$items = Invoke-RestMethod -Uri "$base/api/inventory"
$summary = Invoke-RestMethod -Uri "$base/api/inventory/summary"
if ($items.Count -lt 1 -or $summary.distinct_items -ne $items.Count) {
    throw "Inventory response and summary do not agree."
}

Write-Host "Smoke test passed for $base ($($items.Count) items)."

