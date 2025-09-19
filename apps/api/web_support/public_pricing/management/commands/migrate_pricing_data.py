# pricing/management/commands/migrate_pricing_data.py
from django.core.management.base import BaseCommand
from django.db import transaction
from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, PricingRegion, MobilePlan
from users.models import Tenant
from decimal import Decimal


class Command(BaseCommand):
    help = 'Migrate existing hardcoded pricing data to the new pricing models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating the records',
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant slug to use for pricing data (defaults to first available tenant)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tenant_slug = options.get('tenant')
        
        # Get the tenant to use for pricing data
        try:
            if tenant_slug:
                # Use specific tenant
                try:
                    self.tenant = Tenant.objects.get(slug=tenant_slug)
                    self.stdout.write(f'Using specified tenant: {self.tenant.name} ({tenant_slug})')
                except Tenant.DoesNotExist:
                    available_tenants = ', '.join(Tenant.objects.values_list('slug', flat=True))
                    self.stdout.write(self.style.ERROR(
                        f'Tenant with slug "{tenant_slug}" not found. '
                        f'Available tenants: {available_tenants}'
                    ))
                    return
            else:
                # Use first available tenant
                self.tenant = Tenant.objects.first()
                if not self.tenant:
                    self.stdout.write(self.style.ERROR('No tenants found. Please create a tenant first.'))
                    return
                self.stdout.write(f'Using first available tenant: {self.tenant.name} ({self.tenant.slug})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting tenant: {e}'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be created'))
        
        self.stdout.write(f'Using tenant: {self.tenant.name}')
        
        with transaction.atomic():
            # Create pricing regions
            self.create_pricing_regions(dry_run)
            
            # Create electricity plans
            self.create_electricity_plans(dry_run)
            
            # Create broadband plans
            self.create_broadband_plans(dry_run)
            
            # Create mobile plans
            self.create_mobile_plans(dry_run)
            
            if dry_run:
                # Rollback the transaction in dry run mode
                transaction.set_rollback(True)
                self.stdout.write(self.style.SUCCESS('DRY RUN completed - no changes made'))
            else:
                self.stdout.write(self.style.SUCCESS('Pricing data migration completed successfully'))

    def create_pricing_regions(self, dry_run):
        """Create pricing regions based on current city availability"""
        regions_data = [
            {'city': 'auckland', 'display_name': 'Auckland', 'service_availability': 'both'},
            {'city': 'wellington', 'display_name': 'Wellington', 'service_availability': 'electricity'},
            {'city': 'christchurch', 'display_name': 'Christchurch', 'service_availability': 'electricity'},
            {'city': 'hamilton', 'display_name': 'Hamilton', 'service_availability': 'broadband'},
            {'city': 'tauranga', 'display_name': 'Tauranga', 'service_availability': 'broadband'},
        ]
        
        for region_data in regions_data:
            if not dry_run:
                region, created = PricingRegion.objects.get_or_create(
                    city=region_data['city'],
                    defaults=region_data
                )
                if created:
                    self.stdout.write(f"Created pricing region: {region.display_name}")
                else:
                    self.stdout.write(f"Pricing region already exists: {region.display_name}")
            else:
                self.stdout.write(f"Would create pricing region: {region_data['display_name']}")

    def create_electricity_plans(self, dry_run):
        """Create electricity plans based on current hardcoded logic"""
        cities_config = {
            'auckland': {
                'standard_daily_charge': Decimal('1.50'),
                'standard_variable_charge': Decimal('0.14'),
            },
            'wellington': {
                'standard_daily_charge': Decimal('1.20'),
                'standard_variable_charge': Decimal('0.12'),
            },
            'christchurch': {
                'standard_daily_charge': Decimal('1.00'),
                'standard_variable_charge': Decimal('0.10'),
            }
        }
        
        plan_templates = [
            {
                'plan_id': 1,
                'name': 'Fixed Price Plan',
                'plan_type': 'fixed',
                'description': 'Fixed daily and variable charges for predictable billing.',
                'term': '12_month',
                'terms_url': '/legal/power/fixed',
            },
            {
                'plan_id': 2,
                'name': 'TOU Plan',
                'plan_type': 'tou',
                'description': 'Save during off-peak hours with flexible pricing.',
                'term': '12_month',
                'terms_url': '/legal/power/tou',
            },
            {
                'plan_id': 3,
                'name': 'Spot Plan',
                'plan_type': 'spot',
                'description': 'Track wholesale rates and benefit from low usage times.',
                'term': 'open_term',
                'terms_url': '/legal/power/spot',
            }
        ]
        
        for city, config in cities_config.items():
            for template in plan_templates:
                # Calculate base rate (monthly equivalent)
                base_rate = config['standard_daily_charge'] * 30
                if template['plan_type'] == 'tou':
                    base_rate += Decimal('5.00')
                elif template['plan_type'] == 'spot':
                    base_rate += Decimal('10.00')
                
                plan_data = {
                    'plan_id': template['plan_id'] + (list(cities_config.keys()).index(city) * 10),
                    'name': template['name'],
                    'plan_type': template['plan_type'],
                    'description': template['description'],
                    'term': template['term'],
                    'terms_url': template['terms_url'],
                    'city': city,
                    'base_rate': base_rate,
                    'rate_details': f"{template['name']} for {city.capitalize()}",
                    'standard_daily_charge': config['standard_daily_charge'],
                    'low_user_daily_charge': Decimal('0.30'),
                    'tenant': self.tenant,
                    'is_active': True,
                }
                
                # Add plan-specific charges
                if template['plan_type'] == 'fixed':
                    plan_data.update({
                        'standard_variable_charge': config['standard_variable_charge'],
                        'low_user_variable_charge': config['standard_variable_charge'] + Decimal('0.02'),
                    })
                elif template['plan_type'] == 'tou':
                    plan_data.update({
                        'peak_charge': Decimal('0.12'),
                        'off_peak_charge': Decimal('0.08'),
                        'low_user_peak_charge': Decimal('0.14'),
                        'low_user_off_peak_charge': Decimal('0.10'),
                    })
                elif template['plan_type'] == 'spot':
                    plan_data.update({
                        'wholesale_rate': Decimal('0.10'),
                        'network_charge': Decimal('0.05'),
                    })
                
                if not dry_run:
                    plan, created = ElectricityPlan.objects.get_or_create(
                        plan_id=plan_data['plan_id'],
                        defaults=plan_data
                    )
                    if created:
                        self.stdout.write(f"Created electricity plan: {plan.name} - {plan.city}")
                    else:
                        self.stdout.write(f"Electricity plan already exists: {plan.name} - {plan.city}")
                else:
                    self.stdout.write(f"Would create electricity plan: {plan_data['name']} - {city}")

    def create_broadband_plans(self, dry_run):
        """Create broadband plans based on current hardcoded logic"""
        cities_config = {
            'auckland': {'monthly_charge': Decimal('79.99')},
            'hamilton': {'monthly_charge': Decimal('69.99')},
            'tauranga': {'monthly_charge': Decimal('59.99')},
        }
        
        plan_templates = [
            {
                'plan_id': 101,
                'name': 'Fibre Broadband',
                'plan_type': 'fibre',
                'description': 'Unlimited broadband with fast fibre speeds.',
                'term': '12_month',
                'terms_url': '/legal/broadband/fibre',
                'download_speed': '100 Mbps',
                'upload_speed': '20 Mbps',
            },
            {
                'plan_id': 102,
                'name': 'Fixed Wireless',
                'plan_type': 'wireless',
                'description': 'Reliable connectivity over wireless, ideal for urban areas.',
                'term': 'open_term',
                'terms_url': '/legal/broadband/wireless',
                'download_speed': '50 Mbps',
                'upload_speed': '10 Mbps',
            },
            {
                'plan_id': 103,
                'name': 'Rural Broadband',
                'plan_type': 'rural',
                'description': 'Stay connected in rural zones with wider coverage.',
                'term': 'open_term',
                'terms_url': '/legal/broadband/rural',
                'download_speed': '25 Mbps',
                'upload_speed': '5 Mbps',
            }
        ]
        
        for city, config in cities_config.items():
            for template in plan_templates:
                # Calculate base rate
                base_rate = config['monthly_charge']
                if template['plan_type'] == 'wireless':
                    base_rate += Decimal('10.00')
                elif template['plan_type'] == 'rural':
                    base_rate += Decimal('15.00')
                
                plan_data = {
                    'plan_id': template['plan_id'] + (list(cities_config.keys()).index(city) * 10),
                    'name': template['name'],
                    'plan_type': template['plan_type'],
                    'description': template['description'],
                    'term': template['term'],
                    'terms_url': template['terms_url'],
                    'city': city,
                    'base_rate': base_rate,
                    'rate_details': f"{template['name']} for {city.capitalize()}",
                    'monthly_charge': config['monthly_charge'],
                    'data_allowance': 'Unlimited',
                    'download_speed': template['download_speed'],
                    'upload_speed': template['upload_speed'],
                    'tenant': self.tenant,
                    'is_active': True,
                }
                
                if not dry_run:
                    plan, created = BroadbandPlan.objects.get_or_create(
                        plan_id=plan_data['plan_id'],
                        defaults=plan_data
                    )
                    if created:
                        self.stdout.write(f"Created broadband plan: {plan.name} - {plan.city}")
                    else:
                        self.stdout.write(f"Broadband plan already exists: {plan.name} - {plan.city}")
                else:
                    self.stdout.write(f"Would create broadband plan: {plan_data['name']} - {city}")

    def create_mobile_plans(self, dry_run):
        """Create mobile plans based on current hardcoded logic"""
        plan_templates = [
            {
                'plan_id': 201,
                'name': 'Basic Mobile Plan',
                'plan_type': 'prepaid',
                'description': 'Affordable prepaid plan with essential features.',
                'term': 'open_term',
                'terms_url': '/legal/mobile/prepaid',
                'monthly_charge': Decimal('29.99'),
                'data_allowance': '5GB',
                'minutes': 'Unlimited',
                'texts': 'Unlimited',
                'setup_fee': Decimal('0.00'),
                'sim_card_fee': Decimal('5.00'),
            },
            {
                'plan_id': 202,
                'name': 'Standard Mobile Plan',
                'plan_type': 'postpaid',
                'description': 'Popular postpaid plan with generous data allowance.',
                'term': '12_month',
                'terms_url': '/legal/mobile/postpaid',
                'monthly_charge': Decimal('49.99'),
                'data_allowance': '20GB',
                'minutes': 'Unlimited',
                'texts': 'Unlimited',
                'setup_fee': Decimal('0.00'),
                'sim_card_fee': Decimal('0.00'),
                'international_minutes': '100 minutes',
                'hotspot_data': '5GB',
                'rollover_data': True,
            },
            {
                'plan_id': 203,
                'name': 'Premium Mobile Plan',
                'plan_type': 'postpaid',
                'description': 'Premium plan with unlimited data and international features.',
                'term': '24_month',
                'terms_url': '/legal/mobile/premium',
                'monthly_charge': Decimal('79.99'),
                'data_allowance': 'Unlimited',
                'minutes': 'Unlimited',
                'texts': 'Unlimited',
                'setup_fee': Decimal('0.00'),
                'sim_card_fee': Decimal('0.00'),
                'international_minutes': 'Unlimited',
                'international_texts': 'Unlimited',
                'international_data': '10GB',
                'hotspot_data': 'Unlimited',
                'rollover_data': True,
                'data_speed': 'Full Speed',
            },
            {
                'plan_id': 204,
                'name': 'Business Mobile Plan',
                'plan_type': 'business',
                'description': 'Tailored for business needs with priority support.',
                'term': '12_month',
                'terms_url': '/legal/mobile/business',
                'monthly_charge': Decimal('59.99'),
                'data_allowance': '50GB',
                'minutes': 'Unlimited',
                'texts': 'Unlimited',
                'setup_fee': Decimal('0.00'),
                'sim_card_fee': Decimal('0.00'),
                'international_minutes': '200 minutes',
                'hotspot_data': '20GB',
                'rollover_data': True,
            }
        ]
        
        for template in plan_templates:
            # Calculate base rate
            base_rate = template['monthly_charge']
            if template['plan_type'] == 'business':
                base_rate += Decimal('10.00')  # Business premium
            elif template['plan_type'] == 'postpaid' and template['monthly_charge'] > Decimal('50.00'):
                base_rate += Decimal('5.00')  # Premium postpaid
            
            plan_data = {
                'plan_id': template['plan_id'],
                'name': template['name'],
                'plan_type': template['plan_type'],
                'description': template['description'],
                'term': template['term'],
                'terms_url': template['terms_url'],
                'city': 'nz',  # Mobile plans are nationwide
                'base_rate': base_rate,
                'rate_details': f"{template['name']} - Nationwide Coverage",
                'monthly_charge': template['monthly_charge'],
                'data_allowance': template['data_allowance'],
                'minutes': template['minutes'],
                'texts': template['texts'],
                'setup_fee': template.get('setup_fee', Decimal('0.00')),
                'sim_card_fee': template.get('sim_card_fee', Decimal('0.00')),
                'data_rate': Decimal('0.00'),  # No overage charges for these plans
                'minute_rate': Decimal('0.00'),
                'text_rate': Decimal('0.00'),
                'international_minutes': template.get('international_minutes', '0'),
                'international_texts': template.get('international_texts', '0'),
                'international_data': template.get('international_data', '0'),
                'hotspot_data': template.get('hotspot_data', '0'),
                'rollover_data': template.get('rollover_data', False),
                'data_speed': template.get('data_speed', 'Full Speed'),
                'tenant': self.tenant,
                'is_active': True,
            }
            
            if not dry_run:
                plan, created = MobilePlan.objects.get_or_create(
                    plan_id=plan_data['plan_id'],
                    defaults=plan_data
                )
                if created:
                    self.stdout.write(f"Created mobile plan: {plan.name}")
                else:
                    self.stdout.write(f"Mobile plan already exists: {plan.name}")
            else:
                self.stdout.write(f"Would create mobile plan: {plan_data['name']}")
