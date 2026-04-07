# LlamaIndex MCP Auth Bypass Analysis

**Source:** `https://github.com/run-llama/llama_index` (depth-1 clone, April 2026)
**Package:** `llama-index-tools-mcp` + `llama-index-tools-mcp-discovery`
**Related GitHub Issue:** [#21006](https://github.com/run-llama/llama_index/issues/21006) (open, 2026-03-14) — "MCP tool integration has no per-message authentication or integrity verification"

---

## 1. Vulnerability Overview

The LlamaIndex MCP (Model Context Protocol) integration contains multiple security weaknesses that allow authentication bypass, unauthorized tool execution, credential leakage, and information disclosure. Auth is **optional by default** — the default `BasicMCPClient(url)` constructor requires no credentials whatsoever.

---

## 2. Key Findings

### 2.1 Auth Bypass: SSE Transport vs. Streamable HTTP (Default) — INCONSISTENCY

**File:** `llama_index/tools/mcp/client.py`, method `_run_session()` (lines ~230–262)

```python
if enable_sse(self.command_or_url):
    # SSE: auth passed EXPLICITLY
    async with sse_client(
        self.command_or_url,
        auth=self.auth,          # <-- auth param used directly
        ...
    ) as streams:
        ...
else:
    # Streamable HTTP (DEFAULT): auth NOT passed as param
    async with streamable_http_client(
        url=self.command_or_url,
        http_client=self.http_client,  # <-- auth only works if attached to client
    ) as (read, write, _):
        ...
```

The SSE path passes `auth=self.auth` explicitly. The default Streamable HTTP path relies entirely on `self.http_client.auth` being pre-set. This auth is only attached if the caller passed `auth=` to `BasicMCPClient()`. The constructor creates `BasicMCPClient(url)` with **no auth required**, so the default path has zero authentication.

**Impact:** Any unauthenticated caller can connect to an MCP server over HTTP/Streamable transport and invoke tools without credentials.

---

### 2.2 No Auth on `workflow_as_mcp` Exposed Endpoints

**File:** `llama_index/tools/mcp/utils.py`, function `workflow_as_mcp()` (line 107)

```python
app = FastMCP(**fastmcp_init_kwargs)
```

The helper converts any LlamaIndex `Workflow` into a network-accessible MCP server. `FastMCP` is initialized with no `auth` parameter, and none of the `fastmcp_init_kwargs` documentation or defaults enforce authentication. The resulting server is fully open.

**Impact:** Entire agent workflows (including those with access to databases, APIs, or sensitive data) are exposed as unauthenticated RPC endpoints. Any client that can reach the server can invoke the workflow.

---

### 2.3 Credential Confusion via Mutated Shared `AsyncClient`

**File:** `llama_index/tools/mcp/client.py`, `__init__()` (lines 145–154)

```python
self.client_provided = http_client is not None
self.http_client = (
    http_client
    if self.client_provided
    else create_mcp_http_client(...)
)
if auth is not None:
    self.http_client.auth = auth   # <-- mutates the SHARED external client
```

When a developer provides an external `httpx.AsyncClient` and also passes `auth`, the auth is written onto the shared client object. If the same `AsyncClient` is then reused for a different `BasicMCPClient` instance (pointing to a different server), the auth from the previous client remains — or a new auth overwrites it — causing credentials to be sent to unintended servers.

**Impact:** "Confused Deputy" — credentials of Server A may be sent to Server B. Alternatively, credentials may be stripped unexpectedly if `auth=None` and the `.auth` attribute is not explicitly cleared.

---

### 2.4 Global Log Leakage via `logging.basicConfig`

**File:** `llama_index/tools/mcp/client.py`, `_configure_tool_call_logs_callback()` (called from `call_tool`)

```python
logging.basicConfig(
    level=logging.DEBUG,
    format="...",
    handlers=[stream_handler],
)
fastmcp_logger.setLevel(logging.DEBUG)
http_logger = logging.getLogger("httpx")
http_logger.setLevel(logging.DEBUG)
```

`logging.basicConfig()` configures the **global root logger** for the entire Python process. When `tool_call_logs_callback` is provided by the user, ALL application logs — including those from other threads, coroutines, and libraries — are captured into a `StringIO` buffer and forwarded to the callback.

**Impact:** OAuth tokens, API keys, user PII, internal service URLs, and other sensitive data logged anywhere in the process can be exfiltrated through the `tool_call_logs_callback`. If this callback is user-supplied or routes to a remote endpoint, it becomes an inadvertent data exfiltration channel.

---

### 2.5 Unauthenticated MCP Discovery Requests (`MCPDiscoveryTool`)

**File:** `llama_index/tools/mcp_discovery/base.py`, `discover_tools()` (line ~53)

```python
async with session.post(
    self.api_url, json={"need": user_request, "limit": limit}
) as response:
```

The `MCPDiscoveryTool` POSTs natural language requests to an arbitrary `api_url` with no authentication headers, no TLS validation enforcement, and no URL allowlisting.

**Impact:**
- Natural language agent queries (which may contain sensitive context, user data, or internal business logic) are sent without auth to a potentially untrusted endpoint.
- An attacker who controls or MITMs `api_url` can return malicious tool recommendations, leading to Server-Side Request Forgery (SSRF) or tool poisoning (OWASP MCP03).

---

### 2.6 No Per-Message Integrity / Replay Protection (Architectural)

**GitHub Issue:** [#21006](https://github.com/run-llama/llama_index/issues/21006)

Confirmed by upstream issue: JSON-RPC tool call messages are **unsigned**. There is no nonce, no HMAC, no message-level identity assertion. Tool definitions from `tools/list` are also unsigned and can be tampered with in transit.

**Impact:**
- Tool poisoning: malicious server returns modified tool definitions.
- Parameter tampering: tool call arguments modified in transit.
- Replay attacks: identical tool calls can be replayed indefinitely.

---

## 3. CVE / Existing Reports

| # | Title | State | Date |
|---|-------|-------|------|
| GH #21006 | MCP tool integration has no per-message authentication or integrity verification | Open | 2026-03-14 |

No assigned CVE found at time of analysis.

---

## 4. Severity Assessment

| Finding | CWE | CVSS (estimated) | Severity |
|---------|-----|-----------------|----------|
| 2.1 Auth bypass (Streamable HTTP) | CWE-306 | 9.1 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N) | Critical |
| 2.2 Unauthenticated workflow exposure | CWE-306 | 9.1 | Critical |
| 2.3 Credential confusion / shared client | CWE-441 | 7.4 | High |
| 2.4 Global log leakage | CWE-532 | 6.5 | Medium |
| 2.5 Unauthenticated discovery requests | CWE-306 | 6.5 | Medium |
| 2.6 No message integrity / replay | CWE-345 | 7.5 | High |

---

## 5. Recommendations

1. **2.1 / 2.2:** Make auth **mandatory** (or at minimum emit a `SecurityWarning`) when `BasicMCPClient` and `workflow_as_mcp` are used over HTTP/HTTPS. Document clearly that unauthenticated deployments are insecure.
2. **2.1:** In `_run_session`, pass `auth=self.auth` (or equivalent) to `streamable_http_client` the same way it is passed to `sse_client`.
3. **2.3:** Do not mutate an externally-provided `AsyncClient`'s `.auth` property. Clone it or require callers to configure auth themselves.
4. **2.4:** Replace `logging.basicConfig(...)` with a local `Logger` instance and local handlers scoped to the MCP call, not the root logger.
5. **2.5:** Add optional `api_key` / `Authorization` header support to `MCPDiscoveryTool`; add URL schema validation.
6. **2.6:** Consider adopting `mcp-secure` (PyPI) or the IETF draft [draft-sharif-mcps-secure-mcp](https://datatracker.ietf.org/doc/draft-sharif-mcps-secure-mcp/) for ECDSA-signed messages and replay protection.
