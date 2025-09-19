# This file makes the views directory a Python package
# Import all views from the main_views.py file for backward compatibility
from ..main_views import (
    CreateUserAccountView,
    KeycloakPasswordLoginView,
    TokenVerifyView,
    HandleOTPView,
    LoginOTPRequestView,
    LoginOTPVerifyView,
    PasswordResetRequestOTPView,
    PasswordResetVerifyOTPView,
    CheckEmail,
    # TokenRefreshView removed - Keycloak handles token refresh
    # CustomTokenObtainPairView removed - Keycloak handles token obtain
    ProfileView,
    wiki_proxy,
    wiki_health_check,
    wiki_stats
) 