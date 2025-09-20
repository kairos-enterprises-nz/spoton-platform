"""
Environment-aware URL utilities for Django backend
"""
import os
from django.conf import settings


def get_environment():
    """
    Determine the current environment based on settings or environment variables
    """
    # Check environment variable first
    env = os.getenv('ENVIRONMENT', '').lower()
    if env in ['live', 'production']:
        return 'live'
    elif env in ['uat', 'staging']:
        return 'uat'
    
    # Fallback to Django DEBUG setting
    if hasattr(settings, 'DEBUG') and not settings.DEBUG:
        return 'live'
    else:
        return 'uat'


def get_base_urls():
    """
    Get environment-aware base URLs
    """
    env = get_environment()
    
    if env == 'live':
        return {
            'web': 'https://spoton.co.nz',
            'portal': 'https://portal.spoton.co.nz',
            'staff': 'https://staff.spoton.co.nz',
            'api': 'https://api.spoton.co.nz',
            'auth': 'https://auth.spoton.co.nz'
        }
    else:
        return {
            'web': 'https://uat.spoton.co.nz',
            'portal': 'https://uat.portal.spoton.co.nz',
            'staff': 'https://uat.staff.spoton.co.nz',
            'api': 'https://uat.api.spoton.co.nz',
            'auth': 'https://auth.spoton.co.nz'
        }


def get_env_url(service):
    """
    Get URL for a specific service based on environment
    """
    base_urls = get_base_urls()
    
    # Check for environment variable override
    env_var_map = {
        'web': 'WEB_URL',
        'portal': 'PORTAL_URL',
        'staff': 'STAFF_URL',
        'api': 'API_URL',
        'auth': 'KEYCLOAK_URL'
    }
    
    env_var = env_var_map.get(service)
    if env_var:
        override_url = os.getenv(env_var)
        if override_url:
            return override_url
    
    return base_urls.get(service, '')


def get_redirect_uris(service):
    """
    Get redirect URIs for Keycloak client configuration
    """
    base_url = get_env_url(service)
    return [f"{base_url}/*"]


def get_web_origins(service):
    """
    Get web origins for Keycloak client configuration
    """
    base_url = get_env_url(service)
    return [base_url]