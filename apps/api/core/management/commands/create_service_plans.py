#!/usr/bin/env python3
"""
Management command to create actual service plans in the database
This replaces the placeholder/sample data with real database records
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from users.models import Tenant
from finance.pricing.models import ServicePlan, Tariff
from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan


class Command(BaseCommand):
    help = 'Create actual service plans in the database for both tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Create plans for specific tenant slug (acme-energy or stellar-utilities)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating service plans...'))
        
        # Get tenants
        tenants = []
        if options['tenant']:
            try:
                tenant = Tenant.objects.get(slug=options['tenant'])
                tenants = [tenant]
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Tenant {options["tenant"]} not found'))
                return
        else:
            tenants = Tenant.objects.filter(slug__in=['acme-energy', 'stellar-utilities'])

        if not tenants:
            self.stdout.write(self.style.ERROR('❌ No tenants found'))
            return

        for tenant in tenants:
            self.stdout.write(f'\n📋 Creating plans for: {tenant.name}')
            self.create_plans_for_tenant(tenant)

        self.stdout.write(self.style.SUCCESS('\n✅ Service plans creation completed!'))

    def create_plans_for_tenant(self, tenant):
        """Create plans for a specific tenant"""
        
        # Switch to tenant schema
        client = Client.objects.get(business_tenant=tenant)
        
        # Set the schema for this tenant
        from django.db import connection
        connection.set_schema(client.schema_name)
        
        try:
            with transaction.atomic():
                # Create electricity plans
                self.create_electricity_plans(tenant)
                
                # Create broadband plans  
                self.create_broadband_plans(tenant)
                
                # Create mobile plans
                self.create_mobile_plans(tenant)
                
                # Create generic service plans
                self.create_generic_service_plans(tenant)
                
                self.stdout.write(f'  ✅ Plans created for {tenant.name}')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Error creating plans for {tenant.name}: {str(e)}')
        finally:
            # Reset to public schema
            connection.set_schema('public')

    def create_electricity_plans(self, tenant):
        """Create electricity plans"""
        
        electricity_plans = [
            {
                'plan_id': 1001,
                'name': 'Fixed Rate Residential',
                'plan_type': 'fixed',
                'description': 'Stable electricity pricing for residential customers with fixed daily and unit rates',
                'term': '12_month',
                'terms_url': 'https://terms.example.com/electricity/fixed',
                'city': 'wellington',
                'base_rate': Decimal('0.28'),
                'rate_details': 'Fixed rate plan with no surprises. Daily charge and unit rate remain constant.',
                'standard_daily_charge': Decimal('1.50'),
                'standard_variable_charge': Decimal('0.28'),
                'low_user_daily_charge': Decimal('0.30'),
                'low_user_variable_charge': Decimal('0.32'),
            },
            {
                'plan_id': 1002,
                'name': 'Green Energy Plus',
                'plan_type': 'fixed',
                'description': '100% renewable electricity with carbon neutral guarantee',
                'term': '24_month',
                'terms_url': 'https://terms.example.com/electricity/green',
                'city': 'wellington',
                'base_rate': Decimal('0.30'),
                'rate_details': 'Premium green energy plan sourced from 100% renewable sources.',
                'standard_daily_charge': Decimal('1.60'),
                'standard_variable_charge': Decimal('0.30'),
                'low_user_daily_charge': Decimal('0.35'),
                'low_user_variable_charge': Decimal('0.34'),
            },
            {
                'plan_id': 1003,
                'name': 'Business Power Pro',
                'plan_type': 'fixed',
                'description': 'High-capacity electricity for business operations',
                'term': 'open_term',
                'terms_url': 'https://terms.example.com/electricity/business',
                'city': 'wellington',
                'base_rate': Decimal('0.25'),
                'rate_details': 'Commercial rate plan with volume discounts and priority support.',
                'standard_daily_charge': Decimal('2.50'),
                'standard_variable_charge': Decimal('0.25'),
                'low_user_daily_charge': Decimal('2.50'),
                'low_user_variable_charge': Decimal('0.25'),
            }
        ]

        for plan_data in electricity_plans:
            plan, created = ElectricityPlan.objects.get_or_create(
                plan_id=plan_data['plan_id'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'    ⚡ Created electricity plan: {plan.name}')

    def create_broadband_plans(self, tenant):
        """Create broadband plans"""
        
        broadband_plans = [
            {
                'plan_id': 2001,
                'name': 'Fibre Basic 100/20',
                'plan_type': 'fibre',
                'description': 'Reliable fibre broadband for everyday use',
                'term': '12_month',
                'terms_url': 'https://terms.example.com/broadband/basic',
                'city': 'wellington',
                'base_rate': Decimal('69.99'),
                'rate_details': 'Entry-level fibre plan perfect for streaming and browsing.',
                'monthly_charge': Decimal('69.99'),
                'setup_fee': Decimal('0.00'),
                'data_allowance': 'Unlimited',
                'download_speed': '100 Mbps',
                'upload_speed': '20 Mbps',
            },
            {
                'plan_id': 2002,
                'name': 'Fibre Pro 300/100',
                'plan_type': 'fibre',
                'description': 'High-performance fibre for demanding users',
                'term': '24_month',
                'terms_url': 'https://terms.example.com/broadband/pro',
                'city': 'wellington',
                'base_rate': Decimal('89.99'),
                'rate_details': 'Premium fibre plan with faster speeds and WiFi 6 router included.',
                'monthly_charge': Decimal('89.99'),
                'setup_fee': Decimal('0.00'),
                'data_allowance': 'Unlimited',
                'download_speed': '300 Mbps',
                'upload_speed': '100 Mbps',
            },
            {
                'plan_id': 2003,
                'name': 'Business Fibre 1000/500',
                'plan_type': 'fibre',
                'description': 'Enterprise-grade fibre with SLA guarantee',
                'term': 'open_term',
                'terms_url': 'https://terms.example.com/broadband/business',
                'city': 'wellington',
                'base_rate': Decimal('199.99'),
                'rate_details': 'Business-grade fibre with guaranteed uptime and priority support.',
                'monthly_charge': Decimal('199.99'),
                'setup_fee': Decimal('99.00'),
                'data_allowance': 'Unlimited',
                'download_speed': '1000 Mbps',
                'upload_speed': '500 Mbps',
            }
        ]

        for plan_data in broadband_plans:
            plan, created = BroadbandPlan.objects.get_or_create(
                plan_id=plan_data['plan_id'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'    🌐 Created broadband plan: {plan.name}')

    def create_mobile_plans(self, tenant):
        """Create mobile plans"""
        
        mobile_plans = [
            {
                'plan_id': 3001,
                'name': 'Essential Mobile',
                'plan_type': 'postpaid',
                'description': 'Basic mobile plan for light users',
                'term': '12_month',
                'terms_url': 'https://terms.example.com/mobile/essential',
                'city': 'nz',
                'base_rate': Decimal('29.99'),
                'rate_details': 'Affordable mobile plan with essential features.',
                'monthly_charge': Decimal('29.99'),
                'data_allowance': '5GB',
                'minutes': 'Unlimited',
                'texts': 'Unlimited',
                'setup_fee': Decimal('0.00'),
                'sim_card_fee': Decimal('5.00'),
                'data_rate': Decimal('10.00'),
                'data_speed': '4G',
            },
            {
                'plan_id': 3002,
                'name': 'Mobile Plus',
                'plan_type': 'postpaid',
                'description': 'Comprehensive mobile plan with 5G',
                'term': '24_month',
                'terms_url': 'https://terms.example.com/mobile/plus',
                'city': 'nz',
                'base_rate': Decimal('49.99'),
                'rate_details': 'Feature-rich mobile plan with 5G access and international inclusions.',
                'monthly_charge': Decimal('49.99'),
                'data_allowance': '20GB',
                'minutes': 'Unlimited',
                'texts': 'Unlimited',
                'setup_fee': Decimal('0.00'),
                'sim_card_fee': Decimal('5.00'),
                'data_rate': Decimal('10.00'),
                'international_minutes': '30 minutes',
                'international_texts': '100 texts',
                'data_speed': '5G',
                'rollover_data': True,
            },
            {
                'plan_id': 3003,
                'name': 'Business Mobile Pro',
                'plan_type': 'business',
                'description': 'Enterprise mobile with unlimited data',
                'term': 'open_term',
                'terms_url': 'https://terms.example.com/mobile/business',
                'city': 'nz',
                'base_rate': Decimal('79.99'),
                'rate_details': 'Business mobile plan with unlimited data and global roaming.',
                'monthly_charge': Decimal('79.99'),
                'data_allowance': 'Unlimited',
                'minutes': 'Unlimited',
                'texts': 'Unlimited',
                'setup_fee': Decimal('0.00'),
                'sim_card_fee': Decimal('0.00'),
                'international_minutes': 'Unlimited',
                'international_texts': 'Unlimited',
                'international_data': '10GB',
                'data_speed': '5G Priority',
                'rollover_data': False,
            }
        ]

        for plan_data in mobile_plans:
            plan, created = MobilePlan.objects.get_or_create(
                plan_id=plan_data['plan_id'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'    📱 Created mobile plan: {plan.name}')

    def create_generic_service_plans(self, tenant):
        """Create generic service plans that can be used for contracts"""
        
        # Create electricity service plans
        electricity_plans = [
            {
                'plan_code': f'{tenant.slug.upper()}-ELE-001',
                'plan_name': 'Residential Fixed Rate',
                'service_type': 'electricity',
                'plan_type': 'fixed',
                'description': 'Standard residential electricity plan with fixed rates',
                'base_price': Decimal('150.00'),
                'monthly_fee': Decimal('150.00'),
                'service_config': {
                    'daily_charge': 1.50,
                    'unit_rate': 0.28,
                    'low_user_daily': 0.30,
                    'low_user_rate': 0.32
                },
                'available_from': timezone.now(),
                'status': 'active'
            },
            {
                'plan_code': f'{tenant.slug.upper()}-ELE-002',
                'plan_name': 'Green Energy Premium',
                'service_type': 'electricity',
                'plan_type': 'fixed',
                'description': '100% renewable energy with premium features',
                'base_price': Decimal('165.00'),
                'monthly_fee': Decimal('165.00'),
                'service_config': {
                    'daily_charge': 1.60,
                    'unit_rate': 0.30,
                    'renewable': True,
                    'carbon_neutral': True
                },
                'available_from': timezone.now(),
                'status': 'active'
            }
        ]

        # Create broadband service plans
        broadband_plans = [
            {
                'plan_code': f'{tenant.slug.upper()}-BB-001',
                'plan_name': 'Fibre Basic',
                'service_type': 'broadband',
                'plan_type': 'unlimited',
                'description': 'Basic fibre broadband with unlimited data',
                'base_price': Decimal('69.99'),
                'monthly_fee': Decimal('69.99'),
                'service_config': {
                    'download_speed': '100 Mbps',
                    'upload_speed': '20 Mbps',
                    'data_allowance': 'Unlimited',
                    'technology': 'fibre'
                },
                'available_from': timezone.now(),
                'status': 'active'
            },
            {
                'plan_code': f'{tenant.slug.upper()}-BB-002',
                'plan_name': 'Fibre Pro',
                'service_type': 'broadband',
                'plan_type': 'unlimited',
                'description': 'High-speed fibre with premium features',
                'base_price': Decimal('89.99'),
                'monthly_fee': Decimal('89.99'),
                'service_config': {
                    'download_speed': '300 Mbps',
                    'upload_speed': '100 Mbps',
                    'data_allowance': 'Unlimited',
                    'technology': 'fibre',
                    'wifi6_router': True
                },
                'available_from': timezone.now(),
                'status': 'active'
            }
        ]

        # Create mobile service plans
        mobile_plans = [
            {
                'plan_code': f'{tenant.slug.upper()}-MOB-001',
                'plan_name': 'Mobile Essential',
                'service_type': 'mobile',
                'plan_type': 'postpaid',
                'description': 'Essential mobile plan with basic features',
                'base_price': Decimal('29.99'),
                'monthly_fee': Decimal('29.99'),
                'service_config': {
                    'data_allowance': '5GB',
                    'minutes': 'Unlimited',
                    'texts': 'Unlimited',
                    'network': '4G'
                },
                'available_from': timezone.now(),
                'status': 'active'
            },
            {
                'plan_code': f'{tenant.slug.upper()}-MOB-002',
                'plan_name': 'Mobile Plus',
                'service_type': 'mobile',
                'plan_type': 'postpaid',
                'description': 'Premium mobile plan with 5G and international',
                'base_price': Decimal('49.99'),
                'monthly_fee': Decimal('49.99'),
                'service_config': {
                    'data_allowance': '20GB',
                    'minutes': 'Unlimited',
                    'texts': 'Unlimited',
                    'network': '5G',
                    'international_minutes': 30,
                    'international_texts': 100
                },
                'available_from': timezone.now(),
                'status': 'active'
            }
        ]

        all_plans = electricity_plans + broadband_plans + mobile_plans

        for plan_data in all_plans:
            plan, created = ServicePlan.objects.get_or_create(
                plan_code=plan_data['plan_code'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'    📄 Created service plan: {plan.plan_name}')


if __name__ == '__main__':
    command = Command()
    command.handle() 