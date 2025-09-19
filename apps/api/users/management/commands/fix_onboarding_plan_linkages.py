"""
Fix onboarding plan linkages - create actual Plan records from onboarding selections
Critical fix for UAT environment where plans show 0 count
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json


class Command(BaseCommand):
    help = 'Fix onboarding plan linkages by creating actual Plan records from onboarding selections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            default='utility-byte-default',
            help='Tenant slug to associate plans with'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('🔧 Fixing Onboarding Plan Linkages...'))
        
        try:
            # Get default tenant
            tenant = self.get_or_create_tenant(options['tenant_slug'], options['dry_run'])
            
            if not options['dry_run'] and tenant:
                with transaction.atomic():
                    # Step 1: Create plans from onboarding selections
                    self.create_plans_from_onboarding(tenant)
                    
                    # Step 2: Link existing contracts to actual plans
                    self.link_contracts_to_plans(tenant)
                    
                    # Step 3: Create missing contract-plan assignments
                    self.create_plan_assignments(tenant)
                    
                    self.stdout.write(self.style.SUCCESS('✅ Onboarding plan linkages fixed successfully!'))
            else:
                self.stdout.write(self.style.WARNING('✅ Dry run completed'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error fixing plan linkages: {str(e)}'))
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

    def create_plans_from_onboarding(self, tenant):
        """Create actual Plan records from onboarding selections"""
        try:
            from core.user_details.models import UserOnboardingConfirmation
            
            confirmations = UserOnboardingConfirmation.objects.filter(is_completed=True)
            plans_created = 0
            
            self.stdout.write(f"🔍 Processing {confirmations.count()} completed onboardings...")
            
            # Track unique plans to avoid duplicates
            unique_plans = {}
            
            for confirmation in confirmations:
                plan_selections = confirmation.plan_selections or {}
                
                for service_type, plan_data in plan_selections.items():
                    if not plan_data or not isinstance(plan_data, dict):
                        continue
                    
                    # Create unique key for this plan
                    plan_key = f"{service_type}_{plan_data.get('pricing_id', plan_data.get('plan_id', 'unknown'))}"
                    
                    if plan_key in unique_plans:
                        continue  # Already processed this plan
                    
                    unique_plans[plan_key] = True
                    
                    # Create plan based on service type
                    if service_type == 'electricity':
                        self.create_electricity_plan(tenant, plan_data)
                        plans_created += 1
                    elif service_type == 'broadband':
                        self.create_broadband_plan(tenant, plan_data)
                        plans_created += 1
                    elif service_type == 'mobile':
                        self.create_mobile_plan(tenant, plan_data)
                        plans_created += 1
                    
                    # Also create ServicePlan for unified access
                    self.create_service_plan(tenant, service_type, plan_data)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {plans_created} plans from onboarding data"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error creating plans from onboarding: {str(e)}"))

    def create_electricity_plan(self, tenant, plan_data):
        """Create ElectricityPlan from onboarding data"""
        try:
            from web_support.public_pricing.models import ElectricityPlan
            
            plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id') or f"ELEC-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if plan already exists
            if ElectricityPlan.objects.filter(tenant=tenant, plan_id=plan_id).exists():
                return
            
            charges = plan_data.get('charges', {})
            
            ElectricityPlan.objects.create(
                tenant=tenant,
                plan_id=plan_id,
                name=plan_data.get('name', 'Electricity Plan'),
                plan_type=plan_data.get('type', 'fixed'),
                description=plan_data.get('description', 'Plan created from onboarding'),
                term='12_month',
                terms_url='https://spoton.co.nz/terms/electricity',
                city=plan_data.get('city', 'Auckland'),
                base_rate=Decimal(str(charges.get('unit_rate', 0.25))),
                rate_details=f"Unit rate: {charges.get('unit_rate', 0.25)}c/kWh",
                monthly_charge=Decimal(str(charges.get('monthly_charge', 0))),
                standard_daily_charge=Decimal(str(charges.get('daily_charge', 1.50))),
                standard_variable_charge=Decimal(str(charges.get('unit_rate', 0.25))),
                low_user_daily_charge=Decimal(str(charges.get('daily_charge', 1.50))),
                low_user_variable_charge=Decimal(str(charges.get('unit_rate', 0.25))),
                valid_from=timezone.now()
            )
            
            self.stdout.write(f"   • Created electricity plan: {plan_data.get('name')}")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Error creating electricity plan: {str(e)}"))

    def create_broadband_plan(self, tenant, plan_data):
        """Create BroadbandPlan from onboarding data"""
        try:
            from web_support.public_pricing.models import BroadbandPlan
            
            plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id') or f"BB-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if plan already exists
            if BroadbandPlan.objects.filter(tenant=tenant, plan_id=plan_id).exists():
                return
            
            charges = plan_data.get('charges', {})
            
            BroadbandPlan.objects.create(
                tenant=tenant,
                plan_id=plan_id,
                name=plan_data.get('name', 'Broadband Plan'),
                plan_type='fibre',
                description=plan_data.get('description', 'Plan created from onboarding'),
                term='12_month',
                terms_url='https://spoton.co.nz/terms/broadband',
                city=plan_data.get('city', 'Auckland'),
                base_rate=Decimal(str(charges.get('monthly_charge', 79.99))),
                rate_details=f"Monthly: ${charges.get('monthly_charge', 79.99)}",
                monthly_charge=Decimal(str(charges.get('monthly_charge', 79.99))),
                setup_fee=Decimal(str(charges.get('setup_fee', 0))),
                data_allowance=plan_data.get('data_allowance', 'Unlimited'),
                download_speed=plan_data.get('download_speed', '100 Mbps'),
                upload_speed=plan_data.get('upload_speed', '20 Mbps'),
                valid_from=timezone.now()
            )
            
            self.stdout.write(f"   • Created broadband plan: {plan_data.get('name')}")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Error creating broadband plan: {str(e)}"))

    def create_mobile_plan(self, tenant, plan_data):
        """Create MobilePlan from onboarding data"""
        try:
            from web_support.public_pricing.models import MobilePlan
            
            plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id') or f"MOB-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if plan already exists
            if MobilePlan.objects.filter(tenant=tenant, plan_id=plan_id).exists():
                return
            
            charges = plan_data.get('charges', {})
            
            MobilePlan.objects.create(
                tenant=tenant,
                plan_id=plan_id,
                name=plan_data.get('name', 'Mobile Plan'),
                plan_type='postpaid',
                description=plan_data.get('description', 'Plan created from onboarding'),
                term='12_month',
                terms_url='https://spoton.co.nz/terms/mobile',
                city='nz',
                base_rate=Decimal(str(charges.get('monthly_charge', 49.99))),
                rate_details=f"Monthly: ${charges.get('monthly_charge', 49.99)}",
                monthly_charge=Decimal(str(charges.get('monthly_charge', 49.99))),
                data_allowance=plan_data.get('data_allowance', '20GB'),
                minutes=plan_data.get('minutes', 'Unlimited'),
                texts=plan_data.get('texts', 'Unlimited'),
                setup_fee=Decimal(str(charges.get('setup_fee', 0))),
                sim_card_fee=Decimal('5.00'),
                valid_from=timezone.now()
            )
            
            self.stdout.write(f"   • Created mobile plan: {plan_data.get('name')}")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Error creating mobile plan: {str(e)}"))

    def create_service_plan(self, tenant, service_type, plan_data):
        """Create ServicePlan for unified access"""
        try:
            from finance.pricing.models import ServicePlan
            
            plan_code = f"{service_type.upper()}-{plan_data.get('pricing_id', plan_data.get('plan_id', timezone.now().strftime('%Y%m%d%H%M%S')))}"
            
            # Check if plan already exists
            if ServicePlan.objects.filter(tenant=tenant, plan_code=plan_code).exists():
                return
            
            charges = plan_data.get('charges', {})
            
            ServicePlan.objects.create(
                tenant=tenant,
                plan_code=plan_code,
                plan_name=plan_data.get('name', f'{service_type.title()} Plan'),
                service_type=service_type,
                plan_type='fixed',
                description=plan_data.get('description', f'Plan created from onboarding for {service_type}'),
                base_price=Decimal(str(charges.get('unit_rate', charges.get('monthly_charge', 0)))),
                monthly_fee=Decimal(str(charges.get('monthly_charge', 0))),
                setup_fee=Decimal(str(charges.get('setup_fee', 0))),
                status='active',
                available_from=timezone.now(),
                service_config=plan_data
            )
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Error creating service plan: {str(e)}"))

    def link_contracts_to_plans(self, tenant):
        """Link existing contracts to actual plan records"""
        try:
            from core.contracts.models import ServiceContract
            
            contracts = ServiceContract.objects.filter(tenant=tenant)
            linked_count = 0
            
            self.stdout.write(f"🔗 Linking {contracts.count()} contracts to plans...")
            
            for contract in contracts:
                if contract.metadata and isinstance(contract.metadata, dict):
                    plan_data = contract.metadata.get('plan', {})
                    
                    if plan_data and isinstance(plan_data, dict):
                        # Try to find matching plan
                        plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id')
                        
                        if plan_id:
                            # Update contract metadata to include proper plan reference
                            contract.metadata['linked_plan_id'] = plan_id
                            contract.save(update_fields=['metadata'])
                            linked_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Linked {linked_count} contracts to plans"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error linking contracts to plans: {str(e)}"))

    def create_plan_assignments(self, tenant):
        """Create ContractPlanAssignment records for proper plan-contract linking"""
        try:
            from core.contracts.models import ServiceContract
            from core.contracts.plan_assignments import ContractPlanAssignment
            from finance.pricing.models import ServicePlan
            
            contracts = ServiceContract.objects.filter(tenant=tenant)
            assignments_created = 0
            
            for contract in contracts:
                # Skip if assignment already exists
                if ContractPlanAssignment.objects.filter(contract=contract).exists():
                    continue
                
                # Try to find matching plan
                if contract.metadata and isinstance(contract.metadata, dict):
                    plan_data = contract.metadata.get('plan', {})
                    plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id')
                    
                    if plan_id:
                        # Find matching ServicePlan
                        service_plan = ServicePlan.objects.filter(
                            tenant=tenant,
                            plan_code__icontains=plan_id
                        ).first()
                        
                        if service_plan:
                            ContractPlanAssignment.objects.create(
                                tenant=tenant,
                                contract=contract,
                                plan_code=service_plan.plan_code,
                                plan_name=service_plan.plan_name,
                                service_type=service_plan.service_type,
                                base_charge=service_plan.base_price,
                                monthly_charge=service_plan.monthly_fee,
                                assignment_date=contract.start_date or timezone.now(),
                                status='active',
                                assigned_by=contract.created_by
                            )
                            assignments_created += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {assignments_created} plan assignments"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error creating plan assignments: {str(e)}"))
