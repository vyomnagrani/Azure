#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-http://127.0.0.1:8080}"
base_url="${base_url%/}"

python - "$base_url" <<'PY'
import json
import sys
import urllib.request

base = sys.argv[1]

def get(path):
    with urllib.request.urlopen(base + path, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"{path} returned {response.status}")
        return json.load(response)

assert get("/health/live") == {"status": "ok"}
assert get("/health/ready") == {"status": "ready"}
items = get("/api/inventory")
summary = get("/api/inventory/summary")
assert items and summary["distinct_items"] == len(items)
print(f"Smoke test passed for {base} ({len(items)} items).")
PY

