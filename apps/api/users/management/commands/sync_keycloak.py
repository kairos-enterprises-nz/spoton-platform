import os
import logging
from django.core.management.base import BaseCommand
from users.keycloak_admin_sync import KeycloakAdminClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Synchronize Keycloak users with Django for current environment'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                           help='Run without making changes')

    def handle(self, *args, **options):
        # Determine environment by checking 'ENVIRONMENT' first, then 'DJANGO_ENV'
        environment = os.environ.get('ENVIRONMENT') or os.environ.get('DJANGO_ENV', 'development').lower()
        
        # Map detected environment to the Keycloak realm
        if environment == 'production' or environment == 'live':
            realm = 'spoton-prod'
        else: # 'development', 'uat', or any other default
            realm = 'spoton-uat'
        
        self.stdout.write(f"Starting Keycloak sync for {environment.upper()} environment (realm: {realm})")
        
        if options['dry_run']:
            self.stdout.write("Running in DRY-RUN mode")
        
        try:
            kc_client = KeycloakAdminClient(realm=realm)
            admin_token = kc_client.get_admin_token()
            
            if not admin_token:
                self.stderr.write("Failed to obtain Keycloak admin token. Check KEYCLOAK_ADMIN_CLIENT_ID and KEYCLOAK_ADMIN_CLIENT_SECRET settings.")
                return
            
            self.stdout.write(self.style.SUCCESS("Successfully obtained Keycloak admin token"))
            
            # Get all users from Keycloak
            users = self._get_keycloak_users(kc_client)
            if users is None:
                self.stderr.write("Failed to retrieve users from Keycloak")
                return
            
            self.stdout.write(f"Found {len(users)} users in Keycloak realm '{realm}'")
            
            if options['dry_run']:
                self.stdout.write("DRY-RUN: Would sync the following users:")
                for user in users:
                    email = user.get('email', 'No email')
                    username = user.get('username', 'No username')
                    self.stdout.write(f"  - {email} ({username})")
            else:
                # Perform actual sync
                synced_count = self._sync_users(users, realm)
                self.stdout.write(self.style.SUCCESS(f"Successfully synced {synced_count} users"))
                
        except Exception as e:
            self.stderr.write(f"Unexpected error during sync: {e}")
            logger.exception("Keycloak sync failed")
    
    def _get_keycloak_users(self, kc_client):
        """Get all users from Keycloak"""
        try:
            token = kc_client.get_admin_token()
            if not token:
                return None
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            import requests
            users_url = f"{kc_client.base_url}/admin/realms/{kc_client.realm}/users"
            response = requests.get(
                users_url, 
                headers=headers, 
                timeout=30,
                verify=False  # Bypass SSL verification for development
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get users: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Keycloak users: {e}")
            return None
    
    def _sync_users(self, users, realm):
        """Sync users from Keycloak to Django"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        synced_count = 0
        
        for kc_user in users:
            try:
                email = kc_user.get('email')
                if not email:
                    continue
                
                username = kc_user.get('username', email)
                first_name = kc_user.get('firstName', '')
                last_name = kc_user.get('lastName', '')
                keycloak_id = kc_user.get('id')
                
                # Create or update Django user
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'keycloak_id': keycloak_id,
                        'is_active': kc_user.get('enabled', True),
                        'email_verified': kc_user.get('emailVerified', False)
                    }
                )
                
                if not created:
                    # Update existing user
                    user.first_name = first_name
                    user.last_name = last_name
                    user.keycloak_id = keycloak_id
                    user.is_active = kc_user.get('enabled', True)
                    user.email_verified = kc_user.get('emailVerified', False)
                    
                    # Update phone and verification from Keycloak attributes
                    attributes = kc_user.get('attributes', {})
                    if 'mobile_number' in attributes:
                        user.phone = attributes['mobile_number'][0]
                    if 'mobile_verified' in attributes:
                        user.phone_verified = attributes['mobile_verified'][0].lower() == 'true'
                    
                    user.save()
                
                synced_count += 1
                self.stdout.write(f"{'Created' if created else 'Updated'} user: {email}")
                
            except Exception as e:
                logger.error(f"Error syncing user {kc_user.get('email', 'unknown')}: {e}")
                continue
        
        return synced_count 