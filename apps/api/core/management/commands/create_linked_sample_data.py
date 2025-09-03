"""
Management command to create linked sample data for accounts, contracts, and connections
This ensures all entities have proper relationships and data flows through to the UI
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import Tenant, Account, UserAccountRole, AccountAddress
from core.contracts.models import ServiceContract, ElectricityContract, BroadbandContract, MobileContract
from decimal import Decimal
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create linked sample data for accounts, contracts, and connections'

    def handle(self, *args, **options):
        self.stdout.write('Creating linked sample data...')
        
        # Get or create tenant
        tenant, created = Tenant.objects.get_or_create(
            slug='spoton-energy-client',
            defaults={
                'name': 'SpotOn Energy Client',
                'contact_email': 'admin@spoton.energy',
                'timezone': 'Pacific/Auckland',
                'currency': 'NZD',
                'is_active': True
            }
        )
        
        # Create sample users
        users_data = [
            {
                'email': 'john.smith@gmail.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'user_type': 'residential',
                'mobile': '+64-21-123-4567'
            },
            {
                'email': 'sarah.jones@company.co.nz', 
                'first_name': 'Sarah',
                'last_name': 'Jones',
                'user_type': 'commercial',
                'mobile': '+64-21-234-5678'
            },
            {
                'email': 'mike.wilson@business.co.nz',
                'first_name': 'Mike', 
                'last_name': 'Wilson',
                'user_type': 'business',
                'mobile': '+64-21-345-6789'
            }
        ]
        
        created_users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'user_type': user_data['user_type'],
                    'mobile': user_data['mobile'],
                    'tenant': tenant,
                    'is_active': True,
                    'is_verified': True
                }
            )
            created_users.append(user)
            if created:
                self.stdout.write(f'Created user: {user.email}')
        
        # Create accounts with proper relationships
        accounts_data = [
            {
                'account_number': 'ACC-RES-001-2024',
                'account_type': 'residential',
                'user_index': 0,  # John Smith
                'address': {
                    'address_line1': '123 Queen Street',
                    'city': 'Auckland',
                    'postal_code': '1010'
                }
            },
            {
                'account_number': 'ACC-COM-002-2024',
                'account_type': 'commercial',
                'user_index': 1,  # Sarah Jones
                'address': {
                    'address_line1': '456 Business Ave',
                    'city': 'Wellington', 
                    'postal_code': '6011'
                }
            },
            {
                'account_number': 'ACC-BUS-003-2024',
                'account_type': 'business',
                'user_index': 2,  # Mike Wilson
                'address': {
                    'address_line1': '789 Enterprise Rd',
                    'city': 'Christchurch',
                    'postal_code': '8011'
                }
            }
        ]
        
        created_accounts = []
        for acc_data in accounts_data:
            account, created = Account.objects.get_or_create(
                account_number=acc_data['account_number'],
                defaults={
                    'tenant': tenant,
                    'account_type': acc_data['account_type'],
                    'status': 'active',
                    'billing_cycle': 'monthly',
                    'billing_day': 15,
                    'valid_from': timezone.now().date(),
                    'created_by': created_users[0]  # Use first user as creator
                }
            )
            created_accounts.append(account)
            
            if created:
                self.stdout.write(f'Created account: {account.account_number}')
                
                # Create user-account relationship
                user_role, role_created = UserAccountRole.objects.get_or_create(
                    user=created_users[acc_data['user_index']],
                    account=account,
                    defaults={
                        'tenant': tenant,
                        'role': 'owner',
                        'can_manage_services': True,
                        'can_manage_users': True,
                        'can_manage_billing': True,
                        'can_view_usage': True,
                        'created_by': created_users[0]
                    }
                )
                
                # Create address
                address, addr_created = AccountAddress.objects.get_or_create(
                    account=account,
                    address_line1=acc_data['address']['address_line1'],
                    defaults={
                        'tenant': tenant,
                        'city': acc_data['address']['city'],
                        'postal_code': acc_data['address']['postal_code'],
                        'country': 'New Zealand',
                        'address_type': 'service',
                        'is_primary': True
                    }
                )
        
        # Create service contracts with proper relationships
        contracts_data = [
            {
                'contract_number': 'CONTRACT-ELE-001-2024',
                'contract_type': 'electricity',
                'service_name': 'Residential Electricity Supply',
                'description': 'Fixed rate electricity supply for residential property',
                'account_index': 0,  # John Smith's account
                'user_index': 0,
                'service_details': {
                    'icp_code': 'ICP-0000123456',
                    'gxp_code': 'GXP-AKL-001',
                    'network_code': 'VECT'
                }
            },
            {
                'contract_number': 'CONTRACT-BB-001-2024', 
                'contract_type': 'broadband',
                'service_name': 'Fibre Broadband 100/20',
                'description': 'High-speed fibre broadband service',
                'account_index': 0,  # John Smith's account
                'user_index': 0,
                'service_details': {
                    'ont_serial': 'ONT-JS-001234',
                    'download_speed': '100',
                    'upload_speed': '20'
                }
            },
            {
                'contract_number': 'CONTRACT-ELE-002-2024',
                'contract_type': 'electricity', 
                'service_name': 'Green Energy Commercial Supply',
                'description': '100% renewable electricity for commercial premises',
                'account_index': 1,  # Sarah Jones's account
                'user_index': 1,
                'service_details': {
                    'icp_code': 'ICP-0000234567',
                    'gxp_code': 'GXP-WLG-002',
                    'network_code': 'WELN'
                }
            },
            {
                'contract_number': 'CONTRACT-BB-002-2024',
                'contract_type': 'broadband',
                'service_name': 'Fibre Pro 300/100', 
                'description': 'High-performance fibre for business use',
                'account_index': 1,  # Sarah Jones's account
                'user_index': 1,
                'service_details': {
                    'ont_serial': 'ONT-SJ-002345',
                    'download_speed': '300',
                    'upload_speed': '100'
                }
            },
            {
                'contract_number': 'CONTRACT-MOB-001-2024',
                'contract_type': 'mobile',
                'service_name': 'Mobile Plus Plan',
                'description': '20GB mobile plan with 5G coverage', 
                'account_index': 1,  # Sarah Jones's account
                'user_index': 1,
                'service_details': {
                    'mobile_number': '+64-21-234-5678',
                    'data_allowance': '20GB',
                    'network_type': '5G'
                }
            },
            {
                'contract_number': 'CONTRACT-ELE-003-2024',
                'contract_type': 'electricity',
                'service_name': 'Business Power Pro',
                'description': 'High-capacity electricity for business operations',
                'account_index': 2,  # Mike Wilson's account  
                'user_index': 2,
                'service_details': {
                    'icp_code': 'ICP-0000345678',
                    'gxp_code': 'GXP-CHC-003', 
                    'network_code': 'ORPN'
                }
            }
        ]
        
        for contract_data in contracts_data:
            contract, created = ServiceContract.objects.get_or_create(
                contract_number=contract_data['contract_number'],
                defaults={
                    'tenant': tenant,
                    'customer': created_users[contract_data['user_index']],
                    'account': created_accounts[contract_data['account_index']],
                    'contract_type': contract_data['contract_type'],
                    'service_name': contract_data['service_name'],
                    'description': contract_data['description'],
                    'status': 'active',
                    'start_date': timezone.now(),
                    'end_date': timezone.now().replace(year=timezone.now().year + 1),
                    'created_by': created_users[0],
                    'special_conditions': contract_data['service_details']
                }
            )
            
            if created:
                self.stdout.write(f'Created contract: {contract.contract_number}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created linked sample data:\n'
                f'- {len(created_users)} users\n'
                f'- {len(created_accounts)} accounts\n' 
                f'- {len(contracts_data)} contracts\n'
                f'All entities are properly linked with relationships.'
            )
        ) 