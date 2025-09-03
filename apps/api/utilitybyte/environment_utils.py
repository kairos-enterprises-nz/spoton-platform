"""
Environment-aware utility functions for SpotOn API
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class EnvironmentAwareResponse:
    """
    Utility class for creating environment-aware API responses
    """
    
    @staticmethod
    def success(request, data=None, message=None, status_code=status.HTTP_200_OK):
        """Create a successful response with environment context"""
        response_data = {
            'success': True,
            'environment': getattr(request, 'environment', 'development'),
            'timestamp': request.env_settings.get('timestamp_format', '%Y-%m-%d %H:%M:%S'),
            'api_version': request.env_settings.get('API_VERSION', 'v1')
        }
        
        if data is not None:
            response_data['data'] = data
        
        if message:
            response_data['message'] = message
        
        # Add environment-specific debugging info for UAT
        if getattr(request, 'is_uat', False) and settings.DEBUG:
            response_data['debug'] = {
                'tenant_slug': getattr(request, 'tenant', {}).get('tenant_slug', 'unknown'),
                'host': request.get_host(),
                'path': request.path
            }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(request, message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
        """Create an error response with environment context"""
        response_data = {
            'success': False,
            'error': message,
            'environment': getattr(request, 'environment', 'development'),
            'timestamp': request.env_settings.get('timestamp_format', '%Y-%m-%d %H:%M:%S'),
            'api_version': request.env_settings.get('API_VERSION', 'v1')
        }
        
        if details:
            response_data['details'] = details
        
        # Add environment-specific debugging info for UAT
        if getattr(request, 'is_uat', False) and settings.DEBUG:
            response_data['debug'] = {
                'tenant_slug': getattr(request, 'tenant', {}).get('tenant_slug', 'unknown'),
                'host': request.get_host(),
                'path': request.path
            }
        
        return Response(response_data, status=status_code)


def get_environment_config(request):
    """Get environment-specific configuration"""
    environment = getattr(request, 'environment', 'development')
    
    # Default configurations
    configs = {
        'development': {
            'API_VERSION': 'v1-dev',
            'cache_timeout': 300,
            'enable_debug': True,
            'rate_limit': 1000,
            'timestamp_format': '%Y-%m-%d %H:%M:%S'
        },
        'uat': {
            'API_VERSION': 'v1-uat',
            'cache_timeout': 600,
            'enable_debug': True,
            'rate_limit': 500,
            'timestamp_format': '%Y-%m-%d %H:%M:%S'
        },
        'live': {
            'API_VERSION': 'v1',
            'cache_timeout': 3600,
            'enable_debug': False,
            'rate_limit': 100,
            'timestamp_format': '%Y-%m-%d %H:%M:%S'
        }
    }
    
    return configs.get(environment, configs['development'])


def log_api_call(request, endpoint, params=None):
    """Log API calls with environment context"""
    if settings.DEBUG or getattr(request, 'is_uat', False):
        logger.info(f"API Call - Environment: {getattr(request, 'environment', 'unknown')}, "
                   f"Endpoint: {endpoint}, Host: {request.get_host()}, "
                   f"Tenant: {getattr(request, 'tenant', {}).get('tenant_slug', 'unknown')}")
        
        if params:
            logger.debug(f"API Parameters: {params}")


def get_database_prefix(request):
    """Get database table prefix based on environment"""
    environment = getattr(request, 'environment', 'development')
    
    prefixes = {
        'uat': 'uat_',
        'live': 'live_',
        'development': 'dev_'
    }
    
    return prefixes.get(environment, '')


def apply_environment_filters(request, queryset, model_class):
    """Apply environment-specific filters to querysets"""
    environment = getattr(request, 'environment', 'development')
    
    # Add environment-specific filtering logic here
    # For example, filter by environment-specific flags or tenant context
    
    if hasattr(model_class, 'environment'):
        queryset = queryset.filter(environment=environment)
    
    if hasattr(model_class, 'is_active'):
        # In live environment, only show active items
        if getattr(request, 'is_live', False):
            queryset = queryset.filter(is_active=True)
    
    return queryset 