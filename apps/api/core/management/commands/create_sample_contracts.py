"""
Django management command to create sample contracts data for testing staff portal
"""
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, date

from users.models import Tenant, User, Account, AccountAddress, UserAccountRole
from core.contracts.models import (
    ServiceContract, ElectricityContract, BroadbandContract, MobileContract,
    ContractTemplate
)
from finance.pricing.models import ServicePlan, Tariff


class Command(BaseCommand):
    help = 'Create sample contracts data for testing staff portal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-slug',
            type=str,
            default='utility-byte-default',
            help='Slug of the tenant to create data for'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing sample data before creating new'
        )

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        clear_existing = options['clear_existing']
        
        try:
            # Get the tenant
            tenant = Tenant.objects.get(slug=tenant_slug)
            self.stdout.write(f"Found tenant: {tenant.name}")
            
            if clear_existing:
                self.clear_existing_data(tenant)
            
            # Create sample data
            self.create_sample_users(tenant)
            self.create_sample_accounts(tenant)
            self.create_sample_service_plans()
            self.create_sample_tariffs(tenant)
            self.create_sample_contract_templates(tenant)
            self.create_sample_contracts(tenant)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created sample contracts data')
            )
            
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant with slug "{tenant_slug}" not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample data: {str(e)}')
            )

    def clear_existing_data(self, tenant):
        """Clear existing sample data"""
        self.stdout.write("Clearing existing sample data...")
        
        # Clear contracts
        ServiceContract.objects.filter(tenant=tenant).delete()
        ElectricityContract.objects.filter(tenant=tenant).delete()
        BroadbandContract.objects.filter(tenant=tenant).delete()
        MobileContract.objects.filter(tenant=tenant).delete()
        
        # Clear templates and plans
        ContractTemplate.objects.filter(tenant=tenant).delete()
        Tariff.objects.filter(tenant=tenant).delete()
        
        self.stdout.write("  Cleared existing data")

    def create_sample_users(self, tenant):
        """Create sample users if they don't exist"""
        self.stdout.write("Creating sample users...")
        
        users_data = [
            {
                'email': 'testuser@email.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'user_type': 'residential',
                'is_active': True,
                'tenant': tenant
            },
            {
                'email': 'admin@spoton.co.nz',
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'staff',
                'is_staff': True,
                'is_active': True,
                'tenant': tenant
            },
            {
                'email': 'commercial@business.co.nz',
                'first_name': 'Business',
                'last_name': 'Owner',
                'user_type': 'commercial',
                'is_active': True,
                'tenant': tenant
            }
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults=user_data
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"  Created user: {user.email}")
            else:
                self.stdout.write(f"  User exists: {user.email}")

    def create_sample_accounts(self, tenant):
        """Create sample accounts"""
        self.stdout.write("Creating sample accounts...")
        
        # Get users
        user1 = User.objects.get(email='testuser@email.com')
        user2 = User.objects.get(email='admin@spoton.co.nz')
        user3 = User.objects.get(email='commercial@business.co.nz')
        
        accounts_data = [
            {
                'account_number': 'ACC-001-2024',
                'tenant': tenant,
                'account_type': 'residential',
                'status': 'active',
                'user': user1
            },
            {
                'account_number': 'ACC-002-2024',
                'tenant': tenant,
                'account_type': 'residential',
                'status': 'active',
                'user': user2
            },
            {
                'account_number': 'ACC-003-2024',
                'tenant': tenant,
                'account_type': 'commercial',
                'status': 'active',
                'user': user3
            }
        ]
        
        for account_data in accounts_data:
            user = account_data.pop('user')
            account, created = Account.objects.get_or_create(
                account_number=account_data['account_number'],
                defaults=account_data
            )
            if created:
                self.stdout.write(f"  Created account: {account.account_number}")
                
                # Create user-account relationship
                UserAccountRole.objects.get_or_create(
                    tenant=tenant,
                    user=user,
                    account=account,
                    role='owner',
                    defaults={
                        'can_manage_services': True,
                        'can_manage_billing': True,
                        'can_view_usage': True
                    }
                )
                
                # Create account address
                AccountAddress.objects.create(
                    tenant=tenant,
                    account=account,
                    address_line1=f"{account.account_number} Test Street",
                    city='Wellington',
                    region='Wellington',
                    postal_code='6011',
                    country='New Zealand',
                    address_type='service',
                    is_primary=True
                )
            else:
                self.stdout.write(f"  Account exists: {account.account_number}")

    def create_sample_service_plans(self):
        """Create sample service plans"""
        self.stdout.write("Creating sample service plans...")
        
        plans_data = [
            {
                'plan_code': 'ELE-FIXED-001',
                'plan_name': 'SpotOn Fixed Electricity',
                'service_type': 'electricity',
                'plan_type': 'fixed',
                'description': 'Fixed rate electricity plan with competitive pricing',
                'base_price': Decimal('0.25'),
                'monthly_fee': Decimal('150.00'),
                'available_from': timezone.now(),
                'status': 'active'
            },
            {
                'plan_code': 'ELE-GREEN-001',
                'plan_name': 'SpotOn Green Electricity',
                'service_type': 'electricity',
                'plan_type': 'fixed',
                'description': '100% renewable electricity plan',
                'base_price': Decimal('0.28'),
                'monthly_fee': Decimal('165.00'),
                'available_from': timezone.now(),
                'status': 'active'
            },
            {
                'plan_code': 'BB-FIBRE-001',
                'plan_name': 'SpotOn Fibre Basic',
                'service_type': 'broadband',
                'plan_type': 'unlimited',
                'description': 'Basic fibre broadband for everyday use',
                'monthly_fee': Decimal('69.99'),
                'available_from': timezone.now(),
                'status': 'active',
                'service_config': {
                    'download_speed': '100 Mbps',
                    'upload_speed': '20 Mbps',
                    'data_allowance': 'Unlimited'
                }
            },
            {
                'plan_code': 'BB-FIBRE-002',
                'plan_name': 'SpotOn Fibre Pro',
                'service_type': 'broadband',
                'plan_type': 'unlimited',
                'description': 'High-speed fibre for families and professionals',
                'monthly_fee': Decimal('89.99'),
                'available_from': timezone.now(),
                'status': 'active',
                'service_config': {
                    'download_speed': '300 Mbps',
                    'upload_speed': '100 Mbps',
                    'data_allowance': 'Unlimited'
                }
            },
            {
                'plan_code': 'MOB-ESS-001',
                'plan_name': 'SpotOn Mobile Essential',
                'service_type': 'mobile',
                'plan_type': 'prepaid',
                'description': 'Essential mobile plan with good data allowance',
                'monthly_fee': Decimal('29.99'),
                'available_from': timezone.now(),
                'status': 'active',
                'service_config': {
                    'data_allowance': '5GB',
                    'call_minutes': 'Unlimited',
                    'text_messages': 'Unlimited'
                }
            },
            {
                'plan_code': 'MOB-PLUS-001',
                'plan_name': 'SpotOn Mobile Plus',
                'service_type': 'mobile',
                'plan_type': 'postpaid',
                'description': 'Popular mobile plan with generous data',
                'monthly_fee': Decimal('49.99'),
                'available_from': timezone.now(),
                'status': 'active',
                'service_config': {
                    'data_allowance': '20GB',
                    'call_minutes': 'Unlimited',
                    'text_messages': 'Unlimited'
                }
            }
        ]
        
        for plan_data in plans_data:
            plan, created = ServicePlan.objects.get_or_create(
                plan_code=plan_data['plan_code'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f"  Created service plan: {plan.plan_name}")
            else:
                self.stdout.write(f"  Service plan exists: {plan.plan_name}")

    def create_sample_tariffs(self, tenant):
        """Create sample tariffs"""
        self.stdout.write("Creating sample tariffs...")
        
        tariffs_data = [
            {
                'tenant': tenant,
                'tariff_code': 'ELE-STD-001',
                'tariff_name': 'Standard Electricity Tariff',
                'tariff_type': 'fixed',
                'service_type': 'electricity',
                'base_rate': Decimal('0.25'),
                'daily_charge': Decimal('1.20'),
                'gst_rate': Decimal('0.15'),
                'is_active': True,
                'is_default': True,
                'eligible_customer_types': ['residential', 'commercial']
            },
            {
                'tenant': tenant,
                'tariff_code': 'BB-STD-001',
                'tariff_name': 'Standard Broadband Tariff',
                'tariff_type': 'fixed',
                'service_type': 'broadband',
                'base_rate': Decimal('69.99'),
                'gst_rate': Decimal('0.15'),
                'is_active': True,
                'is_default': True,
                'eligible_customer_types': ['residential', 'commercial']
            },
            {
                'tenant': tenant,
                'tariff_code': 'MOB-STD-001',
                'tariff_name': 'Standard Mobile Tariff',
                'tariff_type': 'fixed',
                'service_type': 'mobile',
                'base_rate': Decimal('29.99'),
                'gst_rate': Decimal('0.15'),
                'is_active': True,
                'is_default': True,
                'eligible_customer_types': ['residential', 'commercial']
            }
        ]
        
        for tariff_data in tariffs_data:
            tariff, created = Tariff.objects.get_or_create(
                tariff_code=tariff_data['tariff_code'],
                defaults=tariff_data
            )
            if created:
                self.stdout.write(f"  Created tariff: {tariff.tariff_name}")
            else:
                self.stdout.write(f"  Tariff exists: {tariff.tariff_name}")

    def create_sample_contract_templates(self, tenant):
        """Create sample contract templates"""
        self.stdout.write("Creating sample contract templates...")
        
        templates_data = [
            {
                'tenant': tenant,
                'template_code': 'ELE-RES-001',
                'template_name': 'Residential Electricity Contract',
                'service_type': 'electricity',
                'customer_segment': 'residential',
                'terms_template': 'Standard residential electricity supply terms and conditions.',
                'default_term_months': 12,
                'is_active': True,
                'is_default': True
            },
            {
                'tenant': tenant,
                'template_code': 'BB-RES-001',
                'template_name': 'Residential Broadband Contract',
                'service_type': 'broadband',
                'customer_segment': 'residential',
                'terms_template': 'Standard residential broadband service terms and conditions.',
                'default_term_months': 24,
                'is_active': True,
                'is_default': True
            },
            {
                'tenant': tenant,
                'template_code': 'MOB-RES-001',
                'template_name': 'Residential Mobile Contract',
                'service_type': 'mobile',
                'customer_segment': 'residential',
                'terms_template': 'Standard residential mobile service terms and conditions.',
                'default_term_months': 12,
                'is_active': True,
                'is_default': True
            }
        ]
        
        for template_data in templates_data:
            template, created = ContractTemplate.objects.get_or_create(
                template_code=template_data['template_code'],
                defaults=template_data
            )
            if created:
                self.stdout.write(f"  Created template: {template.template_name}")
            else:
                self.stdout.write(f"  Template exists: {template.template_name}")

    def create_sample_contracts(self, tenant):
        """Create sample contracts"""
        self.stdout.write("Creating sample contracts...")
        
        # Get accounts and templates
        accounts = list(Account.objects.filter(tenant=tenant))
        tariffs = {t.service_type: t for t in Tariff.objects.filter(tenant=tenant)}
        templates = {t.service_type: t for t in ContractTemplate.objects.filter(tenant=tenant)}
        addresses = {a.account_id: a for a in AccountAddress.objects.filter(tenant=tenant)}
        
        # Get users for contracts
        users = {role.account_id: role.user for role in UserAccountRole.objects.filter(tenant=tenant)}
        
        # Create electricity contracts
        for i, account in enumerate(accounts[:2], 1):
            contract_data = {
                'tenant': tenant,
                'contract_number': f'ELE-{account.account_number}-{i:03d}',
                'account': account,
                'template': templates['electricity'],
                'icp_code': f'ICP{i:03d}024001',
                'gxp_code': f'WLG{i:03d}',
                'network_company': 'Wellington Electricity',
                'tariff': tariffs['electricity'],
                'load_type': 'residential',
                'meter_number': f'METER{i:06d}',
                'meter_type': 'smart',
                'contract_start_date': date.today() - timedelta(days=30*i),
                'term_months': 12,
                'status': 'active',
                'signed_date': date.today() - timedelta(days=30*i),
                'signed_by_customer': True,
                'signed_by_retailer': True
            }
            
            contract, created = ElectricityContract.objects.get_or_create(
                contract_number=contract_data['contract_number'],
                defaults=contract_data
            )
            if created:
                self.stdout.write(f"  Created electricity contract: {contract.contract_number}")

        # Create broadband contracts
        for i, account in enumerate(accounts[:2], 1):
            contract_data = {
                'tenant': tenant,
                'contract_number': f'BB-{account.account_number}-{i:03d}',
                'account': account,
                'template': templates['broadband'],
                'service_address': addresses[account.id],
                'technology_type': 'fibre',
                'ont_serial': f'ONT{i:03d}024BB',
                'plan_name': 'SpotOn Fibre Basic' if i == 1 else 'SpotOn Fibre Pro',
                'download_speed_mbps': 100 if i == 1 else 300,
                'upload_speed_mbps': 20 if i == 1 else 100,
                'monthly_fee': Decimal('69.99') if i == 1 else Decimal('89.99'),
                'contract_start_date': date.today() - timedelta(days=20*i),
                'term_months': 24,
                'status': 'active' if i == 1 else 'pending_installation',
                'signed_date': date.today() - timedelta(days=20*i),
                'signed_by_customer': True
            }
            
            contract, created = BroadbandContract.objects.get_or_create(
                contract_number=contract_data['contract_number'],
                defaults=contract_data
            )
            if created:
                self.stdout.write(f"  Created broadband contract: {contract.contract_number}")

        # Create mobile contracts
        for i, account in enumerate(accounts[:3], 1):
            contract_data = {
                'tenant': tenant,
                'contract_number': f'MOB-{account.account_number}-{i:03d}',
                'account': account,
                'template': templates['mobile'],
                'mobile_number': f'+64 21 {i:03d}024',
                'sim_id': f'SIM{i:06d}',
                'plan_name': 'SpotOn Mobile Essential' if i % 2 == 1 else 'SpotOn Mobile Plus',
                'plan_type': 'prepaid' if i % 2 == 1 else 'postpaid',
                'data_allowance_gb': Decimal('5.00') if i % 2 == 1 else Decimal('20.00'),
                'monthly_fee': Decimal('29.99') if i % 2 == 1 else Decimal('49.99'),
                'contract_start_date': date.today() - timedelta(days=10*i),
                'term_months': 12,
                'status': 'active',
                'signed_date': date.today() - timedelta(days=10*i),
                'signed_by_customer': True
            }
            
            contract, created = MobileContract.objects.get_or_create(
                contract_number=contract_data['contract_number'],
                defaults=contract_data
            )
            if created:
                self.stdout.write(f"  Created mobile contract: {contract.contract_number}")

        # Create some generic service contracts
        for i, account in enumerate(accounts, 1):
            user = users.get(account.id)
            if user:
                contract_data = {
                    'tenant': tenant,
                    'contract_number': f'SVC-{account.account_number}-{i:03d}',
                    'customer': user,
                    'account': account,
                    'contract_type': 'electricity',
                    'service_name': f'Electricity Service {i}',
                    'description': f'Standard electricity supply service for account {account.account_number}',
                    'start_date': timezone.now() - timedelta(days=30*i),
                    'initial_term_months': 12,
                    'status': 'active',
                    'signed_date': timezone.now() - timedelta(days=30*i),
                    'activation_date': timezone.now() - timedelta(days=30*i)
                }
                
                contract, created = ServiceContract.objects.get_or_create(
                    contract_number=contract_data['contract_number'],
                    defaults=contract_data
                )
                if created:
                    self.stdout.write(f"  Created service contract: {contract.contract_number}")

        self.stdout.write(f"Created contracts for {len(accounts)} accounts") 