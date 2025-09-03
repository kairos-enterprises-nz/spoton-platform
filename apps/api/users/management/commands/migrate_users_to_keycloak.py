from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.keycloak_admin import KeycloakAdminService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Migrate existing users to Keycloak'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--realm',
            type=str,
            default='spoton-uat',
            help='Keycloak realm to migrate users to'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of users to process at once'
        )
    
    def handle(self, *args, **options):
        realm = options['realm']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting user migration to Keycloak realm: {realm}')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get users without Keycloak ID
        users_to_migrate = User.objects.filter(keycloak_id__isnull=True)
        total_users = users_to_migrate.count()
        
        if total_users == 0:
            self.stdout.write(
                self.style.SUCCESS('No users found that need migration')
            )
            return
        
        self.stdout.write(f'Found {total_users} users to migrate')
        
        if not dry_run:
            try:
                keycloak_admin = KeycloakAdminService(realm=realm)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to initialize Keycloak admin: {e}')
                )
                return
        
        migrated_count = 0
        failed_count = 0
        
        for i in range(0, total_users, batch_size):
            batch = users_to_migrate[i:i + batch_size]
            
            for user in batch:
                try:
                    self.migrate_user(user, keycloak_admin if not dry_run else None, dry_run)
                    migrated_count += 1
                    
                    if migrated_count % 10 == 0:
                        self.stdout.write(f'Processed {migrated_count}/{total_users} users')
                        
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Failed to migrate user {user.email}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Migration completed: {migrated_count} successful, {failed_count} failed'
            )
        )
    
    def migrate_user(self, user, keycloak_admin, dry_run):
        """Migrate a single user to Keycloak"""
        
        user_data = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': getattr(user, 'phone', None),
            'email_verified': getattr(user, 'email_verified', False),
            'phone_verified': getattr(user, 'phone_verified', False),
            'enabled': user.is_active,
            'username': user.username or user.email
        }
        
        if dry_run:
            self.stdout.write(f'Would migrate user: {user.email} with data: {user_data}')
            return
        
        # Check if user already exists in Keycloak
        existing_user = keycloak_admin.find_user_by_email(user.email)
        
        if existing_user:
            # Update existing user
            keycloak_id = existing_user['id']
            success = keycloak_admin.update_user(keycloak_id, **user_data)
            
            if success:
                # Update Django user with Keycloak ID
                user.keycloak_id = keycloak_id
                user.realm = keycloak_admin.realm
                user.save(update_fields=['keycloak_id', 'realm'])
                
                self.stdout.write(f'Updated existing Keycloak user: {user.email}')
            else:
                raise Exception('Failed to update user in Keycloak')
        else:
            # Create new user
            keycloak_id = keycloak_admin.create_user(**user_data)
            
            if keycloak_id:
                # Update Django user with Keycloak ID
                user.keycloak_id = keycloak_id
                user.realm = keycloak_admin.realm
                user.save(update_fields=['keycloak_id', 'realm'])
                
                # Assign appropriate roles
                if user.is_staff:
                    keycloak_admin.assign_realm_role(keycloak_id, 'staff')
                else:
                    keycloak_admin.assign_realm_role(keycloak_id, 'customer')
                
                self.stdout.write(f'Created new Keycloak user: {user.email}')
            else:
                raise Exception('Failed to create user in Keycloak') 