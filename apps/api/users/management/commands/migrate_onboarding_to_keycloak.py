"""
Django management command to migrate existing onboarding data from Django to Keycloak.

This command:
1. Finds all users with OnboardingProgress records
2. Syncs their onboarding status and step to Keycloak attributes
3. Invalidates their cache entries
4. Provides detailed logging and dry-run mode
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Tenant
from users.models import OnboardingProgress
from users.keycloak_user_service import KeycloakUserService
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate existing onboarding data from Django to Keycloak attributes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of users to process (default: 100)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Process only this specific user email',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        specific_email = options['email']
        
        self.stdout.write("🚀 Starting onboarding data migration to Keycloak...")
        if dry_run:
            self.stdout.write("🔍 DRY RUN MODE - No changes will be made")
        
        # Initialize Keycloak admin service
        try:
            environment = getattr(settings, 'ENVIRONMENT', 'uat')
            realm = f'spoton-{environment}'
            kc_admin = KeycloakAdminService(realm=realm)
            self.stdout.write(f"✅ Connected to Keycloak realm: {realm}")
        except Exception as e:
            self.stderr.write(f"❌ Failed to connect to Keycloak: {e}")
            return
        
        # Get users with onboarding data
        try:
            from web_support.onboarding.models import OnboardingProgress
            
            if specific_email:
                users_query = User.objects.filter(email=specific_email, keycloak_id__isnull=False)
            else:
                users_query = User.objects.filter(keycloak_id__isnull=False)[:limit]
            
            users_with_onboarding = []
            for user in users_query:
                try:
                    progress = OnboardingProgress.objects.get(user=user)
                    users_with_onboarding.append((user, progress))
                except OnboardingProgress.DoesNotExist:
                    continue
            
            self.stdout.write(f"📊 Found {len(users_with_onboarding)} users with onboarding data")
            
        except Exception as e:
            self.stderr.write(f"❌ Failed to query onboarding data: {e}")
            return
        
        # Process each user
        migrated_count = 0
        error_count = 0
        
        for user, progress in users_with_onboarding:
            try:
                self.stdout.write(f"\n👤 Processing {user.email} (keycloak_id: {user.keycloak_id})")
                
                # Determine onboarding status
                is_complete = bool(progress.is_completed)
                current_step = progress.current_step or ''
                
                self.stdout.write(f"   📋 Django data: complete={is_complete}, step='{current_step}'")
                
                if not dry_run:
                    # Update Keycloak
                    updated = kc_admin.set_onboarding_complete(
                        user.keycloak_id, 
                        complete=is_complete, 
                        step=current_step
                    )
                    
                    if updated:
                        # Invalidate cache
                        UserCacheService.invalidate_user_cache(user.keycloak_id)
                        self.stdout.write(f"   ✅ Synced to Keycloak and invalidated cache")
                        migrated_count += 1
                    else:
                        self.stdout.write(f"   ⚠️  Keycloak update failed")
                        error_count += 1
                else:
                    self.stdout.write(f"   🔍 Would sync: complete={is_complete}, step='{current_step}'")
                    migrated_count += 1
                
            except Exception as e:
                self.stderr.write(f"   ❌ Error processing {user.email}: {e}")
                error_count += 1
        
        # Summary
        self.stdout.write(f"\n📊 Migration Summary:")
        self.stdout.write(f"   ✅ Successfully processed: {migrated_count}")
        self.stdout.write(f"   ❌ Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(f"\n💡 Run without --dry-run to apply changes")
        else:
            self.stdout.write(f"\n🎉 Migration complete!")
        
        # Test cache with first user
        if not dry_run and users_with_onboarding:
            test_user, _ = users_with_onboarding[0]
            self.stdout.write(f"\n🧪 Testing cache with {test_user.email}...")
            
            cached_data = UserCacheService.get_user_data(test_user.keycloak_id)
            if cached_data:
                self.stdout.write(f"   ✅ Cache working: onboarding_complete={cached_data['is_onboarding_complete']}")
            else:
                self.stdout.write(f"   ❌ Cache test failed")