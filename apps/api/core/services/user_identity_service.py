"""
Centralized User Identity Management Service

This service ensures that user creation and lookup is consistent across all authentication flows.
It prevents duplicate users and maintains proper identity mapping between Keycloak and Django.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Q
from users.models import User, UserTenantRole, Tenant
from users.models import OnboardingProgress
from users.keycloak_user_service import KeycloakUserService
from users.services.user_cache_service import UserCacheService

logger = logging.getLogger(__name__)
User = get_user_model()


class UserIdentityService:
    """
    Centralized service for user identity management.
    
    This service provides a single point of truth for:
    - Finding existing users by email
    - Creating new users with proper deduplication
    - Linking Keycloak and Django users
    - Maintaining user identity consistency
    """
    
    def __init__(self, tenant: Tenant, environment: str = 'uat'):
        self.tenant = tenant
        self.environment = environment
        self.keycloak_service = KeycloakUserService(tenant=tenant, environment=environment)
    
    def find_user_by_email(self, email: str) -> Optional[User]:
        """
        Find existing user by email address using the email lookup table.
        
        This method uses a dedicated lookup table to efficiently find users by email
        without having to query Keycloak for every search.
        
        Args:
            email: Email address to search for
            
        Returns:
            User object if found, None otherwise
        """
        if not email:
            return None
            
        email = email.lower().strip()
        logger.info(f"[UserIdentityService] Searching for user with email: {email}")
        
        # First, check the email lookup table (most efficient)
        from django.db import connection
        cursor = connection.cursor()
        
        try:
            cursor.execute(
                "SELECT user_id FROM users_user_email_lookup WHERE email = %s LIMIT 1",
                [email]
            )
            row = cursor.fetchone()
            
            if row:
                user_id = row[0]
                logger.info(f"[UserIdentityService] Found user {user_id} in email lookup table")
                
                try:
                    django_user = User.objects.get(id=user_id)
                    logger.info(f"[UserIdentityService] Found existing Django user {django_user.id}")
                    return django_user
                except User.DoesNotExist:
                    logger.warning(f"[UserIdentityService] User {user_id} in lookup table but not in users table")
                    # Clean up stale lookup entry
                    cursor.execute("DELETE FROM users_user_email_lookup WHERE user_id = %s", [user_id])
                    
        except Exception as e:
            logger.warning(f"[UserIdentityService] Error checking email lookup table: {e}")
        
        # Fallback: search Keycloak directly (slower but comprehensive)
        try:
            keycloak_user = self.keycloak_service.get_user_by_email(email)
            if keycloak_user:
                keycloak_id = keycloak_user.get('id')
                logger.info(f"[UserIdentityService] Found Keycloak user {keycloak_id} for email {email}")
                
                # Try to find corresponding Django user
                try:
                    django_user = User.objects.get(id=keycloak_id)
                    logger.info(f"[UserIdentityService] Found existing Django user {django_user.id}")
                    
                    # Update the lookup table for future searches
                    self._update_email_lookup(email, keycloak_id)
                    
                    return django_user
                except User.DoesNotExist:
                    logger.info(f"[UserIdentityService] Keycloak user exists but no Django user found for {keycloak_id}")
                    return None
        except Exception as e:
            logger.warning(f"[UserIdentityService] Error searching Keycloak for {email}: {e}")
        
        logger.info(f"[UserIdentityService] No existing user found for email {email}")
        return None
    
    def find_or_create_user(
        self, 
        email: str, 
        keycloak_id: Optional[str] = None,
        user_data: Optional[Dict[str, Any]] = None,
        create_in_keycloak: bool = True,
        is_social_login: bool = False
    ) -> Tuple[User, bool]:
        """
        Find existing user or create new one with proper deduplication and reconciliation.
        
        This is the main method that should be used by all authentication flows
        to ensure consistent user identity management.
        
        Args:
            email: User's email address
            keycloak_id: Keycloak user ID if known
            user_data: Additional user data for creation
            create_in_keycloak: Whether to create user in Keycloak if not exists
            is_social_login: Flag for social login flow to trigger reconciliation
            
        Returns:
            Tuple of (User object, created_flag)
        """
        if not email:
            raise ValueError("Email is required for user identity management")
        
        email = email.lower().strip()
        user_data = user_data or {}
        
        logger.info(f"[UserIdentityService] find_or_create_user for email: {email}, keycloak_id: {keycloak_id}")
        
        # For social logins, Keycloak is the source of truth. Find the user there first.
        if is_social_login:
            keycloak_user = self.keycloak_service.get_user_by_email(email)
            if keycloak_user:
                actual_keycloak_id = keycloak_user['id']
                logger.info(f"[UserIdentityService] Social login: Found Keycloak user {actual_keycloak_id} for {email}")
                
                # Reconcile with Django user
                return self._reconcile_user(email, actual_keycloak_id, user_data)

        with transaction.atomic():
            # Step 1: Try to find existing user (for non-social flows)
            existing_user = self.find_user_by_email(email)
            if existing_user:
                logger.info(f"[UserIdentityService] Found existing user {existing_user.id} for email {email}")
                
                # Ensure onboarding progress exists for existing users
                self._ensure_onboarding_progress(existing_user)
                
                return existing_user, False
            
            # Step 2: No existing user found, create new one
            logger.info(f"[UserIdentityService] Creating new user for email: {email}")
            
            # If no keycloak_id provided, create user in Keycloak first
            if not keycloak_id and create_in_keycloak:
                try:
                    keycloak_user_data = {
                        'email': email,
                        'firstName': user_data.get('first_name', ''),
                        'lastName': user_data.get('last_name', ''),
                        'enabled': True,
                        'emailVerified': user_data.get('email_verified', False)
                    }
                    
                    # Add phone if provided
                    if user_data.get('phone') or user_data.get('mobile'):
                        mobile = user_data.get('mobile') or user_data.get('phone')  # Normalize to mobile
                        keycloak_user_data['attributes'] = {
                            'mobile': mobile,  # Use mobile as standard field
                            'mobile_verified': str(user_data.get('phone_verified', False)).lower()  # Normalize to mobile_verified
                        }
                    
                    keycloak_id = self.keycloak_service.create_user(
                        keycloak_user_data,
                        email_verified=user_data.get('email_verified', False),
                        mobile_verified=user_data.get('phone_verified', False)
                    )
                    
                    if not keycloak_id:
                        raise Exception("Failed to create user in Keycloak")
                    
                    logger.info(f"[UserIdentityService] Created Keycloak user with ID: {keycloak_id}")
                    
                except Exception as e:
                    logger.error(f"[UserIdentityService] Failed to create Keycloak user for {email}: {e}")
                    raise Exception(f"Failed to create user in identity provider: {e}")
            
            if not keycloak_id:
                raise ValueError("keycloak_id is required for Django user creation")
            
            # Step 3: Create Django user
            return self._create_django_user_and_related_data(email, keycloak_id, user_data)
    
    def _reconcile_user(self, email: str, actual_keycloak_id: str, user_data: Dict) -> Tuple[User, bool]:
        """
        Reconcile Django user with the authoritative Keycloak ID.
        Handles ID mismatches and merges duplicate records.
        """
        try:
            # Check if a Django user already exists with the correct Keycloak ID
            correct_user = User.objects.get(id=actual_keycloak_id)
            logger.info(f"[UserIdentityService] Found correct Django user {correct_user.id}")
            self._ensure_onboarding_progress(correct_user)
            self._update_email_lookup(email, actual_keycloak_id)
            return correct_user, False
        except User.DoesNotExist:
            # No user with the correct ID exists. Check for a user with the same email but wrong ID.
            wrong_user = User.objects.filter(
                usertenantrole__tenant=self.tenant,
                id__in=self._get_user_ids_from_lookup(email)
            ).exclude(id=actual_keycloak_id).first()
            
            if wrong_user:
                with transaction.atomic():
                    logger.warning(f"[UserIdentityService] Reconciling ID mismatch: Django={wrong_user.id}, Keycloak={actual_keycloak_id}")
                    
                    # Hard-update the ID of the existing Django user to match Keycloak
                    # This is a critical recovery operation that preserves related data.
                    from django.db import connection
                    cursor = connection.cursor()
                    
                    # Temporarily disable foreign key checks to allow ID update
                    # This is safe within this transaction
                    cursor.execute("SET CONSTRAINTS ALL DEFERRED")
                    
                    # Update the ID in the users table
                    cursor.execute(
                        "UPDATE users_user SET id = %s WHERE id = %s",
                        [actual_keycloak_id, wrong_user.id]
                    )
                    
                    logger.info(f"[UserIdentityService] Updated Django user ID from {wrong_user.id} to {actual_keycloak_id}")
                    
                    # Update the email lookup table
                    self._update_email_lookup(email, actual_keycloak_id)
                    
                    # Re-fetch the user with the new, correct ID
                    reconciled_user = User.objects.get(id=actual_keycloak_id)
                    self._ensure_onboarding_progress(reconciled_user)
                    
                    return reconciled_user, False
            else:
                # No Django user found, create a new one with the correct ID
                logger.info(f"[UserIdentityService] No Django user found for {email}, creating new one with ID {actual_keycloak_id}")
                return self._create_django_user_and_related_data(email, actual_keycloak_id, user_data)
    
    def _create_django_user_and_related_data(self, email: str, keycloak_id: str, user_data: Dict) -> Tuple[User, bool]:
        """Create Django user and all related data records."""
        try:
            with transaction.atomic():
                django_user = User(
                    id=keycloak_id,
                    is_active=user_data.get('is_active', True),
                    keycloak_client_id=f"customer-{self.environment}-portal",
                    preferred_tenant_slug=self.tenant.slug,
                )
                django_user.save()
                
                logger.info(f"[UserIdentityService] Created Django user {django_user.id} for email {email}")
                
                UserTenantRole.objects.get_or_create(
                    user=django_user,
                    tenant=self.tenant,
                    defaults={'role': 'customer'}
                )
                
                self._ensure_onboarding_progress(django_user)
                self._update_email_lookup(email, keycloak_id)
                
                return django_user, True
                
        except Exception as e:
            logger.error(f"[UserIdentityService] Failed to create Django user and related data: {e}")
            raise Exception(f"Failed to create user record: {e}")

    def _ensure_onboarding_progress(self, user: User):
        """Ensure an onboarding progress record exists for a user."""
        try:
            progress, created = OnboardingProgress.objects.get_or_create(
                user=user,
                defaults={
                    'current_step': '',
                    'step_data': {},
                    'is_completed': False
                }
            )
            if created:
                logger.info(f"[UserIdentityService] Created missing onboarding progress for user {user.id}")
        except Exception as e:
            logger.error(f"[UserIdentityService] Failed to ensure onboarding progress for user {user.id}: {e}")

    def _get_user_ids_from_lookup(self, email: str) -> list:
        """Get all user IDs associated with an email from the lookup table."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users_user_email_lookup WHERE email = %s", [email])
            return [row[0] for row in cursor.fetchall()]

    def merge_duplicate_users(self, primary_user_id: str, duplicate_user_ids: list) -> bool:
        """
        Merge duplicate user records into a single primary user.
        
        Args:
            primary_user_id: ID of the user to keep
            duplicate_user_ids: List of user IDs to merge into primary
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"[UserIdentityService] Merging users: keeping {primary_user_id}, merging {duplicate_user_ids}")
        
        try:
            with transaction.atomic():
                primary_user = User.objects.get(id=primary_user_id)
                
                for dup_id in duplicate_user_ids:
                    try:
                        dup_user = User.objects.get(id=dup_id)
                        
                        # Transfer related records
                        self._transfer_user_data(dup_user, primary_user)
                        
                        # Delete duplicate user
                        dup_user.delete()
                        logger.info(f"[UserIdentityService] Successfully merged and deleted user {dup_id}")
                        
                    except User.DoesNotExist:
                        logger.warning(f"[UserIdentityService] Duplicate user {dup_id} not found")
                        continue
                    except Exception as e:
                        logger.error(f"[UserIdentityService] Error merging user {dup_id}: {e}")
                        return False
                
                return True
                
        except Exception as e:
            logger.error(f"[UserIdentityService] Error in merge_duplicate_users: {e}")
            return False
    
    def _transfer_user_data(self, from_user: User, to_user: User):
        """Transfer all related data from one user to another."""
        from django.db import connection
        
        # Tables that reference users
        tables_to_transfer = [
            'web_support_onboardingprogress',
            'users_usertenantrole', 
            'users_useraccountrole',
            'core_userpreferences',
            'core_useronboardingconfirmation'
        ]
        
        cursor = connection.cursor()
        
        for table in tables_to_transfer:
            try:
                # Check if records exist
                cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE user_id = %s', [str(from_user.id)])
                from_count = cursor.fetchone()[0]
                
                if from_count > 0:
                    cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE user_id = %s', [str(to_user.id)])
                    to_count = cursor.fetchone()[0]
                    
                    if to_count == 0:
                        # Transfer records
                        cursor.execute(f'UPDATE {table} SET user_id = %s WHERE user_id = %s', [str(to_user.id), str(from_user.id)])
                        logger.info(f"[UserIdentityService] Transferred {from_count} records from {table}")
                    else:
                        # Delete duplicates
                        cursor.execute(f'DELETE FROM {table} WHERE user_id = %s', [str(from_user.id)])
                        logger.info(f"[UserIdentityService] Deleted {from_count} duplicate records from {table}")
                        
            except Exception as e:
                logger.error(f"[UserIdentityService] Error transferring data from {table}: {e}")
    
    def _update_email_lookup(self, email: str, user_id: str):
        """Update the email lookup table for a user."""
        from django.db import connection
        
        email = email.lower().strip()
        cursor = connection.cursor()
        
        try:
            # Use INSERT ... ON CONFLICT for PostgreSQL
            cursor.execute("""
                INSERT INTO users_user_email_lookup (email, user_id, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                ON CONFLICT (email) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    updated_at = NOW()
            """, [email, user_id])
            
            logger.info(f"[UserIdentityService] Updated email lookup: {email} -> {user_id}")
            
        except Exception as e:
            logger.error(f"[UserIdentityService] Error updating email lookup table: {e}")
    
    def _remove_email_lookup(self, email: str):
        """Remove an email from the lookup table."""
        from django.db import connection
        
        email = email.lower().strip()
        cursor = connection.cursor()
        
        try:
            cursor.execute("DELETE FROM users_user_email_lookup WHERE email = %s", [email])
            logger.info(f"[UserIdentityService] Removed email lookup: {email}")
        except Exception as e:
            logger.error(f"[UserIdentityService] Error removing email lookup: {e}")


# Convenience functions for backward compatibility
def find_or_create_user_by_email(email: str, tenant: Tenant, **kwargs) -> Tuple[User, bool]:
    """Convenience function for finding or creating users by email."""
    service = UserIdentityService(tenant=tenant)
    return service.find_or_create_user(email=email, user_data=kwargs)


def get_user_identity_service(tenant: Tenant, environment: str = 'uat') -> UserIdentityService:
    """Get a configured UserIdentityService instance."""
    return UserIdentityService(tenant=tenant, environment=environment)
