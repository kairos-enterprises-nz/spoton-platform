#!/usr/bin/env python3
"""
Simple Sample Data Creation Script
Creates basic sample data for testing without complex plan models
"""

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal
import uuid

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Tenant, Account, AccountAddress, UserAccountRole

User = get_user_model()

def create_simple_sample_data():
    """Create simple sample data for testing"""
    print("Creating simple sample data...")
    
    # Get or create tenant
    tenant, created = Tenant.objects.get_or_create(
        slug='spoton',
        defaults={
            'name': 'SpotOn Energy Client',
            'business_number': 'BN123456789',
            'contact_email': 'admin@spoton.co.nz',
            'contact_phone': '+64 9 123 4567',
            'timezone': 'Pacific/Auckland',
            'currency': 'NZD',
            'is_active': True
        }
    )
    print(f"✓ Tenant: {tenant.name}")
    
    # Create sample users
    users_data = [
        {
            'email': 'testuser@email.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'residential',
            'is_active': True,
            'is_verified': True
        },
        {
            'email': 'admin@spoton.co.nz',
            'first_name': 'Admin',
            'last_name': 'User',
            'user_type': 'commercial',
            'is_active': True,
            'is_verified': True,
            'is_staff': True
        },
        {
            'email': 'jane.smith@email.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'user_type': 'residential',
            'is_active': True,
            'is_verified': True
        },
        {
            'email': 'business@company.co.nz',
            'first_name': 'Business',
            'last_name': 'Owner',
            'user_type': 'commercial',
            'is_active': True,
            'is_verified': True
        }
    ]
    
    users = {}
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                **user_data,
                'tenant': tenant,
                'password': 'pbkdf2_sha256$600000$dummy$hash'  # Dummy password hash
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        users[user_data['email']] = user
        print(f"✓ User: {user.email}")
    
    # Create sample accounts
    accounts_data = [
        {
            'account_number': 'ACC-001-2024',
            'account_type': 'residential',
            'primary_user': 'testuser@email.com',
            'billing_cycle': 'monthly',
            'status': 'active'
        },
        {
            'account_number': 'ACC-002-2024',
            'account_type': 'commercial',
            'primary_user': 'admin@spoton.co.nz',
            'billing_cycle': 'monthly',
            'status': 'active'
        },
        {
            'account_number': 'ACC-003-2024',
            'account_type': 'residential',
            'primary_user': 'jane.smith@email.com',
            'billing_cycle': 'monthly',
            'status': 'active'
        },
        {
            'account_number': 'ACC-004-2024',
            'account_type': 'commercial',
            'primary_user': 'business@company.co.nz',
            'billing_cycle': 'quarterly',
            'status': 'active'
        }
    ]
    
    accounts = {}
    for acc_data in accounts_data:
        account, created = Account.objects.get_or_create(
            account_number=acc_data['account_number'],
            defaults={
                'tenant': tenant,
                'account_type': acc_data['account_type'],
                'billing_cycle': acc_data['billing_cycle'],
                'status': acc_data['status'],
                'created_by': users[acc_data['primary_user']]
            }
        )
        
        # Create user role for account
        UserAccountRole.objects.get_or_create(
            user=users[acc_data['primary_user']],
            account=account,
            defaults={
                'tenant': tenant,
                'role': 'primary',
                'can_manage_services': True,
                'can_manage_billing': True,
                'can_view_usage': True
            }
        )
        
        accounts[acc_data['account_number']] = account
        print(f"✓ Account: {account.account_number}")
    
    # Create sample addresses
    addresses_data = [
        {
            'account': 'ACC-001-2024',
            'address_line1': '123 Main Street',
            'city': 'Auckland',
            'postal_code': '1010',
            'address_type': 'service',
            'is_primary': True
        },
        {
            'account': 'ACC-002-2024',
            'address_line1': '456 Business Avenue',
            'city': 'Wellington',
            'postal_code': '6011',
            'address_type': 'service',
            'is_primary': True
        },
        {
            'account': 'ACC-003-2024',
            'address_line1': '789 Residential Road',
            'city': 'Christchurch',
            'postal_code': '8011',
            'address_type': 'service',
            'is_primary': True
        },
        {
            'account': 'ACC-004-2024',
            'address_line1': '321 Commercial Street',
            'city': 'Hamilton',
            'postal_code': '3204',
            'address_type': 'service',
            'is_primary': True
        }
    ]
    
    for addr_data in addresses_data:
        account_obj = accounts[addr_data['account']]
        addr_data_copy = addr_data.copy()
        addr_data_copy.pop('account')  # Remove the string key
        AccountAddress.objects.get_or_create(
            account=account_obj,
            address_line1=addr_data['address_line1'],
            defaults={
                **addr_data_copy,
                'tenant': tenant,
                'region': 'New Zealand',
                'country': 'NZ'
            }
        )
        print(f"✓ Address: {addr_data['address_line1']}")
    
    # Create sample contracts
    try:
        from core.contracts.models import ServiceContract
        
        contracts_data = [
            {
                'contract_number': 'ELE-001-2024',
                'customer': users['testuser@email.com'],
                'account': accounts['ACC-001-2024'],
                'tenant': tenant,
                'contract_type': 'electricity',
                'service_name': 'Residential Electricity',
                'description': 'Standard residential electricity service',
                'status': 'active',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 12, 31),
                'billing_frequency': 'monthly'
            },
            {
                'contract_number': 'BB-001-2024',
                'customer': users['testuser@email.com'],
                'account': accounts['ACC-001-2024'],
                'tenant': tenant,
                'contract_type': 'broadband',
                'service_name': 'Fibre Broadband',
                'description': 'High-speed fiber broadband service',
                'status': 'active',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 12, 31),
                'billing_frequency': 'monthly'
            },
            {
                'contract_number': 'MOB-001-2024',
                'customer': users['admin@spoton.co.nz'],
                'account': accounts['ACC-002-2024'],
                'tenant': tenant,
                'contract_type': 'mobile',
                'service_name': 'Business Mobile',
                'description': 'Business mobile service with premium features',
                'status': 'active',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 12, 31),
                'billing_frequency': 'monthly'
            },
            {
                'contract_number': 'ELE-002-2024',
                'customer': users['jane.smith@email.com'],
                'account': accounts['ACC-003-2024'],
                'tenant': tenant,
                'contract_type': 'electricity',
                'service_name': 'Green Electricity',
                'description': 'Renewable energy electricity service',
                'status': 'active',
                'start_date': date(2024, 2, 1),
                'end_date': date(2025, 1, 31),
                'billing_frequency': 'monthly'
            },
            {
                'contract_number': 'BB-002-2024',
                'customer': users['business@company.co.nz'],
                'account': accounts['ACC-004-2024'],
                'tenant': tenant,
                'contract_type': 'broadband',
                'service_name': 'Business Fibre',
                'description': 'Ultra-fast business fiber broadband',
                'status': 'active',
                'start_date': date(2024, 3, 1),
                'end_date': date(2026, 2, 28),
                'billing_frequency': 'quarterly'
            }
        ]
        
        for contract_data in contracts_data:
            contract, created = ServiceContract.objects.get_or_create(
                contract_number=contract_data['contract_number'],
                defaults={**contract_data, 'created_by': contract_data['customer']}
            )
            print(f"✓ Contract: {contract.contract_number}")
            
        print("✓ All contracts created successfully")
        
    except ImportError as e:
        print(f"⚠ Could not create contracts - models not available: {e}")
    
    print("\n🎉 Simple sample data creation completed!")
    print("\nSample data includes:")
    print("- 1 Tenant (SpotOn Energy Client)")
    print("- 4 Users (2 residential, 2 commercial)")
    print("- 4 Accounts with proper user roles")
    print("- 4 Service addresses")
    print("- 5 Service contracts")
    print("- Plans and connections provided by ViewSet fallback data")
    print("\nYou can now test all CRUD operations in the frontend!")

if __name__ == '__main__':
    create_simple_sample_data() 