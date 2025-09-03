#!/usr/bin/env python3

from users.models import User
from users.services.user_cache_service import UserCacheService
from users.keycloak_admin import KeycloakAdminService

print('=== FIXING TESTUSER1 INFINITE REDIRECT LOOP ===')

# Find testuser1 
testuser1 = User.objects.filter(id='86d8896a-1a83-4d2c-83cd-b2642e9b78ef').first()

if testuser1:
    print(f'Found testuser1: {testuser1.keycloak_id}')
    
    # Get cached data
    cached_data = UserCacheService.get_user_data(testuser1.keycloak_id, force_refresh=True)
    
    if cached_data:
        phone_verified = cached_data.get('phone_verified', False)
        onboarding_complete = cached_data.get('is_onboarding_complete', False)
        
        print(f'Current state: phone_verified={phone_verified}, onboarding_complete={onboarding_complete}')
        
        # Fix the infinite loop condition: phone_verified=False but onboarding_complete=True
        if not phone_verified and onboarding_complete:
            print('🔧 FIXING: Setting phone_verified=true in Keycloak...')
            keycloak_admin = KeycloakAdminService()
            
            success = keycloak_admin.update_user(testuser1.keycloak_id, {
                'attributes': {
                    'phoneVerified': ['true']
                }
            })
            
            if success:
                print('✅ Updated Keycloak successfully')
                UserCacheService.invalidate_cache(testuser1.keycloak_id)
                print('✅ Cleared cache')
                
                fresh_data = UserCacheService.get_user_data(testuser1.keycloak_id, force_refresh=True)
                print(f'✅ VERIFIED: phone_verified is now {fresh_data.get("phone_verified")}')
                print('✅ testuser1 infinite redirect loop should now be FIXED!')
            else:
                print('❌ ERROR: Failed to update Keycloak')
        else:
            print('ℹ️  No fix needed - user state is already correct')
    else:
        print('❌ ERROR: No cached data found')
else:
    print('❌ ERROR: testuser1 not found')

print('\n=== DONE ===')
