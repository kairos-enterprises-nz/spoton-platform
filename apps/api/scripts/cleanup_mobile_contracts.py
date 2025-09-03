#!/usr/bin/env python3
"""
Management script to clean up mobile service contracts and ensure correct service counts.
This addresses the issue where users show incorrect service counts due to historical mobile contracts.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.contracts.models import ServiceContract
from energy.connections.models import Connection
from users.models import UserAccountRole
from core.user_details.models import UserOnboardingConfirmation

User = get_user_model()

def cleanup_mobile_contracts():
    """
    Clean up mobile contracts for users to fix service count discrepancies.
    Since mobile services are now 'coming soon', remove old mobile contracts.
    """
    print("🧹 Starting Mobile Contract Cleanup...")
    
    # Find all mobile contracts
    mobile_contracts = ServiceContract.objects.filter(contract_type='mobile')
    print(f"📱 Found {mobile_contracts.count()} mobile contracts")
    
    deleted_contracts = 0
    deleted_connections = 0
    
    for contract in mobile_contracts:
        print(f"\n🔍 Processing mobile contract {contract.id} for account {contract.account.account_number}")
        
        # Find associated connections
        mobile_connections = Connection.objects.filter(
            account=contract.account,
            service_type='mobile',
            contract_id=contract.id
        )
        
        print(f"  📱 Found {mobile_connections.count()} mobile connections")
        
        # Delete connections first (foreign key constraint)
        for connection in mobile_connections:
            print(f"    🗑️ Deleting connection {connection.id}: {connection.connection_identifier}")
            connection.delete()
            deleted_connections += 1
        
        # Delete the contract
        print(f"  🗑️ Deleting contract {contract.id}: {contract.service_name}")
        contract.delete()
        deleted_contracts += 1
    
    print(f"\n✅ Cleanup Complete!")
    print(f"  📱 Deleted {deleted_contracts} mobile contracts")
    print(f"  🔗 Deleted {deleted_connections} mobile connections")
    
    return deleted_contracts, deleted_connections

def ensure_broadband_contracts():
    """
    Ensure all users have broadband contracts if they selected broadband during onboarding.
    """
    print("\n🌐 Ensuring Broadband Contracts...")
    
    # Find users with broadband in onboarding but no broadband contracts
    onboarding_confirmations = UserOnboardingConfirmation.objects.all()
    
    missing_broadband = 0
    created_contracts = 0
    
    for confirmation in onboarding_confirmations:
        services_chosen = confirmation.services_chosen or {}
        
        if services_chosen.get('broadband', False):
            # Check if user has broadband contract
            user_role = UserAccountRole.objects.filter(user=confirmation.user).first()
            if not user_role:
                print(f"  ⚠️ No account found for user {confirmation.user.email}")
                continue
            
            account = user_role.account
            broadband_contracts = ServiceContract.objects.filter(
                account=account,
                contract_type='broadband'
            )
            
            if not broadband_contracts.exists():
                print(f"  🌐 Creating missing broadband contract for {confirmation.user.email}")
                missing_broadband += 1
                
                # Create broadband contract
                plan_selections = confirmation.plan_selections or {}
                broadband_plan = plan_selections.get('broadband', {})
                
                contract = ServiceContract.objects.create(
                    account=account,
                    tenant=account.tenant,
                    contract_type='broadband',
                    service_name=broadband_plan.get('name', 'Broadband Service'),
                    base_charge=broadband_plan.get('rate', 0.0),
                    status='pending',
                    start_date=confirmation.created_at.date(),
                    metadata={
                        'plan': broadband_plan,
                        'source': 'onboarding_cleanup'
                    }
                )
                created_contracts += 1
                
                # Create connection
                Connection.objects.create(
                    tenant=account.tenant,
                    account=account,
                    contract_id=contract.id,
                    service_address=account.billing_address,
                    service_type='broadband',
                    connection_identifier=f"BB-{account.account_number}",
                    status='pending_activation',
                    metadata={
                        'plan_type': broadband_plan.get('plan_type', 'fibre'),
                        'awaiting_installation': True,
                        'source': 'onboarding_cleanup'
                    }
                )
    
    print(f"  📊 Found {missing_broadband} users missing broadband contracts")
    print(f"  ✅ Created {created_contracts} broadband contracts")
    
    return missing_broadband, created_contracts

def verify_service_counts():
    """
    Verify that service counts are now accurate after cleanup.
    """
    print("\n🔍 Verifying Service Counts...")
    
    # Check a few test users
    test_emails = ['testuser1@email.com', 'hauoralifeindia@gmail.com']
    
    for email in test_emails:
        user = User.objects.filter(email=email).first()
        if not user:
            print(f"  ⚠️ User {email} not found")
            continue
        
        user_role = UserAccountRole.objects.filter(user=user).first()
        if not user_role:
            print(f"  ⚠️ No account for {email}")
            continue
        
        account = user_role.account
        active_contracts = ServiceContract.objects.filter(
            account=account,
            status__in=['pending', 'active']
        )
        
        print(f"  👤 {email}: {active_contracts.count()} active contracts")
        for contract in active_contracts:
            print(f"    - {contract.contract_type}: {contract.service_name}")

if __name__ == "__main__":
    print("🚀 Mobile Contract Cleanup Script")
    print("=" * 50)
    
    try:
        # Step 1: Clean up mobile contracts
        deleted_contracts, deleted_connections = cleanup_mobile_contracts()
        
        # Step 2: Ensure broadband contracts exist
        missing_broadband, created_contracts = ensure_broadband_contracts()
        
        # Step 3: Verify results
        verify_service_counts()
        
        print(f"\n🎉 Script completed successfully!")
        print(f"📊 Summary:")
        print(f"  - Mobile contracts deleted: {deleted_contracts}")
        print(f"  - Mobile connections deleted: {deleted_connections}")
        print(f"  - Broadband contracts created: {created_contracts}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
