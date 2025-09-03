"""
Core API views with environment awareness
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from utilitybyte.environment_utils import EnvironmentAwareResponse, log_api_call, get_environment_config


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint with environment awareness
    """
    log_api_call(request, 'health_check')
    
    environment = getattr(request, 'environment', 'development')
    env_config = get_environment_config(request)
    
    health_data = {
        'status': 'healthy',
        'environment': environment,
        'api_version': env_config.get('API_VERSION', 'v1'),
        'tenant': getattr(request, 'tenant', {}).get('tenant_slug', 'unknown'),
        'database': 'connected',
        'features': env_config.get('features', {})
    }
    
    # Add debug info for non-production environments
    if environment != 'live':
        health_data['debug'] = {
            'host': request.get_host(),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
            'timestamp': settings.ENVIRONMENT_CONFIG[environment]['timestamp_format']
        }
    
    return EnvironmentAwareResponse.success(
        request, 
        data=health_data, 
        message=f"SpotOn API {environment.upper()} environment is healthy"
    )


@api_view(['GET'])
def environment_info(request):
    """
    Get current environment information
    """
    log_api_call(request, 'environment_info')
    
    environment = getattr(request, 'environment', 'development')
    env_config = get_environment_config(request)
    
    info_data = {
        'environment': environment,
        'api_version': env_config.get('API_VERSION', 'v1'),
        'tenant_slug': getattr(request, 'tenant', {}).get('tenant_slug', 'unknown'),
        'tenant_id': getattr(request, 'tenant', {}).get('tenant_id', 'unknown'),
        'features': env_config.get('features', {}),
        'rate_limit': env_config.get('rate_limit', 100),
        'cache_timeout': env_config.get('cache_timeout', 3600)
    }
    
    # Only show detailed info in UAT/development
    if environment != 'live':
        info_data['detailed_config'] = {
            'debug_enabled': settings.DEBUG,
            'database_name': settings.DATABASES['default']['NAME'],
            'host': request.get_host(),
            'path': request.path,
            'method': request.method
        }
    
    return EnvironmentAwareResponse.success(
        request,
        data=info_data,
        message=f"Environment information for {environment.upper()}"
    )


@api_view(['GET'])
def test_environment_routing(request):
    """
    Test endpoint to verify environment-specific routing
    """
    log_api_call(request, 'test_environment_routing')
    
    environment = getattr(request, 'environment', 'development')
    
    test_data = {
        'message': f'Hello from {environment.upper()} environment!',
        'routing_test': 'success',
        'timestamp': request.env_settings.get('timestamp_format', '%Y-%m-%d %H:%M:%S')
    }
    
    if environment == 'uat':
        test_data['uat_specific'] = 'This message only appears in UAT'
    elif environment == 'live':
        test_data['live_specific'] = 'This message only appears in LIVE'
    else:
        test_data['dev_specific'] = 'This message only appears in DEVELOPMENT'
    
    return EnvironmentAwareResponse.success(
        request,
        data=test_data,
        message=f"Environment routing test successful for {environment.upper()}"
    ) 