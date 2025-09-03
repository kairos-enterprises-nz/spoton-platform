import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from users.models import Tenant, Account, UserAccountRole, Address
from core.contracts.models import ServiceContract, ElectricityContract, BroadbandContract, MobileContract

User = get_user_model()


class Command(BaseCommand):
    help = 'Create comprehensive test data for the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing test data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.clean_test_data()
        
        with transaction.atomic():
            self.create_test_data()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created test data')
        )

    def clean_test_data(self):
        """Clean existing test data"""
        self.stdout.write('Cleaning existing test data...')
        
        # Clean contracts
        ServiceContract.objects.filter(tenant__slug__in=['acme-energy', 'stellar-utilities']).delete()
        ElectricityContract.objects.filter(tenant__slug__in=['acme-energy', 'stellar-utilities']).delete()
        BroadbandContract.objects.filter(tenant__slug__in=['acme-energy', 'stellar-utilities']).delete()
        MobileContract.objects.filter(tenant__slug__in=['acme-energy', 'stellar-utilities']).delete()
        
        # Clean accounts and users
        Account.objects.filter(tenant__slug__in=['acme-energy', 'stellar-utilities']).delete()
        User.objects.filter(tenant__slug__in=['acme-energy', 'stellar-utilities']).delete()
        
        # Clean tenants (this will cascade delete domains)
        Tenant.objects.filter(slug__in=['acme-energy', 'stellar-utilities']).delete()
        
        self.stdout.write(self.style.SUCCESS('Cleaned existing test data'))

    def create_test_data(self):
        """Create comprehensive test data"""
        self.stdout.write('Creating test data...')
        
        # Create tenants
        tenants = self.create_tenants()
        
        # Create staff users
        staff_users = self.create_staff_users(tenants)
        
        # Create customer users
        customer_users = self.create_customer_users(tenants)
        
        # Create accounts
        accounts = self.create_accounts(tenants, customer_users)
        
        # Create contracts
        # contracts = self.create_contracts(tenants, accounts)
        
        # Create connections (sample data)
        # connections = self.create_connections(tenants, accounts)
        
        # Create sample plans
        # plans = self.create_plans(tenants)
        
        self.stdout.write(self.style.SUCCESS('Test data creation completed successfully!'))

    def create_tenants(self):
        """Create two test tenants"""
        self.stdout.write('Creating tenants...')
        
        # Create business tenant 1
        tenant1 = Tenant.objects.create(
            name='ACME Energy Solutions',
            slug='acme-energy',
            business_number='12345678901',
            tax_number='GST123456789',
            contact_email='admin@acme-energy.co.nz',
            contact_phone='+64 9 123 4567',
            address='123 Queen Street, Auckland 1010, New Zealand',
            timezone='Pacific/Auckland',
            currency='NZD',
            is_active=True
        )
        
        # Create schema tenant 1 (for django-tenants)
        client1 = Client.objects.create(
            schema_name='acme_energy',
            name='ACME Energy Solutions',
            description='Leading energy retailer specializing in renewable energy solutions',
            business_tenant=tenant1
        )
        
        # Create business tenant 2
        tenant2 = Tenant.objects.create(
            name='Stellar Utilities Ltd',
            slug='stellar-utilities',
            business_number='98765432109',
            tax_number='GST987654321',
            contact_email='admin@stellar-utilities.co.nz',
            contact_phone='+64 4 987 6543',
            address='456 Lambton Quay, Wellington 6011, New Zealand',
            timezone='Pacific/Auckland',
            currency='NZD',
            is_active=True
        )
        
        # Create schema tenant 2 (for django-tenants)
        client2 = Client.objects.create(
            schema_name='stellar_utilities',
            name='Stellar Utilities Ltd',
            description='Comprehensive utility services provider offering electricity, broadband, and mobile services',
            business_tenant=tenant2
        )
        
        # Create domains for tenants
        Domain.objects.create(
            domain='acme-energy.localhost',
            tenant=client1,
            is_primary=True
        )
        
        Domain.objects.create(
            domain='stellar-utilities.localhost',
            tenant=client2,
            is_primary=True
        )
        
        self.stdout.write(f'Created tenants: {tenant1.name}, {tenant2.name}')
        return [tenant1, tenant2]

    def create_staff_users(self, tenants):
        """Create staff users for each tenant"""
        self.stdout.write('Creating staff users...')
        
        staff_users = []
        
        # ACME Energy staff
        acme_admin = User.objects.create_user(
            email='admin@acme-energy.co.nz',
            password='admin123',
            first_name='John',
            last_name='Smith',
            user_type='staff',
            is_staff=True,
            is_active=True,
            is_verified=True,
            tenant=tenants[0]
        )
        staff_users.append(acme_admin)
        
        # Stellar Utilities staff
        stellar_admin = User.objects.create_user(
            email='admin@stellar-utilities.co.nz',
            password='admin123',
            first_name='Sarah',
            last_name='Johnson',
            user_type='staff',
            is_staff=True,
            is_active=True,
            is_verified=True,
            tenant=tenants[1]
        )
        staff_users.append(stellar_admin)
        
        self.stdout.write(f'Created {len(staff_users)} staff users')
        return staff_users

    def create_customer_users(self, tenants):
        """Create customer users for each tenant"""
        self.stdout.write('Creating customer users...')
        
        customer_users = []
        
        # ACME Energy customers
        acme_customers = [
            {
                'email': 'alice.brown@gmail.com',
                'first_name': 'Alice',
                'last_name': 'Brown',
                'phone': '+64 21 123 4567'
            },
            {
                'email': 'bob.wilson@outlook.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'phone': '+64 21 234 5678'
            },
            {
                'email': 'carol.davis@yahoo.com',
                'first_name': 'Carol',
                'last_name': 'Davis',
                'phone': '+64 21 345 6789'
            }
        ]
        
        for customer_data in acme_customers:
            user = User.objects.create_user(
                email=customer_data['email'],
                password='customer123',
                first_name=customer_data['first_name'],
                last_name=customer_data['last_name'],
                mobile=customer_data['phone'],
                user_type='residential',
                is_active=True,
                is_verified=True,
                tenant=tenants[0]
            )
            customer_users.append(user)
        
        # Stellar Utilities customers
        stellar_customers = [
            {
                'email': 'david.taylor@gmail.com',
                'first_name': 'David',
                'last_name': 'Taylor',
                'phone': '+64 21 456 7890'
            },
            {
                'email': 'emma.white@outlook.com',
                'first_name': 'Emma',
                'last_name': 'White',
                'phone': '+64 21 567 8901'
            },
            {
                'email': 'frank.green@yahoo.com',
                'first_name': 'Frank',
                'last_name': 'Green',
                'phone': '+64 21 678 9012'
            }
        ]
        
        for customer_data in stellar_customers:
            user = User.objects.create_user(
                email=customer_data['email'],
                password='customer123',
                first_name=customer_data['first_name'],
                last_name=customer_data['last_name'],
                mobile=customer_data['phone'],
                user_type='residential',
                is_active=True,
                is_verified=True,
                tenant=tenants[1]
            )
            customer_users.append(user)
        
        self.stdout.write(f'Created {len(customer_users)} customer users')
        return customer_users

    def create_accounts(self, tenants, customer_users):
        """Create accounts for customer users"""
        self.stdout.write('Creating accounts...')
        
        accounts = []
        account_counter = 1
        
        for user in customer_users:
            # Create account
            account = Account.objects.create(
                tenant=user.tenant,
                account_number=f'ACC{account_counter:06d}',
                account_type='residential',
                status='active',
                created_by=user
            )
            
            # Create user role (owner)
            UserAccountRole.objects.create(
                tenant=user.tenant,
                user=user,
                account=account,
                role='owner',
                can_manage_services=True,
                can_manage_users=True,
                can_manage_billing=True,
                can_view_usage=True,
                created_by=user
            )
            
            # Create address
            # addresses = [
            #     {'street': '123 Main Street', 'city': 'Auckland', 'postal_code': '1010'},
            #     {'street': '456 Queen Street', 'city': 'Wellington', 'postal_code': '6011'},
            #     {'street': '789 High Street', 'city': 'Christchurch', 'postal_code': '8011'},
            #     {'street': '321 King Street', 'city': 'Hamilton', 'postal_code': '3204'},
            #     {'street': '654 George Street', 'city': 'Dunedin', 'postal_code': '9016'},
            #     {'street': '987 Victoria Street', 'city': 'Rotorua', 'postal_code': '3010'},
            # ]
            
            # address_data = addresses[(account_counter - 1) % len(addresses)]
            # Address.objects.create(
            #     address_line1=address_data['street'],
            #     city=address_data['city'],
            #     postal_code=address_data['postal_code'],
            #     country='New Zealand',
            #     address_type='service',
            #     is_primary=True
            # )
            
            accounts.append(account)
            account_counter += 1
        
        self.stdout.write(f'Created {len(accounts)} accounts')
        return accounts

    def create_contracts(self, tenants, accounts):
        """Create various types of contracts"""
        self.stdout.write('Creating contracts...')
        
        contracts = []
        contract_counter = 1
        
        for account in accounts:
            # Create basic service contract for electricity
            electricity_contract = ServiceContract.objects.create(
                tenant=account.tenant,
                contract_number=f'ELE{contract_counter:06d}',
                customer=account.user_roles.first().user,
                account=account,
                contract_type='electricity',
                service_name='Residential Electricity Supply',
                description='Standard residential electricity supply contract',
                start_date=timezone.now() - timedelta(days=30),
                end_date=timezone.now() + timedelta(days=335),
                initial_term_months=12,
                billing_frequency='monthly',
                status='active',
                signed_date=timezone.now() - timedelta(days=30),
                activation_date=timezone.now() - timedelta(days=30),
                created_by=account.user_roles.first().user
            )
            contracts.append(electricity_contract)
            
            # Create broadband contract for some accounts
            if contract_counter % 2 == 0:
                broadband_contract = ServiceContract.objects.create(
                    tenant=account.tenant,
                    contract_number=f'BB{contract_counter:06d}',
                    customer=account.user_roles.first().user,
                    account=account,
                    contract_type='broadband',
                    service_name='Fibre Broadband Service',
                    description='High-speed fibre broadband internet service',
                    start_date=timezone.now() - timedelta(days=20),
                    end_date=timezone.now() + timedelta(days=345),
                    initial_term_months=12,
                    billing_frequency='monthly',
                    status='active',
                    signed_date=timezone.now() - timedelta(days=20),
                    activation_date=timezone.now() - timedelta(days=20),
                    created_by=account.user_roles.first().user
                )
                contracts.append(broadband_contract)
            
            # Create mobile contract for some accounts
            if contract_counter % 3 == 0:
                mobile_contract = ServiceContract.objects.create(
                    tenant=account.tenant,
                    contract_number=f'MOB{contract_counter:06d}',
                    customer=account.user_roles.first().user,
                    account=account,
                    contract_type='mobile',
                    service_name='Mobile Phone Service',
                    description='Postpaid mobile phone service with data',
                    start_date=timezone.now() - timedelta(days=15),
                    end_date=timezone.now() + timedelta(days=350),
                    initial_term_months=12,
                    billing_frequency='monthly',
                    status='active',
                    signed_date=timezone.now() - timedelta(days=15),
                    activation_date=timezone.now() - timedelta(days=15),
                    created_by=account.user_roles.first().user
                )
                contracts.append(mobile_contract)
            
            contract_counter += 1
        
        self.stdout.write(f'Created {len(contracts)} contracts')
        return contracts 