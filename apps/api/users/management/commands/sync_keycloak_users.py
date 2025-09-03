from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from users.models import Tenant
from users.keycloak_user_service import KeycloakUserService
from users.models import OnboardingProgress
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Synchronize existing Keycloak users with Django'

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
            # Initialize Keycloak Admin client
            keycloak_admin = KeycloakAdmin(
                server_url='https://auth.spoton.co.nz',
                realm_name='master',  # Use master realm for admin operations
                username='admin',     # Should be from environment variables
                password='admin',     # Should be from environment variables
                verify=False          # For development - should be True in production
            )
            
            # Switch to target realm
            keycloak_admin.realm_name = realm
            
            # Get all users from Keycloak
            keycloak_users = keycloak_admin.get_users()
            
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
            
        except KeycloakError as e:
            self.stdout.write(self.style.ERROR(f"Keycloak error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {e}"))

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
            # In single ID architecture, id IS the keycloak_id
            django_user = User.objects.get(id=keycloak_id)
        except User.DoesNotExist:
            # Since we removed email field from User model, we can't look up by email
            # All users must be created with their keycloak_id as the primary key
            created = True
            django_user = None
        
        # Prepare user data (cleaned User model - no email, first_name, etc.)
        user_data = {
            'id': keycloak_id,  # Single ID architecture
            'preferred_tenant_slug': tenant.slug if tenant else 'spoton',
            'is_active': kc_user.get('enabled', True),
        }
        
        # Note: Custom attributes like phone are now stored in Keycloak only
        # The cleaned User model doesn't have phone fields - data comes from cache service
        
        if dry_run:
            action = "CREATE" if created else "UPDATE"
            self.stdout.write(f"{action}: {email} -> {user_data}")
            return 'created' if created else 'updated'
        
        # Create or update user
        if created:
            # Create minimal Django user with single ID architecture
            django_user = User.objects.create(
                id=keycloak_id,  # Single ID architecture - id IS the keycloak_id
                is_active=user_data.get('is_active', True),
                preferred_tenant_slug=user_data.get('preferred_tenant_slug'),
            )
            
            # Create onboarding progress for new user
            try:
                OnboardingProgress.objects.get_or_create(
                    user=django_user,
                    defaults={
                        'current_step': '',
                        'step_data': {},
                        'is_completed': False
                    }
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not create onboarding progress for {email}: {e}"))
            
            self.stdout.write(f"Created user: {email} (keycloak_id: {keycloak_id})")
            return 'created'
        else:
            # Update existing user (minimal fields only)
            django_user.is_active = user_data.get('is_active', True)
            django_user.preferred_tenant_slug = user_data.get('preferred_tenant_slug')
            django_user.save()
            self.stdout.write(f"Updated user: {email} (keycloak_id: {keycloak_id})")
            return 'updated' 