"""
Unified Authentication Cookie Service

This service provides a single, consistent interface for managing authentication cookies
across all login methods (password, social login, token refresh, etc.).

Benefits:
- Single source of truth for cookie configuration
- Consistent behavior across all authentication flows
- Easy to scale for new providers (Apple, Facebook, etc.)
- Centralized security policy management
- Environment-aware configuration
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class AuthCookieService:
    """
    Centralized service for managing authentication cookies across all login methods.
    
    Supports:
    - Traditional password login
    - Social login (Google, Apple, Facebook, etc.)
    - Token refresh
    - Cross-domain authentication
    - Environment-specific security settings
    """
    
    # Cookie configuration constants
    ACCESS_TOKEN_NAME = 'access_token'
    REFRESH_TOKEN_NAME = 'refresh_token'
    SOCIAL_LOGIN_NAME = 'social_login'
    
    # Default expiration times (in seconds)
    ACCESS_TOKEN_MAX_AGE = 3600  # 1 hour
    REFRESH_TOKEN_MAX_AGE = 86400  # 24 hours
    SOCIAL_LOGIN_MAX_AGE = 86400  # 24 hours
    
    # Domain configuration
    COOKIE_DOMAIN = '.spoton.co.nz'  # Works across all subdomains
    
    def __init__(self, environment: str = None):
        """
        Initialize cookie service with environment-specific configuration.
        
        Args:
            environment: 'uat', 'live', or None for auto-detection
        """
        self.environment = environment or self._detect_environment()
        self.is_production = self.environment == 'live'
        self.is_uat = self.environment == 'uat'
        
        logger.info(f"[AuthCookieService] Initialized for environment: {self.environment}")
    
    def _detect_environment(self) -> str:
        """Detect current environment from Django settings or domain."""
        try:
            if hasattr(settings, 'ENVIRONMENT'):
                return settings.ENVIRONMENT.lower()
            
            # Fallback to debug setting
            if getattr(settings, 'DEBUG', False):
                return 'uat'
            else:
                return 'live'
        except:
            return 'uat'  # Safe default
    
    def _get_security_config(self) -> Dict[str, Any]:
        """
        Get security configuration based on environment.
        
        Returns:
            Dict with secure, samesite, and other security settings
        """
        if self.is_production:
            return {
                'secure': True,      # HTTPS only in production
                'samesite': 'Lax',   # Good balance for production
                'httponly': True,    # Always HTTP-only for security
            }
        else:
            return {
                'secure': True,      # Use HTTPS even in UAT (as per user requirement)
                'samesite': 'Lax',   # Consistent with production
                'httponly': True,    # Always HTTP-only for security
            }
    
    def set_authentication_cookies(
        self,
        response: HttpResponse,
        access_token: str,
        refresh_token: Optional[str] = None,
        provider: str = 'keycloak',
        flow_type: str = 'standard'
    ) -> None:
        """
        Set authentication cookies with consistent configuration.
        
        Args:
            response: Django HttpResponse object
            access_token: JWT access token
            refresh_token: Optional JWT refresh token
            provider: Authentication provider ('keycloak', 'google', 'apple', etc.)
            flow_type: Authentication flow ('standard', 'social', 'refresh')
        """
        security_config = self._get_security_config()
        
        # Handle special cases for social login flows
        if flow_type == 'social':
            # Social OAuth flows may need SameSite=None for cross-site redirects
            security_config['samesite'] = 'None'
            # SameSite=None requires Secure=True
            security_config['secure'] = True
        
        # Set access token cookie
        self._set_cookie(
            response=response,
            name=self.ACCESS_TOKEN_NAME,
            value=access_token,
            max_age=self.ACCESS_TOKEN_MAX_AGE,
            security_config=security_config
        )
        
        logger.info(f"[AuthCookieService] Set access_token cookie for {provider} {flow_type} flow")
        
        # Set refresh token cookie if provided
        if refresh_token:
            self._set_cookie(
                response=response,
                name=self.REFRESH_TOKEN_NAME,
                value=refresh_token,
                max_age=self.REFRESH_TOKEN_MAX_AGE,
                security_config=security_config
            )
            
            logger.info(f"[AuthCookieService] Set refresh_token cookie for {provider} {flow_type} flow")
    
    def set_social_login_cookie(
        self,
        response: HttpResponse,
        provider: str,
        user_data: Dict[str, Any]
    ) -> None:
        """
        Set social login tracking cookie.
        
        Args:
            response: Django HttpResponse object
            provider: Social provider name ('google', 'apple', etc.)
            user_data: User data from social provider
        """
        security_config = self._get_security_config()
        
        # Social login cookie value (minimal data for tracking)
        social_cookie_value = f"{provider}:{user_data.get('email', 'unknown')}"
        
        self._set_cookie(
            response=response,
            name=self.SOCIAL_LOGIN_NAME,
            value=social_cookie_value,
            max_age=self.SOCIAL_LOGIN_MAX_AGE,
            security_config=security_config
        )
        
        logger.info(f"[AuthCookieService] Set social_login cookie for {provider}")
    
    def clear_authentication_cookies(self, response: HttpResponse) -> None:
        """
        Clear all authentication cookies consistently.
        
        Args:
            response: Django HttpResponse object
        """
        cookies_to_clear = [
            self.ACCESS_TOKEN_NAME,
            self.REFRESH_TOKEN_NAME,
            self.SOCIAL_LOGIN_NAME,
            # Legacy cookie names for cleanup
            'keycloak_access_token',
            'keycloak_refresh_token',
            'auth_token',
            'jwt_access',
            'jwt_refresh'
        ]
        
        for cookie_name in cookies_to_clear:
            self._clear_cookie(response, cookie_name)
        
        logger.info(f"[AuthCookieService] Cleared {len(cookies_to_clear)} authentication cookies")
    
    def _set_cookie(
        self,
        response: HttpResponse,
        name: str,
        value: str,
        max_age: int,
        security_config: Dict[str, Any]
    ) -> None:
        """
        Internal method to set a cookie with consistent configuration.
        
        Args:
            response: Django HttpResponse object
            name: Cookie name
            value: Cookie value
            max_age: Cookie expiration time in seconds
            security_config: Security configuration dict
        """
        response.set_cookie(
            name,
            value,
            max_age=max_age,
            path='/',
            domain=self.COOKIE_DOMAIN,
            **security_config
        )
        
        logger.debug(f"[AuthCookieService] Set cookie {name} with config: {security_config}")
    
    def _clear_cookie(self, response: HttpResponse, name: str) -> None:
        """
        Internal method to clear a cookie consistently.
        
        Args:
            response: Django HttpResponse object
            name: Cookie name to clear
        """
        # Clear for current domain
        response.set_cookie(
            name,
            '',
            max_age=0,
            expires='Thu, 01 Jan 1970 00:00:00 GMT',
            path='/',
            secure=True,
            samesite='Lax'
        )
        
        # Clear for .spoton.co.nz domain (cross-subdomain)
        response.set_cookie(
            name,
            '',
            max_age=0,
            expires='Thu, 01 Jan 1970 00:00:00 GMT',
            path='/',
            domain=self.COOKIE_DOMAIN,
            secure=True,
            samesite='Lax'
        )
        
        logger.debug(f"[AuthCookieService] Cleared cookie: {name}")


# Singleton instance for easy access
_cookie_service_instance = None

def get_auth_cookie_service(environment: str = None) -> AuthCookieService:
    """
    Get singleton instance of AuthCookieService.
    
    Args:
        environment: Optional environment override
    
    Returns:
        AuthCookieService instance
    """
    global _cookie_service_instance
    
    if _cookie_service_instance is None or environment:
        _cookie_service_instance = AuthCookieService(environment)
    
    return _cookie_service_instance


# Convenience functions for common operations
def set_auth_cookies(response: HttpResponse, access_token: str, refresh_token: str = None, 
                    provider: str = 'keycloak', flow_type: str = 'standard') -> None:
    """Convenience function to set authentication cookies."""
    service = get_auth_cookie_service()
    service.set_authentication_cookies(response, access_token, refresh_token, provider, flow_type)


def clear_auth_cookies(response: HttpResponse) -> None:
    """Convenience function to clear authentication cookies."""
    service = get_auth_cookie_service()
    service.clear_authentication_cookies(response)


def set_social_login_cookie(response: HttpResponse, provider: str, user_data: Dict[str, Any]) -> None:
    """Convenience function to set social login cookie."""
    service = get_auth_cookie_service()
    service.set_social_login_cookie(response, provider, user_data)
