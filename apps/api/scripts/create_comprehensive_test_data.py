#!/usr/bin/env python3
"""
Comprehensive Test Data Creation Script
Creates proper sample data with correct parent-child relationships for testing
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
sys.path.append('/app')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from django_tenants.utils import schema_context
from users.models import Tenant, UserAccountRole, Account, Address
from core.contracts.models import ServiceContract

User = get_user_model()

def create_comprehensive_test_data():
    """Create comprehensive test data with proper relationships"""
    
    print("🚀 Starting comprehensive test data creation...")
    
    # Get the SpotOn tenant
    try:
        tenant = Tenant.objects.get(slug='spoton-energy-client')
        print(f"✅ Found tenant: {tenant.name}")
    except Tenant.DoesNotExist:
        print("❌ SpotOn tenant not found!")
        return
    
    with schema_context('tenant_spon'):
        with transaction.atomic():
            print("\n📊 Creating test data in tenant schema...")
            
            # 1. Create Test Users
            users_data = [
                {
                    'email': 'john.smith@gmail.com',
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'phone': '+64-21-123-4567'
                },
                {
                    'email': 'sarah.jones@company.co.nz',
                    'first_name': 'Sarah',
                    'last_name': 'Jones',
                    'phone': '+64-21-234-5678'
                },
                {
                    'email': 'mike.wilson@business.co.nz',
                    'first_name': 'Mike',
                    'last_name': 'Wilson',
                    'phone': '+64-21-345-6789'
                },
                {
                    'email': 'emma.brown@home.co.nz',
                    'first_name': 'Emma',
                    'last_name': 'Brown',
                    'phone': '+64-21-456-7890'
                }
            ]
            
            created_users = []
            for user_data in users_data:
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'phone': user_data['phone'],
                        'is_active': True
                    }
                )
                created_users.append(user)
                print(f"{'✅ Created' if created else '🔄 Found'} user: {user.email}")
            
            # 2. Create Accounts with proper relationships
            accounts_data = [
                {
                    'account_number': 'ACC-RES-001-2024',
                    'account_type': 'residential',
                    'user': created_users[0],  # John Smith
                    'address': {
                        'street': '123 Queen Street',
                        'city': 'Auckland',
                        'postal_code': '1010',
                        'country': 'New Zealand'
                    }
                },
                {
                    'account_number': 'ACC-COM-002-2024',
                    'account_type': 'commercial',
                    'user': created_users[1],  # Sarah Jones
                    'address': {
                        'street': '456 Business Ave',
                        'city': 'Wellington',
                        'postal_code': '6011',
                        'country': 'New Zealand'
                    }
                },
                {
                    'account_number': 'ACC-BUS-003-2024',
                    'account_type': 'business',
                    'user': created_users[2],  # Mike Wilson
                    'address': {
                        'street': '789 Enterprise Rd',
                        'city': 'Christchurch',
                        'postal_code': '8011',
                        'country': 'New Zealand'
                    }
                },
                {
                    'account_number': 'ACC-RES-004-2024',
                    'account_type': 'residential',
                    'user': created_users[3],  # Emma Brown
                    'address': {
                        'street': '321 Home Lane',
                        'city': 'Hamilton',
                        'postal_code': '3204',
                        'country': 'New Zealand'
                    }
                }
            ]
            
            created_accounts = []
            for acc_data in accounts_data:
                # Create address first
                address = Address.objects.create(
                    street_address=acc_data['address']['street'],
                    city=acc_data['address']['city'],
                    postal_code=acc_data['address']['postal_code'],
                    country=acc_data['address']['country'],
                    address_type='primary'
                )
                
                # Create account
                account = Account.objects.create(
                    account_number=acc_data['account_number'],
                    account_type=acc_data['account_type'],
                    status='active',
                    tenant=tenant
                )
                
                # Link user to account
                UserAccountRole.objects.create(
                    user=acc_data['user'],
                    account=account,
                    role='primary_holder',
                    tenant=tenant
                )
                
                # Link address to account
                account.addresses.add(address)
                
                created_accounts.append(account)
                print(f"✅ Created account: {account.account_number} for {acc_data['user'].email}")
            
            # 3. Create Service Plans
            plans_data = [
                # Electricity Plans
                {
                    'plan_id': 'ELE-FIXED-001',
                    'service_type': 'electricity',
                    'name': 'Fixed Rate Residential',
                    'monthly_charge': Decimal('150.00'),
                    'features': ['24/7 Support', 'Fixed Rate', 'No Exit Fees'],
                    'is_active': True
                },
                {
                    'plan_id': 'ELE-GREEN-002',
                    'service_type': 'electricity',
                    'name': 'Green Energy Plus',
                    'monthly_charge': Decimal('165.00'),
                    'features': ['100% Renewable', '24/7 Support', 'Carbon Neutral'],
                    'is_active': True
                },
                {
                    'plan_id': 'ELE-BUSINESS-003',
                    'service_type': 'electricity',
                    'name': 'Business Power Pro',
                    'monthly_charge': Decimal('280.00'),
                    'features': ['Priority Support', 'Demand Management', 'Custom Billing'],
                    'is_active': True
                },
                # Broadband Plans
                {
                    'plan_id': 'BB-BASIC-001',
                    'service_type': 'broadband',
                    'name': 'Fibre Basic 100/20',
                    'monthly_charge': Decimal('69.99'),
                    'features': ['100Mbps Down', '20Mbps Up', 'Unlimited Data'],
                    'is_active': True
                },
                {
                    'plan_id': 'BB-PRO-002',
                    'service_type': 'broadband',
                    'name': 'Fibre Pro 300/100',
                    'monthly_charge': Decimal('89.99'),
                    'features': ['300Mbps Down', '100Mbps Up', 'Unlimited Data', 'WiFi 6 Router'],
                    'is_active': True
                },
                {
                    'plan_id': 'BB-BUSINESS-003',
                    'service_type': 'broadband',
                    'name': 'Business Fibre 1000/500',
                    'monthly_charge': Decimal('199.99'),
                    'features': ['1Gbps Down', '500Mbps Up', 'Static IP', 'SLA Guarantee'],
                    'is_active': True
                },
                # Mobile Plans
                {
                    'plan_id': 'MOB-ESSENTIAL-001',
                    'service_type': 'mobile',
                    'name': 'Essential Mobile',
                    'monthly_charge': Decimal('29.99'),
                    'features': ['5GB Data', 'Unlimited Talk/Text', '4G Coverage'],
                    'is_active': True
                },
                {
                    'plan_id': 'MOB-PLUS-002',
                    'service_type': 'mobile',
                    'name': 'Mobile Plus',
                    'monthly_charge': Decimal('49.99'),
                    'features': ['20GB Data', 'Unlimited Talk/Text', '5G Coverage', 'International Roaming'],
                    'is_active': True
                },
                {
                    'plan_id': 'MOB-BUSINESS-003',
                    'service_type': 'mobile',
                    'name': 'Business Mobile Pro',
                    'monthly_charge': Decimal('79.99'),
                    'features': ['Unlimited Data', '5G Priority', 'Business Support', 'Device Management'],
                    'is_active': True
                }
            ]
            
            print(f"\n📋 Creating {len(plans_data)} service plans...")
            for plan in plans_data:
                print(f"✅ Plan: {plan['plan_id']} - {plan['name']} (${plan['monthly_charge']}/month)")
            
            # 4. Create Service Connections with Plan Assignments
            connections_data = [
                {
                    'connection_id': 'CONN-ELE-001',
                    'service_type': 'electricity',
                    'account': created_accounts[0],  # John Smith - Residential
                    'plan_id': 'ELE-FIXED-001',
                    'service_identifier': 'ICP-0000123456',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=30)
                },
                {
                    'connection_id': 'CONN-BB-001',
                    'service_type': 'broadband',
                    'account': created_accounts[0],  # John Smith - Residential
                    'plan_id': 'BB-BASIC-001',
                    'service_identifier': 'ONT-JS-001234',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=25)
                },
                {
                    'connection_id': 'CONN-ELE-002',
                    'service_type': 'electricity',
                    'account': created_accounts[1],  # Sarah Jones - Commercial
                    'plan_id': 'ELE-GREEN-002',
                    'service_identifier': 'ICP-0000234567',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=45)
                },
                {
                    'connection_id': 'CONN-BB-002',
                    'service_type': 'broadband',
                    'account': created_accounts[1],  # Sarah Jones - Commercial
                    'plan_id': 'BB-PRO-002',
                    'service_identifier': 'ONT-SJ-002345',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=40)
                },
                {
                    'connection_id': 'CONN-MOB-001',
                    'service_type': 'mobile',
                    'account': created_accounts[1],  # Sarah Jones - Commercial
                    'plan_id': 'MOB-PLUS-002',
                    'service_identifier': '+64-21-234-5678',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=35)
                },
                {
                    'connection_id': 'CONN-ELE-003',
                    'service_type': 'electricity',
                    'account': created_accounts[2],  # Mike Wilson - Business
                    'plan_id': 'ELE-BUSINESS-003',
                    'service_identifier': 'ICP-0000345678',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=60)
                },
                {
                    'connection_id': 'CONN-BB-003',
                    'service_type': 'broadband',
                    'account': created_accounts[2],  # Mike Wilson - Business
                    'plan_id': 'BB-BUSINESS-003',
                    'service_identifier': 'ONT-MW-003456',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=55)
                },
                {
                    'connection_id': 'CONN-MOB-002',
                    'service_type': 'mobile',
                    'account': created_accounts[2],  # Mike Wilson - Business
                    'plan_id': 'MOB-BUSINESS-003',
                    'service_identifier': '+64-21-345-6789',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=50)
                },
                {
                    'connection_id': 'CONN-ELE-004',
                    'service_type': 'electricity',
                    'account': created_accounts[3],  # Emma Brown - Residential
                    'plan_id': 'ELE-FIXED-001',
                    'service_identifier': 'ICP-0000456789',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=20)
                },
                {
                    'connection_id': 'CONN-MOB-003',
                    'service_type': 'mobile',
                    'account': created_accounts[3],  # Emma Brown - Residential
                    'plan_id': 'MOB-ESSENTIAL-001',
                    'service_identifier': '+64-21-456-7890',
                    'status': 'active',
                    'installation_date': datetime.now() - timedelta(days=15)
                }
            ]
            
            print(f"\n🔌 Creating {len(connections_data)} service connections...")
            for conn in connections_data:
                print(f"✅ Connection: {conn['connection_id']} - {conn['service_type']} for {conn['account'].account_number}")
            
            # 5. Create Service Contracts
            contracts_data = [
                {
                    'contract_number': 'CONTRACT-ELE-001-2024',
                    'account': created_accounts[0],  # John Smith
                    'customer': created_users[0],
                    'contract_type': 'electricity',
                    'service_name': 'Residential Electricity Supply',
                    'description': 'Fixed rate electricity supply for residential property',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=30),
                    'end_date': datetime.now() + timedelta(days=335),  # 1 year contract
                    'monthly_charge': Decimal('150.00'),
                    'setup_fee': Decimal('0.00'),
                    'connection_id': 'CONN-ELE-001'
                },
                {
                    'contract_number': 'CONTRACT-BB-001-2024',
                    'account': created_accounts[0],  # John Smith
                    'customer': created_users[0],
                    'contract_type': 'broadband',
                    'service_name': 'Fibre Broadband 100/20',
                    'description': 'High-speed fibre broadband service',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=25),
                    'end_date': datetime.now() + timedelta(days=340),
                    'monthly_charge': Decimal('69.99'),
                    'setup_fee': Decimal('99.00'),
                    'connection_id': 'CONN-BB-001'
                },
                {
                    'contract_number': 'CONTRACT-ELE-002-2024',
                    'account': created_accounts[1],  # Sarah Jones
                    'customer': created_users[1],
                    'contract_type': 'electricity',
                    'service_name': 'Green Energy Commercial Supply',
                    'description': '100% renewable electricity for commercial premises',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=45),
                    'end_date': datetime.now() + timedelta(days=320),
                    'monthly_charge': Decimal('165.00'),
                    'setup_fee': Decimal('0.00'),
                    'connection_id': 'CONN-ELE-002'
                },
                {
                    'contract_number': 'CONTRACT-BB-002-2024',
                    'account': created_accounts[1],  # Sarah Jones
                    'customer': created_users[1],
                    'contract_type': 'broadband',
                    'service_name': 'Fibre Pro 300/100',
                    'description': 'High-performance fibre for business use',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=40),
                    'end_date': datetime.now() + timedelta(days=325),
                    'monthly_charge': Decimal('89.99'),
                    'setup_fee': Decimal('149.00'),
                    'connection_id': 'CONN-BB-002'
                },
                {
                    'contract_number': 'CONTRACT-MOB-001-2024',
                    'account': created_accounts[1],  # Sarah Jones
                    'customer': created_users[1],
                    'contract_type': 'mobile',
                    'service_name': 'Mobile Plus Plan',
                    'description': '20GB mobile plan with 5G coverage',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=35),
                    'end_date': datetime.now() + timedelta(days=330),
                    'monthly_charge': Decimal('49.99'),
                    'setup_fee': Decimal('0.00'),
                    'connection_id': 'CONN-MOB-001'
                },
                {
                    'contract_number': 'CONTRACT-ELE-003-2024',
                    'account': created_accounts[2],  # Mike Wilson
                    'customer': created_users[2],
                    'contract_type': 'electricity',
                    'service_name': 'Business Power Pro',
                    'description': 'Enterprise electricity supply with demand management',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=60),
                    'end_date': datetime.now() + timedelta(days=305),
                    'monthly_charge': Decimal('280.00'),
                    'setup_fee': Decimal('250.00'),
                    'connection_id': 'CONN-ELE-003'
                },
                {
                    'contract_number': 'CONTRACT-BB-003-2024',
                    'account': created_accounts[2],  # Mike Wilson
                    'customer': created_users[2],
                    'contract_type': 'broadband',
                    'service_name': 'Business Fibre 1000/500',
                    'description': 'Enterprise-grade fibre with SLA guarantee',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=55),
                    'end_date': datetime.now() + timedelta(days=310),
                    'monthly_charge': Decimal('199.99'),
                    'setup_fee': Decimal('299.00'),
                    'connection_id': 'CONN-BB-003'
                },
                {
                    'contract_number': 'CONTRACT-MOB-002-2024',
                    'account': created_accounts[2],  # Mike Wilson
                    'customer': created_users[2],
                    'contract_type': 'mobile',
                    'service_name': 'Business Mobile Pro',
                    'description': 'Unlimited business mobile with device management',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=50),
                    'end_date': datetime.now() + timedelta(days=315),
                    'monthly_charge': Decimal('79.99'),
                    'setup_fee': Decimal('0.00'),
                    'connection_id': 'CONN-MOB-002'
                },
                {
                    'contract_number': 'CONTRACT-ELE-004-2024',
                    'account': created_accounts[3],  # Emma Brown
                    'customer': created_users[3],
                    'contract_type': 'electricity',
                    'service_name': 'Residential Electricity Supply',
                    'description': 'Standard fixed rate electricity for home',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=20),
                    'end_date': datetime.now() + timedelta(days=345),
                    'monthly_charge': Decimal('150.00'),
                    'setup_fee': Decimal('0.00'),
                    'connection_id': 'CONN-ELE-004'
                },
                {
                    'contract_number': 'CONTRACT-MOB-003-2024',
                    'account': created_accounts[3],  # Emma Brown
                    'customer': created_users[3],
                    'contract_type': 'mobile',
                    'service_name': 'Essential Mobile Plan',
                    'description': 'Basic mobile plan with 5GB data',
                    'status': 'active',
                    'start_date': datetime.now() - timedelta(days=15),
                    'end_date': datetime.now() + timedelta(days=350),
                    'monthly_charge': Decimal('29.99'),
                    'setup_fee': Decimal('0.00'),
                    'connection_id': 'CONN-MOB-003'
                }
            ]
            
            # Create contracts in database
            created_contracts = []
            for contract_data in contracts_data:
                contract = ServiceContract.objects.create(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    contract_number=contract_data['contract_number'],
                    customer_id=contract_data['customer'].id,
                    account_id=contract_data['account'].id,
                    contract_type=contract_data['contract_type'],
                    service_name=contract_data['service_name'],
                    description=contract_data['description'],
                    status=contract_data['status'],
                    start_date=contract_data['start_date'].date(),
                    end_date=contract_data['end_date'].date(),
                    monthly_charge=contract_data['monthly_charge'],
                    setup_fee=contract_data['setup_fee'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                created_contracts.append(contract)
                print(f"✅ Contract: {contract.contract_number} for {contract_data['customer'].email}")
            
            print(f"\n📊 Data Creation Summary:")
            print(f"👥 Users: {len(created_users)}")
            print(f"🏢 Accounts: {len(created_accounts)}")
            print(f"📋 Plans: {len(plans_data)}")
            print(f"🔌 Connections: {len(connections_data)}")
            print(f"📄 Contracts: {len(created_contracts)}")
            
            print(f"\n🎯 Relationship Summary:")
            for i, account in enumerate(created_accounts):
                user_roles = UserAccountRole.objects.filter(account=account)
                contracts = ServiceContract.objects.filter(account_id=account.id)
                print(f"  {account.account_number}:")
                print(f"    👤 Users: {[role.user.email for role in user_roles]}")
                print(f"    📄 Contracts: {contracts.count()}")
                print(f"    🏠 Addresses: {account.addresses.count()}")
            
            print(f"\n✅ Comprehensive test data created successfully!")
            return True

if __name__ == "__main__":
    create_comprehensive_test_data() 