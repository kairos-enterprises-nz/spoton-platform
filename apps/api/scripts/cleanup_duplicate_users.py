#!/usr/bin/env python
"""
Script to clean up duplicate user records in the database.

This script handles cases where the same user (identified by email) has multiple
Django User records due to OAuth re-authorization creating new keycloak_ids.

Usage:
    python manage.py shell < scripts/cleanup_duplicate_users.py
    
Or:
    python scripts/cleanup_duplicate_users.py
"""

import os
import sys
import django
import logging
from collections import defaultdict
from django.db import transaction
from users.models import User, UserTenantRole, Tenant
from users.models import OnboardingProgress
from users.keycloak_user_service import KeycloakUserService
from core.services.user_identity_service import UserIdentityService

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

def cleanup_duplicate_users():
    """
    Clean up duplicate users by checking Keycloak for users with same email
    and merging their Django records.
    """
    print("🧹 Starting duplicate user cleanup...")
    
    # Get UAT tenant for Keycloak operations
    try:
        tenant = Tenant.objects.filter(slug='spoton').first()
        if not tenant:
            print("❌ No tenant found with slug 'spoton'")
            return
            
        keycloak_service = KeycloakUserService(tenant=tenant, environment='uat')
        admin_client = keycloak_service._get_admin_client()
    except Exception as e:
        print(f"❌ Failed to initialize Keycloak service: {e}")
        return
    
    # Get all Django users
    all_django_users = User.objects.all()
    print(f"📊 Found {all_django_users.count()} Django users")
    
    # Group users by email (from Keycloak)
    email_to_users = {}
    keycloak_id_to_email = {}
    
    for django_user in all_django_users:
        try:
            # Get user data from Keycloak
            keycloak_user = admin_client.get_user(str(django_user.id))
            if keycloak_user and 'email' in keycloak_user:
                email = keycloak_user['email'].lower()
                keycloak_id_to_email[str(django_user.id)] = email
                
                if email not in email_to_users:
                    email_to_users[email] = []
                email_to_users[email].append(django_user)
        except Exception as e:
            print(f"⚠️  Could not get Keycloak data for user {django_user.id}: {e}")
            continue
    
    # Find and merge duplicates
    duplicates_found = 0
    for email, users in email_to_users.items():
        if len(users) > 1:
            duplicates_found += 1
            print(f"\n🔍 Found {len(users)} users for email {email}:")
            for user in users:
                print(f"  - ID: {user.id}, Created: {user.created_at}")
            
            # Keep the most recently created user
            users.sort(key=lambda u: u.created_at, reverse=True)
            primary_user = users[0]
            duplicate_users = users[1:]
            
            print(f"✅ Keeping primary user: {primary_user.id} (created {primary_user.created_at})")
            
            # Transfer any important data from duplicates to primary user
            for dup_user in duplicate_users:
                print(f"🔄 Processing duplicate user: {dup_user.id}")
                
                # Transfer onboarding progress if primary doesn't have it
                try:
                    
                    dup_progress = OnboardingProgress.objects.filter(user=dup_user).first()
                    primary_progress = OnboardingProgress.objects.filter(user=primary_user).first()
                    
                    if dup_progress and not primary_progress:
                        print(f"  📋 Transferring onboarding progress")
                        dup_progress.user = primary_user
                        dup_progress.save()
                    elif dup_progress and primary_progress:
                        # Keep the more complete progress
                        if dup_progress.step_data and len(dup_progress.step_data) > len(primary_progress.step_data or {}):
                            print(f"  📋 Replacing primary onboarding progress with more complete data")
                            primary_progress.step_data = dup_progress.step_data
                            primary_progress.current_step = dup_progress.current_step
                            primary_progress.is_completed = dup_progress.is_completed
                            primary_progress.save()
                        dup_progress.delete()
                    
                except Exception as e:
                    print(f"  ⚠️  Error transferring onboarding progress: {e}")
                
                # Transfer user tenant roles
                try:
                    dup_roles = UserTenantRole.objects.filter(user=dup_user)
                    for role in dup_roles:
                        # Check if primary user already has this role
                        existing_role = UserTenantRole.objects.filter(
                            user=primary_user, 
                            tenant=role.tenant
                        ).first()
                        if not existing_role:
                            print(f"  👤 Transferring role: {role.role} for tenant {role.tenant.slug}")
                            role.user = primary_user
                            role.save()
                        else:
                            role.delete()
                except Exception as e:
                    print(f"  ⚠️  Error transferring user roles: {e}")
                
                # Delete the duplicate user
                print(f"  🗑️  Deleting duplicate user: {dup_user.id}")
                dup_user.delete()
            
            print(f"✅ Merged {len(duplicate_users)} duplicate users into {primary_user.id}")
    
    if duplicates_found == 0:
        print("✨ No duplicate users found!")
    else:
        print(f"\n✅ Cleanup complete! Processed {duplicates_found} duplicate email addresses")

def verify_cleanup():
    """Verify that cleanup was successful"""
    print("\n🔍 Verifying cleanup results...")
    
    try:
        tenant = Tenant.objects.filter(slug='spoton').first()
        if not tenant:
            print("❌ No tenant found with slug 'spoton' for verification")
            return
            
        keycloak_service = KeycloakUserService(tenant=tenant, environment='uat')
        admin_client = keycloak_service._get_admin_client()
    except Exception as e:
        print(f"❌ Failed to initialize Keycloak service for verification: {e}")
        return
    
    all_django_users = User.objects.all()
    email_counts = {}
    
    for django_user in all_django_users:
        try:
            keycloak_user = admin_client.get_user(str(django_user.id))
            if keycloak_user and 'email' in keycloak_user:
                email = keycloak_user['email'].lower()
                email_counts[email] = email_counts.get(email, 0) + 1
        except Exception:
            continue
    
    duplicates = {email: count for email, count in email_counts.items() if count > 1}
    
    if duplicates:
        print(f"⚠️  Still found {len(duplicates)} emails with multiple users:")
        for email, count in duplicates.items():
            print(f"  - {email}: {count} users")
    else:
        print("✅ No duplicate users remaining!")

if __name__ == '__main__':
    cleanup_duplicate_users()
    verify_cleanup()
