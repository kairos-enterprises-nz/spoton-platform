from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Tenant
import requests
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Synchronize existing Keycloak users with Django using HTTP requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--realm',
            type=str,
            default='spoton-uat',
            help='Keycloak realm to sync from (default: spoton-uat)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes'
        )

    def handle(self, *args, **options):
        realm = options['realm']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Syncing users from Keycloak realm: {realm}")
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
        
        try:
            # Get admin token
            admin_token = self.get_admin_token()
            if not admin_token:
                self.stdout.write(self.style.ERROR("Failed to get admin token"))
                return
            
            # Get all users from Keycloak
            keycloak_users = self.get_keycloak_users(realm, admin_token)
            
            self.stdout.write(f"Found {len(keycloak_users)} users in Keycloak realm '{realm}'")
            
            synced = 0
            created = 0
            updated = 0
            errors = 0
            
            for kc_user in keycloak_users:
                try:
                    result = self.sync_user(kc_user, realm, dry_run)
                    if result == 'created':
                        created += 1
                    elif result == 'updated':
                        updated += 1
                    synced += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error syncing user {kc_user.get('email', 'unknown')}: {e}")
                    )
                    errors += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sync complete: {synced} users processed, {created} created, {updated} updated, {errors} errors"
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {e}"))

    def get_admin_token(self):
        """Get admin token using direct HTTP request"""
        try:
            token_url = "https://auth.spoton.co.nz/realms/master/protocol/openid-connect/token"
            
            data = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': 'admin',  # Should be from environment
                'password': 'admin',  # Should be from environment
            }
            
            response = requests.post(token_url, data=data, verify=False, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to get admin token: {e}"))
            return None

    def get_keycloak_users(self, realm, admin_token):
        """Get all users from Keycloak realm"""
        try:
            users_url = f"https://auth.spoton.co.nz/admin/realms/{realm}/users"
            
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(users_url, headers=headers, verify=False, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to get users from Keycloak: {e}"))
            return []

    def sync_user(self, kc_user, realm, dry_run=False):
        """Sync a single Keycloak user to Django"""
        keycloak_id = kc_user.get('id')
        email = kc_user.get('email')
        
        if not keycloak_id or not email:
            raise ValueError(f"Missing keycloak_id or email in user data")
        
        # Get tenant based on realm/client context
        tenant = None
        try:
            tenant = Tenant.objects.get(is_primary_brand=True)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.WARNING("No primary tenant found, using None"))
        
        # Check if user already exists
        django_user = None
        created = False
        
        try:
            django_user = User.objects.get(id=keycloak_id)
        except User.DoesNotExist:
            try:
                django_user = User.objects.get(email=email)
                # Link existing user to Keycloak
                if not dry_run:
                    django_user.keycloak_id = keycloak_id
            except User.DoesNotExist:
                created = True
        
        # Prepare user data
        user_data = {
            'email': email,
            'username': kc_user.get('username', email),
            'first_name': kc_user.get('firstName', ''),
            'last_name': kc_user.get('lastName', ''),
            'keycloak_id': keycloak_id,
            'preferred_tenant_slug': tenant.slug if tenant else 'spoton',
            'email_verified': kc_user.get('emailVerified', False),
            'is_active': kc_user.get('enabled', True),
        }
        
        # Handle custom attributes
        attributes = kc_user.get('attributes', {})
        if 'phone_number' in attributes:
            phone_numbers = attributes['phone_number']
            if phone_numbers and len(phone_numbers) > 0:
                user_data['phone'] = phone_numbers[0]
        
        if 'phone_verified' in attributes:
            phone_verified = attributes['phone_verified']
            if phone_verified and len(phone_verified) > 0:
                user_data['phone_verified'] = phone_verified[0].lower() == 'true'
        
        if dry_run:
            action = "CREATE" if created else "UPDATE"
            self.stdout.write(f"{action}: {email} -> {user_data}")
            return 'created' if created else 'updated'
        
        # Create or update user
        if created:
            # Use strict allowlist to avoid legacy kwargs during bulk syncs
            allowed_keys = {'email','username','first_name','last_name','phone','phone_verified','email_verified','is_active','keycloak_id'}
            sanitized = {k: v for k, v in user_data.items() if k in allowed_keys}
            django_user = User.objects.create(**sanitized)
            self.stdout.write(f"Created user: {email}")
            return 'created'
        else:
            # Update existing user
            for key, value in user_data.items():
                if hasattr(django_user, key) and value is not None:
                    setattr(django_user, key, value)
            django_user.save()
            self.stdout.write(f"Updated user: {email}")
            return 'updated' 