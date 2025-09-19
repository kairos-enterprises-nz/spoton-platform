"""
Management command to detect and optionally fix duplicate users caused by OAuth revoke/re-auth scenarios.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from collections import defaultdict
from users.models import Tenant
from users.models import OnboardingProgress
from users.services import UserCacheService
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Detect and optionally fix duplicate users caused by OAuth revoke/re-auth'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually fix duplicate users (default is dry-run)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Check specific email address only',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Scanning for duplicate users...'))
        
        # Group users by email from cached Keycloak data
        email_to_users = {}
        users_without_cache = []
        
        for user in User.objects.all():
            if options['email'] and options['email'] not in user.keycloak_id:
                continue
                
            try:
                cached_data = UserCacheService.get_user_data(user.keycloak_id)
                if cached_data and cached_data.get('email'):
                    email = cached_data['email']
                    if email not in email_to_users:
                        email_to_users[email] = []
                    email_to_users[email].append(user)
                else:
                    users_without_cache.append(user)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Could not get cache for user {user.keycloak_id}: {e}')
                )
                users_without_cache.append(user)
        
        # Report findings
        duplicates_found = 0
        for email, users in email_to_users.items():
            if len(users) > 1:
                duplicates_found += 1
                self.stdout.write(
                    self.style.ERROR(f'🚨 DUPLICATE: {email} has {len(users)} Django users:')
                )
                
                # Sort by creation date to identify the original
                users_sorted = sorted(users, key=lambda u: u.created_at)
                original_user = users_sorted[0]
                duplicate_users = users_sorted[1:]
                
                self.stdout.write(f'   ✅ Original: {original_user.keycloak_id} (created: {original_user.created_at})')
                for dup_user in duplicate_users:
                    self.stdout.write(f'   ❌ Duplicate: {dup_user.keycloak_id} (created: {dup_user.created_at})')
                
                # Fix if requested
                if options['fix']:
                    self.stdout.write(f'   🔧 Fixing duplicates...')
                    
                    # For each duplicate, transfer any important data to original and delete
                    for dup_user in duplicate_users:
                        try:
                            # Check if duplicate has any important business data
                            dup_progress = OnboardingProgress.objects.filter(user=dup_user).first()
                            original_progress = OnboardingProgress.objects.filter(user=original_user).first()
                            
                            if dup_progress and not original_progress:
                                # Transfer onboarding progress
                                dup_progress.user = original_user
                                dup_progress.save()
                                self.stdout.write(f'     ↗️  Transferred onboarding progress')
                            elif dup_progress and original_progress and dup_progress.is_completed and not original_progress.is_completed:
                                # Duplicate has completed onboarding, original hasn't - transfer
                                original_progress.is_completed = True
                                original_progress.current_step = dup_progress.current_step
                                original_progress.step_data = dup_progress.step_data
                                original_progress.save()
                                self.stdout.write(f'     ↗️  Transferred completed onboarding status')
                            
                            # Clear caches
                            UserCacheService.invalidate_user_cache(dup_user.keycloak_id)
                            
                            # Delete duplicate
                            dup_user.delete()
                            self.stdout.write(f'     ✅ Deleted duplicate user {dup_user.keycloak_id}')
                            
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'     ❌ Failed to fix duplicate {dup_user.keycloak_id}: {e}')
                            )
                else:
                    self.stdout.write(f'   💡 Run with --fix to merge duplicates')
        
        # Report users without cache (potential orphans)
        if users_without_cache:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  Found {len(users_without_cache)} users without cached Keycloak data (potential orphans):')
            )
            for user in users_without_cache:
                self.stdout.write(f'   🔍 {user.keycloak_id} (created: {user.created_at})')
        
        # Summary
        if duplicates_found == 0:
            self.stdout.write(self.style.SUCCESS('✅ No duplicate users found!'))
        else:
            action = "Fixed" if options['fix'] else "Found"
            self.stdout.write(
                self.style.WARNING(f'\n📊 Summary: {action} {duplicates_found} duplicate email(s)')
            )
            if not options['fix']:
                self.stdout.write('💡 Run with --fix to automatically merge duplicates')