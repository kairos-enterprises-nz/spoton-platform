#!/usr/bin/env python3
"""
Comprehensive Sample Data Creation Script
Creates sample connections, plans, and assignments for testing the hierarchical structure
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

def create_sample_data():
    """Create comprehensive sample data for testing"""
    print("Creating comprehensive sample data...")
    
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
    
    # Create sample plans using the public pricing models
    try:
        from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan
        
        # Electricity Plans
        electricity_plans_data = [
            {
                'name': 'Fixed Rate Electricity',
                'description': 'Stable fixed rate electricity plan with competitive pricing',
                'monthly_charge': Decimal('150.00'),
                'is_active': True,
                'rate_type': 'fixed',
                'peak_rate': Decimal('0.28'),
                'daily_charge': Decimal('1.50'),
                'green_energy': False
            },
            {
                'name': 'Green Energy Plan',
                'description': '100% renewable energy from wind and solar sources',
                'monthly_charge': Decimal('165.00'),
                'is_active': True,
                'rate_type': 'fixed',
                'peak_rate': Decimal('0.30'),
                'daily_charge': Decimal('1.50'),
                'green_energy': True
            },
            {
                'name': 'Time of Use Plan',
                'description': 'Variable rates based on time of day usage',
                'monthly_charge': Decimal('140.00'),
                'is_active': True,
                'rate_type': 'time_of_use',
                'peak_rate': Decimal('0.35'),
                'off_peak_rate': Decimal('0.18'),
                'daily_charge': Decimal('1.80'),
                'green_energy': False
            }
        ]
        
        for plan_data in electricity_plans_data:
            plan, created = ElectricityPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            print(f"✓ Electricity Plan: {plan.name}")
        
        # Broadband Plans
        broadband_plans_data = [
            {
                'name': 'Fibre Basic',
                'description': 'Reliable fiber broadband for everyday use',
                'monthly_charge': Decimal('69.99'),
                'is_active': True,
                'download_speed': 100,
                'upload_speed': 20,
                'data_allowance': 'Unlimited',
                'contract_length': 12,
                'modem_included': True
            },
            {
                'name': 'Fibre Pro',
                'description': 'High-speed fiber for heavy users and businesses',
                'monthly_charge': Decimal('89.99'),
                'is_active': True,
                'download_speed': 300,
                'upload_speed': 100,
                'data_allowance': 'Unlimited',
                'contract_length': 24,
                'modem_included': True
            },
            {
                'name': 'Fibre Ultra',
                'description': 'Ultra-fast fiber for demanding applications',
                'monthly_charge': Decimal('129.99'),
                'is_active': True,
                'download_speed': 900,
                'upload_speed': 500,
                'data_allowance': 'Unlimited',
                'contract_length': 24,
                'modem_included': True
            }
        ]
        
        for plan_data in broadband_plans_data:
            plan, created = BroadbandPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            print(f"✓ Broadband Plan: {plan.name}")
        
        # Mobile Plans
        mobile_plans_data = [
            {
                'name': 'Mobile Essential',
                'description': 'Essential mobile plan with good data allowance',
                'monthly_charge': Decimal('29.99'),
                'is_active': True,
                'data_allowance': '15GB',
                'talk_minutes': 'Unlimited',
                'text_allowance': 'Unlimited',
                'plan_type': 'prepaid',
                'international_calls': False
            },
            {
                'name': 'Mobile Plus',
                'description': 'Comprehensive mobile plan with premium features',
                'monthly_charge': Decimal('49.99'),
                'is_active': True,
                'data_allowance': '40GB',
                'talk_minutes': 'Unlimited',
                'text_allowance': 'Unlimited',
                'plan_type': 'postpaid',
                'international_calls': True
            },
            {
                'name': 'Mobile Business',
                'description': 'Business mobile plan with enterprise features',
                'monthly_charge': Decimal('79.99'),
                'is_active': True,
                'data_allowance': '100GB',
                'talk_minutes': 'Unlimited',
                'text_allowance': 'Unlimited',
                'plan_type': 'postpaid',
                'international_calls': True
            }
        ]
        
        for plan_data in mobile_plans_data:
            plan, created = MobilePlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            print(f"✓ Mobile Plan: {plan.name}")
            
        print("✓ All plans created successfully")
        
    except ImportError as e:
        print(f"⚠ Could not create plans - models not available: {e}")
    
    # Create sample connections (this would normally be in the energy.connections app)
    # For now, we'll create sample data that the ViewSets can use
    print("✓ Sample connections will be provided by ViewSet fallback data")
    
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
    
    print("\n🎉 Comprehensive sample data creation completed!")
    print("\nSample data includes:")
    print("- 1 Tenant (SpotOn Energy Client)")
    print("- 4 Users (2 residential, 2 commercial)")
    print("- 4 Accounts with proper user roles")
    print("- 4 Service addresses")
    print("- 9 Service plans (3 electricity, 3 broadband, 3 mobile)")
    print("- 5 Service contracts")
    print("- Sample connections provided by ViewSet fallback")
    print("\nYou can now test all CRUD operations in the frontend!")

if __name__ == '__main__':
    create_sample_data() 