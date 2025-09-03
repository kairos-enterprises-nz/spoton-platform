from django.urls import path
from .main_views import (
    HandleOTPView, CreateUserAccountView, 
    KeycloakPasswordLoginView, TokenVerifyView, LoginOTPRequestView,
    LoginOTPVerifyView, PasswordResetRequestOTPView, PasswordResetVerifyOTPView,
    UserInfoView, LogoutView, ProfileView, CheckAuthView, TokenRefreshView
)
from .performance_views import EnhancedUserInfoView, PerformanceMetricsView
from .portal_views import UserPortalDataView, UserServiceDetailsView, UserServiceInterestView

from .views import (
    CheckEmail, wiki_proxy, wiki_health_check, wiki_stats
)

# Add OTP endpoints
from .otp_views import OTPSendView, OTPVerifyView
from .phone_verification_views import PhoneVerificationSendView, PhoneVerificationVerifyView

urlpatterns = [
    # Registration
    path('register/', CreateUserAccountView.as_view(), name='register'),

    # Customer Login (password-based)
    # Legacy password login & logout endpoints removed (Keycloak SSO enforced)
    
    # Authentication endpoints
    path('auth/login/', KeycloakPasswordLoginView.as_view(), name='keycloak-password-login'),
    path('auth/me/', UserInfoView.as_view(), name='user-info'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token-verify'),
    path('auth/check/', CheckAuthView.as_view(), name='auth-check'),
    
    # Performance-optimized endpoints
    path('auth/me/enhanced/', EnhancedUserInfoView.as_view(), name='enhanced-user-info'),
    path('performance/metrics/', PerformanceMetricsView.as_view(), name='performance-metrics'),


    # Login (OTP-based)
    path('login-otp-request/', LoginOTPRequestView.as_view(), name='login_otp_request'),
    path('login-otp-verify/', LoginOTPVerifyView.as_view(), name='login_otp_verify'),

    # Email availability check
    path('check-email/', CheckEmail, name='check-email'),

    # OTP general handler (signup / verification)
    path('otp/', HandleOTPView.as_view(), name='handle_otp'),

    # Password reset via OTP
    path('password-reset-request-otp/', PasswordResetRequestOTPView.as_view(), name='password_reset_request_otp'),
    path('password-reset-verify-otp/', PasswordResetVerifyOTPView.as_view(), name='password_reset_verify_otp'),

    # OTP endpoints
    path('otp/send/', OTPSendView.as_view(), name='otp-send'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),

    # Phone verification endpoints (authenticated)
    path('phone/send-otp/', PhoneVerificationSendView.as_view(), name='phone-send-otp'),
    path('phone/verify-otp/', PhoneVerificationVerifyView.as_view(), name='phone-verify-otp'),

    path('profile/', ProfileView.as_view(), name='profile'),

    # Portal data endpoints
    path('portal-data/', UserPortalDataView.as_view(), name='user-portal-data'),
    path('service/<str:service_type>/', UserServiceDetailsView.as_view(), name='user-service-details'),
    path('service-interest/', UserServiceInterestView.as_view(), name='user-service-interest'),

    # Wiki.js integration - proxy endpoint
    path('wiki-proxy/', wiki_proxy, name='wiki_proxy'),
    path('wiki-proxy/<path:path>', wiki_proxy, name='wiki_proxy_path'),
    
    # Wiki.js monitoring endpoints
    path('wiki-health/', wiki_health_check, name='wiki_health_check'),
    path('wiki-stats/', wiki_stats, name='wiki_stats'),

]
