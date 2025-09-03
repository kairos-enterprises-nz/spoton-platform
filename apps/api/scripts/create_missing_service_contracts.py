#!/usr/bin/env python3
"""
Create missing service contracts for users who completed onboarding before the 
contract creation feature was implemented.

This script identifies users who have:
1. Completed onboarding (UserOnboardingConfirmation exists)
2. Selected services (mobile, broadband, electricity)
3. But don't have corresponding ServiceContract and Connection records

It then creates the missing contracts and connections using the same logic
as the OnboardingFinalizeView.
"""

import os
import sys
import django
from django.utils import timezone
from django.db import transaction
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from users.models import User, UserAccountRole, Tenant, Account, Address
from core.user_details.models import UserOnboardingConfirmation
from core.contracts.models import ServiceContract
from energy.connections.models import Connection


def create_missing_contracts():
    """Create missing service contracts for users who completed onboarding"""
    
    print("🔍 Finding users with missing service contracts...")
    
    # Get all users with completed onboarding
    confirmations = UserOnboardingConfirmation.objects.filter(is_completed=True)
    
    total_users = confirmations.count()
    users_processed = 0
    contracts_created = 0
    connections_created = 0
    
    print(f"📊 Found {total_users} users with completed onboarding")
    
    for confirmation in confirmations:
        user = confirmation.user
        services_chosen = confirmation.services_chosen or {}
        plan_selections = confirmation.plan_selections or {}
        
        # Check if user has an account
        try:
            role = UserAccountRole.objects.filter(user=user).first()
            if not role:
                print(f"⚠️  User {user.id} has no account, skipping")
                continue
                
            account = role.account
            tenant = account.tenant
            
            # Check which services are selected but don't have contracts
            existing_contracts = ServiceContract.objects.filter(account=account)
            existing_service_types = set(contract.contract_type for contract in existing_contracts)
            
            services_to_create = []
            for service_type in ['mobile', 'broadband', 'electricity']:
                if services_chosen.get(service_type) and service_type not in existing_service_types:
                    services_to_create.append(service_type)
            
            if not services_to_create:
                users_processed += 1
                continue  # User already has all their contracts
            
            print(f"\n👤 User {user.id}")
            print(f"   Services to create: {services_to_create}")
            
            # Get service address
            service_address = None
            if account.billing_address:
                service_address = account.billing_address
            else:
                # Try to create from onboarding address info
                address_info = confirmation.address_info or {}
                full_addr = address_info.get('full_address', '')
                if full_addr:
                    # Simple address parsing
                    parts = [p.strip() for p in full_addr.split(',') if p.strip()]
                    address_line1 = parts[0] if parts else ''
                    city = parts[-1] if len(parts) > 1 else 'Auckland'
                    
                    service_address, _ = Address.objects.get_or_create(
                        tenant=tenant,
                        address_line1=address_line1,
                        city=city,
                        postal_code='0000',
                        defaults={
                            'country': 'New Zealand',
                            'address_type': 'service',
                            'is_primary': True,
                        }
                    )
                    account.billing_address = service_address
                    account.save(update_fields=['billing_address'])
            
            # Create contracts and connections for missing services
            with transaction.atomic():
                for service_type in services_to_create:
                    plan_data = plan_selections.get(service_type) or {}
                    
                    if service_type == 'mobile':
                        # Create mobile contract
                        contract = ServiceContract.objects.create(
                            tenant=tenant,
                            account=account,
                            contract_type='mobile',
                            service_name=plan_data.get('name') or 'Mobile Service',
                            description='Created by migration script',
                            start_date=timezone.now(),
                            status='pending',
                            billing_frequency='monthly',
                            base_charge=plan_data.get('charges', {}).get('monthly_charge') or plan_data.get('rate') or 0,
                            metadata={
                                'plan': plan_data,
                                'plan_type': plan_data.get('plan_type') or 'postpaid',
                                'migration_created': True,
                            },
                            created_by=user,
                            updated_by=user,
                        )
                        contracts_created += 1
                        
                        # Create mobile connection
                        # Generate a placeholder mobile number for validation
                        placeholder_mobile = f"+64-MOB-{account.account_number[-6:]}"
                        
                        connection = Connection.objects.create(
                            tenant=tenant,
                            account=account,
                            contract_id=contract.id,
                            service_address=None,  # Mobile doesn't need address
                            service_type='mobile',
                            connection_identifier=placeholder_mobile,
                            mobile_number=placeholder_mobile,  # Required for validation
                            status='pending_activation',
                            metadata={
                                'plan_type': plan_data.get('plan_type') or 'postpaid',
                                'awaiting_sim_activation': True,
                                'migration_created': True,
                                'placeholder_number': True,  # Flag to indicate this is a placeholder
                            }
                        )
                        connections_created += 1
                        print(f"   ✅ Created mobile contract {contract.id}")
                    
                    elif service_type == 'broadband':
                        # Create broadband contract
                        contract = ServiceContract.objects.create(
                            tenant=tenant,
                            account=account,
                            contract_type='broadband',
                            service_name=plan_data.get('name') or 'Broadband Service',
                            description='Created by migration script',
                            start_date=timezone.now(),
                            status='pending',
                            billing_frequency='monthly',
                            base_charge=plan_data.get('charges', {}).get('monthly_charge') or plan_data.get('rate') or 0,
                            metadata={
                                'plan': plan_data,
                                'migration_created': True,
                            },
                            created_by=user,
                            updated_by=user,
                        )
                        contracts_created += 1
                        
                        # Create broadband connection
                        line_speed = None
                        dl, ul = plan_data.get('download_speed'), plan_data.get('upload_speed')
                        if dl or ul:
                            line_speed = f"{(dl or '').replace(' Mbps','')}/{(ul or '').replace(' Mbps','')} Mbps".strip()
                        
                        connection = Connection.objects.create(
                            tenant=tenant,
                            account=account,
                            contract_id=contract.id,
                            service_address=service_address,
                            service_type='broadband',
                            connection_identifier=f"BB-{account.account_number}",
                            status='pending',
                            line_speed=line_speed or '',
                            metadata={'migration_created': True}
                        )
                        connections_created += 1
                        print(f"   ✅ Created broadband contract {contract.id}")
                    
                    elif service_type == 'electricity':
                        # Create electricity contract
                        charges = plan_data.get('charges', {})
                        base_charge = 0
                        if charges:
                            standard_charges = charges.get('standard', {})
                            daily_charge = standard_charges.get('daily_charge', {}).get('amount', 0)
                            base_charge = float(daily_charge) * 30 if daily_charge else 0
                        
                        contract = ServiceContract.objects.create(
                            tenant=tenant,
                            account=account,
                            contract_type='electricity',
                            service_name=plan_data.get('name') or 'Electricity Supply',
                            description='Created by migration script',
                            start_date=timezone.now(),
                            status='pending',
                            billing_frequency='monthly',
                            base_charge=base_charge,
                            metadata={
                                'plan': plan_data,
                                'charges': charges,
                                'migration_created': True,
                            },
                            created_by=user,
                            updated_by=user,
                        )
                        contracts_created += 1
                        
                        # Create electricity connection
                        # Generate a placeholder ICP code for validation
                        placeholder_icp = f"ICP-{account.account_number[-6:]}"
                        
                        connection = Connection.objects.create(
                            tenant=tenant,
                            account=account,
                            contract_id=contract.id,
                            service_address=service_address,
                            service_type='electricity',
                            connection_identifier=placeholder_icp,
                            icp_code=placeholder_icp,  # Required for validation
                            status='pending_switch',
                            metadata={
                                'awaiting_retailer_switch': True,
                                'migration_created': True,
                                'placeholder_icp': True,  # Flag to indicate this is a placeholder
                            }
                        )
                        connections_created += 1
                        print(f"   ✅ Created electricity contract {contract.id}")
            
            users_processed += 1
            
        except Exception as e:
            print(f"❌ Error processing user {user.id}: {e}")
            continue
    
    print(f"\n🎉 Migration completed!")
    print(f"   Users processed: {users_processed}/{total_users}")
    print(f"   Contracts created: {contracts_created}")
    print(f"   Connections created: {connections_created}")


if __name__ == '__main__':
    create_missing_contracts()
