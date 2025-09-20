import logging
import jwt  # Used for Keycloak token processing only
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import JsonResponse
from users.models import Tenant, User
from utilitybyte.middleware import set_tenant_context, get_tenant_context

logger = logging.getLogger(__name__)


class ClientBasedTenantMiddleware(MiddlewareMixin):
    """
    Client-based multi-tenancy middleware with Keycloak integration.
    
    Features:
    - Extracts Bearer tokens from HttpOnly cookies
    - Determines tenant from Keycloak client_id in token
    - Sets tenant context based on client-based tenancy
    - Supports domain-based tenant resolution as fallback
    """
    
    def process_request(self, request):
        """Process request to extract token, determine tenant, and set context"""
        try:
            # Step 1: Extract token from cookie and inject into Authorization header
            self._extract_token_from_cookie(request)
            
            # Step 2: Determine tenant context from token or domain
            tenant_context = self._determine_tenant_context(request)
            
            # Step 3: Set tenant context and user context
            if tenant_context:
                set_tenant_context(tenant_context)
                request.tenant = tenant_context
                request.tenant_obj = tenant_context.get('tenant_obj')
            
            # Step 4: Environment detection
            self._detect_environment(request)
            
        except Exception as e:
            logger.error(f"Error in ClientBasedTenantMiddleware: {e}")
            # Don't fail the request, use default context
            request.tenant = get_tenant_context()
            
        return None
    
    def _extract_token_from_cookie(self, request):
        """
        Extract Bearer token from HttpOnly cookie and inject into Authorization header.
        This allows Django to work with cookie-based authentication while maintaining
        Bearer token compatibility.
        """
        # Check if Authorization header already exists
        if request.META.get('HTTP_AUTHORIZATION'):
            return
            
        # Extract token from cookie
        token_cookie_name = getattr(settings, 'AUTH_COOKIE_NAME', 'access_token')
        token = request.COOKIES.get(token_cookie_name)
        
        if token:
            # Inject token into Authorization header for DRF authentication
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
            logger.debug("Token extracted from cookie and injected into Authorization header")
    
    def _determine_tenant_context(self, request):
        """
        Determine tenant context using multiple methods:
        1. Keycloak client_id from token claims
        2. Domain-based resolution
        3. X-Tenant header
        4. Default tenant
        """
        # Method 1: Extract tenant from Keycloak token
        tenant_context = self._get_tenant_from_token(request)
        if tenant_context:
            return tenant_context
        
        # Method 2: Domain-based tenant resolution
        tenant_context = self._get_tenant_from_domain(request)
        if tenant_context:
            return tenant_context
            
        # Method 3: Header-based tenant (for API calls)
        tenant_context = self._get_tenant_from_header(request)
        if tenant_context:
            return tenant_context
            
        # Method 4: Default tenant
        return self._get_default_tenant_context()
    
    def _get_tenant_from_token(self, request):
        """Extract tenant information from Keycloak token claims"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        
        try:
            # Decode token without verification to get claims
            # Note: Token verification happens in authentication backend
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            
            # Extract realm and client_id from token
            realm = unverified_payload.get('iss', '').split('/')[-1]  # Extract realm from issuer
            client_id = unverified_payload.get('azp') or unverified_payload.get('aud')
            
            logger.info(f"Token analysis: realm={realm}, client_id={client_id}, iss={unverified_payload.get('iss', 'missing')}")
            
            if not client_id or not realm:
                logger.warning(f"Missing client_id or realm: client_id={client_id}, realm={realm}")
                return None
            
            # Determine environment from realm
            environment = None
            if realm == 'spoton-uat':
                environment = 'uat'
            elif realm == 'spoton-prod':
                environment = 'live'
            elif realm == 'spoton-staff':
                # Staff realm - no tenant-based client separation
                return self._handle_staff_realm(request, unverified_payload, client_id, realm)
            elif realm == 'spoton-admin':
                # Admin realm - cross-environment staff access
                return self._handle_admin_realm(request, unverified_payload, client_id, realm)
            
            if not environment:
                logger.warning(f"Unknown realm: {realm}")
                return None
                
            # Find tenant by client_id and environment
            tenant = Tenant.get_by_client_id(client_id, environment)
            
            # Always store Keycloak claims in request for later use (even without tenant)
            request.keycloak_claims = unverified_payload
            request.keycloak_client_id = client_id
            request.keycloak_realm = realm
            request.keycloak_environment = environment
            
            if not tenant:
                logger.warning(f"No tenant found for client_id: {client_id} in environment: {environment}")
                # For staff clients, we still want to allow access without tenant mapping
                if 'staff' in client_id.lower():
                    logger.info(f"Staff client detected, allowing access without tenant: {client_id}")
                    return {
                        'tenant_id': 'staff',
                        'tenant_name': 'Staff Access',
                        'tenant_slug': 'staff',
                        'tenant_obj': None,
                        'keycloak_client_id': client_id,
                        'keycloak_realm': realm,
                        'environment': environment,
                        'method': 'staff_client'
                    }
                return None
            
            return {
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'tenant_slug': tenant.slug,
                'tenant_obj': tenant,
                'keycloak_client_id': client_id,
                'keycloak_realm': realm,
                'environment': environment,
                'method': 'token_client_id'
            }
            
        except jwt.PyJWTError as e:
            logger.debug(f"JWT decode error (expected during token verification): {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting tenant from token: {e}")
            return None
    
    def _handle_staff_realm(self, request, payload, client_id, realm):
        """Handle staff realm which doesn't use client-based tenancy"""
        request.keycloak_claims = payload
        request.keycloak_client_id = client_id
        request.keycloak_realm = realm
        request.keycloak_environment = 'staff'
        
        # For staff, we might want a default "system" tenant or no tenant
        return {
            'tenant_id': 'staff',
            'tenant_name': 'SpotOn Staff',
            'tenant_slug': 'staff',
            'tenant_obj': None,  # No specific tenant for staff
            'keycloak_client_id': client_id,
            'keycloak_realm': realm,
            'environment': 'staff',
            'method': 'staff_realm'
        }
    
    def _handle_admin_realm(self, request, payload, client_id, realm):
        """Handle admin realm - cross-environment staff access"""
        request.keycloak_claims = payload
        request.keycloak_client_id = client_id
        request.keycloak_realm = realm
        
        # Determine environment from client_id
        environment = 'uat'  # default
        if 'uat' in client_id.lower():
            environment = 'uat'
        elif 'live' in client_id.lower() or 'prod' in client_id.lower():
            environment = 'live'
        
        request.keycloak_environment = environment
        
        # For admin realm, provide cross-environment access
        return {
            'tenant_id': 'admin',
            'tenant_name': 'SpotOn Admin',
            'tenant_slug': 'admin',
            'tenant_obj': None,  # No specific tenant for admin
            'keycloak_client_id': client_id,
            'keycloak_realm': realm,
            'environment': environment,
            'method': 'admin_realm'
        }
    
    def _get_tenant_from_domain(self, request):
        """Get tenant based on request domain"""
        host = request.get_host()
        
        # Remove port if present
        domain = host.split(':')[0]
        
        # Determine environment from domain
        environment = self._get_environment_from_host(host)
        
        tenant = Tenant.get_by_domain(domain)
        if tenant:
            client_id = tenant.get_client_id_for_environment(environment)
            realm = tenant.get_realm_for_environment(environment)
            
            return {
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'tenant_slug': tenant.slug,
                'tenant_obj': tenant,
                'keycloak_client_id': client_id,
                'keycloak_realm': realm,
                'environment': environment,
                'method': 'domain'
            }
        
        return None
    
    def _get_tenant_from_header(self, request):
        """Get tenant from X-Tenant header"""
        tenant_header = (request.META.get('HTTP_X_TENANT_ID') or 
                        request.META.get('HTTP_X_TENANT_SLUG') or
                        request.META.get('HTTP_X_CLIENT_ID'))
        
        if not tenant_header:
            return None
            
        # Try to find tenant by different identifiers
        tenant = None
        
        # Try by client_id first
        if tenant_header.startswith('client-'):
            tenant = Tenant.get_by_client_id(tenant_header)
        
        # Try by UUID
        if not tenant:
            try:
                tenant = Tenant.objects.get(id=tenant_header)
            except (Tenant.DoesNotExist, ValueError):
                pass
        
        # Try by slug
        if not tenant:
            try:
                tenant = Tenant.objects.get(slug=tenant_header)
            except Tenant.DoesNotExist:
                pass
        
        if tenant:
            return {
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'tenant_slug': tenant.slug,
                'tenant_obj': tenant,
                'keycloak_client_id': tenant.keycloak_client_id,
                'keycloak_realm': tenant.keycloak_realm,
                'method': 'header'
            }
        
        return None
    
    def _get_default_tenant_context(self):
        """Get default tenant context - always use primary SpotOn brand"""
        try:
            # Try to get the primary SpotOn brand
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            
            if not tenant:
                # Create the primary SpotOn tenant if it doesn't exist
                tenant = self._create_primary_spoton_tenant()
            
            # Determine environment for client/realm selection
            environment = getattr(self, '_current_environment', 'uat')  # Default to UAT
            
            client_id = tenant.get_client_id_for_environment(environment)
            realm = tenant.get_realm_for_environment(environment)
            
            return {
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'tenant_slug': tenant.slug,
                'tenant_obj': tenant,
                'keycloak_client_id': client_id,
                'keycloak_realm': realm,
                'environment': environment,
                'method': 'primary_brand'
            }
            
        except Exception as e:
            logger.error(f"Error getting default tenant: {e}")
            # Fallback to basic context
            return {
                'tenant_id': 'spoton-primary',
                'tenant_name': 'SpotOn Energy',
                'tenant_slug': 'spoton',
                'tenant_obj': None,
                'keycloak_client_id': 'customer-uat-portal',
                'keycloak_realm': 'spoton-uat',
                'environment': 'uat',
                'method': 'fallback'
            }
    
    def _create_primary_spoton_tenant(self):
        """Create the primary SpotOn tenant"""
        from users.models import Tenant
        
        tenant = Tenant.objects.create(
            name='SpotOn Energy',
            slug='spoton',
            is_primary_brand=True,
            keycloak_client_id_uat='customer-uat-portal',
            keycloak_client_id_live='customer-live-portal',
            primary_domain='portal.spoton.co.nz',
            additional_domains=['uat.portal.spoton.co.nz'],
            contact_email='support@spoton.co.nz',
            contact_phone='+64 9 123 4567',
            branding_config={}  # Use defaults
        )
        
        logger.info("Created primary SpotOn tenant")
        return tenant
    
    def _get_environment_from_host(self, host):
        """Get environment from host"""
        if 'uat.' in host or 'localhost' in host or host.startswith('192.') or host.startswith('172.'):
            return 'uat'
        elif any(domain in host for domain in ['spoton.co.nz', 'portal.spoton.co.nz', 'staff.spoton.co.nz', 'api.spoton.co.nz']):
            return 'live'
        else:
            return getattr(settings, 'ENVIRONMENT', 'development')
    
    def _detect_environment(self, request):
        """Detect environment based on host"""
        host = request.get_host()
        environment = self._get_environment_from_host(host)
        
        # Store for use in default tenant context
        self._current_environment = environment
        
        # Add environment context to request
        request.environment = environment
        request.is_uat = environment == 'uat'
        request.is_live = environment == 'live'
        request.is_development = environment == 'development'
        request.is_staff = environment == 'staff'
        
        # Add environment-specific settings
        request.env_settings = settings.ENVIRONMENT_CONFIG.get(
            environment, 
            settings.ENVIRONMENT_CONFIG['development']
        )
        
        if settings.DEBUG:
            logger.debug(f"Environment detected: {environment} for host: {host}")
    
    def process_response(self, request, response):
        """Add tenant information to response headers"""
        if hasattr(request, 'tenant') and request.tenant:
            # Handle both dictionary (legacy) and Tenant object (new) cases
            if isinstance(request.tenant, dict):
                # Legacy dictionary format
                response['X-Tenant-ID'] = request.tenant.get('tenant_id', '')
                response['X-Tenant-Name'] = request.tenant.get('tenant_name', '')
                response['X-Tenant-Client-ID'] = request.tenant.get('keycloak_client_id', '')
                response['X-Tenant-Method'] = request.tenant.get('method', '')
            else:
                # New Tenant object format
                response['X-Tenant-ID'] = getattr(request.tenant, 'slug', '')
                response['X-Tenant-Name'] = getattr(request.tenant, 'name', '')
                response['X-Tenant-Client-ID'] = getattr(request, 'client_context', '')
                response['X-Tenant-Method'] = 'keycloak_jwt'
        
        return response 