import logging
import jwt  # Used for Keycloak token processing only
import requests
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from users.models import Tenant

logger = logging.getLogger(__name__)
User = get_user_model()

class KeycloakUserSyncMiddleware:
    """
    Middleware to sync users from Keycloak tokens and extract tenant context
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request and sync user
        self.process_request(request)
        
        # Extract tenant context from Keycloak JWT
        self.extract_tenant_context(request)
        
        # Process the request
        response = self.get_response(request)
        return response

    def extract_tenant_context(self, request):
        """Extract tenant context from Keycloak JWT custom claims"""
        access_token = request.COOKIES.get('access_token')
        
        if not access_token:
            # Set default context for unauthenticated requests
            request.tenant_id = 'spoton'
            request.environment = 'uat'  # Default to UAT
            request.client_context = None
            # Don't override request.tenant if it's already set by ClientBasedTenantMiddleware
            if not hasattr(request, 'tenant'):
                request.tenant = None
            return

        try:
            # Decode JWT without verification to extract custom claims
            # Note: Token verification is done separately in the authentication views
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            
            # Extract custom claims added by Keycloak mappers
            tenant_id = decoded.get('tenant_id', 'spoton')
            environment = decoded.get('environment', 'uat')
            client_context = decoded.get('client_context')
            
            # Set tenant context on request
            request.tenant_id = tenant_id
            request.environment = environment
            request.client_context = client_context
            
            # Check if ClientBasedTenantMiddleware already set tenant context
            if hasattr(request, 'tenant') and isinstance(request.tenant, dict):
                # Extract the tenant object from the existing context
                tenant_obj = request.tenant.get('tenant_obj')
                if tenant_obj and isinstance(tenant_obj, Tenant):
                    request.tenant = tenant_obj
                    logger.debug(f"Using tenant from ClientBasedTenantMiddleware: {tenant_obj}")
                    return
            
            # If no existing tenant context, get or create tenant object
            try:
                tenant, created = Tenant.objects.get_or_create(
                    slug=tenant_id,
                    defaults={
                        'name': f'{tenant_id.title()} Energy',
                        'is_primary_brand': tenant_id == 'spoton'
                    }
                )
                request.tenant = tenant
                
                if created:
                    logger.info(f"Created new tenant: {tenant_id}")
                    
            except Exception as e:
                logger.error(f"Failed to get/create tenant {tenant_id}: {e}")
                request.tenant = None
                
            logger.debug(f"Tenant context extracted: tenant_id={tenant_id}, environment={environment}, client={client_context}")
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            # Set default context for invalid tokens
            request.tenant_id = 'spoton'
            request.environment = 'uat'
            request.client_context = None
            if not hasattr(request, 'tenant'):
                request.tenant = None
            
        except Exception as e:
            logger.error(f"Failed to extract tenant context from JWT: {e}")
            # Set default context on error
            request.tenant_id = 'spoton'
            request.environment = 'uat'
            request.client_context = None
            if not hasattr(request, 'tenant'):
                request.tenant = None
    
    def get_keycloak_public_key(self, realm='spoton-uat', kid=None):
        """Get Keycloak public key for JWT verification. Prefer matching by kid when provided."""
        # Temporarily disable caching due to Redis auth issues
        # cache_key = f"keycloak_public_key_{realm}"
        # cached_key = cache.get(cache_key)
        # if cached_key:
        #     return cached_key
            
        try:
            keycloak_url = 'http://core-keycloak:8080'  # Use internal URL for container-to-container communication
            # Correct OIDC JWKS path uses a hyphen: openid-connect
            certs_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
            logger.info(f"Fetching public key from: {certs_url}")
            
            response = requests.get(
                certs_url,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Successfully fetched certs for realm {realm}")
            
            data = response.json()
            keys = data.get('keys', [])
            selected = None
            if kid:
                for k in keys:
                    if k.get('kid') == kid:
                        selected = k
                        break
            if not selected and keys:
                selected = keys[0]
            if selected:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(selected)
                # Temporarily disable caching due to Redis auth issues
                # cache.set(cache_key, public_key, 3600)  # Cache for 1 hour
                return public_key
                
        except Exception as e:
            logger.error(f"Failed to get Keycloak public key for {realm}: {e}")
            
        return None
    
    def decode_keycloak_token(self, token):
        """Decode and verify Keycloak JWT token"""
        try:
            # First decode without verification to get the realm and header
            unverified = jwt.decode(token, options={"verify_signature": False})
            header = jwt.get_unverified_header(token)
            issuer = unverified.get('iss', '')
            
            # Extract realm from issuer URL
            realm = 'spoton-uat'  # default
            if '/realms/' in issuer:
                realm = issuer.split('/realms/')[-1]
            
            # Get public key for the specific realm (match kid if available)
            public_key = self.get_keycloak_public_key(realm, kid=header.get('kid'))
            if not public_key:
                logger.error(f"No public key available for realm {realm}")
                return None
                
            # Verify and decode token
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=None,
                options={"verify_aud": False}
            )
            
            return decoded
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error decoding JWT token: {e}")
        return None
    
    def sync_keycloak_user(self, keycloak_data):
        """Sync Keycloak user data with Django user"""
        try:
            keycloak_id = keycloak_data.get('sub')
            email = keycloak_data.get('email')
            
            if not keycloak_id or not email:
                logger.warning("Missing keycloak_id or email in token")
                return None
            
            # Extract realm and client info
            issuer = keycloak_data.get('iss', '')
            realm = 'spoton-uat'  # default
            if '/realms/' in issuer:
                realm = issuer.split('/realms/')[-1]
            
            client_id = keycloak_data.get('azp') or keycloak_data.get('aud')
            
            # Try to find existing user by keycloak_id or email (prevent duplicates)
            user = None
            try:
                # First try by keycloak_id (most reliable)
                user = User.objects.get(id=keycloak_id)
            except User.DoesNotExist:
                # If not found by keycloak_id, check by email but handle duplicates
                try:
                    # Since email is no longer in Django User model, we can't find by email
                    # This is expected with the clean architecture - users should be found by keycloak_id
                    logger.info(f"User not found by keycloak_id {keycloak_id}, will create new user")
                    user = None
                except Exception as e:
                    logger.warning(f"Error in user lookup: {e}")
                    user = None
            
            # Get tenant based on client_id
            tenant = None
            if client_id:
                environment = 'uat' if 'uat' in realm else 'live'
                tenant = Tenant.get_by_client_id(client_id, environment)
            
            # Extract user data from Keycloak token
            from django.utils import timezone
            user_data = {
                'email': email,
                'first_name': keycloak_data.get('given_name', ''),
                'last_name': keycloak_data.get('family_name', ''),
                'username': keycloak_data.get('preferred_username', email),
                'is_active': True,
                'keycloak_id': keycloak_id,
                'keycloak_client_id': client_id,
                'preferred_tenant_slug': tenant.slug if tenant else 'spoton',
                'email_verified': keycloak_data.get('email_verified', False),
                'phone_verified': keycloak_data.get('phone_verified', False),
            }
            
            # Handle phone number from custom attributes
            if 'phone_number' in keycloak_data:
                user_data['phone'] = keycloak_data['phone_number']
            
            # Create or update user (Keycloak as single source of truth)
            if user:
                # Update existing user with latest Keycloak data
                for key, value in user_data.items():
                    if hasattr(user, key) and value is not None and key not in ['email', 'username', 'first_name', 'last_name', 'phone', 'email_verified', 'phone_verified']:
                        setattr(user, key, value)
                user.save()
                user_email = user.get_email() if hasattr(user, 'get_email') else email
                logger.info(f"[KeycloakSync] Updated user {user_email} from Keycloak")
            else:
                # Create new user only if we have valid Keycloak data
                try:
                    # Use centralized user identity service for consistent user management
                    try:
                        from core.services.user_identity_service import UserIdentityService
                        
                        # Get tenant for the identity service
                        client_id = keycloak_data.get('azp') or keycloak_data.get('aud')
                        tenant = None
                        if client_id:
                            environment = 'uat' if 'uat' in realm else 'live'
                            tenant = Tenant.get_by_client_id(client_id, environment)
                        
                        if not tenant:
                            # Fallback to primary tenant
                            tenant = Tenant.objects.filter(is_primary_brand=True).first()
                        
                        if tenant:
                            identity_service = UserIdentityService(tenant=tenant, environment='uat' if 'uat' in realm else 'live')
                            
                            user, created = identity_service.find_or_create_user(
                                email=email,
                                keycloak_id=keycloak_id,
                                user_data={
                                    'is_active': user_data.get('is_active', True),
                                    'email_verified': keycloak_data.get('email_verified', False),
                                    'phone_verified': False,  # Will be set during phone verification
                                },
                                create_in_keycloak=False  # User already exists in Keycloak
                            )
                            
                            logger.info(f"[KeycloakSync] UserIdentityService result: user={user.id}, created={created}")
                        else:
                            logger.error(f"[KeycloakSync] No tenant found for client_id {client_id}, falling back to old logic")
                            raise Exception("No tenant found")
                            
                    except Exception as e:
                        logger.warning(f"[KeycloakSync] UserIdentityService failed, using fallback: {e}")
                        
                        # Fallback to old logic
                        existing_user = User.objects.filter(id=keycloak_id).first()
                        if existing_user:
                            user = existing_user
                            for key, value in user_data.items():
                                if hasattr(user, key) and value is not None and key not in ['email', 'username', 'first_name', 'last_name', 'phone', 'email_verified', 'phone_verified']:
                                    setattr(user, key, value)
                            user.save()
                            logger.info(f"[KeycloakSync] Fallback: Updated existing user {email}")
                        else:
                            sanitized_kwargs = {
                                'is_active': user_data.get('is_active', True),
                                'keycloak_client_id': user_data.get('keycloak_client_id'),
                                'preferred_tenant_slug': user_data.get('preferred_tenant_slug'),
                            }
                            user = User.objects.create_user(
                                keycloak_id=keycloak_id,
                                **sanitized_kwargs
                            )
                            logger.info(f"[KeycloakSync] Fallback: Created new user from Keycloak")
                except Exception as e:
                    logger.error(f"[KeycloakSync] Error creating user {email}: {e}")
                    return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error syncing Keycloak user: {e}")
            return None
    
    def process_request(self, request):
        """Process incoming request and sync Keycloak user if authenticated"""
        
        logger.info(f"KeycloakUserSyncMiddleware: Processing request to {request.path}")
        
        # Skip for certain paths
        skip_paths = [
            '/admin/', '/static/', '/media/', '/api/health/', 
            '/api/auth/keycloak/create-user/', '/auth/logout/', '/check-email/',
            '/api/auth/logout/', '/api/check-email/', '/users/check-email/',
            '/auth/me/', '/api/auth/me/', '/auth/refresh/', '/api/auth/refresh/',
            '/auth/login/', '/api/auth/login/'
        ]
        if any(request.path.startswith(path) for path in skip_paths):
            logger.info(f"KeycloakUserSyncMiddleware: Skipping path {request.path}")
            return None
        
        # Check for access token in cookies (preferred) or Authorization header
        token = None
        
        # Priority 1: Secure HTTP cookie (preferred method)
        access_token = request.COOKIES.get('access_token')
        if access_token:
            token = access_token
        else:
            # Priority 2: Authorization header (fallback for API calls)
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            logger.info(f"KeycloakUserSyncMiddleware: No token found")
            return None
        
        # Check cache first to avoid repeated token decoding
        # Temporarily disable caching due to Redis auth issues
        # cache_key = f"keycloak_user_{hash(token)}"
        # cached_user = cache.get(cache_key)
        # if cached_user:
        #     request.user = cached_user
        #     return None
        
        # Decode and verify token
        logger.info(f"KeycloakUserSyncMiddleware: Attempting to decode token")
        keycloak_data = self.decode_keycloak_token(token)
        
        if not keycloak_data:
            return None  # Don't return error, just skip syncing
        
        # Sync user with Django
        user = self.sync_keycloak_user(keycloak_data)
        if not user:
            return None  # Don't return error, just skip syncing
        
        # Cache user for 5 minutes to reduce database hits
        # Temporarily disable caching due to Redis auth issues
        # cache.set(cache_key, user, 300)
        
        # Attach user to request
        request.user = user
        request.keycloak_data = keycloak_data
        
        user_email = user.get_email() if hasattr(user, 'get_email') else 'unknown@example.com'
        logger.info(f"KeycloakUserSyncMiddleware: User authenticated: {user_email}")
        logger.info(f"KeycloakUserSyncMiddleware: Set request.user = {request.user}, is_authenticated = {request.user.is_authenticated}")
        
        return None


class SocialLoginCompletionMiddleware(MiddlewareMixin):
    """
    Middleware to handle social login completion and profile requirements
    """
    
    def process_request(self, request):
        """Check if social login user needs to complete profile"""
        
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Only check for API endpoints that require complete profile
        api_paths_requiring_profile = [
            '/api/onboarding/',
            '/api/billing/',
            '/api/energy/',
            '/api/profile/',
        ]
        
        if not any(request.path.startswith(path) for path in api_paths_requiring_profile):
            return None
        
        user = request.user
        
        # Check if social login user needs to complete phone verification
        if (user.registration_method == 'social' and 
            not user.phone_verified and 
            not user.mobile):
            
            return JsonResponse({
                'error': 'Profile completion required',
                'required_fields': ['mobile'],
                'message': 'Please complete your profile by adding and verifying your mobile number.',
                'redirect_url': '/user/complete-profile'
            }, status=422)  # Unprocessable Entity
        
        return None


class KeycloakAuthentication(BaseAuthentication):
    """
    Custom authentication class for DRF that recognizes users set by KeycloakUserSyncMiddleware.
    This ensures that middleware-authenticated users are properly recognized by DRF permissions.
    """
    
    def authenticate(self, request):
        # Check if middleware has already set an authenticated user
        # Use _request to access the underlying Django request to avoid DRF recursion
        django_request = getattr(request, '_request', request)
        
        logger.info(f"KeycloakAuthentication: Checking authentication for path {request.path}")
        logger.info(f"KeycloakAuthentication: hasattr user: {hasattr(django_request, 'user')}")
        
        if hasattr(django_request, 'user'):
            user = django_request.user
            logger.info(f"KeycloakAuthentication: User object: {user}, is_authenticated: {user.is_authenticated if user else 'No user'}")
            
            if user and user.is_authenticated:
                logger.info(f"KeycloakAuthentication: Recognizing middleware-authenticated user: {user}")
                return (user, None)
        
        # No authentication found
        logger.info(f"KeycloakAuthentication: No authenticated user found")
        return None 