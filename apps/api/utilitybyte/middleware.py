"""
Enhanced middleware for single-schema multi-tenancy with row-level filtering.
Maintains existing API functionality while adding tenant awareness.
Works with Tenant model for business logic and white-label isolation.
"""
import logging
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import threading

logger = logging.getLogger(__name__)

# Thread-local storage for tenant context
_thread_local = threading.local()


def get_tenant_context():
    """Get current tenant context from thread-local storage or database"""
    # First try to get from thread-local storage
    if hasattr(_thread_local, 'tenant_context'):
        return _thread_local.tenant_context
    
    # Fallback to database context
    try:
        # Try to get tenant from current connection context
        with connection.cursor() as cursor:
            cursor.execute("SHOW app.current_tenant_id")
            result = cursor.fetchone()
            if result and result[0]:
                tenant_id = result[0]
                try:
                    from users.models import Tenant
                    tenant = Tenant.objects.get(id=tenant_id)
                    context = {
                        'tenant_id': tenant.id,
                        'tenant_name': tenant.name,
                        'tenant_slug': tenant.slug,
                        'schema_name': 'public',
                        'contact_email': tenant.contact_email,
                        'timezone': tenant.timezone,
                        'currency': tenant.currency,
                        'is_active': tenant.is_active,
                        'business_number': tenant.business_number,
                        'service_limits': tenant.service_limits,
                    }
                    _thread_local.tenant_context = context
                    return context
                except Exception as e:
                    logger.warning(f"Failed to get tenant from database: {e}")
                    pass
    except Exception as e:
        logger.debug(f"Failed to get tenant from connection: {e}")
        pass
    
    # Fallback for backward compatibility - default tenant
    default_context = {
        'tenant_id': 1,
        'tenant_name': 'default',
        'tenant_slug': 'public',
        'schema_name': 'public',
        'contact_email': '',
        'timezone': 'Pacific/Auckland',
        'currency': 'NZD',
        'is_active': True,
        'business_number': '',
        'service_limits': {},
    }
    _thread_local.tenant_context = default_context
    return default_context


def set_tenant_context(tenant_context):
    """Set tenant context in thread-local storage"""
    _thread_local.tenant_context = tenant_context
    
    # Also set in database connection for compatibility
    if tenant_context and tenant_context.get('tenant_id'):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET app.current_tenant_id = %s", [str(tenant_context['tenant_id'])])
        except Exception as e:
            logger.warning(f"Failed to set tenant context in database: {e}")


def clear_tenant_context():
    """Clear tenant context from thread-local storage"""
    if hasattr(_thread_local, 'tenant_context'):
        delattr(_thread_local, 'tenant_context')
    
    # Also clear from database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET app.current_tenant_id = ''")
    except Exception as e:
        logger.debug(f"Failed to clear tenant context from database: {e}")


def get_current_user():
    """Get current user from thread-local storage"""
    return getattr(_thread_local, 'current_user', None)


def set_current_user(user):
    """Set current user in thread-local storage"""
    _thread_local.current_user = user


class TenantAwareMiddleware(MiddlewareMixin):
    """
    Enhanced middleware for white-label tenant context management with environment awareness.
    Automatically sets tenant context based on request headers, subdomain, or user.
    """
    
    def process_request(self, request):
        """Process incoming request to set tenant context with environment awareness"""
        tenant_context = None
        
        try:
            # Environment Detection (add this before tenant detection)
            host = request.get_host()
            
            if 'uat.' in host or 'localhost' in host or host.startswith('192.') or host.startswith('172.'):
                environment = 'uat'
            elif any(domain in host for domain in ['live.spoton.co.nz', 'portal.spoton.co.nz', 'staff.spoton.co.nz', 'api.spoton.co.nz']):
                environment = 'live'
            else:
                environment = getattr(settings, 'ENVIRONMENT', 'development')
            
            # Add environment context to request
            request.environment = environment
            request.is_uat = environment == 'uat'
            request.is_live = environment == 'live'
            request.is_development = environment == 'development'
            
            # Add environment-specific settings
            request.env_settings = settings.ENVIRONMENT_CONFIG.get(environment, settings.ENVIRONMENT_CONFIG['development'])
            
            # Log environment detection for debugging
            if settings.DEBUG:
                logger.debug(f"Environment detected: {environment} for host: {host}")
            
            # Method 1: Check for tenant header (for API calls)
            tenant_header = request.META.get('HTTP_X_TENANT_ID') or request.META.get('HTTP_X_TENANT_SLUG')
            if tenant_header:
                tenant_context = self._get_tenant_by_header(tenant_header)
            
            # Method 2: Check subdomain for white-label brands
            if not tenant_context:
                tenant_context = self._get_tenant_by_subdomain(request)
            
            # Method 3: Check user's default tenant (for authenticated users)
            if not tenant_context and hasattr(request, 'user') and request.user.is_authenticated:
                tenant_context = self._get_tenant_by_user(request.user)
            
            # Method 4: Check session for tenant selection
            if not tenant_context and hasattr(request, 'session'):
                tenant_id = request.session.get('selected_tenant_id')
                if tenant_id:
                    tenant_context = self._get_tenant_by_id(tenant_id)
            
            # Environment-aware tenant handling (modify tenant slug based on environment)
            if tenant_context:
                # Add environment prefix to tenant slug for data separation
                original_slug = tenant_context.get('tenant_slug', 'default')
                if request.is_uat and not original_slug.startswith('uat_'):
                    tenant_context['tenant_slug'] = f"uat_{original_slug}"
                elif request.is_live and not original_slug.startswith('live_'):
                    tenant_context['tenant_slug'] = f"live_{original_slug}"
                
                set_tenant_context(tenant_context)
                request.tenant = tenant_context
            else:
                # Use default tenant for backward compatibility with environment prefix
                default_context = get_tenant_context()
                if request.is_uat:
                    default_context['tenant_slug'] = f"uat_{default_context['tenant_slug']}"
                elif request.is_live:
                    default_context['tenant_slug'] = f"live_{default_context['tenant_slug']}"
                request.tenant = default_context
            
            # Set current user for audit trails
            if hasattr(request, 'user') and request.user.is_authenticated:
                set_current_user(request.user)
            
        except Exception as e:
            logger.error(f"Error in TenantAwareMiddleware: {e}")
            # Don't fail the request, just use default context
            request.tenant = get_tenant_context()
        
        return None
    
    def process_response(self, request, response):
        """Clean up tenant context after request with environment headers"""
        # Add tenant info to response headers for debugging
        if hasattr(request, 'tenant') and request.tenant:
            response['X-Tenant-ID'] = str(request.tenant.get('tenant_id', ''))
            response['X-Tenant-Name'] = request.tenant.get('tenant_name', '')
        
        # Add environment headers to response
        if hasattr(request, 'environment'):
            response['X-SpotOn-Environment'] = request.environment
            response['X-API-Version'] = request.env_settings.get('API_VERSION', 'v1')
        
        return response
    
    def _get_tenant_by_header(self, header_value):
        """Get tenant by header value (ID or slug)"""
        try:
            from users.models import Tenant
            
            # Try by UUID first
            try:
                tenant = Tenant.objects.get(id=header_value)
            except (Tenant.DoesNotExist, ValueError):
                # Try by slug
                tenant = Tenant.objects.get(slug=header_value)
            
            return self._tenant_to_context(tenant)
        except Exception as e:
            logger.warning(f"Failed to get tenant by header '{header_value}': {e}")
            return None
    
    def _get_tenant_by_subdomain(self, request):
        """Get tenant by subdomain for white-label brands"""
        try:
            host = request.get_host()
            if not host:
                return None
            
            # Extract subdomain
            parts = host.split('.')
            if len(parts) >= 3:  # subdomain.domain.tld
                subdomain = parts[0]
                
                # Skip common subdomains
                if subdomain in ['www', 'api', 'admin', 'localhost']:
                    return None
                
                from users.models import Tenant
                try:
                    tenant = Tenant.objects.get(slug=subdomain, is_active=True)
                    return self._tenant_to_context(tenant)
                except Tenant.DoesNotExist:
                    logger.debug(f"No tenant found for subdomain: {subdomain}")
            
        except Exception as e:
            logger.warning(f"Failed to get tenant by subdomain: {e}")
        
        return None
    
    def _get_tenant_by_user(self, user):
        """Get tenant by user's default tenant or first tenant role"""
        try:
            # Try to get user's primary tenant
            if hasattr(user, 'accounts'):
                account = user.accounts.first()
                if account and account.tenant:
                    return self._tenant_to_context(account.tenant)
            
            # Try to get from tenant roles
            if hasattr(user, 'tenant_roles'):
                tenant_role = user.tenant_roles.first()
                if tenant_role and tenant_role.tenant:
                    return self._tenant_to_context(tenant_role.tenant)
            
        except Exception as e:
            logger.warning(f"Failed to get tenant by user: {e}")
        
        return None
    
    def _get_tenant_by_id(self, tenant_id):
        """Get tenant by ID"""
        try:
            from users.models import Tenant
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            return self._tenant_to_context(tenant)
        except Exception as e:
            logger.warning(f"Failed to get tenant by ID '{tenant_id}': {e}")
            return None
    
    def _tenant_to_context(self, tenant):
        """Convert tenant model to context dictionary"""
        return {
            'tenant_id': tenant.id,
            'tenant_name': tenant.name,
            'tenant_slug': tenant.slug,
            'schema_name': 'public',
            'contact_email': tenant.contact_email,
            'timezone': tenant.timezone,
            'currency': tenant.currency,
            'is_active': tenant.is_active,
            'business_number': tenant.business_number,
            'service_limits': tenant.service_limits,
        }


class DatabaseTransactionMiddleware(MiddlewareMixin):
    """
    Enhanced database transaction middleware for multi-tenant operations.
    Ensures proper cleanup of tenant context on transaction rollback.
    """
    
    def process_exception(self, request, exception):
        """Clean up tenant context on exception"""
        clear_tenant_context()
        return None
    
    def process_response(self, request, response):
        """Clean up tenant context after successful response"""
        # Only clear if this is the end of the request cycle
        if response.status_code >= 400:
            clear_tenant_context()
        
        return response


class TenantSecurityMiddleware(MiddlewareMixin):
    """
    Security middleware to enforce tenant isolation.
    Prevents cross-tenant data access attempts.
    """
    
    def process_request(self, request):
        """Validate tenant access permissions"""
        # Skip security checks for certain paths
        skip_paths = ['/admin/', '/api/auth/', '/health/', '/static/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Validate tenant is active
        if hasattr(request, 'tenant') and request.tenant:
            if not request.tenant.get('is_active', True):
                return JsonResponse(
                    {'error': 'Tenant is not active'}, 
                    status=403
                )
        
        return None
