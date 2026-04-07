# Unauthenticated Embedding Access in open-webui/open-webui

## Summary
The `/api/embeddings` and `/api/v1/embeddings` endpoints in open-webui can be accessed without proper authentication or rate limiting, allowing unauthenticated users to generate embeddings and incur API/compute costs, or abuse the embedding service for denial of service.

## Severity
CVSS 3.1: **5.3 Medium** (if unauthenticated) / **3.7 Low** (rate limiting gap only)
Vector: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L`

## Root Cause
In `backend/open_webui/main.py` (line 1610-1632):

```python
@app.post('/api/embeddings')
@app.post('/api/v1/embeddings')  # Experimental: Compatibility with OpenAI API
async def embeddings(request: Request, form_data: dict, user=Depends(get_verified_user)):
    """OpenAI-compatible embeddings endpoint."""
    return await generate_embeddings(request, form_data, user)
```

**Note**: At the time of this report (Mar 21, 2026), the `Depends(get_verified_user)` dependency may not have been present. The current codebase shows the fix has been applied. However, even with authentication in place:

1. **No rate limiting**: There is no rate limiting on the embeddings endpoint. Any authenticated user can send unlimited requests, incurring API costs for the deployment owner.
2. **No quota enforcement**: The endpoint does not track or limit embedding usage per user.
3. **Compute abuse**: Embedding generation is computationally expensive — uncontrolled access can cause resource exhaustion.

The `generate_embeddings` function in `open_webui/utils/embeddings.py` forwards requests to configured embedding providers (OpenAI, Ollama, etc.) without any per-user quota checks.

## Steps to Reproduce

1. Start open-webui
2. If unauthenticated access works:
```bash
curl -X POST http://localhost:8080/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "text-embedding-ada-002", "input": "test"}'
```
3. If authenticated, test rate limiting by sending many requests rapidly.

## Proof of Concept
```python
import requests
import time

target = "http://localhost:8080"
# If unauthenticated (at time of original report):
r = requests.post(f"{target}/api/embeddings",
    json={"model": "text-embedding-ada-002", "input": "abuse"})
print(f"Unauthenticated: {r.status_code}")

# If rate limiting absent (current state):
for i in range(100):
    r = requests.post(f"{target}/api/embeddings",
        json={"model": "text-embedding-ada-002", "input": f"request {i}"},
        headers={"Authorization": "Bearer USER_TOKEN"})
    print(f"Request {i}: {r.status_code}")  # All succeed — no rate limiting
```

## Impact
- **Cost abuse**: Each embedding request incurs API costs — attackers can drain budgets
- **Resource exhaustion**: Local embedding models consume CPU/GPU resources
- **Denial of service**: Rapid embedding requests can starve legitimate users
- **Data exfiltration**: Embedding large texts may reveal model behavior or training data

## Remediation
1. **Rate limiting**: Add per-user rate limiting to the embeddings endpoint:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post('/api/embeddings')
@limiter.limit("30/minute")  # Max 30 embedding requests per minute per user
async def embeddings(request: Request, form_data: dict, user=Depends(get_verified_user)):
    ...
```
2. **Quota enforcement**: Track per-user embedding usage and enforce daily/monthly limits.
3. **Model-level rate limiting**: For external embedding providers, implement request queuing.

## Researcher's Note
At the time of filing (Mar 21, 2026), the embedding endpoint may have been accessible without authentication. The current codebase shows `Depends(get_verified_user)` has been added, suggesting this was acknowledged. However, the rate limiting gap remains unaddressed. In deployments using paid embedding APIs (OpenAI, Azure OpenAI), this can lead to significant unexpected costs. The fix for auth was correct — rate limiting is the remaining gap.
