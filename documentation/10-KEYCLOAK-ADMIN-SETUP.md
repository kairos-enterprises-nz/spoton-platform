# Keycloak Admin API Setup

## Overview

The SpotOn system now syncs user verification status (email and mobile) from Django to Keycloak via the Admin REST API. This ensures that verification status is centralized in Keycloak.

## Setup Required

### Option 1: Service Account (Recommended)

1. **Create Service Account Client in Keycloak:**
   - Go to `https://auth.spoton.co.nz/admin/master/console/#/spoton-customers/clients`
   - Create new client: `spoton-backend-admin`
   - Client Type: `OpenID Connect`
   - Client authentication: `ON`
   - Service accounts roles: `ON`

2. **Configure Client Roles:**
   - Go to Service account roles tab
   - Assign roles: `manage-users`, `view-users`

3. **Set Environment Variables:**
   ```bash
   KEYCLOAK_ADMIN_CLIENT_ID=spoton-backend-admin
   KEYCLOAK_ADMIN_CLIENT_SECRET=<client-secret-from-keycloak>
   ```

### Option 2: Admin User (Alternative)

1. **Create Admin User:**
   - Create a dedicated admin user in Keycloak
   - Assign admin roles

2. **Set Environment Variables:**
   ```bash
   KEYCLOAK_ADMIN_USERNAME=spoton-admin
   KEYCLOAK_ADMIN_PASSWORD=<secure-password>
   ```

## What Gets Synced

### On Email OTP Verification
- Sets `emailVerified: true` in Keycloak user
- Adds `email_verified: "true"` to user attributes
- Adds `email_verified_at: <timestamp>` to user attributes

### On Mobile OTP Verification  
- Adds `mobile_number: "<phone>"` to user attributes
- Adds `mobile_verified: "true"` to user attributes
- Adds `mobile_verified_at: <timestamp>` to user attributes

### On User Account Creation
- Syncs both email and mobile verification status
- Ensures Keycloak has complete verification data

## Current Status

- ✅ Python Keycloak Admin client implemented
- ✅ Django OTP flow updated to sync to Keycloak
- ✅ Error handling (sync failures don't break OTP verification)
- ⏳ **Admin credentials need to be configured**

## Testing

Once admin credentials are configured, test with:

```bash
docker exec spoton-uat-api python test_keycloak_sync.py
```

## Benefits

1. **Centralized Verification:** All verification status in Keycloak
2. **No Data Duplication:** Django handles OTP, Keycloak stores status
3. **Flexible Authentication:** Keycloak can use verification status for flows
4. **Audit Trail:** Timestamps for when verification occurred 