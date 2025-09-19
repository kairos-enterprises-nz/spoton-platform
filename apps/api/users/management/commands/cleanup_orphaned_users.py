from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.keycloak_admin import KeycloakAdminService
from users.services.user_cache_service import UserCacheService
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Clean up Django users with invalid Keycloak IDs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--fix-invalid-ids',
            action='store_true',
            help='Attempt to fix users with invalid Keycloak IDs by finding correct ones',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_invalid_ids = options['fix_invalid_ids']
        
        self.stdout.write("🔍 Scanning for orphaned Django users...")
        
        kc_admin = KeycloakAdminService()
        orphaned_users = []
        fixable_users = []
        
        for user in User.objects.all():
            if not user.keycloak_id:
                self.stdout.write(f"❌ User {user.id} has no keycloak_id")
                orphaned_users.append(user)
                continue
                
            # Test if Keycloak ID is valid
            try:
                cached_data = UserCacheService.get_user_data(user.keycloak_id, force_refresh=True)
                if not cached_data:
                    self.stdout.write(f"❌ User {user.id} has invalid keycloak_id: {user.keycloak_id}")
                    orphaned_users.append(user)
                    
                    # Try to find correct Keycloak user by email if available
                    if fix_invalid_ids:
                        try:
                            # Get email from user's helper method if available
                            email = user.get_email() if hasattr(user, 'get_email') else None
                            if email and email != f"{user.keycloak_id}@example.com":
                                admin_client = kc_admin._get_admin_client()
                                keycloak_users = admin_client.get_users({'email': email})
                                if keycloak_users:
                                    correct_user = keycloak_users[0]
                                    fixable_users.append((user, correct_user['id'], email))
                                    self.stdout.write(f"  🔧 Found correct Keycloak ID for {email}: {correct_user['id']}")
                        except Exception as e:
                            logger.warning(f"Could not search for correct Keycloak user: {e}")
                else:
                    email = cached_data.get('email', 'N/A')
                    self.stdout.write(f"✅ User {user.id} is valid: {email}")
                    
            except Exception as e:
                self.stdout.write(f"❌ User {user.id} has invalid keycloak_id: {user.keycloak_id} (Error: {e})")
                orphaned_users.append(user)
        
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"  Total users: {User.objects.count()}")
        self.stdout.write(f"  Orphaned users: {len(orphaned_users)}")
        self.stdout.write(f"  Fixable users: {len(fixable_users)}")
        
        if fixable_users and fix_invalid_ids:
            self.stdout.write(f"\n🔧 Fixing users with correctable Keycloak IDs...")
            for user, correct_keycloak_id, email in fixable_users:
                if not dry_run:
                    try:
                        with transaction.atomic():
                            user.keycloak_id = correct_keycloak_id
                            user.save(update_fields=['keycloak_id'])
                            # Invalidate cache to refresh
                            UserCacheService.invalidate_user_cache(correct_keycloak_id)
                            self.stdout.write(f"  ✅ Fixed user {email}: {user.id} -> {correct_keycloak_id}")
                    except Exception as e:
                        self.stdout.write(f"  ❌ Failed to fix user {email}: {e}")
                else:
                    self.stdout.write(f"  🔧 Would fix user {email}: {user.id} -> {correct_keycloak_id}")
        
        # Remove orphaned users that couldn't be fixed
        unfixable_orphans = [u for u in orphaned_users if u not in [f[0] for f in fixable_users]]
        
        if unfixable_orphans:
            self.stdout.write(f"\n🗑️  Cleaning up {len(unfixable_orphans)} unfixable orphaned users...")
            for user in unfixable_orphans:
                if not dry_run:
                    try:
                        with transaction.atomic():
                            user_id = user.id
                            user.delete()
                            self.stdout.write(f"  ✅ Deleted orphaned user: {user_id}")
                    except Exception as e:
                        self.stdout.write(f"  ❌ Failed to delete user {user.id}: {e}")
                else:
                    self.stdout.write(f"  🗑️  Would delete orphaned user: {user.id}")
        
        if dry_run:
            self.stdout.write(f"\n🔍 This was a dry run. Use --fix-invalid-ids to attempt fixes, or run without --dry-run to apply changes.")
        else:
            self.stdout.write(f"\n✅ Cleanup completed!")
