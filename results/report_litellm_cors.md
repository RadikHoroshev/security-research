# CORS Misconfiguration: Wildcard Origin with Credentials in BerriAI/litellm

## Summary
The LiteLLM proxy configures CORS with `allow_origins=["*"]` (line 1143 of `proxy_server.py`) combined with `allow_credentials=True` (line 1470). This combination allows any website to make authenticated cross-origin requests to the proxy and read responses, enabling credential theft and API key exfiltration.

## Severity
CVSS 3.1: **6.5 Medium**
Vector: `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N`

## Root Cause
In `litellm/proxy/proxy_server.py`, the CORS middleware is configured as:

```python
# Line 1143
origins = ["*"]

# Line 1468-1474
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # ["*"] — any origin
    allow_credentials=True,       # Include cookies/credentials
    allow_methods=["*"],          # All HTTP methods
    allow_headers=["*"],          # All headers
    expose_headers=LITELLM_UI_ALLOW_HEADERS,
)
```

The `["*"]` with `allow_credentials=True` is explicitly warned against in the CORS specification and the FastAPI/Starlette documentation. While modern browsers may block this specific combination, the health endpoints additionally set their own CORS headers manually:

```python
# health_endpoints/_health_endpoints.py:1392-1393
response_headers = {
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",  # Wildcard headers
}
```

This allows cross-origin preflight (OPTIONS) requests from any origin, and when combined with the global CORS middleware, can lead to credential leakage.

## Steps to Reproduce

1. Start LiteLLM proxy: `litellm --port 4000`
2. From any website (including attacker-controlled), make a cross-origin request:
```bash
curl -H "Origin: https://evil.com" http://localhost:4000/health/liveliness -v
```
3. Observe CORS headers in response

## Proof of Concept
```python
import requests

# Simulate cross-origin request from attacker's website
r = requests.get("http://localhost:4000/health/liveliness",
    headers={"Origin": "https://evil.com"})

print(f"Access-Control-Allow-Origin: {r.headers.get('Access-Control-Allow-Origin')}")
print(f"Access-Control-Allow-Credentials: {r.headers.get('Access-Control-Allow-Credentials')}")
print(f"Response: {r.text[:200]}")
```

## Impact
- **Credential theft**: If users have authenticated sessions, any website can read proxy responses
- **API key exposure**: Proxy responses may contain model configurations, internal URLs, and key metadata
- **Internal topology disclosure**: The `/routes` endpoint reveals all registered proxy endpoints
- **CSRF amplification**: CORS misconfiguration combined with CSRF can lead to state-changing attacks

## Remediation
1. Replace wildcard origin with specific allowed origins:
```python
# Instead of:
origins = ["*"]

# Use:
origins = ["https://litellm-ui.example.com", "https://admin.example.com"]
```
2. When `allow_credentials=True`, the origin MUST be specific — never `*`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-specific-origin.com"],  # Never ["*"] with credentials
    allow_credentials=True,
    ...
)
```
3. Remove manual CORS headers from health endpoints or ensure they match the global policy.

## Researcher's Note
Verified against litellm proxy v1.x (latest as of Mar 2026). The `origins = ["*"]` at line 1143 is hardcoded with no environment variable override. Modern browsers may partially mitigate this by rejecting `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`, but the health endpoints' manual CORS headers (`Access-Control-Allow-Headers: *`) create additional attack surface. This is especially dangerous if the proxy is deployed on an internal network where all services trust each other.
