"""
Unified Social Authentication Framework for SpotOn

This framework provides a consistent approach for integrating social authentication
providers (Google, Apple, etc.) with the existing email signup flow.

Key Features:
- Unified post-authentication flow
- Consistent auto-login mechanism  
- Extensible provider support
- Phone verification integration
- Proper user linking logic
"""

import logging
from abc import ABC, abstractmethod
from urllib.parse import urlencode
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from social_core.backends.oauth import BaseOAuth2
from users.models import User, Tenant
from users.models import OnboardingProgress
from users.keycloak_user_service import KeycloakUserService

logger = logging.getLogger(__name__)


class SocialAuthProvider(ABC):
    """
    Abstract base class for social authentication providers
    """
    
    @property
    @abstractmethod
    def provider_name(self):
        """Return the provider name (e.g., 'google', 'apple')"""
        pass
    
    @property
    @abstractmethod
    def keycloak_idp_hint(self):
        """Return the Keycloak IDP hint for this provider"""
        pass
    
    @abstractmethod
    def get_redirect_params(self, base_params):
        """
        Get provider-specific redirect parameters
        Args:
            base_params (dict): Base OAuth parameters
        Returns:
            dict: Updated parameters for this provider
        """
        pass


class GoogleAuthProvider(SocialAuthProvider):
    """Google OAuth provider implementation"""
    
    @property
    def provider_name(self):
        return 'google'
    
    @property
    def keycloak_idp_hint(self):
        return 'google'
    
    def get_redirect_params(self, base_params):
        """Google-specific OAuth parameters"""
        params = base_params.copy()
        params.update({
            'kc_idp_hint': self.keycloak_idp_hint,
            'scope': 'openid profile email',
            # Google-specific parameters can be added here
        })
        return params


class AppleAuthProvider(SocialAuthProvider):
    """Apple Sign In provider implementation (future)"""
    
    @property
    def provider_name(self):
        return 'apple'
    
    @property
    def keycloak_idp_hint(self):
        return 'apple'
    
    def get_redirect_params(self, base_params):
        """Apple-specific OAuth parameters"""
        params = base_params.copy()
        params.update({
            'kc_idp_hint': self.keycloak_idp_hint,
            'scope': 'openid name email',
            # Apple-specific parameters can be added here
        })
        return params


class SocialAuthFramework:
    """
    Unified framework for managing social authentication flows
    """
    
    # Registry of supported providers
    PROVIDERS = {
        'google': GoogleAuthProvider(),
        'apple': AppleAuthProvider(),
    }
    
    @classmethod
    def get_provider(cls, provider_name):
        """Get a provider instance by name"""
        return cls.PROVIDERS.get(provider_name.lower())
    
    @classmethod
    def get_supported_providers(cls):
        """Get list of supported provider names"""
        return list(cls.PROVIDERS.keys())
    
    @staticmethod
    def get_environment():
        """Get current environment (uat/live)"""
        return getattr(settings, 'ENVIRONMENT', 'uat')
    
    @staticmethod
    def get_keycloak_login_url(environment):
        """Get the Keycloak login URL for the environment"""
        if environment == 'live':
            return "https://live.spoton.co.nz/api/auth/keycloak/login/"
        else:
            return "https://uat.spoton.co.nz/api/auth/keycloak/login/"
    
    @staticmethod
    def get_portal_url(environment, path=""):
        """Get the portal URL for the environment"""
        if environment == 'live':
            base_url = "https://portal.spoton.co.nz"
        else:
            base_url = "https://uat.portal.spoton.co.nz"
        
        return f"{base_url}{path}"
    
    @classmethod
    def generate_social_login_url(cls, provider_name, redirect_uri, state, code_challenge):
        """
        Generate social login URL for a provider
        
        Args:
            provider_name (str): Name of the provider ('google', 'apple', etc.)
            redirect_uri (str): OAuth callback URL
            state (str): OAuth state parameter
            code_challenge (str): PKCE code challenge
            
        Returns:
            str: Complete OAuth authorization URL
        """
        provider = cls.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        environment = cls.get_environment()
        
        # Get tenant configuration
        from users.models import Tenant
        tenant = Tenant.objects.filter(is_primary_brand=True).first()
        if not tenant:
            raise Exception("Primary tenant not found")
        
        keycloak_config = tenant.get_keycloak_config(environment)
        if not keycloak_config:
            raise Exception(f"Keycloak configuration not found for environment: {environment}")
        
        # Base OAuth parameters
        base_params = {
            'client_id': keycloak_config['client_id'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        
        # Get provider-specific parameters
        oauth_params = provider.get_redirect_params(base_params)
        
        # Build authorization URL
        if environment == 'live':
            auth_base_url = f"https://auth.spoton.co.nz/realms/spoton-prod/protocol/openid-connect/auth"
        else:
            auth_base_url = f"https://auth.spoton.co.nz/realms/spoton-uat/protocol/openid-connect/auth"
        
        auth_url = f"{auth_base_url}?{urlencode(oauth_params)}"
        
        logger.info(f"[SocialAuthFramework] Generated {provider_name} login URL: {auth_url}")
        return auth_url
    
    @classmethod
    def generate_auto_login_url(cls, user, redirect_path=None):
        """
        Generate auto-login URL for consistent post-authentication experience
        
        Args:
            user: Django user instance
            redirect_path (str): Optional specific redirect path
            
        Returns:
            str: Auto-login URL
        """
        try:
            environment = cls.get_environment()
            
            # Check onboarding completion status from the proper table
            is_onboarding_complete = False
            try:
                from users.models import OnboardingProgress
                onboarding_progress = OnboardingProgress.objects.filter(user=user).first()
                is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
            except Exception:
                # Default to false if we can't check
                is_onboarding_complete = False
            
            # Determine redirect destination
            if redirect_path:
                redirect_to = cls.get_portal_url(environment, redirect_path)
            elif is_onboarding_complete:
                redirect_to = cls.get_portal_url(environment, "/")  # Dashboard
            else:
                redirect_to = cls.get_portal_url(environment, "/onboarding")
            
            # Create auto-login parameters (consistent with email signup)
            login_params = {
                'email': user.email,
                'auto_login': 'true',
                'redirect_to': redirect_to
            }
            
            base_login_url = cls.get_keycloak_login_url(environment)
            auto_login_url = f"{base_login_url}?{urlencode(login_params)}"
            
            logger.info(f"[SocialAuthFramework] Generated auto-login URL for {user.email}: {auto_login_url}")
            return auto_login_url
            
        except Exception as e:
            logger.error(f"[SocialAuthFramework] Error generating auto-login URL: {e}")
            # Fallback to regular login URL
            return cls.get_keycloak_login_url(cls.get_environment())
    
    @classmethod
    def determine_post_auth_flow(cls, user, is_social_login=False):
        """
        Determine the appropriate post-authentication flow
        
        Args:
            user: Django user instance
            is_social_login (bool): Whether this is a social login
            
        Returns:
            dict: Flow information with type, destination, and URLs
        """
        environment = cls.get_environment()
        
        # For social logins, always require phone verification first
        if is_social_login and not user.phone_verified:
            return {
                'type': 'phone_verification',
                'destination': 'phone_verification',
                'url': cls.get_portal_url(environment, '/auth/verify-phone'),
                'message': 'Please verify your phone number to complete setup'
            }
        
        # Check onboarding completion status using only is_completed
        is_onboarding_complete = False
        try:
            from users.models import OnboardingProgress
            onboarding_progress = OnboardingProgress.objects.filter(user=user).first()
            is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
        except Exception:
            is_onboarding_complete = False

        # After phone verification (or for email signups), determine final destination
        if is_onboarding_complete:
            return {
                'type': 'auto_login',
                'destination': 'dashboard',
                'url': cls.get_portal_url(environment, '/'),
                'login_url': cls.generate_auto_login_url(user),
                'message': 'Welcome back! Redirecting to dashboard...'
            }
        else:
            return {
                'type': 'auto_login',
                'destination': 'onboarding',
                'url': cls.get_portal_url(environment, '/onboarding'),
                'login_url': cls.generate_auto_login_url(user),
                'message': 'Account setup complete! Redirecting to onboarding...'
            }
    
    @classmethod
    def add_provider(cls, provider_name, provider_instance):
        """
        Add a new social authentication provider
        
        Args:
            provider_name (str): Name of the provider
            provider_instance (SocialAuthProvider): Provider implementation
        """
        if not isinstance(provider_instance, SocialAuthProvider):
            raise TypeError("Provider must be an instance of SocialAuthProvider")
        
        cls.PROVIDERS[provider_name.lower()] = provider_instance
        logger.info(f"[SocialAuthFramework] Added provider: {provider_name}")


# Framework usage examples:
"""
# 1. Generate social login URL
framework = SocialAuthFramework()
google_url = framework.generate_social_login_url(
    provider_name='google',
    redirect_uri='https://uat.portal.spoton.co.nz/auth/callback',
    state='secure_state_token',
    code_challenge='pkce_challenge'
)

# 2. Determine post-authentication flow
flow_info = framework.determine_post_auth_flow(user, is_social_login=True)

# 3. Generate auto-login URL
auto_login_url = framework.generate_auto_login_url(user)

# 4. Add new provider (future)
class FacebookAuthProvider(SocialAuthProvider):
    @property
    def provider_name(self):
        return 'facebook'
    
    @property 
    def keycloak_idp_hint(self):
        return 'facebook'
    
    def get_redirect_params(self, base_params):
        params = base_params.copy()
        params.update({
            'kc_idp_hint': self.keycloak_idp_hint,
            'scope': 'openid profile email'
        })
        return params

framework.add_provider('facebook', FacebookAuthProvider())
"""