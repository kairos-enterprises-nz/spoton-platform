"""
User Cache Service - Smart caching for user data to eliminate sync issues.

This service provides a unified interface for user data that combines:
- Identity data from Keycloak (email, phone, verification status)
- Business data from Django (onboarding, account info)

Uses Redis caching with automatic TTL and manual invalidation.
"""

import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.conf import settings
from users.models import User
# KeycloakUserService imported in methods to avoid import issues

logger = logging.getLogger(__name__)

class UserCacheService:
    """
    Centralized user data caching service that combines Keycloak and Django data.
    """
    
    # Cache configuration
    CACHE_TTL = 300  # 5 minutes
    CACHE_PREFIX = "user_complete"
    
    @classmethod
    def get_user_data(cls, keycloak_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get complete user data from cache or fetch fresh if needed.
        
        Args:
            keycloak_id: Keycloak user ID (sub claim)
            force_refresh: Skip cache and fetch fresh data
            
        Returns:
            Dictionary with complete user data or None if user not found
        """
        cache_key = cls._get_cache_key(keycloak_id)
        
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"[UserCache] Cache hit for {keycloak_id}")
                return cached_data
        
        logger.info(f"[UserCache] Cache miss for {keycloak_id}, fetching fresh data")
        return cls._fetch_and_cache_user_data(keycloak_id)
    
    @classmethod
    def invalidate_user_cache(cls, keycloak_id: str) -> bool:
        """
        Invalidate cached user data for a specific user.
        
        Args:
            keycloak_id: Keycloak user ID
            
        Returns:
            True if cache was invalidated successfully
        """
        try:
            cache_key = cls._get_cache_key(keycloak_id)
            cache.delete(cache_key)
            logger.info(f"[UserCache] Invalidated cache for {keycloak_id}")
            return True
        except Exception as e:
            logger.error(f"[UserCache] Failed to invalidate cache for {keycloak_id}: {e}")
            return False
    
    @classmethod
    def warm_user_cache(cls, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """
        Proactively warm the cache with fresh user data.
        
        Args:
            keycloak_id: Keycloak user ID
            
        Returns:
            Fresh user data or None if fetch failed
        """
        logger.info(f"[UserCache] Warming cache for {keycloak_id}")
        return cls._fetch_and_cache_user_data(keycloak_id)
    
    @classmethod
    def _fetch_and_cache_user_data(cls, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user data from both Keycloak and Django, then cache it.
        
        Args:
            keycloak_id: Keycloak user ID
            
        Returns:
            Combined user data or None if fetch failed
        """
        try:
            # Fetch from Keycloak
            keycloak_data = cls._fetch_keycloak_data(keycloak_id)
            if not keycloak_data:
                logger.warning(f"[UserCache] No Keycloak data found for {keycloak_id}")
                return None
            
            # Fetch from Django
            django_data = cls._fetch_django_data(keycloak_id)
            
            # Combine data
            combined_data = {
                # Identity data from Keycloak
                'keycloak_id': keycloak_id,
                'email': keycloak_data.get('email', ''),
                'username': keycloak_data.get('username', ''),
                'first_name': keycloak_data.get('firstName', ''),
                'last_name': keycloak_data.get('lastName', ''),
                'email_verified': keycloak_data.get('emailVerified', False),
                'enabled': keycloak_data.get('enabled', True),
                
                # Phone data from Keycloak attributes
                'phone': cls._extract_phone(keycloak_data),
                'phone_verified': cls._extract_phone_verified(keycloak_data),
                
                # Onboarding data from Keycloak attributes
                'is_onboarding_complete': cls._extract_onboarding_complete(keycloak_data),
                'onboarding_step': cls._extract_onboarding_step(keycloak_data),
                
                # Business data from Django
                'is_staff': django_data.get('is_staff', False),
                'is_superuser': django_data.get('is_superuser', False),
                
                # Social login data from Keycloak attributes
                'registration_method': cls._extract_registration_method(keycloak_data),
                'social_provider': cls._extract_social_provider(keycloak_data),
                
                # Metadata
                'cache_timestamp': cls._get_current_timestamp(),
                'data_sources': {
                    'keycloak': bool(keycloak_data),
                    'django': bool(django_data)
                }
            }
            
            # Cache the combined data
            cache_key = cls._get_cache_key(keycloak_id)
            cache.set(cache_key, combined_data, cls.CACHE_TTL)
            
            logger.info(f"[UserCache] Cached fresh data for {keycloak_id}")
            return combined_data
            
        except Exception as e:
            logger.error(f"[UserCache] Failed to fetch and cache data for {keycloak_id}: {e}")
            return None
    
    @classmethod
    def _fetch_keycloak_data(cls, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user data from Keycloak using working KeycloakUserService."""
        try:
            # Use the working KeycloakUserService instead of KeycloakAdminService
            from users.keycloak_user_service import KeycloakUserService
            from users.models import Tenant
            
            # Get primary tenant and use UAT environment
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                tenant = Tenant.objects.first()
            
            if not tenant:
                logger.error("[UserCache] No tenant found for Keycloak connection")
                return None
            
            # Use the same service that works in direct calls
            service = KeycloakUserService(tenant=tenant, environment='uat')
            admin = service._get_keycloak_admin()
            
            keycloak_user = admin.get_user(keycloak_id)
            logger.info(f"[UserCache] Successfully fetched Keycloak data for {keycloak_id}")
            
            return keycloak_user
            
        except Exception as e:
            logger.error(f"[UserCache] Failed to fetch Keycloak data for {keycloak_id}: {e}")
            
            # Fallback: try to search all users
            try:
                from users.keycloak_user_service import KeycloakUserService
                from users.models import Tenant
                
                tenant = Tenant.objects.filter(is_primary_brand=True).first()
                service = KeycloakUserService(tenant=tenant, environment='uat')
                
                # Search all users and find the one with matching ID
                admin = service._get_keycloak_admin()
                admin.realm_name = service.keycloak_config['realm']
                
                # Get users with a broad search and filter by ID
                all_users = admin.get_users({"max": 1000})  # Limit to avoid performance issues
                matching_user = next((user for user in all_users if user.get('id') == keycloak_id), None)
                
                if matching_user:
                    logger.info(f"[UserCache] Fallback successful: found user {keycloak_id} by searching all users")
                    return matching_user
                else:
                    logger.warning(f"[UserCache] Fallback failed: user {keycloak_id} not found in user list")
                    
            except Exception as fallback_error:
                logger.error(f"[UserCache] Fallback search failed for {keycloak_id}: {fallback_error}")
            
            return None
    
    @classmethod
    def _fetch_django_data(cls, keycloak_id: str) -> Dict[str, Any]:
        """Fetch user data from Django."""
        try:
            django_user = User.objects.get(id=keycloak_id)
            
            return {
                'django_id': str(django_user.id),
                'is_staff': django_user.is_staff,
                'is_superuser': django_user.is_superuser,
                'registration_method': getattr(django_user, 'registration_method', None),
                'social_provider': getattr(django_user, 'social_provider', None),
                'preferred_tenant_slug': django_user.preferred_tenant_slug,
                'date_joined': django_user.date_joined.isoformat() if django_user.date_joined else None,
            }
            
        except User.DoesNotExist:
            logger.warning(f"[UserCache] Django user not found for keycloak_id {keycloak_id}")
            return {}
        except Exception as e:
            logger.error(f"[UserCache] Failed to fetch Django data for {keycloak_id}: {e}")
            return {}
    
    @classmethod
    def _extract_phone(cls, keycloak_data: Dict[str, Any]) -> str:
        """Extract mobile number from Keycloak attributes (normalized to mobile)."""
        attributes = keycloak_data.get('attributes', {})
        
        # Use normalized mobile field first
        if 'mobile' in attributes:
            mobile = attributes['mobile']
            return mobile[0] if isinstance(mobile, list) else str(mobile)
        
        # Fallback to legacy phone keys for backward compatibility
        for key in ['phone', 'phone_number']:
            if key in attributes:
                phone = attributes[key]
                return phone[0] if isinstance(phone, list) else str(phone)
        
        return ''
    
    @classmethod
    def _extract_phone_verified(cls, keycloak_data: Dict[str, Any]) -> bool:
        """Extract mobile verification status from Keycloak attributes (normalized to mobile_verified)."""
        attributes = keycloak_data.get('attributes', {})
        
        # Use normalized mobile_verified field first
        if 'mobile_verified' in attributes:
            mobile_verified = attributes['mobile_verified']
            mobile_verified_str = mobile_verified[0] if isinstance(mobile_verified, list) else str(mobile_verified)
            return mobile_verified_str.lower() == 'true'
        
        # Fallback to legacy phone_verified keys for backward compatibility
        for key in ['phone_verified', 'phoneVerified']:
            if key in attributes:
                phone_verified = attributes[key]
                phone_verified_str = phone_verified[0] if isinstance(phone_verified, list) else str(phone_verified)
                return phone_verified_str.lower() == 'true'
        
        return False
    
    @classmethod
    def _extract_onboarding_complete(cls, keycloak_data: Dict[str, Any]) -> bool:
        """Extract onboarding completion status from Keycloak attributes."""
        attributes = keycloak_data.get('attributes', {})
        
        if 'is_onboarding_complete' in attributes:
            onboarding_complete = attributes['is_onboarding_complete']
            onboarding_complete_str = onboarding_complete[0] if isinstance(onboarding_complete, list) else str(onboarding_complete)
            return onboarding_complete_str.lower() == 'true'
        
        return False
    
    @classmethod
    def _extract_onboarding_step(cls, keycloak_data: Dict[str, Any]) -> str:
        """Extract current onboarding step from Keycloak attributes."""
        attributes = keycloak_data.get('attributes', {})
        
        if 'onboarding_step' in attributes:
            step = attributes['onboarding_step']
            return step[0] if isinstance(step, list) else str(step)
        
        return ''
    
    @classmethod
    def _extract_registration_method(cls, keycloak_data: Dict[str, Any]) -> str:
        """Extract registration method from Keycloak attributes."""
        attributes = keycloak_data.get('attributes', {})
        
        if 'registration_method' in attributes:
            method = attributes['registration_method']
            return method[0] if isinstance(method, list) else str(method)
        
        return ''
    
    @classmethod
    def _extract_social_provider(cls, keycloak_data: Dict[str, Any]) -> str:
        """Extract social provider from Keycloak attributes."""
        attributes = keycloak_data.get('attributes', {})
        
        if 'social_provider' in attributes:
            provider = attributes['social_provider']
            return provider[0] if isinstance(provider, list) else str(provider)
        
        return ''
    
    @classmethod
    def _get_cache_key(cls, keycloak_id: str) -> str:
        """Generate cache key for user data."""
        return f"{cls.CACHE_PREFIX}:{keycloak_id}"
    
    @classmethod
    def _get_current_timestamp(cls) -> str:
        """Get current timestamp for cache metadata."""
        from django.utils import timezone
        return timezone.now().isoformat()
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        try:
            # This is a simple implementation - Redis has more detailed stats
            return {
                'cache_backend': 'redis',
                'ttl_seconds': cls.CACHE_TTL,
                'prefix': cls.CACHE_PREFIX,
                'status': 'healthy'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }