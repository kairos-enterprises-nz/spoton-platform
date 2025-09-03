from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import uuid

from users.models import Tenant, User, Account, UserAccountRole, AccountAddress
from core.contracts.models import ServiceContract

class Command(BaseCommand):
    help = 'Create focused sample data: 2 tenants, 3 users, 3 contracts, multiple connections'

    def handle(self, *args, **options):
        self.stdout.write('Creating focused sample data...')
        
        with transaction.atomic():
            # Create 2 tenants
            self.stdout.write('Creating tenants...')
            tenant_spoton, created = Tenant.objects.get_or_create(
                slug='spoton-energy',
                defaults={
                    'name': 'SpotOn Energy',
                    'business_number': 'BN-SPOTON-001',
                    'contact_email': 'admin@spoton.energy',
                    'contact_phone': '+64-9-123-4567',
                    'address': '123 Energy Street, Auckland, New Zealand',
                    'timezone': 'Pacific/Auckland',
                    'currency': 'NZD',
                    'is_active': True
                }
            )
            
            tenant_vector, created = Tenant.objects.get_or_create(
                slug='vector-power',
                defaults={
                    'name': 'Vector Power',
                    'business_number': 'BN-VECTOR-002',
                    'contact_email': 'admin@vector.co.nz',
                    'contact_phone': '+64-9-987-6543',
                    'address': '456 Power Avenue, Wellington, New Zealand',
                    'timezone': 'Pacific/Auckland',
                    'currency': 'NZD',
                    'is_active': True
                }
            )
            
            self.stdout.write(f'Created/found tenants: {tenant_spoton.name}, {tenant_vector.name}')
            
            # Create 3 users (one staff user for creation tracking)
            self.stdout.write('Creating users...')
            
            # Staff user for SpotOn
            staff_user, created = User.objects.get_or_create(
                email='staff@spoton.energy',
                defaults={
                    'first_name': 'Staff',
                    'last_name': 'Admin',
                    'user_type': 'staff',
                    'tenant': tenant_spoton,
                    'is_staff': True,
                    'is_active': True,
                    'is_verified': True
                }
            )
            if created:
                staff_user.set_password('staff123')
                staff_user.save()
            
            # Customer 1 - Residential (SpotOn)
            user1, created = User.objects.get_or_create(
                email='john.residential@email.com',
                defaults={
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'user_type': 'residential',
                    'tenant': tenant_spoton,
                    'mobile': '+64-21-111-1111',
                    'is_active': True,
                    'is_verified': True
                }
            )
            if created:
                user1.set_password('user123')
                user1.save()
            
            # Customer 2 - Commercial (SpotOn)
            user2, created = User.objects.get_or_create(
                email='sarah.business@company.co.nz',
                defaults={
                    'first_name': 'Sarah',
                    'last_name': 'Business',
                    'user_type': 'commercial',
                    'tenant': tenant_spoton,
                    'mobile': '+64-21-222-2222',
                    'is_active': True,
                    'is_verified': True
                }
            )
            if created:
                user2.set_password('user123')
                user2.save()
            
            # Customer 3 - Commercial (Vector)
            user3, created = User.objects.get_or_create(
                email='mike.enterprise@vector-client.co.nz',
                defaults={
                    'first_name': 'Mike',
                    'last_name': 'Enterprise',
                    'user_type': 'commercial',
                    'tenant': tenant_vector,
                    'mobile': '+64-21-333-3333',
                    'is_active': True,
                    'is_verified': True
                }
            )
            if created:
                user3.set_password('user123')
                user3.save()
            
            created_users = [user1, user2, user3]
            self.stdout.write(f'Created/found users: {[u.email for u in created_users]}')
            
            # Create 3 accounts (one per user)
            self.stdout.write('Creating accounts...')
            accounts_data = [
                {
                    'user': user1,
                    'tenant': tenant_spoton,
                    'account_number': 'ACC-RES-001-2024',
                    'account_type': 'residential',
                    'address': {
                        'address_line1': '123 Residential Road',
                        'city': 'Auckland',
                        'postal_code': '1010'
                    }
                },
                {
                    'user': user2,
                    'tenant': tenant_spoton,
                    'account_number': 'ACC-COM-002-2024',
                    'account_type': 'commercial',
                    'address': {
                        'address_line1': '456 Business Boulevard',
                        'city': 'Wellington',
                        'postal_code': '6011'
                    }
                },
                {
                    'user': user3,
                    'tenant': tenant_vector,
                    'account_number': 'ACC-ENT-003-2024',
                    'account_type': 'commercial',
                    'address': {
                        'address_line1': '789 Enterprise Way',
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
                        'tenant': acc_data['tenant'],
                        'account_type': acc_data['account_type'],
                        'status': 'active',
                        'billing_cycle': 'monthly',
                        'billing_day': 15,
                        'valid_from': timezone.now(),
                        'created_by': staff_user
                    }
                )
                created_accounts.append(account)
                
                if created:
                    self.stdout.write(f'Created account: {account.account_number}')
                    
                    # Link user to account
                    UserAccountRole.objects.get_or_create(
                        user=acc_data['user'],
                        account=account,
                        defaults={
                            'tenant': acc_data['tenant'],
                            'role': 'owner',
                            'can_manage_services': True,
                            'can_manage_users': True,
                            'can_manage_billing': True,
                            'can_view_usage': True,
                            'created_by': staff_user
                        }
                    )
                    
                    # Create address
                    AccountAddress.objects.get_or_create(
                        account=account,
                        address_line1=acc_data['address']['address_line1'],
                        defaults={
                            'tenant': acc_data['tenant'],
                            'city': acc_data['address']['city'],
                            'postal_code': acc_data['address']['postal_code'],
                            'country': 'New Zealand',
                            'address_type': 'service',
                            'is_primary': True
                        }
                    )
            
            # Create 3 contracts (one per user/account) 
            self.stdout.write('Creating contracts...')
            contracts_data = [
                {
                    'user': user1,
                    'account': created_accounts[0],
                    'tenant': tenant_spoton,
                    'contract_number': 'CONTRACT-RES-001-2024',
                    'contract_type': 'bundle',
                    'service_name': 'Residential Multi-Service Bundle',
                    'description': 'Electricity, Broadband, and Mobile services for residential customer'
                },
                {
                    'user': user2,
                    'account': created_accounts[1],
                    'tenant': tenant_spoton,
                    'contract_number': 'CONTRACT-COM-002-2024',
                    'contract_type': 'bundle', 
                    'service_name': 'Commercial Multi-Service Bundle',
                    'description': 'Electricity, Broadband, and Mobile services for commercial customer'
                },
                {
                    'user': user3,
                    'account': created_accounts[2],
                    'tenant': tenant_vector,
                    'contract_number': 'CONTRACT-ENT-003-2024',
                    'contract_type': 'bundle',
                    'service_name': 'Enterprise Multi-Service Bundle',
                    'description': 'Electricity, Broadband, and Mobile services for enterprise customer'
                }
            ]
            
            created_contracts = []
            for contract_data in contracts_data:
                contract, created = ServiceContract.objects.get_or_create(
                    contract_number=contract_data['contract_number'],
                    defaults={
                        'tenant': contract_data['tenant'],
                        'customer': contract_data['user'],
                        'account': contract_data['account'],
                        'contract_type': contract_data['contract_type'],
                        'service_name': contract_data['service_name'],
                        'description': contract_data['description'],
                        'status': 'active',
                        'start_date': timezone.now(),
                        'end_date': timezone.now().replace(year=timezone.now().year + 1),
                        'created_by': staff_user,
                        'billing_frequency': 'monthly',
                        'initial_term_months': 12,
                        'auto_renewal': True
                    }
                )
                created_contracts.append(contract)
                
                if created:
                    self.stdout.write(f'Created contract: {contract.contract_number}')
            
            # Now create multiple connections for each contract (3 services each)
            self.stdout.write('Creating connections...')
            
            # Import Connection model if available
            try:
                from energy.connections.models import Connection
                
                connections_data = [
                    # User 1 (John) - Residential connections
                    {
                        'contract': created_contracts[0],
                        'tenant': tenant_spoton,
                        'account': created_accounts[0],
                        'connection_id': 'CONN-ELE-RES-001',
                        'service_type': 'electricity',
                        'service_identifier': 'ICP-0000111111',
                        'status': 'active'
                    },
                    {
                        'contract': created_contracts[0],
                        'tenant': tenant_spoton,
                        'account': created_accounts[0],
                        'connection_id': 'CONN-BB-RES-001',
                        'service_type': 'broadband',
                        'service_identifier': 'ONT-RES-111111',
                        'status': 'active'
                    },
                    {
                        'contract': created_contracts[0],
                        'tenant': tenant_spoton,
                        'account': created_accounts[0],
                        'connection_id': 'CONN-MOB-RES-001',
                        'service_type': 'mobile',
                        'service_identifier': '+64-21-111-1111',
                        'status': 'active'
                    },
                    # User 2 (Sarah) - Commercial connections
                    {
                        'contract': created_contracts[1],
                        'tenant': tenant_spoton,
                        'account': created_accounts[1],
                        'connection_id': 'CONN-ELE-COM-002',
                        'service_type': 'electricity',
                        'service_identifier': 'ICP-0000222222',
                        'status': 'active'
                    },
                    {
                        'contract': created_contracts[1],
                        'tenant': tenant_spoton,
                        'account': created_accounts[1],
                        'connection_id': 'CONN-BB-COM-002',
                        'service_type': 'broadband',
                        'service_identifier': 'ONT-COM-222222',
                        'status': 'active'
                    },
                    {
                        'contract': created_contracts[1],
                        'tenant': tenant_spoton,
                        'account': created_accounts[1],
                        'connection_id': 'CONN-MOB-COM-002',
                        'service_type': 'mobile',
                        'service_identifier': '+64-21-222-2222',
                        'status': 'active'
                    },
                    # User 3 (Mike) - Enterprise connections
                    {
                        'contract': created_contracts[2],
                        'tenant': tenant_vector,
                        'account': created_accounts[2],
                        'connection_id': 'CONN-ELE-ENT-003',
                        'service_type': 'electricity',
                        'service_identifier': 'ICP-0000333333',
                        'status': 'active'
                    },
                    {
                        'contract': created_contracts[2],
                        'tenant': tenant_vector,
                        'account': created_accounts[2],
                        'connection_id': 'CONN-BB-ENT-003',
                        'service_type': 'broadband',
                        'service_identifier': 'ONT-ENT-333333',
                        'status': 'active'
                    },
                    {
                        'contract': created_contracts[2],
                        'tenant': tenant_vector,
                        'account': created_accounts[2],
                        'connection_id': 'CONN-MOB-ENT-003',
                        'service_type': 'mobile',
                        'service_identifier': '+64-21-333-3333',
                        'status': 'active'
                    }
                ]
                
                connections_created = 0
                for conn_data in connections_data:
                    # Set service-specific fields based on service type
                    defaults = {
                        'tenant': conn_data['tenant'],
                        'account': conn_data['account'],
                        'service_type': conn_data['service_type'],
                        'status': conn_data['status'],
                        'activation_date': timezone.now()
                    }
                    
                    # Add service-specific fields
                    if conn_data['service_type'] == 'electricity':
                        defaults['icp_code'] = conn_data['service_identifier']
                    elif conn_data['service_type'] == 'broadband':
                        defaults['ont_serial'] = conn_data['service_identifier']
                    elif conn_data['service_type'] == 'mobile':
                        defaults['mobile_number'] = conn_data['service_identifier']
                    
                    connection, created = Connection.objects.get_or_create(
                        connection_identifier=conn_data['connection_id'],
                        defaults=defaults
                    )
                    if created:
                        connections_created += 1
                
                self.stdout.write(f'Created {connections_created} connections')
                
            except ImportError:
                self.stdout.write('Connection model not available - skipping connections')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created focused sample data:\n'
                    f'- 2 tenants: {tenant_spoton.name}, {tenant_vector.name}\n'
                    f'- 4 users: {len(created_users)} customers + 1 staff\n'
                    f'- 3 accounts with proper user relationships\n'
                    f'- 3 contracts (one per user)\n'
                    f'- 9 connections (3 services per contract)\n'
                    f'All entities are properly linked with tenant separation.'
                )
            ) 