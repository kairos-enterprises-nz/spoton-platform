import logging
import requests
from django.conf import settings
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

logger = logging.getLogger(__name__)

class KeycloakAdminService:
    """
    Service for interacting with Keycloak Admin API to manage users.
    
    This service handles:
    - Creating users in Keycloak
    - Updating user attributes
    - Setting email verification status
    - Setting phone verification status
    - Managing roles and groups
    """
    
    def __init__(self, realm=None):
        """Initialize Keycloak Admin client for the specified realm"""
        # Prefer new consolidated KEYCLOAK_CONFIG; fall back to legacy settings if present
        kc = getattr(settings, 'KEYCLOAK_CONFIG', {})
        self.realm = realm or kc.get('REALM') or getattr(settings, 'KEYCLOAK_REALM', None)
        if not self.realm:
            # Sensible default for UAT
            self.realm = 'spoton-uat'
        self.server_url = kc.get('SERVER_URL') or getattr(settings, 'KEYCLOAK_SERVER_URL', None) or 'https://auth.spoton.co.nz'
        # Admin auth can be via client credentials or username/password
        self.client_id = kc.get('ADMIN_CLIENT_ID') or getattr(settings, 'KEYCLOAK_ADMIN_CLIENT_ID', None) or 'admin-cli'
        self.client_secret = kc.get('ADMIN_CLIENT_SECRET') or getattr(settings, 'KEYCLOAK_ADMIN_CLIENT_SECRET', None)
        self.admin_username = kc.get('ADMIN_USERNAME') or getattr(settings, 'KEYCLOAK_ADMIN_USERNAME', None)
        self.admin_password = kc.get('ADMIN_PASSWORD') or getattr(settings, 'KEYCLOAK_ADMIN_PASSWORD', None)
        self.admin_client = None
        
    def _get_admin_client(self):
        """Get or create Keycloak Admin client"""
        if not self.admin_client:
            try:
                if self.client_secret:
                    # Client credentials flow
                    self.admin_client = KeycloakAdmin(
                        server_url=self.server_url,
                        realm_name=self.realm,
                        client_id=self.client_id,
                        client_secret_key=self.client_secret,
                        verify=True
                    )
                elif self.admin_username and self.admin_password:
                    # Username/password (admin) flow authenticates against master realm
                    self.admin_client = KeycloakAdmin(
                        server_url=self.server_url,
                        realm_name='master',
                        username=self.admin_username,
                        password=self.admin_password,
                        verify=True
                    )
                else:
                    raise KeycloakError(error_message='Missing admin credentials for KeycloakAdminService')
            except KeycloakError as e:
                logger.error(f"Failed to initialize Keycloak Admin client: {e}")
                raise
                
        return self.admin_client
    
    def create_user(self, email, first_name=None, last_name=None, phone=None, 
                   email_verified=False, phone_verified=False, enabled=True, 
                   username=None, temporary_password=None):
        """
        Create a new user in Keycloak
        
        Args:
            email (str): User's email address
            first_name (str, optional): User's first name
            last_name (str, optional): User's last name
            phone (str, optional): User's phone number
            email_verified (bool, optional): Email verification status
            phone_verified (bool, optional): Phone verification status
            enabled (bool, optional): Account enabled status
            username (str, optional): Username (defaults to email if not provided)
            temporary_password (str, optional): Temporary password for the user
            
        Returns:
            str: Keycloak user ID (sub) if successful, None otherwise
        """
        try:
            admin = self._get_admin_client()
            
            # Prepare user data
            user_data = {
                "email": email,
                "username": username or email,
                "emailVerified": email_verified,
                "enabled": enabled,
                "attributes": {
                    "phone": phone,
                    "phone_verified": str(phone_verified).lower(),
                    "is_onboarding_complete": "false",
                    "onboarding_step": ""
                }
            }
            
            if first_name:
                user_data["firstName"] = first_name
                
            if last_name:
                user_data["lastName"] = last_name
            
            # Create user
            user_id = admin.create_user(user_data)
            
            # Set temporary password if provided
            if temporary_password:
                admin.set_user_password(user_id, temporary_password, temporary=True)
            
            logger.info(f"Created Keycloak user with ID {user_id}")
            return user_id
            
        except KeycloakError as e:
            logger.error(f"Failed to create Keycloak user: {e}")
            return None
    
    def find_user_by_email(self, email):
        """
        Find a user by email address
        
        Args:
            email (str): Email address to search for
            
        Returns:
            dict: User data if found, None otherwise
        """
        try:
            admin = self._get_admin_client()
            users = admin.get_users({"email": email})
            
            if users and len(users) > 0:
                return users[0]
            
            return None
            
        except KeycloakError as e:
            logger.error(f"Failed to find Keycloak user by email: {e}")
            return None
    
    def update_user(self, user_id, **kwargs):
        """
        Update user attributes
        
        Args:
            user_id (str): Keycloak user ID
            **kwargs: Attributes to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            admin = self._get_admin_client()
            
            # Get current user data
            user_data = admin.get_user(user_id)
            
            # Update fields
            if 'email' in kwargs:
                user_data['email'] = kwargs['email']
                
            if 'first_name' in kwargs:
                user_data['firstName'] = kwargs['first_name']
                
            if 'last_name' in kwargs:
                user_data['lastName'] = kwargs['last_name']
                
            if 'email_verified' in kwargs:
                user_data['emailVerified'] = kwargs['email_verified']
                
            if 'enabled' in kwargs:
                user_data['enabled'] = kwargs['enabled']
            
            # Update attributes
            attributes = user_data.get('attributes', {})
            
            if 'phone' in kwargs:
                # Canonical write: only 'phone' (E.164)
                attributes['phone'] = kwargs['phone']
                
            if 'phone_verified' in kwargs:
                # Canonical write: only snake_case
                attributes['phone_verified'] = str(kwargs['phone_verified']).lower()
                
            if 'is_onboarding_complete' in kwargs:
                # Onboarding completion status
                attributes['is_onboarding_complete'] = str(kwargs['is_onboarding_complete']).lower()
                
            if 'onboarding_step' in kwargs:
                # Current onboarding step
                attributes['onboarding_step'] = str(kwargs['onboarding_step'])
            
            user_data['attributes'] = attributes
            
            # Update user
            admin.update_user(user_id, user_data)
            
            logger.info(f"Updated Keycloak user {user_id}")
            return True
            
        except KeycloakError as e:
            logger.error(f"Failed to update Keycloak user: {e}")
            return False
    
    def set_email_verified(self, user_id, verified=True):
        """Set email verification status"""
        return self.update_user(user_id, email_verified=verified)
    
    def set_phone_verified(self, user_id, verified=True):
        """Set phone verification status"""
        return self.update_user(user_id, phone_verified=verified)
    
    def set_onboarding_complete(self, user_id, complete=True, step='completed'):
        """Set onboarding completion status"""
        return self.update_user(user_id, is_onboarding_complete=complete, onboarding_step=step)
    
    def update_onboarding_step(self, user_id, step):
        """Update current onboarding step"""
        return self.update_user(user_id, onboarding_step=step)
    
    def add_user_to_group(self, user_id, group_name):
        """Add user to a group"""
        try:
            admin = self._get_admin_client()
            
            # Find group by name
            groups = admin.get_groups({"search": group_name})
            
            if not groups:
                logger.error(f"Group {group_name} not found")
                return False
            
            group_id = groups[0]['id']
            
            # Add user to group
            admin.group_user_add(user_id, group_id)
            
            logger.info(f"Added user {user_id} to group {group_name}")
            return True
            
        except KeycloakError as e:
            logger.error(f"Failed to add user to group: {e}")
            return False
    
    def assign_realm_role(self, user_id, role_name):
        """Assign a realm role to a user"""
        try:
            admin = self._get_admin_client()
            
            # Find role by name
            role = admin.get_realm_role(role_name)
            
            if not role:
                logger.error(f"Role {role_name} not found")
                return False
            
            # Assign role to user
            admin.assign_realm_roles(user_id, [role])
            
            logger.info(f"Assigned role {role_name} to user {user_id}")
            return True
            
        except KeycloakError as e:
            logger.error(f"Failed to assign role: {e}")
            return False 