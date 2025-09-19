"""
Keycloak Admin API integration for syncing user verification status
"""

import logging
import requests
from django.conf import settings
from typing import Dict, Optional, Any
import time
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class KeycloakAdminClient:
    """
    Keycloak Admin API client for managing user attributes and verification status
    """
    
    def __init__(self, realm: str = 'spoton-uat'):
        self.realm = realm
        # Always start with HTTPS URL, but allow fallback for UAT
        self.base_url = settings.KEYCLOAK_SERVER_URL  # Use HTTPS first
        self.fallback_url = None
        
        # Set fallback URL for UAT environment
        import os
        environment = os.environ.get('ENVIRONMENT', 'development').lower()
        if environment in ['uat', 'development']:
            self.fallback_url = 'http://core-keycloak:8080'
        
        # Use admin client credentials from settings
        self.admin_client_id = getattr(settings, 'KEYCLOAK_ADMIN_CLIENT_ID', 'admin-cli')
        self.admin_client_secret = getattr(settings, 'KEYCLOAK_ADMIN_CLIENT_SECRET', '')
        self.admin_username = getattr(settings, 'KEYCLOAK_ADMIN_USERNAME', 'admin')
        self.admin_password = getattr(settings, 'KEYCLOAK_ADMIN_PASSWORD', 'spoton_keycloak_admin_2024')
        self._access_token = None
        
    def get_admin_token(self) -> Optional[str]:
        """
        Get admin access token for Keycloak Admin API
        """
        try:
            # Try client credentials first (service account)
            if self.admin_client_secret:
                return self._get_token_via_client_credentials()
            
            # Fallback to password grant with admin user
            if self.admin_username and self.admin_password:
                return self._get_token_via_password()
                
            logger.error("No Keycloak admin credentials configured")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get Keycloak admin token: {e}")
            return None
    
    def _get_token_via_client_credentials(self) -> Optional[str]:
        """Get token using client credentials grant"""
        token_url = f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.admin_client_id,
            'client_secret': self.admin_client_secret
        }
        
        try:
            response = requests.post(
                token_url, 
                data=data, 
                timeout=10,
                verify=True  # Use proper SSL verification for production-like behavior
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"Failed to get admin token via client credentials: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error getting admin token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting admin token via client credentials: {e}")
            return None
    
    def _get_token_via_password(self) -> Optional[str]:
        """Get token using password grant (admin user)"""
        # Try HTTPS first
        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'password',
            'client_id': self.admin_client_id,
            'username': self.admin_username,
            'password': self.admin_password
        }
        
        try:
            response = requests.post(
                token_url, 
                data=data, 
                timeout=10,
                verify=True  # Use proper SSL verification for production-like behavior
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"Failed to get admin token via password (HTTPS): {response.status_code} - {response.text}")
                
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL error with HTTPS, trying fallback: {e}")
            
        except Exception as e:
            logger.error(f"Error getting admin token via password (HTTPS): {e}")
        
        # Try HTTP fallback if HTTPS failed and fallback URL is available
        if self.fallback_url:
            try:
                fallback_token_url = f"{self.fallback_url}/realms/master/protocol/openid-connect/token"
                response = requests.post(
                    fallback_token_url, 
                    data=data, 
                    timeout=10
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully obtained admin token using HTTP fallback")
                    # Switch to fallback URL for subsequent requests
                    self.base_url = self.fallback_url
                    return token_data.get('access_token')
                else:
                    logger.error(f"Failed to get admin token via password (HTTP fallback): {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"Error getting admin token via password (HTTP fallback): {e}")
        
        return None
    
    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find user in Keycloak by email address
        """
        token = self.get_admin_token()
        if not token:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Search for user by email
            search_url = f"{self.base_url}/admin/realms/{self.realm}/users"
            params = {'email': email, 'exact': 'true'}
            
            response = requests.get(
                search_url, 
                headers=headers, 
                params=params, 
                timeout=10,
                verify=True  # Use proper SSL verification for production-like behavior
            )
            
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
            else:
                logger.error(f"Failed to search user by email: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error searching user by email {email}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching user by email {email}: {e}")
            return None
    
    def update_user_attributes(self, user_id: str, attributes: Dict[str, Any]) -> bool:
        """
        Update user attributes in Keycloak
        """
        token = self.get_admin_token()
        if not token:
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get current user data
            user_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}"
            response = requests.get(user_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to get user {user_id}: {response.status_code}")
                return False
            
            user_data = response.json()
            
            # Update attributes
            current_attributes = user_data.get('attributes', {})
            current_attributes.update(attributes)
            
            # Update user
            update_data = {
                'attributes': current_attributes
            }
            
            response = requests.put(user_url, headers=headers, json=update_data, timeout=10)
            
            if response.status_code == 204:
                logger.info(f"Successfully updated attributes for user {user_id}")
                return True
            else:
                logger.error(f"Failed to update user attributes: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user attributes for {user_id}: {e}")
            return False
    
    def sync_mobile_verification(self, email: str, mobile: str, verified: bool = True) -> bool:
        """
        Sync mobile verification status to Keycloak user attributes
        """
        try:
            # Find user by email
            user = self.find_user_by_email(email)
            if not user:
                logger.warning(f"User not found in Keycloak: {email}")
                return False
            
            user_id = user['id']
            
            # Prepare attributes to update (normalized structure)
            # Normalize mobile number to international format
            from users.main_views import normalize_mobile
            normalized_mobile = normalize_mobile(mobile)
            
            attributes = {
                'mobile': [normalized_mobile],  # Normalized field name and format
                'mobile_verified': ['true' if verified else 'false'],
                'registration_method': ['email']  # Traditional registration via email
            }
            
            # Remove None values
            attributes = {k: v for k, v in attributes.items() if v is not None}
            
            # Update user attributes
            success = self.update_user_attributes(user_id, attributes)
            
            if success:
                logger.info(f"Mobile verification synced to Keycloak for {email}: {mobile} (verified: {verified})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing mobile verification for {email}: {e}")
            return False
    
    def sync_email_verification(self, email: str, verified: bool = True) -> bool:
        """
        Sync email verification status to Keycloak user attributes
        """
        try:
            # Find user by email
            user = self.find_user_by_email(email)
            if not user:
                logger.warning(f"User not found in Keycloak: {email}")
                return False
            
            user_id = user['id']
            
            # Prepare attributes to update
            attributes = {
                'email_verified': ['true' if verified else 'false'],
                'email_verified_at': [str(int(time.time()))] if verified else None
            }
            
            # Remove None values
            attributes = {k: v for k, v in attributes.items() if v is not None}
            
            # Update user attributes and emailVerified field
            user_data = {
                'emailVerified': verified,
                'attributes': attributes
            }
            
            token = self.get_admin_token()
            if not token:
                return False
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            user_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}"
            response = requests.put(user_url, headers=headers, json=user_data, timeout=10)
            
            if response.status_code == 204:
                logger.info(f"Email verification synced to Keycloak for {email} (verified: {verified})")
                return True
            else:
                logger.error(f"Failed to sync email verification: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error syncing email verification for {email}: {e}")
            return False


# Convenience functions for easy use
def sync_mobile_verification_to_keycloak(email: str, mobile: str, verified: bool = True) -> bool:
    """
    Convenience function to sync mobile verification status to Keycloak
    """
    client = KeycloakAdminClient()
    return client.sync_mobile_verification(email, mobile, verified)


def sync_email_verification_to_keycloak(email: str, verified: bool = True) -> bool:
    """
    Convenience function to sync email verification status to Keycloak
    """
    client = KeycloakAdminClient()
    return client.sync_email_verification(email, verified)


def find_keycloak_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find user in Keycloak by email
    """
    client = KeycloakAdminClient()
    return client.find_user_by_email(email) 