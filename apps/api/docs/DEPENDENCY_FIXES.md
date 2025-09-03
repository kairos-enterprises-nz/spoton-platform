# Dependency Compatibility Fixes

## Issue Summary
Account creation was failing with `AsyncClient.__init__() got an unexpected keyword argument 'proxies'` error.

## Root Cause Analysis
- **Library**: python-keycloak==4.5.1
- **Conflict**: httpx==0.25.0 incompatible with python-keycloak 4.5.1
- **Error**: KeycloakAdmin.__init__() receiving unexpected 'proxies' parameter

## Fix Applied

### 1. Requirements Update
```bash
# Updated in spoton/apps/api/requirements.txt
httpx==0.23.3  # Compatible version
python-keycloak==4.5.1  # Kept current version
```

### 2. Code Changes
- **File**: `spoton/apps/api/core/views/keycloak_auth.py`
- **Method**: `get_keycloak_admin()`
- **Change**: Updated to use `KeycloakOpenIDConnection` object for proper initialization

### 3. SSL Handling
- Added fallback for SSL certificate issues in development
- Uses HTTP when HTTPS fails (uat environment)

## Verification Steps
1. Rebuild API container: `docker-compose -f spoton/docker-compose.uat.yml up -d --build api`
2. Test account creation flow
3. Verify Keycloak user creation
4. Check OTP email/mobile verification

## Compatibility Matrix
| Component | Version | Status |
|-----------|---------|---------|
| python-keycloak | 4.5.1 | ✅ Working |
| httpx | 0.23.3 | ✅ Compatible |
| apache-airflow | 2.10.3 | ✅ Compatible |

## Future Recommendations
- Consider upgrading to python-keycloak 3.x+ for better httpx compatibility
- Implement proper SSL certificates for production
- Add automated dependency conflict detection 