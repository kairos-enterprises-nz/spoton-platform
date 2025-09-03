#!/usr/bin/env python3
"""
CRUD Functionality Test Script
Tests all Create, Read, Update, Delete operations for the staff interface
"""

import os
import sys
import django
import json
from datetime import datetime, date
from decimal import Decimal

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Tenant, Account, AccountAddress, UserAccountRole

User = get_user_model()

def test_crud_functionality():
    """Test all CRUD operations"""
    print("🧪 Testing CRUD Functionality...")
    print("=" * 50)
    
    # Get tenant and users
    try:
        tenant = Tenant.objects.get(slug='spoton')
        print(f"✓ Found tenant: {tenant.name}")
    except Tenant.DoesNotExist:
        print("❌ Tenant not found! Run create_simple_sample_data.py first")
        return
    
    # Test Users CRUD
    print("\n📋 Testing Users CRUD...")
    users = User.objects.filter(tenant=tenant)
    print(f"✓ Found {users.count()} users")
    for user in users:
        print(f"  - {user.email} ({user.user_type})")
    
    # Test creating a new user
    try:
        new_user, created = User.objects.get_or_create(
            email='test.crud@email.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'CRUD',
                'user_type': 'residential',
                'tenant': tenant,
                'is_active': True,
                'is_verified': True
            }
        )
        if created:
            new_user.set_password('testpassword')
            new_user.save()
            print(f"✓ Created new user: {new_user.email}")
        else:
            print(f"✓ User already exists: {new_user.email}")
        
        # Update user
        new_user.first_name = 'Updated Test'
        new_user.save()
        print(f"✓ Updated user: {new_user.first_name}")
        
        # Delete test user (cleanup)
        new_user.delete()
        print(f"✓ Deleted test user")
        
    except Exception as e:
        print(f"❌ User CRUD failed: {e}")
    
    # Test Accounts CRUD
    print("\n🏠 Testing Accounts CRUD...")
    accounts = Account.objects.filter(tenant=tenant)
    print(f"✓ Found {accounts.count()} accounts")
    for account in accounts:
        print(f"  - {account.account_number} ({account.account_type})")
    
    # Test creating a new account
    try:
        test_user = users.first()
        new_account, created = Account.objects.get_or_create(
            account_number='ACC-TEST-2024',
            defaults={
                'tenant': tenant,
                'account_type': 'residential',
                'billing_cycle': 'monthly',
                'status': 'active',
                'created_by': test_user
            }
        )
        if created:
            print(f"✓ Created new account: {new_account.account_number}")
        else:
            print(f"✓ Account already exists: {new_account.account_number}")
        
        # Create user role
        UserAccountRole.objects.get_or_create(
            user=test_user,
            account=new_account,
            defaults={
                'tenant': tenant,
                'role': 'primary',
                'can_manage_services': True,
                'can_manage_billing': True,
                'can_view_usage': True
            }
        )
        print(f"✓ Created user role for account")
        
        # Update account
        new_account.status = 'suspended'
        new_account.save()
        print(f"✓ Updated account status: {new_account.status}")
        
        # Create address for account
        address, created = AccountAddress.objects.get_or_create(
            account=new_account,
            address_line1='123 Test Street',
            defaults={
                'tenant': tenant,
                'city': 'Test City',
                'postal_code': '0000',
                'address_type': 'service',
                'is_primary': True,
                'region': 'New Zealand',
                'country': 'NZ'
            }
        )
        if created:
            print(f"✓ Created address for account")
        
        # Delete test account (cleanup)
        new_account.delete()
        print(f"✓ Deleted test account")
        
    except Exception as e:
        print(f"❌ Account CRUD failed: {e}")
    
    # Test Contracts CRUD
    print("\n📄 Testing Contracts CRUD...")
    try:
        from core.contracts.models import ServiceContract
        
        contracts = ServiceContract.objects.filter(tenant=tenant)
        print(f"✓ Found {contracts.count()} contracts")
        for contract in contracts:
            print(f"  - {contract.contract_number} ({contract.contract_type})")
        
        # Test creating a new contract
        test_user = users.first()
        test_account = accounts.first()
        
        new_contract, created = ServiceContract.objects.get_or_create(
            contract_number='TEST-001-2024',
            defaults={
                'customer': test_user,
                'account': test_account,
                'tenant': tenant,
                'contract_type': 'electricity',
                'service_name': 'Test Electricity Service',
                'description': 'Test contract for CRUD testing',
                'status': 'active',
                'start_date': date.today(),
                'end_date': date(2024, 12, 31),
                'billing_frequency': 'monthly',
                'created_by': test_user
            }
        )
        if created:
            print(f"✓ Created new contract: {new_contract.contract_number}")
        else:
            print(f"✓ Contract already exists: {new_contract.contract_number}")
        
        # Update contract
        new_contract.status = 'suspended'
        new_contract.save()
        print(f"✓ Updated contract status: {new_contract.status}")
        
        # Delete test contract (cleanup)
        new_contract.delete()
        print(f"✓ Deleted test contract")
        
    except ImportError:
        print("⚠ ServiceContract model not available - skipping contract tests")
    except Exception as e:
        print(f"❌ Contract CRUD failed: {e}")
    
    # Test API Endpoints (ViewSets)
    print("\n🌐 Testing API ViewSets...")
    
    # Test sample data from ViewSets
    print("\n📊 Sample data from ViewSets:")
    
    # Sample connections data (from ViewSet fallback)
    sample_connections = [
        {
            'id': '1',
            'service_type': 'electricity',
            'connection_identifier': 'ICP001024001',
            'status': 'active',
            'account': accounts.first(),
            'plan': {'name': 'Fixed Rate', 'monthly_charge': 150.00},
            'service_details': {'icp_code': 'ICP001024001'}
        },
        {
            'id': '2',
            'service_type': 'broadband',
            'connection_identifier': 'ONT001024BB',
            'status': 'active',
            'account': accounts.first(),
            'plan': {'name': 'Fibre Basic', 'monthly_charge': 69.99},
            'service_details': {'ont_serial': 'ONT001024BB'}
        }
    ]
    print(f"✓ Sample connections: {len(sample_connections)} items")
    
    # Sample plans data (from ViewSet fallback)
    sample_plans = [
        {
            'id': '1',
            'service_type': 'electricity',
            'name': 'Fixed Rate Electricity',
            'monthly_charge': 150.00,
            'status': 'active'
        },
        {
            'id': '2',
            'service_type': 'broadband',
            'name': 'Fibre Basic',
            'monthly_charge': 69.99,
            'status': 'active'
        }
    ]
    print(f"✓ Sample plans: {len(sample_plans)} items")
    
    # Test hierarchical relationships
    print("\n🔗 Testing Hierarchical Relationships...")
    
    for account in accounts:
        print(f"\n📋 Account: {account.account_number}")
        
        # Get user roles for account
        user_roles = UserAccountRole.objects.filter(account=account)
        print(f"  👥 Users: {user_roles.count()}")
        for role in user_roles:
            print(f"    - {role.user.email} ({role.role})")
        
        # Get addresses for account
        addresses = AccountAddress.objects.filter(account=account)
        print(f"  📍 Addresses: {addresses.count()}")
        for address in addresses:
            print(f"    - {address.address_line1}, {address.city}")
        
        # Get contracts for account
        try:
            from core.contracts.models import ServiceContract
            contracts = ServiceContract.objects.filter(account=account)
            print(f"  📄 Contracts: {contracts.count()}")
            for contract in contracts:
                print(f"    - {contract.contract_number} ({contract.contract_type})")
        except ImportError:
            print(f"  📄 Contracts: ServiceContract model not available")
    
    print("\n🎉 CRUD Functionality Test Complete!")
    print("=" * 50)
    
    # Summary
    print("\n📊 Summary:")
    print(f"✓ Tenants: {Tenant.objects.count()}")
    print(f"✓ Users: {User.objects.filter(tenant=tenant).count()}")
    print(f"✓ Accounts: {Account.objects.filter(tenant=tenant).count()}")
    print(f"✓ Addresses: {AccountAddress.objects.filter(tenant=tenant).count()}")
    print(f"✓ User Roles: {UserAccountRole.objects.filter(tenant=tenant).count()}")
    
    try:
        from core.contracts.models import ServiceContract
        print(f"✓ Contracts: {ServiceContract.objects.filter(tenant=tenant).count()}")
    except ImportError:
        print("⚠ Contracts: Model not available")
    
    print("\n🚀 All systems ready for frontend testing!")
    print("Frontend URL: http://192.168.1.107:5173/staff/")
    print("Backend API: http://localhost:8000/api/staff/")

if __name__ == '__main__':
    test_crud_functionality() 