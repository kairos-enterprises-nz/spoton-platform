"""
Django management command to create sample connections and plans data
"""
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta

from users.models import Tenant, User, Account, AccountAddress
from energy.connections.models import Connection
from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan


class Command(BaseCommand):
    help = 'Create sample connections and plans data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='SpotOn Energy Client',
            help='Name of the tenant to create data for'
        )

    def handle(self, *args, **options):
        tenant_name = options['tenant_name']
        
        try:
            # Get the tenant
            tenant = Tenant.objects.get(name=tenant_name)
            self.stdout.write(f"Found tenant: {tenant.name}")
            
            # Create sample plans first
            self.create_sample_plans()
            
            # Create sample connections
            self.create_sample_connections(tenant)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created sample connections and plans')
            )
            
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant "{tenant_name}" not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample data: {str(e)}')
            )

    def create_sample_plans(self):
        """Create sample service plans"""
        self.stdout.write("Creating sample plans...")
        
        # Electricity Plans
        electricity_plans = [
            {
                'plan_id': 1001,
                'name': 'SpotOn Fixed Electricity',
                'plan_type': 'fixed',
                'description': 'Fixed rate electricity plan with competitive pricing',
                'term': '12_month',
                'city': 'wellington',
                'base_rate': Decimal('0.25'),
                'rate_details': 'Fixed rate of 25c per kWh',
                'standard_daily_charge': Decimal('1.20'),
                'standard_variable_charge': Decimal('0.25'),
                'low_user_daily_charge': Decimal('0.30'),
                'low_user_variable_charge': Decimal('0.27'),
                'terms_url': 'https://spoton.co.nz/terms/electricity',
            },
            {
                'plan_id': 1002,
                'name': 'SpotOn Green Electricity',
                'plan_type': 'fixed',
                'description': '100% renewable electricity plan',
                'term': '24_month',
                'city': 'wellington',
                'base_rate': Decimal('0.28'),
                'rate_details': 'Premium renewable energy at 28c per kWh',
                'standard_daily_charge': Decimal('1.50'),
                'standard_variable_charge': Decimal('0.28'),
                'low_user_daily_charge': Decimal('0.40'),
                'low_user_variable_charge': Decimal('0.30'),
                'terms_url': 'https://spoton.co.nz/terms/electricity',
            },
            {
                'plan_id': 1003,
                'name': 'SpotOn Time of Use',
                'plan_type': 'tou',
                'description': 'Time of use plan with peak and off-peak rates',
                'term': '12_month',
                'city': 'wellington',
                'base_rate': Decimal('0.22'),
                'rate_details': 'Variable rates: Peak 35c, Off-peak 18c per kWh',
                'standard_daily_charge': Decimal('1.00'),
                'standard_variable_charge': Decimal('0.22'),
                'low_user_daily_charge': Decimal('0.25'),
                'low_user_variable_charge': Decimal('0.24'),
                'peak_charge': Decimal('0.35'),
                'off_peak_charge': Decimal('0.18'),
                'terms_url': 'https://spoton.co.nz/terms/electricity',
            }
        ]
        
        for plan_data in electricity_plans:
            plan, created = ElectricityPlan.objects.get_or_create(
                plan_id=plan_data['plan_id'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f"  Created electricity plan: {plan.name}")
            else:
                self.stdout.write(f"  Electricity plan exists: {plan.name}")

        # Broadband Plans
        broadband_plans = [
            {
                'plan_id': 2001,
                'name': 'SpotOn Fibre Basic',
                'plan_type': 'fibre',
                'description': 'Basic fibre broadband for everyday use',
                'term': '12_month',
                'city': 'wellington',
                'base_rate': Decimal('69.99'),
                'rate_details': 'Basic fibre plan with reliable speeds',
                'monthly_charge': Decimal('69.99'),
                'setup_fee': Decimal('0.00'),
                'data_allowance': 'Unlimited',
                'download_speed': '100 Mbps',
                'upload_speed': '20 Mbps',
                'terms_url': 'https://spoton.co.nz/terms/broadband',
            },
            {
                'plan_id': 2002,
                'name': 'SpotOn Fibre Pro',
                'plan_type': 'fibre',
                'description': 'High-speed fibre for families and professionals',
                'term': '24_month',
                'city': 'wellington',
                'base_rate': Decimal('89.99'),
                'rate_details': 'Professional grade fibre with faster speeds',
                'monthly_charge': Decimal('89.99'),
                'setup_fee': Decimal('0.00'),
                'data_allowance': 'Unlimited',
                'download_speed': '300 Mbps',
                'upload_speed': '100 Mbps',
                'terms_url': 'https://spoton.co.nz/terms/broadband',
            },
            {
                'plan_id': 2003,
                'name': 'SpotOn Fibre Gigabit',
                'plan_type': 'fibre',
                'description': 'Ultra-fast gigabit fibre for power users',
                'term': '12_month',
                'city': 'wellington',
                'base_rate': Decimal('129.99'),
                'rate_details': 'Gigabit speeds for maximum performance',
                'monthly_charge': Decimal('129.99'),
                'setup_fee': Decimal('99.00'),
                'data_allowance': 'Unlimited',
                'download_speed': '1000 Mbps',
                'upload_speed': '500 Mbps',
                'terms_url': 'https://spoton.co.nz/terms/broadband',
            }
        ]
        
        for plan_data in broadband_plans:
            plan, created = BroadbandPlan.objects.get_or_create(
                plan_id=plan_data['plan_id'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f"  Created broadband plan: {plan.name}")
            else:
                self.stdout.write(f"  Broadband plan exists: {plan.name}")

        # Mobile Plans
        mobile_plans = [
            {
                'plan_id': 3001,
                'name': 'SpotOn Mobile Essential',
                'plan_type': 'prepaid',
                'description': 'Essential mobile plan with good data allowance',
                'term': 'open_term',
                'base_rate': Decimal('29.99'),
                'rate_details': 'Monthly prepaid plan with 5GB data',
                'monthly_charge': Decimal('29.99'),
                'setup_fee': Decimal('0.00'),
                'data_allowance': '5GB',
                'call_minutes': 'Unlimited',
                'text_messages': 'Unlimited',
                'terms_url': 'https://spoton.co.nz/terms/mobile',
            },
            {
                'plan_id': 3002,
                'name': 'SpotOn Mobile Plus',
                'plan_type': 'postpaid',
                'description': 'Popular mobile plan with generous data',
                'term': '12_month',
                'base_rate': Decimal('49.99'),
                'rate_details': 'Monthly postpaid plan with 20GB data',
                'monthly_charge': Decimal('49.99'),
                'setup_fee': Decimal('0.00'),
                'data_allowance': '20GB',
                'call_minutes': 'Unlimited',
                'text_messages': 'Unlimited',
                'terms_url': 'https://spoton.co.nz/terms/mobile',
            },
            {
                'plan_id': 3003,
                'name': 'SpotOn Mobile Unlimited',
                'plan_type': 'postpaid',
                'description': 'Unlimited mobile plan for heavy users',
                'term': '24_month',
                'base_rate': Decimal('79.99'),
                'rate_details': 'Monthly postpaid plan with unlimited data',
                'monthly_charge': Decimal('79.99'),
                'setup_fee': Decimal('25.00'),
                'data_allowance': 'Unlimited',
                'call_minutes': 'Unlimited',
                'text_messages': 'Unlimited',
                'terms_url': 'https://spoton.co.nz/terms/mobile',
            }
        ]
        
        for plan_data in mobile_plans:
            plan, created = MobilePlan.objects.get_or_create(
                plan_id=plan_data['plan_id'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f"  Created mobile plan: {plan.name}")
            else:
                self.stdout.write(f"  Mobile plan exists: {plan.name}")

    def create_sample_connections(self, tenant):
        """Create sample connections for existing accounts"""
        self.stdout.write("Creating sample connections...")
        
        # Get existing accounts in the tenant
        accounts = Account.objects.filter(tenant=tenant)
        
        if not accounts.exists():
            self.stdout.write("No accounts found. Creating sample accounts first...")
            # Create sample accounts if none exist
            self.create_sample_accounts(tenant)
            accounts = Account.objects.filter(tenant=tenant)
        
        for account in accounts:
            self.stdout.write(f"  Creating connections for account: {account.account_number}")
            
            # Get or create a service address for this account
            service_address = account.addresses.first()
            if not service_address:
                service_address = AccountAddress.objects.create(
                    account=account,
                    address_line1=f"{account.account_number[4:7]} Example Street",
                    city="Wellington",
                    postal_code="6011",
                    country="New Zealand",
                    address_type="service"
                )
            
            # Create electricity connection
            elec_connection, created = Connection.objects.get_or_create(
                tenant=tenant,
                account=account,
                service_type='electricity',
                connection_identifier=f"ICP{account.account_number[-6:]}001",
                defaults={
                    'service_address': service_address,
                    'icp_code': f"ICP{account.account_number[-6:]}001",
                    'gxp_code': 'WLG001',
                    'network_code': 'WEL',
                    'status': 'active',
                    'connection_date': timezone.now() - timedelta(days=30),
                    'last_reading_date': timezone.now() - timedelta(days=1),
                }
            )
            if created:
                self.stdout.write(f"    Created electricity connection: {elec_connection.connection_identifier}")
            
            # Create broadband connection
            bb_connection, created = Connection.objects.get_or_create(
                tenant=tenant,
                account=account,
                service_type='broadband',
                connection_identifier=f"ONT{account.account_number[-6:]}BB",
                defaults={
                    'service_address': service_address,
                    'ont_serial': f"ONT{account.account_number[-6:]}BB",
                    'circuit_id': f"CIR{account.account_number[-4:]}",
                    'connection_type': 'fibre',
                    'status': 'active',
                    'connection_date': timezone.now() - timedelta(days=20),
                    'last_reading_date': timezone.now() - timedelta(days=1),
                }
            )
            if created:
                self.stdout.write(f"    Created broadband connection: {bb_connection.connection_identifier}")
            
            # Create mobile connection (only for first two accounts to avoid too many)
            if account == accounts.first() or account == accounts.last():
                mobile_connection, created = Connection.objects.get_or_create(
                    tenant=tenant,
                    account=account,
                    service_type='mobile',
                    connection_identifier=f"+64 21 {account.account_number[-6:]}",
                    defaults={
                        'mobile_number': f"+64 21 {account.account_number[-6:]}",
                        'sim_id': f"SIM{account.account_number[-8:]}",
                        'imei': f"35{account.account_number[-12:]}",
                        'status': 'active',
                        'connection_date': timezone.now() - timedelta(days=10),
                        'last_reading_date': timezone.now() - timedelta(days=1),
                    }
                )
                if created:
                    self.stdout.write(f"    Created mobile connection: {mobile_connection.connection_identifier}")

    def create_sample_accounts(self, tenant):
        """Create sample accounts if none exist"""
        self.stdout.write("Creating sample accounts...")
        
        # Get existing users in the tenant
        users = User.objects.filter(tenant=tenant)
        
        if not users.exists():
            self.stdout.write("No users found in tenant")
            return
        
        for i, user in enumerate(users[:3]):  # Create accounts for first 3 users
            account_number = f"ACC-{str(uuid.uuid4())[:8].upper()}-2024"
            account_type = 'residential' if i % 2 == 0 else 'commercial'
            
            account, created = Account.objects.get_or_create(
                tenant=tenant,
                account_number=account_number,
                defaults={
                    'account_type': account_type,
                    'status': 'active',
                    'created_by': user,
                }
            )
            
            if created:
                self.stdout.write(f"  Created account: {account.account_number} for user: {user.email}")
                
                # Create user account role
                from users.models import UserAccountRole
                UserAccountRole.objects.get_or_create(
                    user=user,
                    account=account,
                    defaults={'role': 'primary'}
                ) 