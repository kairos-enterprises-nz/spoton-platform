"""
Fix tenant associations for existing data
Addresses orphaned records and missing tenant linkages
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from collections import defaultdict


class Command(BaseCommand):
    help = 'Fix tenant associations for existing data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['users', 'accounts', 'contracts', 'connections', 'plans', 'all'],
            default='all',
            help='Which model to fix associations for'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            default='utility-byte-default',
            help='Default tenant slug to use for orphaned records'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('🔧 Fixing Tenant Associations...'))
        
        tenant_slug = options['tenant_slug']
        model_type = options['model']
        
        try:
            # Get default tenant
            default_tenant = self.get_default_tenant(tenant_slug)
            if not default_tenant and not options['dry_run']:
                self.stdout.write(self.style.ERROR(f'❌ Default tenant "{tenant_slug}" not found. Create it first with: python manage.py create_default_tenant'))
                return
            
            # Fix associations based on model type
            if model_type == 'all':
                self.fix_all_associations(default_tenant, options['dry_run'])
            elif model_type == 'users':
                self.fix_user_associations(default_tenant, options['dry_run'])
            elif model_type == 'accounts':
                self.fix_account_associations(default_tenant, options['dry_run'])
            elif model_type == 'contracts':
                self.fix_contract_associations(default_tenant, options['dry_run'])
            elif model_type == 'connections':
                self.fix_connection_associations(default_tenant, options['dry_run'])
            elif model_type == 'plans':
                self.fix_plan_associations(default_tenant, options['dry_run'])
            
            if not options['dry_run']:
                self.stdout.write(self.style.SUCCESS('✅ Tenant associations fixed successfully!'))
            else:
                self.stdout.write(self.style.WARNING('✅ Dry run completed - no changes made'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error fixing tenant associations: {str(e)}'))
            raise

    def get_default_tenant(self, slug):
        """Get the default tenant"""
        try:
            from users.models import Tenant
            return Tenant.objects.filter(slug=slug).first()
        except Exception:
            return None

    def fix_all_associations(self, tenant, dry_run=False):
        """Fix all tenant associations"""
        self.fix_user_associations(tenant, dry_run)
        self.fix_account_associations(tenant, dry_run)
        self.fix_contract_associations(tenant, dry_run)
        self.fix_connection_associations(tenant, dry_run)
        self.fix_plan_associations(tenant, dry_run)

    def fix_user_associations(self, tenant, dry_run=False):
        """Fix user-tenant associations"""
        try:
            from users.models import User
            
            orphaned_users = User.objects.filter(tenant__isnull=True)
            count = orphaned_users.count()
            
            if count == 0:
                self.stdout.write("✅ All users already have tenant associations")
                return
            
            if dry_run:
                self.stdout.write(f"Would associate {count} users with tenant '{tenant.slug if tenant else 'default'}'")
                return
            
            # Associate with tenant
            orphaned_users.update(tenant=tenant)
            self.stdout.write(self.style.SUCCESS(f"✅ Associated {count} users with tenant '{tenant.slug}'"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not fix user associations: {str(e)}"))

    def fix_account_associations(self, tenant, dry_run=False):
        """Fix account-tenant associations with smart linking"""
        try:
            from users.models import Account, User
            
            orphaned_accounts = Account.objects.filter(tenant__isnull=True)
            count = orphaned_accounts.count()
            
            if count == 0:
                self.stdout.write("✅ All accounts already have tenant associations")
                return
            
            if dry_run:
                self.stdout.write(f"Would associate {count} accounts with tenant '{tenant.slug if tenant else 'default'}'")
                # Show smart linking analysis
                self.analyze_account_linking(orphaned_accounts)
                return
            
            # Smart linking: Try to associate accounts with tenant based on user relationships
            linked_via_user = 0
            linked_to_default = 0
            
            for account in orphaned_accounts:
                # Try to find tenant through user relationships
                user_roles = account.user_roles.select_related('user', 'user__tenant').all()
                user_tenants = [role.user.tenant for role in user_roles if role.user.tenant]
                
                if user_tenants:
                    # Use the tenant from the first user relationship
                    account.tenant = user_tenants[0]
                    account.save()
                    linked_via_user += 1
                else:
                    # Fallback to default tenant
                    account.tenant = tenant
                    account.save()
                    linked_to_default += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Account associations completed:"))
            self.stdout.write(f"   • {linked_via_user} accounts linked via user relationships")
            self.stdout.write(f"   • {linked_to_default} accounts linked to default tenant")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not fix account associations: {str(e)}"))

    def analyze_account_linking(self, orphaned_accounts):
        """Analyze how accounts would be linked"""
        linkable_via_user = 0
        default_fallback = 0
        
        for account in orphaned_accounts:
            user_roles = account.user_roles.select_related('user', 'user__tenant').all()
            user_tenants = [role.user.tenant for role in user_roles if role.user.tenant]
            
            if user_tenants:
                linkable_via_user += 1
            else:
                default_fallback += 1
        
        self.stdout.write(f"   Analysis: {linkable_via_user} via user relationships, {default_fallback} to default")

    def fix_contract_associations(self, tenant, dry_run=False):
        """Fix contract-tenant associations with smart linking"""
        try:
            from core.contracts.models import ServiceContract
            
            orphaned_contracts = ServiceContract.objects.filter(tenant__isnull=True)
            count = orphaned_contracts.count()
            
            if count == 0:
                self.stdout.write("✅ All contracts already have tenant associations")
                return
            
            if dry_run:
                self.stdout.write(f"Would associate {count} contracts with tenant '{tenant.slug if tenant else 'default'}'")
                return
            
            # Smart linking: Try to associate contracts with tenant based on account relationships
            linked_via_account = 0
            linked_to_default = 0
            
            for contract in orphaned_contracts:
                if contract.account and contract.account.tenant:
                    # Use tenant from account
                    contract.tenant = contract.account.tenant
                    contract.save()
                    linked_via_account += 1
                else:
                    # Fallback to default tenant
                    contract.tenant = tenant
                    contract.save()
                    linked_to_default += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Contract associations completed:"))
            self.stdout.write(f"   • {linked_via_account} contracts linked via account relationships")
            self.stdout.write(f"   • {linked_to_default} contracts linked to default tenant")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not fix contract associations: {str(e)}"))

    def fix_connection_associations(self, tenant, dry_run=False):
        """Fix connection-tenant associations with smart linking"""
        try:
            from energy.connections.models import Connection
            
            orphaned_connections = Connection.objects.filter(tenant__isnull=True)
            count = orphaned_connections.count()
            
            if count == 0:
                self.stdout.write("✅ All connections already have tenant associations")
                return
            
            if dry_run:
                self.stdout.write(f"Would associate {count} connections with tenant '{tenant.slug if tenant else 'default'}'")
                return
            
            # Smart linking: Try to associate connections with tenant based on relationships
            linked_via_account = 0
            linked_via_contract = 0
            linked_to_default = 0
            
            for connection in orphaned_connections:
                tenant_found = False
                
                # Try account relationship first
                if connection.account and connection.account.tenant:
                    connection.tenant = connection.account.tenant
                    connection.save()
                    linked_via_account += 1
                    tenant_found = True
                
                # Try contract relationship if no account tenant
                elif hasattr(connection, 'contract_id') and connection.contract_id:
                    try:
                        from core.contracts.models import ServiceContract
                        contract = ServiceContract.objects.filter(id=connection.contract_id).first()
                        if contract and contract.tenant:
                            connection.tenant = contract.tenant
                            connection.save()
                            linked_via_contract += 1
                            tenant_found = True
                    except:
                        pass
                
                # Fallback to default tenant
                if not tenant_found:
                    connection.tenant = tenant
                    connection.save()
                    linked_to_default += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Connection associations completed:"))
            self.stdout.write(f"   • {linked_via_account} connections linked via account relationships")
            self.stdout.write(f"   • {linked_via_contract} connections linked via contract relationships")
            self.stdout.write(f"   • {linked_to_default} connections linked to default tenant")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not fix connection associations: {str(e)}"))

    def fix_plan_associations(self, tenant, dry_run=False):
        """Fix plan-tenant associations"""
        plan_fixes = []
        
        # Fix ServicePlan associations
        try:
            from finance.pricing.models import ServicePlan
            orphaned_plans = ServicePlan.objects.filter(tenant__isnull=True)
            count = orphaned_plans.count()
            
            if count > 0:
                if dry_run:
                    plan_fixes.append(f"Would associate {count} service plans")
                else:
                    orphaned_plans.update(tenant=tenant)
                    plan_fixes.append(f"Associated {count} service plans")
        except Exception as e:
            plan_fixes.append(f"Could not fix service plans: {str(e)}")
        
        # Fix ElectricityPlan associations
        try:
            from web_support.public_pricing.models import ElectricityPlan
            orphaned_plans = ElectricityPlan.objects.filter(tenant__isnull=True)
            count = orphaned_plans.count()
            
            if count > 0:
                if dry_run:
                    plan_fixes.append(f"Would associate {count} electricity plans")
                else:
                    orphaned_plans.update(tenant=tenant)
                    plan_fixes.append(f"Associated {count} electricity plans")
        except Exception as e:
            plan_fixes.append(f"Could not fix electricity plans: {str(e)}")
        
        # Fix BroadbandPlan associations
        try:
            from web_support.public_pricing.models import BroadbandPlan
            orphaned_plans = BroadbandPlan.objects.filter(tenant__isnull=True)
            count = orphaned_plans.count()
            
            if count > 0:
                if dry_run:
                    plan_fixes.append(f"Would associate {count} broadband plans")
                else:
                    orphaned_plans.update(tenant=tenant)
                    plan_fixes.append(f"Associated {count} broadband plans")
        except Exception as e:
            plan_fixes.append(f"Could not fix broadband plans: {str(e)}")
        
        # Fix MobilePlan associations
        try:
            from web_support.public_pricing.models import MobilePlan
            orphaned_plans = MobilePlan.objects.filter(tenant__isnull=True)
            count = orphaned_plans.count()
            
            if count > 0:
                if dry_run:
                    plan_fixes.append(f"Would associate {count} mobile plans")
                else:
                    orphaned_plans.update(tenant=tenant)
                    plan_fixes.append(f"Associated {count} mobile plans")
        except Exception as e:
            plan_fixes.append(f"Could not fix mobile plans: {str(e)}")
        
        if plan_fixes:
            self.stdout.write(self.style.SUCCESS("✅ Plan associations:"))
            for fix in plan_fixes:
                self.stdout.write(f"   • {fix}")
        else:
            self.stdout.write("✅ All plans already have tenant associations")
