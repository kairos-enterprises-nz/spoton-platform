import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from users.models import Tenant

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])  # Public endpoint for tenant configuration
def get_tenant_config(request):
    """
    Get tenant configuration for React frontend.
    Can be accessed by domain, client_id, or falls back to primary SpotOn brand.
    
    Query parameters:
    - domain: Get config by domain
    - client_id: Get config by Keycloak client ID
    - environment: Specify environment (uat/live)
    """
    try:
        # Get parameters
        domain = request.GET.get('domain') or request.get_host().split(':')[0]
        client_id = request.GET.get('client_id')
        environment = request.GET.get('environment') or getattr(request, 'environment', 'uat')
        
        tenant = None
        
        # Method 1: Find by client_id
        if client_id:
            tenant = Tenant.get_by_client_id(client_id, environment)
            
        # Method 2: Find by domain
        if not tenant and domain:
            tenant = Tenant.get_by_domain(domain)
            
        # Method 3: Use primary SpotOn brand as fallback
        if not tenant:
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            
        # Method 4: Create primary tenant if none exists
        if not tenant:
            tenant = _create_primary_spoton_tenant()
        
        # Get branding configuration
        branding_config = tenant.get_branding_config()
        
        # Add environment-specific information
        branding_config['environment'] = {
            'current': environment,
            'is_uat': environment == 'uat',
            'is_live': environment == 'live',
            'api_base_url': _get_api_base_url(environment),
            'auth_server_url': settings.KEYCLOAK_SERVER_URL
        }
        
        # Add tenant metadata
        branding_config['tenant'] = {
            'id': str(tenant.id),
            'name': tenant.name,
            'slug': tenant.slug,
            'is_primary': tenant.is_primary_brand,
            'timezone': tenant.timezone,
            'currency': tenant.currency
        }
        
        return Response({
            'success': True,
            'data': branding_config
        })
        
    except Exception as e:
        logger.error(f"Error getting tenant config: {e}")
        return Response({
            'success': False,
            'error': 'Failed to load tenant configuration',
            'data': _get_fallback_config(environment)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_keycloak_config(request):
    """
    Get Keycloak configuration for React frontend authentication.
    Returns environment-specific Keycloak settings.
    """
    try:
        environment = request.GET.get('environment') or getattr(request, 'environment', 'uat')
        domain = request.GET.get('domain') or request.get_host().split(':')[0]
        
        # Get tenant for client-specific configuration
        tenant = Tenant.get_by_domain(domain)
        if not tenant:
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            
        if not tenant:
            tenant = _create_primary_spoton_tenant()
        
        # Get environment-specific client and realm
        client_id = tenant.get_client_id_for_environment(environment)
        realm = tenant.get_realm_for_environment(environment)
        
        keycloak_config = {
            'server_url': settings.KEYCLOAK_SERVER_URL,
            'realm': realm,
            'client_id': client_id,
            'environment': environment,
            'redirect_uris': _get_redirect_uris(environment, domain),
            'web_origins': _get_web_origins(environment, domain),
            'features': {
                'social_login': True,
                'account_linking': True,
                'phone_verification': True
            }
        }
        
        return Response({
            'success': True,
            'data': keycloak_config
        })
        
    except Exception as e:
        logger.error(f"Error getting Keycloak config: {e}")
        return Response({
            'success': False,
            'error': 'Failed to load Keycloak configuration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_tenant_list(request):
    """
    Get list of available tenants/brands.
    Used for tenant selection or multi-brand scenarios.
    """
    try:
        environment = request.GET.get('environment') or getattr(request, 'environment', 'uat')
        
        tenants = Tenant.objects.filter(is_active=True).order_by('is_primary_brand', 'name')
        
        tenant_list = []
        for tenant in tenants:
            client_id = tenant.get_client_id_for_environment(environment)
            
            tenant_info = {
                'id': str(tenant.id),
                'name': tenant.name,
                'slug': tenant.slug,
                'is_primary': tenant.is_primary_brand,
                'client_id': client_id,
                'domain': tenant.primary_domain,
                'logo': tenant.get_branding_config().get('logos', {}).get('main_logo'),
                'theme_color': tenant.get_branding_config().get('theme', {}).get('primary_color')
            }
            
            tenant_list.append(tenant_info)
        
        return Response({
            'success': True,
            'data': {
                'tenants': tenant_list,
                'environment': environment,
                'primary_tenant': next((t for t in tenant_list if t['is_primary']), None)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting tenant list: {e}")
        return Response({
            'success': False,
            'error': 'Failed to load tenant list'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _create_primary_spoton_tenant():
    """Create the primary SpotOn tenant if it doesn't exist"""
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
        branding_config={}
    )
    logger.info("Created primary SpotOn tenant")
    return tenant


def _get_api_base_url(environment):
    """Get API base URL for environment"""
    if environment == 'live':
        return 'https://api.spoton.co.nz'
    elif environment == 'uat':
        return 'https://uat.api.spoton.co.nz'
    else:
        return 'http://localhost:8000'  # Development


def _get_redirect_uris(environment, domain):
    """Get redirect URIs for Keycloak client"""
    if environment == 'live':
        return [
            'https://portal.spoton.co.nz/*',
            'https://spoton.co.nz/*',
            f'https://{domain}/*' if domain != 'portal.spoton.co.nz' else 'https://portal.spoton.co.nz/*'
        ]
    else:
        return [
            'https://uat.portal.spoton.co.nz/*',
            'https://uat.spoton.co.nz/*',
            'http://localhost:3000/*',
            'http://localhost:3001/*'
        ]


def _get_web_origins(environment, domain):
    """Get web origins for Keycloak client"""
    if environment == 'live':
        return [
            'https://portal.spoton.co.nz',
            'https://spoton.co.nz',
            f'https://{domain}' if domain != 'portal.spoton.co.nz' else 'https://portal.spoton.co.nz'
        ]
    else:
        return [
            'https://uat.portal.spoton.co.nz',
            'https://uat.spoton.co.nz',
            'http://localhost:3000',
            'http://localhost:3001'
        ]


def _get_fallback_config(environment):
    """Get fallback configuration if tenant lookup fails"""
    return {
        'theme': {
            'primary_color': '#2563eb',
            'secondary_color': '#64748b',
            'accent_color': '#0ea5e9'
        },
        'branding': {
            'company_name': 'SpotOn Energy',
            'tagline': 'Your Energy Partner'
        },
        'keycloak': {
            'client_id_uat': 'customer-uat-portal',
            'client_id_live': 'customer-live-portal',
            'realm_uat': 'spoton-uat',
            'realm_live': 'spoton-prod'
        },
        'environment': {
            'current': environment,
            'api_base_url': _get_api_base_url(environment)
        }
    } 