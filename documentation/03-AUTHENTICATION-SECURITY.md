# Keycloak SSO Integration Plan - SpotOn Energy

## Current State ✅

The SpotOn Energy platform currently has a **working authentication system**:
- JWT tokens with HTTP-only cookies
- Separate customer and staff login endpoints
- Multi-tenant user management
- Role-based permissions
- React frontend with AuthContext

## Implementation Strategy

### Phase 1: Foundation Setup (Week 1)
**Goal**: Set up Keycloak infrastructure without breaking existing authentication

#### Tasks:
1. **Keycloak Server Configuration**
   - Configure three realms: `spoton-customers`, `spoton-staff`, `spoton-system`
   - Set up clients for each service
   - Configure realm-level security policies

2. **User Migration Scripts**
   - Create scripts to bulk import existing Django users to Keycloak
   - Map user roles and groups
   - Preserve existing user relationships

3. **Parallel Authentication (Hybrid Mode)**
   - Keep existing JWT authentication as primary
   - Add optional Keycloak authentication for testing
   - No disruption to current users

#### Deliverables:
- [ ] Keycloak realms configured
- [ ] User migration scripts ready
- [ ] Hybrid authentication mode working

### Phase 2: Backend Integration (Week 2-3)
**Goal**: Add Keycloak support to Django backend while maintaining current functionality

#### Tasks:
1. **Add OIDC Packages**
   ```bash
   pip install mozilla-django-oidc python-keycloak
   ```

2. **Create Keycloak Authentication Backend**
   ```python
   # users/auth/keycloak.py
   class KeycloakOIDCBackend:
       # Handle OIDC authentication
       # Sync users between Keycloak and Django
       # Map groups and permissions
   ```

3. **Update User Model (Optional Fields)**
   ```python
   # Add optional Keycloak fields without breaking existing users
   keycloak_sub = models.CharField(max_length=64, null=True, blank=True)
   keycloak_realm = models.CharField(max_length=50, null=True, blank=True)
   ```

4. **Hybrid Authentication Chain**
   ```python
   AUTHENTICATION_BACKENDS = [
       'users.auth.keycloak.KeycloakOIDCBackend',  # Try Keycloak first
       'django.contrib.auth.backends.ModelBackend',  # Fallback to Django
   ]
   
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': (
           'users.auth.keycloak.KeycloakOIDCAuthentication',  # Try OIDC first
           'rest_framework_simplejwt.authentication.JWTAuthentication',  # Fallback
           'users.authentication.JWTHttpOnlyCookieAuthentication',  # Fallback
       ),
   }
   ```

#### Deliverables:
- [ ] Keycloak authentication backend working
- [ ] User synchronization between Keycloak and Django
- [ ] Hybrid authentication mode tested

### Phase 3: Frontend Integration (Week 4)
**Goal**: Add Keycloak support to React frontend with fallback to current auth

#### Tasks:
1. **Install Keycloak JS Adapter**
   ```bash
   npm install keycloak-js
   ```

2. **Create Keycloak Service**
   ```javascript
   // src/services/keycloak.js
   import Keycloak from 'keycloak-js';
   
   const keycloak = new Keycloak({
     url: 'https://auth.spoton.co.nz',
     realm: 'spoton-customers', // or spoton-staff
     clientId: 'customer-portal'
   });
   ```

3. **Update AuthContext for Hybrid Mode**
   ```javascript
   // Try Keycloak authentication first, fallback to current JWT
   const checkAuthStatus = async () => {
     if (KEYCLOAK_ENABLED) {
       // Try Keycloak auth
       const kcAuthenticated = await keycloak.init({ onLoad: 'check-sso' });
       if (kcAuthenticated) return setKeycloakUser();
     }
     
     // Fallback to current JWT auth
     return checkJWTAuth();
   };
   ```

#### Deliverables:
- [ ] Keycloak JS integration working
- [ ] Hybrid frontend authentication
- [ ] Seamless fallback to current auth

### Phase 4: Service Integration (Week 5)
**Goal**: Configure all administrative services for SSO

#### Services to Configure:
1. **Grafana** - Already has partial OIDC, complete the integration
2. **Wiki.js** - Configure OIDC authentication
3. **Gitea** - Set up OAuth2 with Keycloak
4. **pgAdmin** - Configure OAuth2 authentication
5. **Airflow** - Set up OIDC for webserver

#### Configuration Examples:
```ini
# Grafana
[auth.generic_oauth]
enabled = true
client_id = grafana
client_secret = ${GRAFANA_KEYCLOAK_SECRET}
auth_url = https://auth.spoton.co.nz/realms/spoton-staff/protocol/openid-connect/auth
token_url = https://auth.spoton.co.nz/realms/spoton-staff/protocol/openid-connect/token
api_url = https://auth.spoton.co.nz/realms/spoton-staff/protocol/openid-connect/userinfo
```

#### Deliverables:
- [ ] All services configured for SSO
- [ ] Role mapping implemented
- [ ] Cross-service authentication tested

### Phase 5: Testing & Gradual Migration (Week 6)
**Goal**: Test thoroughly and begin migrating users

#### Tasks:
1. **Comprehensive Testing**
   - End-to-end authentication flows
   - Cross-service SSO validation
   - Token refresh scenarios
   - Logout propagation

2. **Gradual User Migration**
   - Start with staff users (lower risk)
   - Migrate customer users in batches
   - Monitor for issues and rollback capability

3. **Performance Testing**
   - Authentication endpoint load testing
   - Token validation performance
   - Database synchronization efficiency

#### Deliverables:
- [ ] Full test suite passing
- [ ] Staff users migrated successfully
- [ ] Customer migration plan ready

### Phase 6: Full Deployment (Week 7)
**Goal**: Complete migration and remove legacy authentication

#### Tasks:
1. **Complete Customer Migration**
   - Migrate all customer users to Keycloak
   - Update all frontend flows to use OIDC
   - Remove JWT fallback authentication

2. **Cleanup Legacy Code**
   - Remove old authentication backends
   - Clean up unused JWT code
   - Update documentation

3. **Monitoring & Support**
   - Set up authentication monitoring
   - Create user support procedures
   - Monitor system performance

#### Deliverables:
- [ ] All users migrated to Keycloak
- [ ] Legacy authentication removed
- [ ] Full SSO operational

## Risk Mitigation

### Rollback Strategy
- Keep existing JWT authentication as fallback during migration
- Ability to disable Keycloak and revert to JWT at any time
- Database backups before each migration phase

### Testing Strategy
- Comprehensive automated tests for all authentication flows
- Manual testing of all user journeys
- Load testing of authentication endpoints

### User Communication
- Clear communication about SSO benefits
- Migration timeline and expectations
- Support procedures for issues

## Success Metrics

### Technical Metrics
- **SSO Success Rate**: >99.5% across all services
- **Authentication Response Time**: <500ms average
- **Zero Downtime**: No service interruptions during migration

### User Experience Metrics
- **Single Sign-On**: Users only need to login once
- **Cross-Service Navigation**: Seamless access to all tools
- **Support Tickets**: Reduction in authentication-related issues

## Implementation Notes

### Current System Preservation
- **No Breaking Changes**: Existing authentication continues to work
- **Gradual Migration**: Users moved in controlled batches
- **Fallback Capability**: Ability to revert at any stage

### Security Considerations
- **Token Security**: Proper OIDC token handling
- **Session Management**: Secure session timeout and refresh
- **Multi-Factor Authentication**: Enhanced security for staff users

This phased approach ensures that the existing working system remains operational while gradually introducing Keycloak SSO capabilities. 