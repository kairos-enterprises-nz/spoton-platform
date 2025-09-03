"""
Core app URLs with environment awareness
"""
from django.urls import path, include
from .views.keycloak_auth import (
    KeycloakLoginView,
    KeycloakCallbackView,
    KeycloakSocialCallbackView,
    KeycloakLogoutView,
    KeycloakRefreshView,
    KeycloakCreateUserView,
    PKCEStorageView
)
from .views.global_auth import GlobalLogoutView
from users.views.profile_completion import (
    ProfileCompletionView,
    MobileVerificationView,
    check_profile_completion,
    complete_social_profile
)
from .views.tenant_config_views import (
    get_tenant_config,
    get_keycloak_config, 
    get_tenant_list
)

urlpatterns = [
    # Tenant Configuration API (Public endpoints)
    path('tenant/config/', get_tenant_config, name='tenant_config'),
    path('tenant/keycloak/', get_keycloak_config, name='keycloak_config'),
    path('tenant/list/', get_tenant_list, name='tenant_list'),
    
    # Global authentication coordination
    path('auth/global-logout/', GlobalLogoutView.as_view(), name='global_logout'),
    
    # Keycloak authentication endpoints
    path('auth/keycloak/login/', KeycloakLoginView.as_view(), name='keycloak_login'),
    path('auth/keycloak/callback/', KeycloakCallbackView.as_view(), name='keycloak_callback'),
    path('auth/keycloak/social-callback/', KeycloakSocialCallbackView.as_view(), name='keycloak_social_callback'),
    path('auth/keycloak/logout/', KeycloakLogoutView.as_view(), name='keycloak_logout'),
    path('auth/keycloak/refresh/', KeycloakRefreshView.as_view(), name='keycloak_refresh'),
    path('auth/keycloak/create-user/', KeycloakCreateUserView.as_view(), name='keycloak_create_user'),
    path('auth/keycloak/store-pkce/', PKCEStorageView.as_view(), name='store_pkce'),
    
    # Profile completion endpoints
    path('profile/completion/', ProfileCompletionView.as_view(), name='profile_completion'),
    path('profile/mobile-verification/', MobileVerificationView.as_view(), name='mobile_verification'),
    path('profile/check-completion/', check_profile_completion, name='check_profile_completion'),
    path('profile/complete-social/', complete_social_profile, name='complete_social_profile'),
    
    # Include other core URLs if they exist
    # path('api/', include('core.api_urls')),  # Commented out - file doesn't exist
] 