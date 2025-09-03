"""
Create sample plans for all service types
Critical fix for UAT environment showing 0 plans
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import uuid


class Command(BaseCommand):
    help = 'Create sample plans for all service types to fix 0 plans issue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-slug',
            type=str,
            default='utility-byte-default',
            help='Slug for the tenant to create plans for'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing plans'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('📋 Creating Sample Plans...'))
        
        tenant_slug = options['tenant_slug']
        
        try:
            # Get or create tenant
            tenant = self.get_or_create_tenant(tenant_slug, options['dry_run'])
            
            if not options['dry_run'] and tenant:
                with transaction.atomic():
                    # Create service plans (generic)
                    self.create_service_plans(tenant, options['overwrite'])
                    
                    # Create specific plans
                    self.create_electricity_plans(tenant, options['overwrite'])
                    self.create_broadband_plans(tenant, options['overwrite'])
                    self.create_mobile_plans(tenant, options['overwrite'])
                    
                    self.stdout.write(self.style.SUCCESS('✅ Sample plans created successfully!'))
            else:
                self.stdout.write(self.style.WARNING('✅ Dry run completed - no changes made'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating sample plans: {str(e)}'))
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
                is_active=True,
                contact_email='admin@spoton.co.nz',
                created_at=timezone.now()
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created tenant: {tenant.name} ({slug})"))
            return tenant
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error with tenant: {str(e)}"))
            raise

    def create_service_plans(self, tenant, overwrite=False):
        """Create generic service plans"""
        try:
            from finance.pricing.models import ServicePlan
            
            service_plans_data = [
                {
                    'plan_code': 'ELEC-BASIC-001',
                    'plan_name': 'Basic Electricity Plan',
                    'service_type': 'electricity',
                    'plan_type': 'fixed',
                    'description': 'Basic fixed-rate electricity plan for residential customers',
                    'short_description': 'Affordable fixed-rate electricity',
                    'base_price': Decimal('0.25'),
                    'monthly_fee': Decimal('15.00'),
                    'setup_fee': Decimal('0.00'),
                    'status': 'active',
                    'available_from': timezone.now(),
                    'minimum_term_months': 12,
                    'is_featured': True
                },
                {
                    'plan_code': 'ELEC-PREMIUM-001',
                    'plan_name': 'Premium Electricity Plan',
                    'service_type': 'electricity',
                    'plan_type': 'variable',
                    'description': 'Premium variable-rate electricity plan with green energy options',
                    'short_description': 'Premium variable-rate with green energy',
                    'base_price': Decimal('0.22'),
                    'monthly_fee': Decimal('20.00'),
                    'setup_fee': Decimal('0.00'),
                    'status': 'active',
                    'available_from': timezone.now(),
                    'minimum_term_months': 24,
                    'is_featured': False
                },
                {
                    'plan_code': 'BB-FIBRE-100',
                    'plan_name': 'Fibre 100 Broadband',
                    'service_type': 'broadband',
                    'plan_type': 'unlimited',
                    'description': 'High-speed fibre broadband with unlimited data',
                    'short_description': '100Mbps fibre with unlimited data',
                    'base_price': Decimal('0.00'),
                    'monthly_fee': Decimal('79.99'),
                    'setup_fee': Decimal('99.00'),
                    'status': 'active',
                    'available_from': timezone.now(),
                    'minimum_term_months': 12,
                    'is_featured': True,
                    'service_config': {
                        'download_speed': '100 Mbps',
                        'upload_speed': '20 Mbps',
                        'data_allowance': 'Unlimited'
                    }
                },
                {
                    'plan_code': 'MOBILE-POSTPAID-20GB',
                    'plan_name': 'Mobile 20GB Plan',
                    'service_type': 'mobile',
                    'plan_type': 'postpaid',
                    'description': '20GB mobile plan with unlimited calls and texts',
                    'short_description': '20GB with unlimited calls/texts',
                    'base_price': Decimal('0.00'),
                    'monthly_fee': Decimal('49.99'),
                    'setup_fee': Decimal('25.00'),
                    'status': 'active',
                    'available_from': timezone.now(),
                    'minimum_term_months': 12,
                    'is_featured': True,
                    'service_config': {
                        'data_allowance': '20GB',
                        'minutes': 'Unlimited',
                        'texts': 'Unlimited'
                    }
                }
            ]
            
            created_count = 0
            for plan_data in service_plans_data:
                plan_code = plan_data['plan_code']
                
                # Check if plan exists
                existing_plan = ServicePlan.objects.filter(
                    tenant=tenant, 
                    plan_code=plan_code
                ).first()
                
                if existing_plan and not overwrite:
                    self.stdout.write(f"   • Service plan '{plan_code}' already exists")
                    continue
                
                if existing_plan and overwrite:
                    existing_plan.delete()
                    self.stdout.write(f"   • Replaced service plan '{plan_code}'")
                
                # Create plan
                ServicePlan.objects.create(
                    tenant=tenant,
                    **plan_data
                )
                created_count += 1
                self.stdout.write(f"   • Created service plan '{plan_code}'")
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {created_count} service plans"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not create service plans: {str(e)}"))

    def create_electricity_plans(self, tenant, overwrite=False):
        """Create electricity-specific plans"""
        try:
            from web_support.public_pricing.models import ElectricityPlan
            
            electricity_plans_data = [
                {
                    'plan_id': 'ELEC-AUCKLAND-BASIC',
                    'name': 'Auckland Basic Electricity',
                    'plan_type': 'fixed',
                    'description': 'Basic fixed-rate electricity plan for Auckland customers',
                    'term': '12_month',
                    'terms_url': 'https://spoton.co.nz/terms/electricity',
                    'city': 'Auckland',
                    'base_rate': Decimal('0.2450'),
                    'rate_details': 'Fixed rate of 24.50c per kWh',
                    'monthly_charge': Decimal('15.00'),
                    'standard_daily_charge': Decimal('1.25'),
                    'standard_variable_charge': Decimal('0.2450'),
                    'low_user_daily_charge': Decimal('0.75'),
                    'low_user_variable_charge': Decimal('0.2650'),
                    'valid_from': timezone.now()
                },
                {
                    'plan_id': 'ELEC-WELLINGTON-PREMIUM',
                    'name': 'Wellington Premium Electricity',
                    'plan_type': 'tou',
                    'description': 'Time-of-use electricity plan for Wellington customers',
                    'term': '24_month',
                    'terms_url': 'https://spoton.co.nz/terms/electricity',
                    'city': 'Wellington',
                    'base_rate': Decimal('0.2200'),
                    'rate_details': 'Time-of-use rates: Peak 28c, Off-peak 18c per kWh',
                    'monthly_charge': Decimal('20.00'),
                    'standard_daily_charge': Decimal('1.50'),
                    'standard_variable_charge': Decimal('0.2200'),
                    'low_user_daily_charge': Decimal('0.90'),
                    'low_user_variable_charge': Decimal('0.2400'),
                    'valid_from': timezone.now()
                }
            ]
            
            created_count = 0
            for plan_data in electricity_plans_data:
                plan_id = plan_data['plan_id']
                
                # Check if plan exists
                existing_plan = ElectricityPlan.objects.filter(
                    tenant=tenant, 
                    plan_id=plan_id
                ).first()
                
                if existing_plan and not overwrite:
                    self.stdout.write(f"   • Electricity plan '{plan_id}' already exists")
                    continue
                
                if existing_plan and overwrite:
                    existing_plan.delete()
                    self.stdout.write(f"   • Replaced electricity plan '{plan_id}'")
                
                # Create plan
                ElectricityPlan.objects.create(
                    tenant=tenant,
                    **plan_data
                )
                created_count += 1
                self.stdout.write(f"   • Created electricity plan '{plan_id}'")
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {created_count} electricity plans"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not create electricity plans: {str(e)}"))

    def create_broadband_plans(self, tenant, overwrite=False):
        """Create broadband-specific plans"""
        try:
            from web_support.public_pricing.models import BroadbandPlan
            
            broadband_plans_data = [
                {
                    'plan_id': 'BB-FIBRE-100-AKL',
                    'name': 'Fibre 100 Auckland',
                    'plan_type': 'fibre',
                    'description': '100Mbps fibre broadband plan for Auckland',
                    'term': '12_month',
                    'terms_url': 'https://spoton.co.nz/terms/broadband',
                    'city': 'Auckland',
                    'base_rate': Decimal('79.99'),
                    'rate_details': 'Monthly charge of $79.99 for unlimited fibre',
                    'monthly_charge': Decimal('79.99'),
                    'setup_fee': Decimal('99.00'),
                    'data_allowance': 'Unlimited',
                    'download_speed': '100 Mbps',
                    'upload_speed': '20 Mbps',
                    'valid_from': timezone.now()
                },
                {
                    'plan_id': 'BB-WIRELESS-50-RURAL',
                    'name': 'Rural Wireless 50',
                    'plan_type': 'wireless',
                    'description': '50Mbps fixed wireless for rural areas',
                    'term': '12_month',
                    'terms_url': 'https://spoton.co.nz/terms/broadband',
                    'city': 'Rural',
                    'base_rate': Decimal('69.99'),
                    'rate_details': 'Monthly charge of $69.99 for rural wireless',
                    'monthly_charge': Decimal('69.99'),
                    'setup_fee': Decimal('149.00'),
                    'data_allowance': '500GB',
                    'download_speed': '50 Mbps',
                    'upload_speed': '10 Mbps',
                    'valid_from': timezone.now()
                }
            ]
            
            created_count = 0
            for plan_data in broadband_plans_data:
                plan_id = plan_data['plan_id']
                
                # Check if plan exists
                existing_plan = BroadbandPlan.objects.filter(
                    tenant=tenant, 
                    plan_id=plan_id
                ).first()
                
                if existing_plan and not overwrite:
                    self.stdout.write(f"   • Broadband plan '{plan_id}' already exists")
                    continue
                
                if existing_plan and overwrite:
                    existing_plan.delete()
                    self.stdout.write(f"   • Replaced broadband plan '{plan_id}'")
                
                # Create plan
                BroadbandPlan.objects.create(
                    tenant=tenant,
                    **plan_data
                )
                created_count += 1
                self.stdout.write(f"   • Created broadband plan '{plan_id}'")
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {created_count} broadband plans"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not create broadband plans: {str(e)}"))

    def create_mobile_plans(self, tenant, overwrite=False):
        """Create mobile-specific plans"""
        try:
            from web_support.public_pricing.models import MobilePlan
            
            mobile_plans_data = [
                {
                    'plan_id': 'MOBILE-POSTPAID-20GB',
                    'name': 'Mobile 20GB Postpaid',
                    'plan_type': 'postpaid',
                    'description': '20GB postpaid mobile plan with unlimited calls and texts',
                    'term': '12_month',
                    'terms_url': 'https://spoton.co.nz/terms/mobile',
                    'city': 'nz',
                    'base_rate': Decimal('49.99'),
                    'rate_details': 'Monthly charge of $49.99 for 20GB with unlimited calls/texts',
                    'monthly_charge': Decimal('49.99'),
                    'data_allowance': '20GB',
                    'minutes': 'Unlimited',
                    'texts': 'Unlimited',
                    'setup_fee': Decimal('25.00'),
                    'sim_card_fee': Decimal('5.00'),
                    'valid_from': timezone.now()
                },
                {
                    'plan_id': 'MOBILE-PREPAID-5GB',
                    'name': 'Mobile 5GB Prepaid',
                    'plan_type': 'prepaid',
                    'description': '5GB prepaid mobile plan',
                    'term': 'open_term',
                    'terms_url': 'https://spoton.co.nz/terms/mobile',
                    'city': 'nz',
                    'base_rate': Decimal('29.99'),
                    'rate_details': 'Monthly charge of $29.99 for 5GB prepaid',
                    'monthly_charge': Decimal('29.99'),
                    'data_allowance': '5GB',
                    'minutes': '300 minutes',
                    'texts': 'Unlimited',
                    'setup_fee': Decimal('0.00'),
                    'sim_card_fee': Decimal('5.00'),
                    'valid_from': timezone.now()
                }
            ]
            
            created_count = 0
            for plan_data in mobile_plans_data:
                plan_id = plan_data['plan_id']
                
                # Check if plan exists
                existing_plan = MobilePlan.objects.filter(
                    tenant=tenant, 
                    plan_id=plan_id
                ).first()
                
                if existing_plan and not overwrite:
                    self.stdout.write(f"   • Mobile plan '{plan_id}' already exists")
                    continue
                
                if existing_plan and overwrite:
                    existing_plan.delete()
                    self.stdout.write(f"   • Replaced mobile plan '{plan_id}'")
                
                # Create plan
                MobilePlan.objects.create(
                    tenant=tenant,
                    **plan_data
                )
                created_count += 1
                self.stdout.write(f"   • Created mobile plan '{plan_id}'")
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {created_count} mobile plans"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not create mobile plans: {str(e)}"))
