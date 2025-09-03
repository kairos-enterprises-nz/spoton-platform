"""
User Sync Service - Robust synchronization strategy for critical user flows

This service ensures that critical user operations have fresh, accurate data
by implementing multiple sync strategies based on operation criticality.
"""
import logging
import time
from typing import Dict, Optional, Any, Tuple
from django.core.cache import cache
from django.contrib.auth import get_user_model
from users.keycloak_user_service import KeycloakUserService
from users.services.user_cache_service import UserCacheService
from .user_identity_service import UserIdentityService

logger = logging.getLogger(__name__)
User = get_user_model()


class UserSyncService:
    """
    Manages user synchronization between Django and Keycloak with different
    strategies based on operation criticality.
    """
    
    # Critical operations that require real-time sync
    CRITICAL_OPERATIONS = {
        'phone_verification',
        'email_verification', 
        'profile_update',
        'payment_method_change',
        'permission_change',
        'password_change',
        'account_activation',
        'two_factor_setup'
    }
    
    # Semi-critical operations that need fresh data but can tolerate some staleness
    SEMI_CRITICAL_OPERATIONS = {
        'login',
        'onboarding_progress',
        'preference_update',
        'subscription_check'
    }
    
    def __init__(self, tenant, environment='uat'):
        self.tenant = tenant
        self.environment = environment
        self.keycloak_service = KeycloakUserService(tenant=tenant, environment=environment)
        self.identity_service = UserIdentityService(tenant=tenant, environment=environment)
    
    def sync_user_for_operation(
        self, 
        user_id: str, 
        operation: str, 
        force_sync: bool = False
    ) -> Tuple[Optional[Dict], bool]:
        """
        Sync user data based on operation criticality.
        
        Args:
            user_id: User ID to sync
            operation: Operation being performed
            force_sync: Force real-time sync regardless of operation type
            
        Returns:
            Tuple of (user_data, sync_successful)
        """
        sync_strategy = self._determine_sync_strategy(operation, force_sync)
        
        logger.info(f"[UserSync] Syncing user {user_id} for operation '{operation}' with strategy '{sync_strategy}'")
        
        try:
            if sync_strategy == 'real_time':
                return self._real_time_sync(user_id, operation)
            elif sync_strategy == 'fresh_preferred':
                return self._fresh_preferred_sync(user_id, operation)
            else:  # lazy
                return self._lazy_sync(user_id, operation)
                
        except Exception as e:
            logger.error(f"[UserSync] Sync failed for user {user_id}, operation {operation}: {e}")
            return self._fallback_sync(user_id, operation)
    
    def _determine_sync_strategy(self, operation: str, force_sync: bool) -> str:
        """Determine the appropriate sync strategy."""
        if force_sync or operation in self.CRITICAL_OPERATIONS:
            return 'real_time'
        elif operation in self.SEMI_CRITICAL_OPERATIONS:
            return 'fresh_preferred'
        else:
            return 'lazy'
    
    def _real_time_sync(self, user_id: str, operation: str) -> Tuple[Optional[Dict], bool]:
        """
        Real-time sync: Always fetch fresh data from Keycloak.
        Used for critical operations.
        """
        logger.info(f"[UserSync] Real-time sync for user {user_id}, operation {operation}")
        
        try:
            # Force fresh fetch from Keycloak
            UserCacheService.invalidate_user_cache(user_id)
            
            # Get fresh data
            keycloak_data = self._fetch_keycloak_data(user_id)
            
            if not keycloak_data:
                # User doesn't exist in Keycloak - attempt recovery
                logger.warning(f"[UserSync] User {user_id} not found in Keycloak, attempting recovery")
                return self._recover_missing_user(user_id, operation)
            
            # Update cache with fresh data
            UserCacheService._store_user_cache(user_id, keycloak_data)
            
            logger.info(f"[UserSync] Real-time sync successful for user {user_id}")
            return keycloak_data, True
            
        except Exception as e:
            logger.error(f"[UserSync] Real-time sync failed for user {user_id}: {e}")
            return self._fallback_sync(user_id, operation)
    
    def _fresh_preferred_sync(self, user_id: str, operation: str) -> Tuple[Optional[Dict], bool]:
        """
        Fresh-preferred sync: Try to get fresh data, fallback to cache if needed.
        Used for semi-critical operations.
        """
        logger.info(f"[UserSync] Fresh-preferred sync for user {user_id}, operation {operation}")
        
        try:
            # Try to get fresh data first
            keycloak_data = self._fetch_keycloak_data(user_id)
            
            if keycloak_data:
                # Update cache and return fresh data
                UserCacheService._store_user_cache(user_id, keycloak_data)
                return keycloak_data, True
            
            # Fall back to cached data
            logger.info(f"[UserSync] Fresh data unavailable, using cached data for user {user_id}")
            cached_data = UserCacheService._get_user_cache(user_id)
            return cached_data, cached_data is not None
            
        except Exception as e:
            logger.error(f"[UserSync] Fresh-preferred sync failed for user {user_id}: {e}")
            return self._fallback_sync(user_id, operation)
    
    def _lazy_sync(self, user_id: str, operation: str) -> Tuple[Optional[Dict], bool]:
        """
        Lazy sync: Use cached data if available, fetch if cache miss.
        Used for non-critical operations.
        """
        logger.info(f"[UserSync] Lazy sync for user {user_id}, operation {operation}")
        
        try:
            # Try cache first
            cached_data = UserCacheService._get_user_cache(user_id)
            
            if cached_data and not self._is_cache_stale(user_id):
                return cached_data, True
            
            # Cache miss or stale - fetch fresh data
            keycloak_data = self._fetch_keycloak_data(user_id)
            
            if keycloak_data:
                UserCacheService._store_user_cache(user_id, keycloak_data)
                return keycloak_data, True
            
            # Return stale cache if available
            if cached_data:
                logger.warning(f"[UserSync] Using stale cache for user {user_id}")
                return cached_data, False
            
            return None, False
            
        except Exception as e:
            logger.error(f"[UserSync] Lazy sync failed for user {user_id}: {e}")
            return self._fallback_sync(user_id, operation)
    
    def _recover_missing_user(self, user_id: str, operation: str) -> Tuple[Optional[Dict], bool]:
        """
        Recover a user that exists in Django but not in Keycloak.
        This handles the ID mismatch scenario.
        """
        logger.info(f"[UserSync] Attempting user recovery for {user_id}")
        
        try:
            # Get Django user
            django_user = User.objects.filter(id=user_id).first()
            if not django_user:
                logger.error(f"[UserSync] Django user {user_id} not found for recovery")
                return None, False
            
            # Find user in Keycloak by email
            email = self._get_user_email(user_id)
            if not email:
                logger.error(f"[UserSync] No email found for user {user_id}")
                return None, False
            
            # Search Keycloak by email
            admin_client = self.keycloak_service._get_keycloak_admin()
            users = admin_client.get_users({'email': email})
            
            if users:
                keycloak_user = users[0]
                actual_keycloak_id = keycloak_user.get('id')
                
                logger.info(f"[UserSync] Found Keycloak user {actual_keycloak_id} for email {email}")
                
                if actual_keycloak_id != user_id:
                    logger.warning(f"[UserSync] ID mismatch detected: Django={user_id}, Keycloak={actual_keycloak_id}")
                    # This would trigger a more comprehensive recovery process
                    # For now, return the Keycloak data
                    return keycloak_user, True
            
            logger.error(f"[UserSync] Could not recover user {user_id}")
            return None, False
            
        except Exception as e:
            logger.error(f"[UserSync] User recovery failed for {user_id}: {e}")
            return None, False
    
    def _fallback_sync(self, user_id: str, operation: str) -> Tuple[Optional[Dict], bool]:
        """
        Fallback sync strategy when primary sync fails.
        Returns any available data, even if stale.
        """
        logger.info(f"[UserSync] Fallback sync for user {user_id}, operation {operation}")
        
        try:
            # Try to get any cached data
            cached_data = UserCacheService._get_user_cache(user_id)
            if cached_data:
                logger.warning(f"[UserSync] Using fallback cached data for user {user_id}")
                return cached_data, False
            
            # Try to get Django user data as last resort
            django_user = User.objects.filter(id=user_id).first()
            if django_user:
                logger.warning(f"[UserSync] Using Django-only data for user {user_id}")
                return {
                    'id': str(django_user.id),
                    'username': self._get_user_email(user_id) or 'unknown',
                    'emailVerified': False,  # Conservative default
                    'attributes': {}
                }, False
            
            return None, False
            
        except Exception as e:
            logger.error(f"[UserSync] Fallback sync failed for user {user_id}: {e}")
            return None, False
    
    def _fetch_keycloak_data(self, user_id: str, retries: int = 3, delay: float = 0.5) -> Optional[Dict]:
        """
        Fetch user data from Keycloak with a retry mechanism for new users.
        This handles replication delays for newly created users.
        """
        attempt = 0
        while attempt < retries:
            try:
                admin_client = self.keycloak_service._get_keycloak_admin()
                user_data = admin_client.get_user(user_id)
                if user_data:
                    return user_data
                
                # If user not found, it could be a replication delay
                logger.warning(f"[UserSync] Attempt {attempt + 1}: User {user_id} not found, retrying in {delay}s...")
                
            except Exception as e:
                # Check for 404 specifically
                if "404" in str(e):
                    logger.warning(f"[UserSync] Attempt {attempt + 1}: User {user_id} not found (404), retrying in {delay}s...")
                else:
                    logger.error(f"[UserSync] Keycloak fetch failed for {user_id}: {e}")
                    # For non-404 errors, don't retry
                    return None
            
            time.sleep(delay)
            attempt += 1
            delay *= 2  # Exponential backoff
        
        logger.error(f"[UserSync] Failed to fetch user {user_id} from Keycloak after {retries} attempts.")
        return None
    
    def _is_cache_stale(self, user_id: str, max_age_seconds: int = 300) -> bool:
        """Check if cached data is stale (default: 5 minutes)."""
        cache_key = f"user_cache_timestamp:{user_id}"
        timestamp = cache.get(cache_key)
        
        if not timestamp:
            return True
        
        return (time.time() - timestamp) > max_age_seconds
    
    def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email from email lookup table."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT email FROM users_user_email_lookup WHERE user_id = %s',
                    [user_id]
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"[UserSync] Failed to get email for user {user_id}: {e}")
            return None
    
    def validate_user_sync_health(self, user_id: str) -> Dict[str, Any]:
        """
        Validate the sync health between Django and Keycloak for a user.
        Returns a health report.
        """
        health_report = {
            'user_id': user_id,
            'django_exists': False,
            'keycloak_exists': False,
            'ids_match': False,
            'email_lookup_exists': False,
            'sync_status': 'unknown',
            'recommendations': []
        }
        
        try:
            # Check Django user
            django_user = User.objects.filter(id=user_id).first()
            health_report['django_exists'] = django_user is not None
            
            # Check email lookup
            email = self._get_user_email(user_id)
            health_report['email_lookup_exists'] = email is not None
            
            # Check Keycloak user
            keycloak_data = self._fetch_keycloak_data(user_id)
            health_report['keycloak_exists'] = keycloak_data is not None
            
            # Check ID consistency
            if keycloak_data:
                health_report['ids_match'] = keycloak_data.get('id') == user_id
            
            # Determine sync status and recommendations
            if health_report['django_exists'] and health_report['keycloak_exists'] and health_report['ids_match']:
                health_report['sync_status'] = 'healthy'
            elif health_report['django_exists'] and not health_report['keycloak_exists']:
                health_report['sync_status'] = 'keycloak_missing'
                health_report['recommendations'].append('Recreate user in Keycloak')
            elif not health_report['django_exists'] and health_report['keycloak_exists']:
                health_report['sync_status'] = 'django_missing'
                health_report['recommendations'].append('Recreate user in Django')
            elif health_report['django_exists'] and health_report['keycloak_exists'] and not health_report['ids_match']:
                health_report['sync_status'] = 'id_mismatch'
                health_report['recommendations'].append('Fix ID synchronization')
            else:
                health_report['sync_status'] = 'broken'
                health_report['recommendations'].append('Full user recovery needed')
            
            return health_report
            
        except Exception as e:
            logger.error(f"[UserSync] Health check failed for user {user_id}: {e}")
            health_report['sync_status'] = 'error'
            health_report['error'] = str(e)
            return health_report
