"""
Realm detection middleware for Keycloak multi-realm support
"""
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RealmDetectionMiddleware(MiddlewareMixin):
    """
    Middleware to detect and set the appropriate Keycloak realm based on the request domain
    """
    
    DOMAIN_REALM_MAP = {
        # UAT domains
        'uat.api.spoton.co.nz': 'uat',
        'uat.portal.spoton.co.nz': 'uat', 
        'uat.staff.spoton.co.nz': 'uat',
        
        # Production domains
        'api.spoton.co.nz': 'prod',
        'portal.spoton.co.nz': 'prod',
        'staff.spoton.co.nz': 'prod',
        
        # Live domains (alias for prod)
        'spoton.co.nz': 'prod',
        
        # Staff domains (use staff realm for admin access)
        'staff.spoton.co.nz': 'staff',
        'uat.staff.spoton.co.nz': 'staff',
        
        # Default/development
        'localhost': 'uat',
        '127.0.0.1': 'uat',
    }
    
    def process_request(self, request):
        """
        Process incoming request to detect realm
        """
        # Get the host from the request
        host = request.get_host()
        
        # Remove port if present
        if ':' in host:
            host = host.split(':')[0]
        
        # Detect realm based on domain
        realm = self.DOMAIN_REALM_MAP.get(host, settings.DEFAULT_KEYCLOAK_REALM)
        
        # Special handling for staff domains
        if 'staff' in host:
            realm = 'staff'
        elif 'uat' in host:
            realm = 'uat'
        elif host in ['api.spoton.co.nz', 'portal.spoton.co.nz', 'spoton.co.nz']:
            realm = 'prod'
        
        # Set realm in request for use by authentication backends
        request.keycloak_realm = realm
        
        # Also set in thread-local storage for global access
        if hasattr(settings, 'THREAD_LOCAL'):
            settings.THREAD_LOCAL.keycloak_realm = realm
        
        # Log realm detection for debugging
        logger.debug(f"Detected realm '{realm}' for host '{host}'")
        
        return None
    
    def process_response(self, request, response):
        """
        Add realm information to response headers for debugging
        """
        if hasattr(request, 'keycloak_realm'):
            response['X-Keycloak-Realm'] = request.keycloak_realm
        
        return response

class ThreadLocalMiddleware(MiddlewareMixin):
    """
    Middleware to set up thread-local storage for request-specific data
    """
    
    def process_request(self, request):
        """
        Initialize thread-local storage
        """
        import threading
        
        # Create thread-local storage if it doesn't exist
        if not hasattr(settings, 'THREAD_LOCAL'):
            settings.THREAD_LOCAL = threading.local()
        
        # Store request in thread-local for global access
        settings.THREAD_LOCAL.request = request
        
        return None
    
    def process_response(self, request, response):
        """
        Clean up thread-local storage
        """
        if hasattr(settings, 'THREAD_LOCAL'):
            # Clean up thread-local data
            if hasattr(settings.THREAD_LOCAL, 'request'):
                delattr(settings.THREAD_LOCAL, 'request')
            if hasattr(settings.THREAD_LOCAL, 'keycloak_realm'):
                delattr(settings.THREAD_LOCAL, 'keycloak_realm')
        
        return response 