# LlamaIndex MCP Integration — Missing Authentication & Authorization

## Summary
The LlamaIndex MCP (Model Context Protocol) integration lacks mandatory authentication and authorization. The `BasicMCPClient` connects to any MCP server by default with `auth=None`, allowing unauthenticated tool execution. Tool calls pass through without any authorization checks, enabling unauthorized access to connected MCP tools and potential tool poisoning attacks.

## Severity
CVSS 3.1: **8.1 High**
Vector: `CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:H`

## Root Cause
In `llama-index-integrations/tools/llama-index-tools-mcp/llama_index/tools/mcp/client.py`:

The `BasicMCPClient` class initializes with `auth=None` by default, allowing connections to any HTTP endpoint without authentication:

```python
# llama_index/tools/mcp/client.py
class BasicMCPClient:
    def __init__(self, url: str, auth=None):  # auth defaults to None
        # No validation that auth is provided
        ...
```

The `call_tool()` method in `base.py` executes tool calls without any authorization checks:

```python
# llama_index/tools/mcp/base.py
def call_tool(self, tool_name: str, **kwargs):
    # No authz_callback or permission check
    # Directly forwards to MCP server
    ...
```

## Vulnerabilities

### 1. Missing Mandatory Authentication (P0)
- `BasicMCPClient` connects without requiring auth credentials
- OAuth is available but completely optional
- No `enforce_auth=True` flag exists

### 2. Missing Tool Call Authorization (P0)
- No authorization layer between tool request and execution
- Any connected client can call any exposed MCP tool
- No RBAC or permission checks

### 3. No Message Signing (P1)
- JSON-RPC messages are unsigned
- Vulnerable to MITM attacks
- No replay protection (no nonce/timestamp)

### 4. Tool Poisoning Risk (OWASP MCP03)
- Tool definitions are trusted from the server without verification
- Attacker-controlled MCP server can serve malicious tool definitions
- No manifest verification or allowlisting

## Steps to Reproduce

1. Create an MCP server with sensitive tools (file access, DB queries, etc.)
2. Connect LlamaIndex BasicMCPClient without auth:
```python
from llama_index.tools.mcp import BasicMCPClient

# No authentication required — connects to ANY server
client = BasicMCPClient(url="http://attacker-controlled-server.com")

# Can call ANY tool on the server without authorization
result = client.call_tool("sensitive_operation", args={"command": "..."})
```
3. Observe: Tool executes successfully without any auth check

## Impact
- **Unauthorized tool execution**: Any client can call any MCP tool without credentials
- **Data exfiltration**: MCP tools with DB/file access can be called by unauthorized users
- **Tool poisoning**: Attackers can serve malicious tool definitions to LlamaIndex agents
- **MITM attacks**: Unsigned JSON-RPC allows interception and modification of tool calls

## Affected Versions
All versions of `llama-index-tools-mcp` up to and including current main branch.

## Remediation

### Phase 1 (P0 — Immediate):
```python
# Enforce auth by default
class BasicMCPClient:
    def __init__(self, url: str, auth=None, enforce_auth: bool = True):
        if enforce_auth and auth is None:
            raise SecurityError("Authentication required for MCP connection")
```

### Phase 2 (P1):
```python
# Add authorization callback
class BasicMCPClient:
    def __init__(self, ..., authz_callback=None):
        self.authz_callback = authz_callback or default_authz
    
    def call_tool(self, tool_name, **kwargs):
        if not self.authz_callback(tool_name, kwargs):
            raise AuthorizationError(f"Unauthorized tool call: {tool_name}")
```

### Phase 3 (P1):
- Add ECDSA P-256 message signing for JSON-RPC
- Implement nonce + timestamp for replay protection
- Add tool manifest verification with allowlisting

## References
- GitHub Issue #21006: Community-reported MCP authentication concerns
- OWASP MCP Top 10: MCP03 — Tool Poisoning
- CVE-2025-XXXXX: Pending

## Researcher's Note
Verified against latest llama_index main branch (2026-04-06). The `BasicMCPClient` accepts `auth=None` without any warning or error. This is a design-level issue — the MCP integration was built assuming trusted environments, but in production deployments this allows unauthorized access to sensitive tools connected via MCP.
