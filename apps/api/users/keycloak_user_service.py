"""
Keycloak User Service - Centralized service for all Keycloak user operations
This is the single point of interaction with Keycloak for user management.
"""
import logging
import time
from typing import Dict, List, Optional, Any
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from keycloak.exceptions import KeycloakError, KeycloakConnectionError
from django.contrib.auth import get_user_model
from .models import Tenant, UserTenantRole

logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakUserService:
    """
    Centralized service for all Keycloak user operations.
    This service implements the Keycloak-first architecture where Keycloak is the single source of truth.
    """
    
    def __init__(self, tenant: Tenant, environment: str = 'uat'):
        self.tenant = tenant
        self.environment = environment
        self.keycloak_config = tenant.get_keycloak_config(environment)
        self._keycloak_admin = None
    
    def _get_keycloak_admin(self):
        """
        Get Keycloak admin client using python-keycloak with HTTP fallback for SSL issues
        """
        import os
        import requests
        from keycloak.exceptions import KeycloakConnectionError
        
        # Determine fallback URL for UAT environment
        environment = os.environ.get('ENVIRONMENT', 'development').lower()
        fallback_url = None
        if environment in ['uat', 'development']:
            fallback_url = 'http://core-keycloak:8080'
        
        # First try HTTPS
        try:
            logger.debug(f"[KeycloakUserService] Attempting HTTPS connection to {self.keycloak_config['url']}")
            connection = KeycloakOpenIDConnection(
                server_url=self.keycloak_config['url'],
                username=self.keycloak_config.get('admin_username'),
                password=self.keycloak_config.get('admin_password'),
                realm_name='master',  # Authenticate against master realm
                client_id=self.keycloak_config.get('admin_client_id', 'admin-cli'),
                client_secret_key=self.keycloak_config.get('admin_client_secret'),
                verify=True
            )
            keycloak_admin = KeycloakAdmin(connection=connection)
            
            # Switch to tenant-specific realm for operations
            keycloak_admin.realm_name = self.keycloak_config['realm']
            
            # Test the connection by attempting to get a token
            try:
                keycloak_admin.connection.token
                logger.debug(f"[KeycloakUserService] HTTPS connection successful, operating on realm: {self.keycloak_config['realm']}")
                return keycloak_admin
            except Exception as token_error:
                logger.warning(f"[KeycloakUserService] HTTPS token test failed: {token_error}")
                raise token_error
                
        except Exception as https_error:
            logger.warning(f"[KeycloakUserService] HTTPS connection failed: {https_error}")
            
            # Check if it's an SSL-related error and we have a fallback URL
            error_str = str(https_error).lower()
            is_ssl_error = any(ssl_term in error_str for ssl_term in [
                'ssl', 'handshake', 'certificate', 'tls', 'sslv3_alert'
            ])
            
            if is_ssl_error and fallback_url:
                logger.warning(f"[KeycloakUserService] SSL error detected, trying HTTP fallback: {fallback_url}")
                try:
                    # Try HTTP fallback
                    connection = KeycloakOpenIDConnection(
                        server_url=fallback_url,
                        username=self.keycloak_config.get('admin_username'),
                        password=self.keycloak_config.get('admin_password'),
                        realm_name='master',  # Authenticate against master realm
                        client_id=self.keycloak_config.get('admin_client_id', 'admin-cli'),
                        client_secret_key=self.keycloak_config.get('admin_client_secret'),
                        verify=False  # No SSL verification for HTTP
                    )
                    keycloak_admin = KeycloakAdmin(connection=connection)
                    
                    # Switch to tenant-specific realm for operations
                    keycloak_admin.realm_name = self.keycloak_config['realm']
                    
                    # Test the HTTP connection
                    try:
                        keycloak_admin.connection.token
                        logger.info(f"[KeycloakUserService] Successfully connected using HTTP fallback, operating on realm: {self.keycloak_config['realm']}")
                        return keycloak_admin
                    except Exception as fallback_token_error:
                        logger.error(f"[KeycloakUserService] HTTP fallback token test failed: {fallback_token_error}")
                        raise fallback_token_error
                        
                except Exception as fallback_error:
                    logger.error(f"[KeycloakUserService] HTTP fallback failed: {fallback_error}")
                    raise Exception(f"Failed to get Keycloak admin client: HTTPS failed ({https_error}), HTTP fallback failed ({fallback_error})")
            else:
                # Re-raise the original error if it's not SSL-related or no fallback available
                raise Exception(f"Failed to get Keycloak admin client: {str(https_error)}")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user from Keycloak by email address.
        Returns None if user not found.
        """
        try:
            keycloak_admin = self._get_keycloak_admin()
            # Switch to the correct customer realm
            keycloak_admin.realm_name = self.keycloak_config['realm']
            
            # Search for user by email
            users = keycloak_admin.get_users({"email": email, "exact": True})
            
            if users:
                logger.info(f"[KeycloakUserService] Found user in Keycloak: {email}")
                return users[0]
            else:
                logger.info(f"[KeycloakUserService] User not found in Keycloak: {email}")
                return None
                
        except Exception as e:
            logger.error(f"[KeycloakUserService] Error searching for user {email}: {e}")
            return None

    def create_user(self, user_data: Dict[str, Any], email_verified: bool = False, mobile_verified: bool = False) -> Optional[str]:
        """
        Create a new user in Keycloak.
        Returns the Keycloak user ID if successful, None otherwise.
        """
        try:
            keycloak_admin = self._get_keycloak_admin()
            # Switch to the correct customer realm
            keycloak_admin.realm_name = self.keycloak_config['realm']
            
            # Prepare user data for Keycloak
            keycloak_user_data = {
                "email": user_data['email'],
                "username": user_data.get('username', user_data['email']),  # Use email as username if not provided
                "firstName": user_data.get('firstName', ''),
                "lastName": user_data.get('lastName', ''),
                "enabled": True,
                "emailVerified": email_verified,
                "attributes": {}
            }
            
            # Set registration method for traditional users (email-based registration)
            keycloak_user_data["attributes"]["registration_method"] = ["email"]
            
            # Add mobile to attributes if provided
            if user_data.get('mobile'):
                # Normalize mobile number to international format
                from users.main_views import normalize_mobile
                normalized_mobile = normalize_mobile(user_data['mobile'])
                # Use mobile as standard field name - no duplication
                keycloak_user_data["attributes"]["mobile"] = [normalized_mobile]
                keycloak_user_data["attributes"]["mobile_verified"] = [str(mobile_verified).lower()]
                # DO NOT create phone_verified - causes duplication
            
            # Create user in Keycloak
            user_id = keycloak_admin.create_user(keycloak_user_data)
            logger.info(f"[KeycloakUserService] Created user in Keycloak: {user_data['email']} -> {user_id}")
            
            # Set password if provided
            if user_data.get('password'):
                try:
                    keycloak_admin.set_user_password(
                        user_id=user_id, 
                        password=user_data['password'], 
                        temporary=False
                    )
                    logger.info(f"[KeycloakUserService] Set password for user: {user_data['email']}")
                except Exception as password_error:
                    logger.error(f"[KeycloakUserService] Failed to set password for {user_data['email']}: {password_error}")
                    # Don't fail the entire user creation if password setting fails
            
            return user_id
            
        except Exception as e:
            logger.error(f"[KeycloakUserService] Error creating user {user_data['email']}: {e}")
            return None

    def update_user_attributes(self, keycloak_id: str, attributes: Dict[str, Any]) -> bool:
        """
        Update user attributes in Keycloak.
        Returns True if successful, False otherwise.
        """
        try:
            keycloak_admin = self._get_keycloak_admin()
            # Switch to the correct customer realm
            keycloak_admin.realm_name = self.keycloak_config['realm']
            
            # Get current user data
            user_data = keycloak_admin.get_user(keycloak_id)
            if not user_data:
                logger.error(f"[KeycloakUserService] User not found for attribute update: {keycloak_id}")
                return False
            
            # Update attributes
            current_attributes = user_data.get('attributes', {})
            current_attributes.update(attributes)
            
            # Update user
            keycloak_admin.update_user(keycloak_id, {"attributes": current_attributes})
            logger.info(f"[KeycloakUserService] Updated user attributes: {keycloak_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"[KeycloakUserService] Error updating user attributes {keycloak_id}: {e}")
            return False

    def get_user_by_id(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user from Keycloak by keycloak ID.
        Returns None if user not found.
        """
        try:
            keycloak_admin = self._get_keycloak_admin()
            # Switch to the correct customer realm
            keycloak_admin.realm_name = self.keycloak_config['realm']
            
            # Get user by ID
            user_data = keycloak_admin.get_user(keycloak_id)
            
            if user_data:
                logger.info(f"[KeycloakUserService] Found user in Keycloak by ID: {keycloak_id}")
                return user_data
            else:
                logger.warning(f"[KeycloakUserService] User not found in Keycloak by ID: {keycloak_id}")
                return None
                
        except Exception as e:
            logger.error(f"[KeycloakUserService] Error getting user by ID {keycloak_id}: {e}")
            return None

    def sync_user_to_django(self, keycloak_user: Dict[str, Any]) -> User:
        """
        Sync a Keycloak user to Django User model.
        Creates or updates the Django user based on Keycloak data.
        """
        keycloak_id = keycloak_user['id']
        email = keycloak_user['email']
        
        try:
            # Try to find existing user by ID (single ID architecture: id IS the Keycloak ID)
            django_user = User.objects.get(id=keycloak_id)
            logger.info(f"[KeycloakUserService] Found existing Django user: {email}")
            
        except User.DoesNotExist:
            # Create new Django user with tenant context
            django_user = User.objects.create_user(
                keycloak_id=keycloak_id  # This sets id=keycloak_id in single ID architecture
            )
            # Set additional fields after creation
            django_user.keycloak_client_id = f"customer-{self.environment}-portal"
            django_user.preferred_tenant_slug = self.tenant.slug
            django_user.save()
            logger.info(f"[KeycloakUserService] Created new Django user: {email} with tenant context")
            
            # Create UserTenantRole relationship
            UserTenantRole.objects.get_or_create(
                user=django_user,
                tenant=self.tenant,
                defaults={'role': 'customer'}
            )
        
        # Sync data from Keycloak
        django_user.sync_from_keycloak(keycloak_user)
        
        # Ensure tenant fields are set for existing users too
        updated_fields = []
        if not django_user.keycloak_client_id:
            django_user.keycloak_client_id = f"customer-{self.environment}-portal"
            updated_fields.append('keycloak_client_id')
        if not django_user.preferred_tenant_slug:
            django_user.preferred_tenant_slug = self.tenant.slug
            updated_fields.append('preferred_tenant_slug')
        
        if updated_fields:
            django_user.save(update_fields=updated_fields + ['updated_at'])
            logger.info(f"[KeycloakUserService] Updated tenant fields for {email}: {updated_fields}")
        
        return django_user

    def create_or_sync_user(self, user_data: Dict[str, Any], email_verified: bool = False, mobile_verified: bool = False) -> User:
        """
        Create or sync user using Keycloak-first approach.
        
        1. Check if user exists in Keycloak by email
        2. If not, create user in Keycloak
        3. Sync/create Django user from Keycloak data
        """
        email = user_data['email']
        
        # Check if user already exists in Keycloak
        keycloak_user = self.get_user_by_email(email)
        
        if not keycloak_user:
            # Create new user in Keycloak
            keycloak_id = self.create_user(user_data, email_verified, mobile_verified)
            if not keycloak_id:
                raise Exception("Failed to create user in Keycloak")
            
            # Fetch the created user data
            keycloak_user = self.get_user_by_email(email)
            if not keycloak_user:
                raise Exception("Failed to fetch created user from Keycloak")
        
        # Sync to Django
        try:
            django_user = self.sync_user_to_django(keycloak_user)
            return django_user
        except Exception as e:
            raise Exception(f"Failed to sync user to Django: {e}") 