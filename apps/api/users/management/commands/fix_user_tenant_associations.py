"""
Fix user-tenant associations and login tracking
Critical fix for staff portal showing N/A tenant information
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Fix user-tenant associations and ensure proper login tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            default='utility-byte-default',
            help='Default tenant slug to associate users with'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('🔧 Fixing User-Tenant Associations...'))
        
        try:
            # Get or create default tenant
            tenant = self.get_or_create_tenant(options['tenant_slug'], options['dry_run'])
            
            if not options['dry_run'] and tenant:
                with transaction.atomic():
                    # Step 1: Fix users without tenant associations
                    self.fix_user_tenant_associations(tenant)
                    
                    # Step 2: Ensure users have account roles (if they have accounts)
                    self.fix_user_account_roles(tenant)
                    
                    # Step 3: Update last login tracking
                    self.update_last_login_tracking()
                    
                    # Step 4: Sync with Keycloak data
                    self.sync_keycloak_user_data()
                    
                    self.stdout.write(self.style.SUCCESS('✅ User-tenant associations fixed successfully!'))
            else:
                self.stdout.write(self.style.WARNING('✅ Dry run completed'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error fixing user associations: {str(e)}'))
            raise

    def get_or_create_tenant(self, slug, dry_run=False):
        """Get or create the tenant"""
        try:
            from users.models import Tenant
            
            tenant = Tenant.objects.filter(slug=slug).first()
            if tenant:
                self.stdout.write(f"✅ Using tenant: {tenant.name} ({slug})")
                return tenant
            
            if dry_run:
                self.stdout.write(f"Would create tenant: {slug}")
                return None
            
            # Create tenant if it doesn't exist
            tenant = Tenant.objects.create(
                name='SpotOn Default',
                slug=slug,
                subdomain=slug,
                is_active=True,
                contact_email='admin@spoton.co.nz',
                created_at=timezone.now()
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created tenant: {tenant.name} ({slug})"))
            return tenant
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error with tenant: {str(e)}"))
            raise

    def fix_user_tenant_associations(self, tenant):
        """Fix users without proper tenant associations"""
        try:
            from users.models import User, TenantUserRole, UserTenantRole
            
            # Find users without tenant associations
            users_without_tenant_roles = User.objects.filter(tenant_roles__isnull=True)
            users_without_user_tenant_roles = User.objects.filter(usertenantrole__isnull=True)
            
            # Combine and deduplicate
            users_needing_association = (users_without_tenant_roles | users_without_user_tenant_roles).distinct()
            
            self.stdout.write(f"🔍 Found {users_needing_association.count()} users needing tenant associations")
            
            fixed_tenant_roles = 0
            fixed_user_tenant_roles = 0
            
            for user in users_needing_association:
                try:
                    # Create TenantUserRole if missing
                    tenant_role, created = TenantUserRole.objects.get_or_create(
                        tenant=tenant,
                        user=user,
                        defaults={
                            'role': 'staff' if user.is_staff else 'viewer',
                            'can_access_billing': user.is_staff,
                            'can_access_metering': user.is_staff,
                            'can_manage_contracts': user.is_staff and user.is_superuser,
                        }
                    )
                    if created:
                        fixed_tenant_roles += 1
                        self.stdout.write(f"   • Created TenantUserRole for {user.id}")
                    
                    # Create UserTenantRole if missing  
                    user_tenant_role, created = UserTenantRole.objects.get_or_create(
                        user=user,
                        tenant=tenant,
                        defaults={
                            'role': 'admin' if user.is_superuser else ('staff' if user.is_staff else 'customer')
                        }
                    )
                    if created:
                        fixed_user_tenant_roles += 1
                        self.stdout.write(f"   • Created UserTenantRole for {user.id}")
                        
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ Error fixing user {user.id}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Fixed tenant associations:"))
            self.stdout.write(f"   • TenantUserRole: {fixed_tenant_roles} created")
            self.stdout.write(f"   • UserTenantRole: {fixed_user_tenant_roles} created")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error fixing user-tenant associations: {str(e)}"))

    def fix_user_account_roles(self, tenant):
        """Ensure users with accounts have proper account roles"""
        try:
            from users.models import User, Account, UserAccountRole
            
            # Find users who have accounts but no account roles
            users_with_accounts = User.objects.filter(
                account_roles__isnull=True
            ).filter(
                # Users who created accounts or have accounts somehow linked
                account_set__isnull=False
            ).distinct()
            
            self.stdout.write(f"🔍 Found {users_with_accounts.count()} users with accounts but no account roles")
            
            fixed_account_roles = 0
            
            for user in users_with_accounts:
                try:
                    # Get user's accounts
                    accounts = Account.objects.filter(created_by=user) | Account.objects.filter(
                        # Users who might be linked through onboarding
                        useraccountrole__user=user
                    )
                    
                    for account in accounts.distinct():
                        # Create UserAccountRole if missing
                        account_role, created = UserAccountRole.objects.get_or_create(
                            tenant=tenant,
                            user=user,
                            account=account,
                            defaults={
                                'role': 'primary',
                                'can_manage_services': True,
                                'can_manage_users': True,
                                'can_manage_billing': True,
                                'can_view_usage': True,
                                'created_by': user
                            }
                        )
                        if created:
                            fixed_account_roles += 1
                            self.stdout.write(f"   • Created account role for {user.id} -> {account.account_number}")
                        
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ Error fixing account roles for user {user.id}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Fixed {fixed_account_roles} account role associations"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error fixing user-account roles: {str(e)}"))

    def update_last_login_tracking(self):
        """Update last login tracking for users"""
        try:
            from users.models import User
            
            # Update last_keycloak_sync for users who don't have it set
            users_without_sync = User.objects.filter(last_keycloak_sync__isnull=True)
            
            self.stdout.write(f"🔍 Found {users_without_sync.count()} users without last sync timestamp")
            
            # Set a reasonable default - when they were created or now
            updated_count = 0
            for user in users_without_sync:
                try:
                    # Use created_at as a reasonable proxy for first login
                    user.last_keycloak_sync = user.created_at or timezone.now()
                    user.save(update_fields=['last_keycloak_sync'])
                    updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ Error updating sync for user {user.id}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Updated last sync timestamp for {updated_count} users"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error updating login tracking: {str(e)}"))

    def sync_keycloak_user_data(self):
        """Sync user data from Keycloak"""
        try:
            from users.models import User
            
            # Get users that need Keycloak sync
            users_needing_sync = User.objects.filter(
                last_keycloak_sync__lt=timezone.now() - timezone.timedelta(hours=1)
            ) | User.objects.filter(last_keycloak_sync__isnull=True)
            
            self.stdout.write(f"🔍 Found {users_needing_sync.count()} users needing Keycloak sync")
            
            synced_count = 0
            for user in users_needing_sync:
                try:
                    # Try to refresh user data from Keycloak
                    # This will populate cached data and update last_keycloak_sync
                    user.get_email()  # This triggers Keycloak sync
                    synced_count += 1
                    
                    if synced_count % 10 == 0:  # Progress indicator
                        self.stdout.write(f"   • Synced {synced_count} users...")
                        
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ Error syncing user {user.id}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Synced {synced_count} users with Keycloak"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error syncing Keycloak data: {str(e)}"))
