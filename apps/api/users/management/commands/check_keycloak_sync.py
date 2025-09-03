"""
Django management command to check and fix data consistency between Django and Keycloak.

Usage:
    python manage.py check_keycloak_sync --dry-run  # Check only, no fixes
    python manage.py check_keycloak_sync --fix      # Check and fix issues
    python manage.py check_keycloak_sync --email user@example.com  # Check specific user
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import User, Tenant
from users.keycloak_admin import KeycloakAdminService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check and fix data consistency between Django and Keycloak'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Check only, do not fix issues',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix detected issues',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Check specific user by email',
        )
        parser.add_argument(
            '--environment',
            type=str,
            default='uat',
            help='Environment (uat or live)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_issues = options['fix']
        email_filter = options['email']
        environment = options['environment']
        
        if not dry_run and not fix_issues:
            self.stdout.write(
                self.style.WARNING('Please specify either --dry-run or --fix')
            )
            return
        
        self.stdout.write(f"🔍 Checking Keycloak sync consistency (environment: {environment})")
        
        # Get Keycloak admin service
        realm = f'spoton-{environment}'
        try:
            kc_admin = KeycloakAdminService(realm=realm)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize Keycloak admin service: {e}')
            )
            return
        
        # Get users to check
        if email_filter:
            users = User.objects.filter(email=email_filter)
            if not users.exists():
                self.stdout.write(
                    self.style.WARNING(f'No user found with email: {email_filter}')
                )
                return
        else:
            # Check all users with keycloak_id
            users = User.objects.exclude(keycloak_id='').exclude(keycloak_id__isnull=True)
        
        total_users = users.count()
        issues_found = 0
        issues_fixed = 0
        
        self.stdout.write(f"📊 Checking {total_users} users...")
        
        for user in users:
            user_issues = self.check_user_sync(user, kc_admin)
            if user_issues:
                issues_found += len(user_issues)
                self.stdout.write(
                    self.style.WARNING(f"❌ {user.email} ({user.keycloak_id}):")
                )
                for issue in user_issues:
                    self.stdout.write(f"   • {issue['description']}")
                    
                    if fix_issues and not dry_run:
                        try:
                            if self.fix_issue(user, issue, kc_admin):
                                issues_fixed += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f"   ✅ Fixed: {issue['description']}")
                                )
                            else:
                                self.stdout.write(
                                    self.style.ERROR(f"   ❌ Failed to fix: {issue['description']}")
                                )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"   ❌ Error fixing issue: {e}")
                            )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {user.email} - No issues found")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"📊 SUMMARY:")
        self.stdout.write(f"   Users checked: {total_users}")
        self.stdout.write(f"   Issues found: {issues_found}")
        if fix_issues and not dry_run:
            self.stdout.write(f"   Issues fixed: {issues_fixed}")
        
        if dry_run and issues_found > 0:
            self.stdout.write(
                self.style.WARNING(f"\n💡 Run with --fix to resolve {issues_found} issues")
            )
    
    def check_user_sync(self, user, kc_admin):
        """Check a single user for sync issues"""
        issues = []
        
        if not user.keycloak_id:
            issues.append({
                'type': 'missing_keycloak_id',
                'description': 'User has no keycloak_id'
            })
            return issues
        
        try:
            # Get user from Keycloak
            kc_user = kc_admin._get_admin_client().get_user(user.keycloak_id)
            if not kc_user:
                issues.append({
                    'type': 'user_not_found_in_keycloak',
                    'description': 'User not found in Keycloak'
                })
                return issues
            
            # Check email verification
            kc_email_verified = kc_user.get('emailVerified', False)
            if user.email_verified != kc_email_verified:
                issues.append({
                    'type': 'email_verified_mismatch',
                    'description': f'email_verified mismatch: Django={user.email_verified}, Keycloak={kc_email_verified}',
                    'django_value': user.email_verified,
                    'keycloak_value': kc_email_verified
                })
            
            # Check phone attributes
            kc_attributes = kc_user.get('attributes', {})
            
            # Check phone number
            kc_phone = ''
            if 'phone' in kc_attributes and kc_attributes['phone']:
                kc_phone = kc_attributes['phone'][0] if isinstance(kc_attributes['phone'], list) else str(kc_attributes['phone'])
            
            if user.phone != kc_phone:
                issues.append({
                    'type': 'phone_mismatch',
                    'description': f'phone mismatch: Django="{user.phone}", Keycloak="{kc_phone}"',
                    'django_value': user.phone,
                    'keycloak_value': kc_phone
                })
            
            # Check phone verification
            kc_phone_verified = False
            if 'phone_verified' in kc_attributes:
                phone_verified_attr = kc_attributes['phone_verified']
                if isinstance(phone_verified_attr, list) and phone_verified_attr:
                    kc_phone_verified = str(phone_verified_attr[0]).lower() == 'true'
                else:
                    kc_phone_verified = str(phone_verified_attr).lower() == 'true'
            
            if user.phone_verified != kc_phone_verified:
                issues.append({
                    'type': 'phone_verified_mismatch',
                    'description': f'phone_verified mismatch: Django={user.phone_verified}, Keycloak={kc_phone_verified}',
                    'django_value': user.phone_verified,
                    'keycloak_value': kc_phone_verified
                })
            
            # Check for legacy attribute keys that should be cleaned up
            legacy_keys = []
            if 'phone_number' in kc_attributes:
                legacy_keys.append('phone_number')
            if 'mobile' in kc_attributes:
                legacy_keys.append('mobile')
            if 'phoneVerified' in kc_attributes:
                legacy_keys.append('phoneVerified')
            
            if legacy_keys:
                issues.append({
                    'type': 'legacy_attributes',
                    'description': f'Legacy attribute keys found: {", ".join(legacy_keys)}',
                    'legacy_keys': legacy_keys
                })
        
        except Exception as e:
            issues.append({
                'type': 'keycloak_fetch_error',
                'description': f'Error fetching from Keycloak: {e}'
            })
        
        return issues
    
    def fix_issue(self, user, issue, kc_admin):
        """Fix a specific issue"""
        try:
            if issue['type'] == 'email_verified_mismatch':
                # Use Django value as source of truth for social users
                if getattr(user, 'registration_method', None) == 'social':
                    # Social users should have email_verified=True
                    return kc_admin.update_user(user.keycloak_id, email_verified=True)
                else:
                    # Use Keycloak value for traditional users
                    user.email_verified = issue['keycloak_value']
                    user.save(update_fields=['email_verified'])
                    return True
            
            elif issue['type'] == 'phone_mismatch':
                # Use Django value as source of truth
                return kc_admin.update_user(user.keycloak_id, phone=user.phone)
            
            elif issue['type'] == 'phone_verified_mismatch':
                # Use Django value as source of truth
                return kc_admin.update_user(user.keycloak_id, phone_verified=user.phone_verified)
            
            elif issue['type'] == 'legacy_attributes':
                # Clean up legacy attribute keys
                admin = kc_admin._get_admin_client()
                kc_user = admin.get_user(user.keycloak_id)
                attributes = kc_user.get('attributes', {})
                
                # Remove legacy keys
                for key in issue['legacy_keys']:
                    if key in attributes:
                        del attributes[key]
                
                # Update user with cleaned attributes
                kc_user['attributes'] = attributes
                admin.update_user(user.keycloak_id, kc_user)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error fixing issue {issue['type']} for user {user.email}: {e}")
            return False