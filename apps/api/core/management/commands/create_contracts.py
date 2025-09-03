from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context, get_tenant_model
from users.models import User, Account
from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan
from decimal import Decimal
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Create sample service contracts linking customers to real service plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating the records',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be created'))
        
        # Get tenant clients to work with
        Client = get_tenant_model()
        tenant_clients = Client.objects.exclude(schema_name='public')
        
        for client in tenant_clients:
            self.stdout.write(f"\nProcessing tenant: {client.name} ({client.schema_name})")
            
            with schema_context(client.schema_name):
                self.create_contracts_for_tenant(client, dry_run)
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('DRY RUN completed - no changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('Service contracts creation completed successfully'))

    def create_contracts_for_tenant(self, client, dry_run):
        """Create contracts for a specific tenant"""
        try:
            # Import ServiceContract model - it should exist in tenant schema
            from core.contracts.models import ServiceContract
        except ImportError:
            self.stdout.write(self.style.ERROR(f'ServiceContract model not found for tenant {client.name}'))
            return
        
        # Get customer accounts for this tenant
        customer_accounts = Account.objects.filter(
            account_type__in=['residential', 'commercial']
        ).prefetch_related('user_roles__user')
        
        if not customer_accounts.exists():
            self.stdout.write(self.style.WARNING(f'No customer accounts found for tenant {client.name}'))
            return
        
        # Get available plans for this tenant
        electricity_plans = list(ElectricityPlan.objects.filter(is_active=True))
        broadband_plans = list(BroadbandPlan.objects.filter(is_active=True))
        mobile_plans = list(MobilePlan.objects.filter(is_active=True))
        
        all_plans = electricity_plans + broadband_plans + mobile_plans
        
        if not all_plans:
            self.stdout.write(self.style.WARNING(f'No service plans found for tenant {client.name}'))
            return
        
        contracts_created = 0
        
        for account in customer_accounts:
            # Get the primary user for this account
            primary_user = account.user_roles.filter(role='primary').first()
            if not primary_user:
                primary_user = account.user_roles.first()
            
            if not primary_user:
                continue
            
            customer = primary_user.user
            
            # Create 1-3 contracts per customer (different service types)
            num_contracts = random.randint(1, 3)
            selected_plans = random.sample(all_plans, min(num_contracts, len(all_plans)))
            
            for plan in selected_plans:
                # Determine plan type and create appropriate contract
                if isinstance(plan, ElectricityPlan):
                    service_type = 'electricity'
                    monthly_charge = plan.base_rate
                elif isinstance(plan, BroadbandPlan):
                    service_type = 'broadband'
                    monthly_charge = plan.monthly_charge
                elif isinstance(plan, MobilePlan):
                    service_type = 'mobile'
                    monthly_charge = plan.monthly_charge
                else:
                    continue
                
                # Generate contract data
                contract_data = {
                    'contract_number': f'CON-{client.schema_name.upper()}-{service_type.upper()}-{random.randint(100000, 999999)}',
                    'customer': customer,
                    'account': account,
                    'tenant': customer.tenant,  # Add tenant reference
                    'contract_type': service_type,
                    'service_name': plan.name,
                    'description': plan.description,
                    'status': random.choice(['active', 'pending', 'suspended']),
                    'start_date': datetime.now() - timedelta(days=random.randint(1, 365)),
                    'end_date': datetime.now() + timedelta(days=random.randint(30, 730)),
                    'initial_term_months': random.choice([12, 24, 36]),
                    'auto_renewal': random.choice([True, False]),
                    'billing_frequency': random.choice(['monthly', 'quarterly', 'annual']),
                    'billing_day': random.choice([1, 15, 28]),
                    'setup_fee': Decimal('0.00'),
                    'early_termination_fee': Decimal('100.00'),
                    'security_deposit': Decimal('50.00'),
                    'terms_version': '1.0',
                }
                
                # Add service-specific details to special_conditions
                if service_type == 'electricity':
                    contract_data['special_conditions'] = {
                        'plan_type': plan.plan_type,
                        'daily_charge': float(plan.standard_daily_charge),
                        'variable_charge': float(plan.standard_variable_charge or 0),
                        'city': plan.city,
                        'term': plan.term,
                        'monthly_charge': float(monthly_charge),
                        'plan_id': plan.plan_id
                    }
                elif service_type == 'broadband':
                    contract_data['special_conditions'] = {
                        'plan_type': plan.plan_type,
                        'download_speed': plan.download_speed,
                        'upload_speed': plan.upload_speed,
                        'data_allowance': plan.data_allowance,
                        'city': plan.city,
                        'term': plan.term,
                        'monthly_charge': float(monthly_charge),
                        'plan_id': plan.plan_id
                    }
                elif service_type == 'mobile':
                    contract_data['special_conditions'] = {
                        'plan_type': plan.plan_type,
                        'data_allowance': plan.data_allowance,
                        'minutes': plan.minutes,
                        'texts': plan.texts,
                        'term': plan.term,
                        'monthly_charge': float(monthly_charge),
                        'plan_id': plan.plan_id
                    }
                
                if not dry_run:
                    try:
                        contract = ServiceContract.objects.create(**contract_data)
                        contracts_created += 1
                        self.stdout.write(f"Created contract: {contract.contract_number} for {customer.email}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed to create contract for {customer.email}: {e}"))
                else:
                    contracts_created += 1
                    self.stdout.write(f"Would create contract: {contract_data['contract_number']} for {customer.email}")
        
        self.stdout.write(f"Total contracts {'would be created' if dry_run else 'created'} for {client.name}: {contracts_created}") 