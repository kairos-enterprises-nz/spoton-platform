"""
Unified Authentication Service

This service provides a single interface for all authentication methods:
- Keycloak RS256 tokens (social login, password login)
- Custom HS256 tokens (auto-login)
- Test tokens (development)
- Session-based authentication

Key Benefits:
- Authentication method agnostic - onboarding flow works regardless of auth source
- Consistent user data format across all methods
- Centralized cookie management
- Easy to extend for new providers (Apple, etc.)
"""

import logging
import json
import jwt
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union

from django.http import HttpRequest, HttpResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from users.models import User, Tenant, OnboardingProgress
from users.services import UserCacheService
from .auth_cookie_service import set_auth_cookies, clear_auth_cookies
from core.services.user_identity_service import UserIdentityService

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    """Standardized authentication result"""
    is_authenticated: bool
    user: Optional[User] = None
    user_data: Optional[Dict[str, Any]] = None
    auth_method: str = 'unknown'
    error: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None


class UnifiedAuthService:
    """
    Single service for all authentication operations
    """
    
    @staticmethod
    def authenticate_user(request: HttpRequest, force_fresh_data: bool = True) -> AuthResult:
        """
        Authenticate user using any available method
        Returns standardized AuthResult regardless of auth source
        
        Args:
            request: HTTP request object
            force_fresh_data: If True, bypasses cache and fetches fresh data from Keycloak (DEFAULT: True)
        """
        access_token = request.COOKIES.get('access_token')
        
        if not access_token:
            return AuthResult(
                is_authenticated=False,
                error="No access token found",
                auth_method='none'
            )
        
        try:
            # 1. Test tokens (development)
            if access_token.startswith('test-access-token-'):
                return UnifiedAuthService._handle_test_token(access_token)
            
            # 2. Detect token algorithm
            try:
                token_header = jwt.get_unverified_header(access_token)
                token_algorithm = token_header.get('alg', '')
                logger.info(f"[UnifiedAuth] Token algorithm detected: {token_algorithm}")
            except Exception as e:
                logger.debug(f"[UnifiedAuth] Could not detect token algorithm: {e}")
                token_algorithm = 'unknown'
            
            # 3. Route to appropriate handler
            if token_algorithm == 'HS256':
                return UnifiedAuthService._handle_custom_token(request, access_token)
            elif token_algorithm == 'RS256':
                return UnifiedAuthService._handle_keycloak_token(request, access_token, force_fresh_data)
            else:
                # Try Keycloak first (most common), then custom
                keycloak_result = UnifiedAuthService._handle_keycloak_token(request, access_token, force_fresh_data)
                if keycloak_result.is_authenticated:
                    return keycloak_result
                return UnifiedAuthService._handle_custom_token(request, access_token)
                
        except Exception as e:
            logger.error(f"[UnifiedAuth] Authentication error: {e}")
            return AuthResult(
                is_authenticated=False,
                error="Authentication failed",
                debug_info={"exception": str(e)},
                auth_method='error'
            )
    
    @staticmethod
    def _handle_test_token(access_token: str) -> AuthResult:
        """Handle test tokens for development"""
        try:
            user_role = access_token.replace('test-access-token-', '')
            is_staff = user_role in ['staff', 'admin']
            is_superuser = user_role == 'admin'
            is_onboarding_complete = user_role in ["staff", "admin", "onboarding-complete"]
            
            test_users = {
                "customer": "testcustomer@spoton.co.nz",
                "staff": "teststaff@spoton.co.nz", 
                "admin": "testadmin@spoton.co.nz",
                "onboarding-complete": "onboarding-complete@spoton.co.nz"
            }
            
            email = test_users.get(user_role, "test@spoton.co.nz")
            
            user_data = {
                "id": f"test-user-{user_role}",
                "email": email,
                "first_name": "Test" if user_role != "onboarding-complete" else "Onboarding",
                "last_name": user_role.title() if user_role != "onboarding-complete" else "Complete",
                "phone": "021234567",
                "mobile": "021234567",
                "phone_verified": True,
                "email_verified": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_onboarding_complete": is_onboarding_complete,
                "isAuthenticated": True
            }
            
            return AuthResult(
                is_authenticated=True,
                user=None,  # Test users don't have Django User objects
                user_data=user_data,
                auth_method='test'
            )
            
        except Exception as e:
            logger.error(f"[UnifiedAuth] Test token error: {e}")
            return AuthResult(
                is_authenticated=False,
                error="Invalid test token",
                auth_method='test'
            )
    
    @staticmethod
    def _handle_custom_token(request: HttpRequest, access_token: str) -> AuthResult:
        """Handle custom HS256 auto-login tokens"""
        try:
            # Get tenant configuration
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                return AuthResult(
                    is_authenticated=False,
                    error="Tenant configuration not found",
                    auth_method='custom'
                )
            
            environment = getattr(request, 'environment', 'uat')
            keycloak_config = tenant.get_keycloak_config(environment)
            
            if not keycloak_config:
                return AuthResult(
                    is_authenticated=False,
                    error="Keycloak configuration not found",
                    auth_method='custom'
                )
            
            # Decode custom token
            secret = f"auto-login-{keycloak_config['realm']}-{tenant.id}"
            payload = jwt.decode(access_token, secret, algorithms=['HS256'], options={"verify_aud": False})
            
            # Get Django user
            django_user = User.objects.get(id=payload['sub'])
            
            # Get tenant configuration for fresh data fetch
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            environment = getattr(request, 'environment', 'uat')
            
            # Get fresh user data from cache/Keycloak instead of relying on token payload
            # This ensures we have the latest mobile data, registration_method, etc.
            cached_user_data = UserCacheService.get_user_data(str(django_user.id))
            
            if not cached_user_data:
                # Fallback to fresh Keycloak data if cache miss
                logger.warning(f"[UnifiedAuth] Cache miss for custom token user {django_user.id}, fetching fresh data")
                cached_user_data = UnifiedAuthService._fetch_fresh_keycloak_data(
                    django_user, 
                    payload,  # Use token payload as fallback user_info
                    tenant, 
                    environment
                )
            
            # Build complete user data using the same structure as Keycloak tokens
            user_data = {
                "id": str(django_user.id),
                "email": cached_user_data.get('email', payload.get('email', '')),
                "first_name": cached_user_data.get('first_name', payload.get('given_name', '')),
                "last_name": cached_user_data.get('last_name', payload.get('family_name', '')),
                "phone": cached_user_data.get('phone', ''),
                "mobile": cached_user_data.get('mobile', cached_user_data.get('phone', '')),
                "phone_verified": cached_user_data.get('phone_verified', False),
                "mobile_verified": cached_user_data.get('mobile_verified', cached_user_data.get('phone_verified', False)),
                "email_verified": cached_user_data.get('email_verified', payload.get('email_verified', False)),
                "is_staff": cached_user_data.get('is_staff', django_user.is_staff),
                "is_superuser": cached_user_data.get('is_superuser', django_user.is_superuser),
                "is_onboarding_complete": cached_user_data.get('is_onboarding_complete', False),
                "registration_method": cached_user_data.get('registration_method', ''),
                "social_provider": cached_user_data.get('social_provider', ''),
                "isAuthenticated": True
            }
            
            logger.info(f"[UnifiedAuth] Custom token validated for: {payload.get('email', 'unknown')}")
            
            return AuthResult(
                is_authenticated=True,
                user=django_user,
                user_data=user_data,
                auth_method='custom'
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                is_authenticated=False,
                error="Token expired",
                auth_method='custom'
            )
        except jwt.InvalidTokenError as e:
            logger.debug(f"[UnifiedAuth] Invalid custom token: {e}")
            return AuthResult(
                is_authenticated=False,
                error="Invalid custom token",
                auth_method='custom'
            )
        except User.DoesNotExist:
            return AuthResult(
                is_authenticated=False,
                error="User not found",
                auth_method='custom'
            )
        except Exception as e:
            logger.error(f"[UnifiedAuth] Custom token error: {e}")
            return AuthResult(
                is_authenticated=False,
                error="Custom token validation failed",
                auth_method='custom'
            )
    
    @staticmethod
    def _handle_keycloak_token(request: HttpRequest, access_token: str, force_fresh_data: bool = False) -> AuthResult:
        """Handle Keycloak RS256 tokens"""
        try:
            # Get tenant configuration
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                return AuthResult(
                    is_authenticated=False,
                    error="Authentication service not configured",
                    auth_method='keycloak'
                )
            
            environment = getattr(request, 'environment', 'uat')
            keycloak_config = tenant.get_keycloak_config(environment)
            
            if not keycloak_config:
                return AuthResult(
                    is_authenticated=False,
                    error="Keycloak configuration not found",
                    auth_method='keycloak'
                )
            
            # Validate with Keycloak userinfo endpoint
            userinfo_url = f"http://core-keycloak:8080/realms/{keycloak_config['realm']}/protocol/openid-connect/userinfo"
            
            userinfo_response = requests.get(
                userinfo_url,
                headers={'Authorization': f"Bearer {access_token}"},
                timeout=10
            )
            
            if userinfo_response.status_code != 200:
                logger.error(f"[UnifiedAuth] Keycloak userinfo failed: {userinfo_response.status_code}")
                return AuthResult(
                    is_authenticated=False,
                    error="Invalid or expired Keycloak token",
                    debug_info={
                        "status_code": userinfo_response.status_code,
                        "keycloak_error": userinfo_response.text[:200] if userinfo_response.text else "No error message"
                    },
                    auth_method='keycloak'
                )
            
            user_info = userinfo_response.json()
            keycloak_id = user_info.get('sub')
            
            # Ensure Django user exists
            django_user = UnifiedAuthService._ensure_django_user(keycloak_id, user_info, keycloak_config, tenant)
            
            # Get user data - bypass cache if force_fresh_data is True
            if force_fresh_data:
                logger.info(f"[UnifiedAuth] Force fresh data requested - bypassing cache for {user_info.get('email', 'unknown')}")
                cached_user_data = UnifiedAuthService._fetch_fresh_keycloak_data(django_user, user_info, tenant, getattr(request, 'environment', 'uat'))
            else:
                # Get cached user data
                cached_user_data = UserCacheService.get_user_data(keycloak_id)
                
                if not cached_user_data:
                    # Fallback to basic user info from Keycloak
                    cached_user_data = UnifiedAuthService._create_fallback_user_data(django_user, user_info)
            
            user_data = {
                "id": str(django_user.id),
                "email": cached_user_data['email'],
                "first_name": cached_user_data['first_name'],
                "last_name": cached_user_data['last_name'],
                "phone": cached_user_data.get('phone', ''),
                "mobile": cached_user_data.get('mobile', cached_user_data.get('phone', '')),
                "phone_verified": cached_user_data.get('phone_verified', False),
                "mobile_verified": cached_user_data.get('mobile_verified', cached_user_data.get('phone_verified', False)),
                "email_verified": cached_user_data.get('email_verified', False),
                "is_staff": cached_user_data.get('is_staff', False),
                "is_superuser": cached_user_data.get('is_superuser', False),
                "is_onboarding_complete": cached_user_data.get('is_onboarding_complete', False),
                "registration_method": cached_user_data.get('registration_method', ''),
                "social_provider": cached_user_data.get('social_provider', ''),
                "isAuthenticated": True
            }
            
            logger.info(f"[UnifiedAuth] Keycloak token validated for: {cached_user_data.get('email', 'unknown')}")
            
            return AuthResult(
                is_authenticated=True,
                user=django_user,
                user_data=user_data,
                auth_method='keycloak'
            )
            
        except requests.RequestException as e:
            logger.error(f"[UnifiedAuth] Keycloak request error: {e}")
            return AuthResult(
                is_authenticated=False,
                error="Authentication service temporarily unavailable",
                auth_method='keycloak'
            )
        except Exception as e:
            logger.error(f"[UnifiedAuth] Keycloak token error: {e}")
            return AuthResult(
                is_authenticated=False,
                error="Keycloak token validation failed",
                auth_method='keycloak'
            )
    
    @staticmethod
    def _ensure_django_user(keycloak_id: str, user_info: Dict, keycloak_config: Dict, tenant: Tenant) -> User:
        """Ensure Django user exists for Keycloak user using centralized identity service"""
        try:
            # Try direct lookup first for performance
            return User.objects.get(id=keycloak_id)
        except User.DoesNotExist:
            # Use centralized identity service for consistent user creation
            try:
                identity_service = UserIdentityService(tenant=tenant, environment='uat')
                
                email = user_info.get('email')
                if not email:
                    # Fallback email if not provided
                    email = f"{keycloak_id}@example.com"
                
                django_user, created = identity_service.find_or_create_user(
                    email=email,
                    keycloak_id=keycloak_id,
                    user_data={
                        'is_active': True,
                        'email_verified': user_info.get('email_verified', False),
                        'phone_verified': False,
                    },
                    create_in_keycloak=False  # User already exists in Keycloak
                )
                
                logger.info(f"[UnifiedAuth] UserIdentityService result: user={django_user.id}, created={created}")
                return django_user
                
            except Exception as e:
                logger.error(f"[UnifiedAuth] UserIdentityService failed, using fallback: {e}")
                
                # Fallback to old logic
                django_user = User.objects.create(
                    id=keycloak_id,  # Single ID architecture
                    is_active=True
                )
                django_user.keycloak_client_id = keycloak_config['client_id']
                django_user.preferred_tenant_slug = tenant.slug
                django_user.save()
                
                # Create onboarding progress
                try:
                    OnboardingProgress.objects.get_or_create(
                        user=django_user,
                        defaults={
                            'current_step': '',
                            'step_data': {},
                            'is_completed': False
                        }
                    )
                except Exception as e:
                    logger.error(f"[UnifiedAuth] Error creating onboarding progress: {e}")
                
                return django_user
    
    @staticmethod
    def _fetch_fresh_keycloak_data(django_user: User, user_info: Dict, tenant: Tenant, environment: str) -> Dict:
        """
        Fetch fresh user data directly from Keycloak, bypassing cache.
        Used for authentication-critical operations like phone verification.
        """
        try:
            from users.keycloak_user_service import KeycloakUserService
            
            keycloak_service = KeycloakUserService(tenant=tenant, environment=environment)
            admin_client = keycloak_service._get_keycloak_admin()
            
            # Fetch fresh user data from Keycloak
            fresh_user_data = admin_client.get_user(str(django_user.id))
            
            if not fresh_user_data:
                logger.warning(f"[UnifiedAuth] Could not fetch fresh Keycloak data for user {django_user.id}, using fallback")
                return UnifiedAuthService._create_fallback_user_data(django_user, user_info)
            
            # Extract attributes
            attributes = fresh_user_data.get('attributes', {})
            
            # Get onboarding status
            is_onboarding_complete = UnifiedAuthService._get_onboarding_status(django_user)
            
            # Parse mobile verification status from Keycloak attributes (normalized)
            mobile_verified = attributes.get('mobile_verified', ['false'])[0].lower() == 'true' if 'mobile_verified' in attributes else attributes.get('phone_verified', ['false'])[0].lower() == 'true'
            mobile = attributes.get('mobile', [''])[0] or attributes.get('phone', [''])[0]
            
            # Get registration method and social provider
            registration_method = attributes.get('registration_method', [''])[0]
            social_provider = attributes.get('social_provider', [''])[0]
            
            fresh_data = {
                'id': str(django_user.id),
                'email': fresh_user_data.get('email', user_info.get('email', '')),
                'first_name': fresh_user_data.get('firstName', user_info.get('given_name', '')),
                'last_name': fresh_user_data.get('lastName', user_info.get('family_name', '')),
                'mobile': mobile,                           # Normalized field
                'phone': mobile,                            # Legacy compatibility
                'mobile_verified': mobile_verified,         # Normalized field
                'phone_verified': mobile_verified,          # Legacy compatibility
                'email_verified': fresh_user_data.get('emailVerified', False),
                'is_staff': django_user.is_staff,
                'is_superuser': django_user.is_superuser,
                'is_onboarding_complete': is_onboarding_complete,
                'registration_method': registration_method,
                'social_provider': social_provider,
            }
            
            logger.info(f"[UnifiedAuth] Fresh Keycloak data fetched for {fresh_data['email']}: mobile_verified={mobile_verified}, mobile={mobile}, registration_method={registration_method}")
            
            # No cache operations - always fetch fresh data
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"[UnifiedAuth] Error fetching fresh Keycloak data for user {django_user.id}: {e}")
            return UnifiedAuthService._create_fallback_user_data(django_user, user_info)
    
    @staticmethod
    def _create_fallback_user_data(django_user: User, user_info: Dict) -> Dict[str, Any]:
        """Create fallback user data when cache is unavailable"""
        
        # For recent users, assume phone verification completed during signup
        time_since_creation = timezone.now() - django_user.date_joined
        is_recent_user = time_since_creation.total_seconds() < 3600  # Less than 1 hour
        
        fallback_email = user_info.get('email', 'unknown@example.com')
        fallback_email_verified = user_info.get('email_verified', False)
        fallback_phone_verified = is_recent_user and fallback_email_verified
        
        is_onboarding_complete = UnifiedAuthService._get_onboarding_status(django_user)
        
        return {
            'email': fallback_email,
            'first_name': user_info.get('given_name', ''),
            'last_name': user_info.get('family_name', ''),
            'phone': '+64231564564' if is_recent_user else '',
            'phone_verified': fallback_phone_verified,
            'email_verified': fallback_email_verified,
            'is_staff': django_user.is_staff,
            'is_superuser': django_user.is_superuser,
            'is_onboarding_complete': is_onboarding_complete,
        }
    
    @staticmethod
    def _get_onboarding_status(django_user: User) -> bool:
        """Get onboarding completion status"""
        try:
            progress = OnboardingProgress.objects.filter(user=django_user).first()
            return bool(progress and progress.is_completed)
        except Exception as e:
            logger.debug(f"[UnifiedAuth] Could not check onboarding status: {e}")
            return False
    
    @staticmethod
    def set_authentication(response: HttpResponse, user_data: Dict[str, Any], auth_method: str, access_token: str = None, refresh_token: str = None) -> None:
        """
        Set authentication cookies using unified service
        """
        if access_token:
            # Determine provider and flow type from auth method
            provider_map = {
                'keycloak': 'keycloak',
                'custom': 'keycloak',  # Custom tokens are still Keycloak-based
                'test': 'test'
            }
            
            flow_type_map = {
                'keycloak': 'standard',
                'custom': 'social',  # Custom tokens often come from social flows
                'test': 'test'
            }
            
            provider = provider_map.get(auth_method, 'keycloak')
            flow_type = flow_type_map.get(auth_method, 'standard')
            
            set_auth_cookies(
                response=response,
                access_token=access_token,
                refresh_token=refresh_token,
                provider=provider,
                flow_type=flow_type
            )
        
        # Set social login tracking if needed
        if auth_method in ['custom', 'social']:
            try:
                response.set_cookie('social_login', 'true', max_age=3600, samesite='Lax')
            except Exception:
                pass
    
    @staticmethod
    def clear_authentication(response: HttpResponse) -> None:
        """
        Clear authentication cookies using unified service
        """
        clear_auth_cookies(response)
        
        # Also clear any additional cookies
        additional_cookies = ['social_login', 'sessionid', 'csrftoken']
        for cookie_name in additional_cookies:
            response.set_cookie(
                cookie_name,
                '',
                max_age=0,
                expires='Thu, 01 Jan 1970 00:00:00 GMT',
                path='/',
                secure=True,
                samesite='Lax'
            )
    
    @staticmethod
    def create_response(auth_result: AuthResult) -> Response:
        """
        Create standardized API response from AuthResult
        """
        if not auth_result.is_authenticated:
            return Response(
                {
                    "error": auth_result.error or "Authentication failed",
                    "isAuthenticated": False,
                    "user": None,
                    "debug_info": auth_result.debug_info
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response({
            "user": auth_result.user_data,
            "onboarding": {
                "is_completed": auth_result.user_data.get('is_onboarding_complete', False),
                "next_step": "dashboard" if auth_result.user_data.get('is_onboarding_complete', False) else "onboarding"
            }
        })
