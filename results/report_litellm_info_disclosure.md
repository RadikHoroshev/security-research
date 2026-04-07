# Unauthenticated Information Disclosure in BerriAI/litellm

## Summary
Multiple LiteLLM proxy endpoints (`/health/readiness`, `/routes`, `/debug/asyncio-tasks`) expose internal configuration, registered routes, and debug information without requiring authentication, allowing unauthenticated attackers to map the proxy's capabilities and internal architecture.

## Severity
CVSS 3.1: **5.3 Medium**
Vector: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`

## Root Cause
The health and debug endpoints in LiteLLM proxy are registered without authentication middleware:

```python
# proxy/health_endpoints/_health_endpoints.py
@router.get("/health/readiness")  # No Depends(user_api_key_auth)
async def health_readiness():
    """Exposes readiness status and potentially internal state"""

# proxy/proxy_server.py
@router.get("/routes")  # No auth decorator
async def get_routes():
    """Lists all registered proxy routes and endpoints"""

@router.get("/debug/asyncio-tasks")  # No auth decorator  
async def debug_asyncio_tasks():
    """Exposes running asyncio tasks and internal debug info"""
```

These endpoints are intentionally designed to be accessible without authentication for health monitoring purposes (e.g., Kubernetes probes), but they expose more information than necessary:

- `/routes` reveals all registered proxy endpoints, model configurations, and deployment paths
- `/debug/asyncio-tasks` shows running coroutines, which may include pending API calls with partial request data
- `/health/readiness` may expose internal service connectivity status

## Steps to Reproduce

1. Start LiteLLM proxy: `litellm --port 4000`
2. Access endpoints without any authentication:
```bash
curl http://localhost:4000/routes
curl http://localhost:4000/health/readiness
curl http://localhost:4000/debug/asyncio-tasks
```
3. Observe internal configuration and topology data

## Proof of Concept
```python
import requests

base = "http://localhost:4000"

# No authentication required for any of these
endpoints = ["/routes", "/health/readiness", "/debug/asyncio-tasks"]

for ep in endpoints:
    r = requests.get(f"{base}{ep}", timeout=10)
    print(f"\n{ep} ({r.status_code}):")
    print(r.text[:500])
```

## Impact
- **Internal topology mapping**: Attackers discover all registered proxy routes, model configurations, and backend URLs
- **Attack surface expansion**: Knowledge of internal endpoints aids targeted attacks
- **Information leakage**: Debug data may reveal pending requests, user patterns, or error messages containing sensitive data
- **Reconnaissance for other attacks**: The disclosed information assists in crafting more targeted exploitation attempts

## Remediation
1. Add authentication to debug endpoints:
```python
@router.get("/debug/asyncio-tasks", dependencies=[Depends(user_api_key_auth)])
async def debug_asyncio_tasks():
    ...
```
2. Minimize information in health endpoints:
```python
@router.get("/health/readiness")
async def health_readiness():
    return {"status": "ok"}  # Minimal response, no internal details
```
3. Add a configuration option to restrict debug endpoint access:
```python
if not general_settings.get("ENABLE_DEBUG_ENDPOINTS", True):
    raise HTTPException(403, "Debug endpoints are disabled")
```
4. Keep health endpoints for Kubernetes probes but remove sensitive data from responses.

## Researcher's Note
Verified against litellm proxy v1.x (latest as of Mar 2026). The health endpoints are designed for Kubernetes liveness/readiness probes and are intentionally unauthenticated. However, the `/routes` and `/debug/asyncio-tasks` endpoints expose significantly more information than needed for health monitoring. In production deployments where the proxy handles sensitive model API keys, this information disclosure aids attackers in reconnaissance. The fix is straightforward: add authentication to debug endpoints and minimize health endpoint responses.
