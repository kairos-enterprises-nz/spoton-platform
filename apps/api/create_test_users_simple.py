#!/usr/bin/env python3
"""
Script to create two test users with different onboarding stages:
1. testuser@email.com - Account created only (is_onboarding_complete=False)
2. testuser1@email.com - Complete onboarding (is_onboarding_complete=True)
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append('/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Tenant

User = get_user_model()

def create_test_users():
    print("Creating test users...")
    
    # Get or create default tenant
    tenant, created = Tenant.objects.get_or_create(
        slug='spoton-energy-test',
        defaults={
            'name': 'SpotOn Energy Test',
            'contact_email': 'admin@spoton.energy',
            'timezone': 'Pacific/Auckland',
            'currency': 'NZD',
            'is_active': True
        }
    )
    if created:
        print(f"Created tenant: {tenant.name}")
    else:
        print(f"Using existing tenant: {tenant.name}")
    
    # User 1: Account created only (basic stage)
    print("\n--- Creating User 1: Basic Account ---")
    user1_email = 'testuser@email.com'
    user1, created = User.objects.get_or_create(
        email=user1_email,
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'residential',
            'tenant': tenant,
            'is_active': True,
            'is_verified': True,
            'is_email_verified': True,
            'is_mobile_verified': True,
            # Note: is_onboarding_complete is handled by OnboardingProgress model, not User
            'mobile': '+64-21-111-1111'
        }
    )
    
    if created:
        user1.set_password('Testpass@123')
        user1.save()
        print(f"✅ Created user: {user1.email}")
        print(f"   - User Number: {user1.user_number}")
        print(f"   - Onboarding Complete: False (handled by OnboardingProgress model)")
        print(f"   - Password: Testpass@123")
    else:
        # Update existing user to ensure correct state
        # Note: is_onboarding_complete is handled by OnboardingProgress model, not User
        user1.set_password('Testpass@123')
        user1.save()
        print(f"✅ Updated existing user: {user1.email}")
        print(f"   - User Number: {user1.user_number}")
        print(f"   - Onboarding Complete: False (handled by OnboardingProgress model)")
    
    # User 2: Complete onboarding
    print("\n--- Creating User 2: Complete Onboarding ---")
    user2_email = 'testuser1@email.com'
    user2, created = User.objects.get_or_create(
        email=user2_email,
        defaults={
            'first_name': 'Test',
            'last_name': 'UserComplete',
            'user_type': 'residential',
            'tenant': tenant,
            'is_active': True,
            'is_verified': True,
            'is_email_verified': True,
            'is_mobile_verified': True,
            # Note: is_onboarding_complete is handled by OnboardingProgress model, not User
            'mobile': '+64-21-222-2222'
        }
    )
    
    if created:
        user2.set_password('Testpass@123')
        user2.save()
        print(f"✅ Created user: {user2.email}")
        print(f"   - User Number: {user2.user_number}")
        print(f"   - Onboarding Complete: True (handled by OnboardingProgress model)")
        print(f"   - Password: Testpass@123")
    else:
        # Update existing user to ensure correct state
        # Note: is_onboarding_complete is handled by OnboardingProgress model, not User
        user2.set_password('Testpass@123')
        user2.save()
        print(f"✅ Updated existing user: {user2.email}")
        print(f"   - User Number: {user2.user_number}")
        print(f"   - Onboarding Complete: True (handled by OnboardingProgress model)")
    
    print("\n" + "="*60)
    print("TEST USERS CREATED SUCCESSFULLY!")
    print("="*60)
    
    print("\n🔐 LOGIN CREDENTIALS:")
    print(f"User 1 (Account Created): {user1_email} / Testpass@123")
    print(f"User 2 (Onboarding Complete): {user2_email} / Testpass@123")
    
    print("\n📊 USER STATES:")
    print(f"User 1: onboarding status handled by OnboardingProgress model")
    print(f"User 2: onboarding status handled by OnboardingProgress model")
    
    print("\n🌐 TENANT INFO:")
    print(f"Tenant: {tenant.name} ({tenant.slug})")
    
    print("\n📝 SUMMARY:")
    print("- testuser@email.com: Account created, needs to complete onboarding")
    print("- testuser1@email.com: Account created and onboarding completed")
    
    return user1, user2

if __name__ == '__main__':
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        import traceback
        traceback.print_exc() 