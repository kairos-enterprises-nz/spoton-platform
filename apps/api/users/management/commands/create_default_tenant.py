"""
Create default tenant and essential setup for multi-tenancy
Critical fix for UAT environment
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import uuid


class Command(BaseCommand):
    help = 'Create default tenant and essential multi-tenant setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='SpotOn Default',
            help='Name for the default tenant'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            default='utility-byte-default',
            help='Slug for the default tenant'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('🏢 Creating Default Tenant Setup...'))
        
        tenant_name = options['tenant_name']
        tenant_slug = options['tenant_slug']
        
        try:
            with transaction.atomic():
                # Create default tenant
                tenant = self.create_default_tenant(tenant_name, tenant_slug, options['dry_run'])
                
                if not options['dry_run']:
                    # Associate existing users with tenant
                    self.associate_users_with_tenant(tenant)
                    
                    # Associate existing data with tenant
                    self.associate_existing_data_with_tenant(tenant)
                    
                    self.stdout.write(self.style.SUCCESS('✅ Default tenant setup completed successfully!'))
                    self.stdout.write(f"   Tenant ID: {tenant.id}")
                    self.stdout.write(f"   Tenant Name: {tenant.name}")
                    self.stdout.write(f"   Tenant Slug: {tenant.slug}")
                else:
                    self.stdout.write(self.style.WARNING('✅ Dry run completed - no changes made'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating tenant setup: {str(e)}'))
            raise

    def create_default_tenant(self, name, slug, dry_run=False):
        """Create the default tenant"""
        try:
            from users.models import Tenant
            
            # Check if tenant already exists
            existing_tenant = Tenant.objects.filter(slug=slug).first()
            if existing_tenant:
                self.stdout.write(f"✅ Tenant '{slug}' already exists")
                return existing_tenant
            
            if dry_run:
                self.stdout.write(f"Would create tenant: {name} ({slug})")
                return None
            
            # Create new tenant
            tenant = Tenant.objects.create(
                name=name,
                slug=slug,
                is_active=True,
                contact_email='admin@spoton.co.nz',
                created_at=timezone.now()
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created tenant: {name} ({slug})"))
            return tenant
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating tenant: {str(e)}"))
            raise

    def associate_users_with_tenant(self, tenant):
        """Associate existing users with the default tenant"""
        try:
            from users.models import User
            
            # Find users without tenant association
            orphaned_users = User.objects.filter(tenant__isnull=True)
            count = orphaned_users.count()
            
            if count == 0:
                self.stdout.write("✅ All users already have tenant associations")
                return
            
            # Associate with default tenant
            orphaned_users.update(tenant=tenant)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Associated {count} users with tenant '{tenant.slug}'"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error associating users: {str(e)}"))
            # Don't raise - continue with other associations

    def associate_existing_data_with_tenant(self, tenant):
        """Associate existing data with the default tenant"""
        associations = []
        
        # Associate accounts
        try:
            from users.models import Account
            orphaned_accounts = Account.objects.filter(tenant__isnull=True)
            count = orphaned_accounts.count()
            if count > 0:
                orphaned_accounts.update(tenant=tenant)
                associations.append(f"Accounts: {count}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not associate accounts: {str(e)}"))
        
        # Associate contracts
        try:
            from core.contracts.models import ServiceContract
            orphaned_contracts = ServiceContract.objects.filter(tenant__isnull=True)
            count = orphaned_contracts.count()
            if count > 0:
                orphaned_contracts.update(tenant=tenant)
                associations.append(f"Contracts: {count}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not associate contracts: {str(e)}"))
        
        # Associate connections
        try:
            from energy.connections.models import Connection
            orphaned_connections = Connection.objects.filter(tenant__isnull=True)
            count = orphaned_connections.count()
            if count > 0:
                orphaned_connections.update(tenant=tenant)
                associations.append(f"Connections: {count}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not associate connections: {str(e)}"))
        
        # Associate service plans
        try:
            from finance.pricing.models import ServicePlan
            orphaned_plans = ServicePlan.objects.filter(tenant__isnull=True)
            count = orphaned_plans.count()
            if count > 0:
                orphaned_plans.update(tenant=tenant)
                associations.append(f"Service Plans: {count}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not associate service plans: {str(e)}"))
        
        # Associate electricity plans
        try:
            from web_support.public_pricing.models import ElectricityPlan
            orphaned_elec_plans = ElectricityPlan.objects.filter(tenant__isnull=True)
            count = orphaned_elec_plans.count()
            if count > 0:
                orphaned_elec_plans.update(tenant=tenant)
                associations.append(f"Electricity Plans: {count}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not associate electricity plans: {str(e)}"))
        
        # Associate broadband plans
        try:
            from web_support.public_pricing.models import BroadbandPlan
            orphaned_bb_plans = BroadbandPlan.objects.filter(tenant__isnull=True)
            count = orphaned_bb_plans.count()
            if count > 0:
                orphaned_bb_plans.update(tenant=tenant)
                associations.append(f"Broadband Plans: {count}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not associate broadband plans: {str(e)}"))
        
        # Associate mobile plans
        try:
            from web_support.public_pricing.models import MobilePlan
            orphaned_mobile_plans = MobilePlan.objects.filter(tenant__isnull=True)
            count = orphaned_mobile_plans.count()
            if count > 0:
                orphaned_mobile_plans.update(tenant=tenant)
                associations.append(f"Mobile Plans: {count}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not associate mobile plans: {str(e)}"))
        
        if associations:
            self.stdout.write(self.style.SUCCESS("✅ Data associations completed:"))
            for association in associations:
                self.stdout.write(f"   • {association}")
        else:
            self.stdout.write("✅ No orphaned data found to associate")