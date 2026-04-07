## Supplemental Evidence — Vulnerability Confirmed Live (Apr 7, 2026)

The `embeddings` endpoint remains **unauthenticated** in the current source.

**File:** `backend/open_webui/routers/openai.py`
**Function signature:** `async def embeddings(request: Request, form_data: dict, user)`

The `user` parameter is a plain function argument, **not** `user=Depends(get_verified_user)`. There is no authentication decorator on this endpoint. This means any caller can invoke `/api/embeddings` (and `/api/v1/embeddings`) without providing credentials.

**Impact:** Unauthenticated access to the embedding API allows arbitrary callers to consume model inference resources, leading to:
- **Cost amplification** — attacker drives up API charges to the OpenAI/LLM provider
- **Denial of service** — resource exhaustion degrades service for legitimate users
- **No rate limiting per identity** — without auth, per-user throttling is impossible

This is **not post-fix** — the vulnerability is present in the current `main` branch.

Source: https://github.com/open-webui/open-webui/blob/main/backend/open_webui/routers/openai.py
