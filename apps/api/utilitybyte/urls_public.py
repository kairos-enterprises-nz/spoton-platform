"""
Public schema URLs for django-tenants.
These URLs are accessible from the public schema and handle tenant management.
"""
from django.contrib import admin
from django.urls import path, include
# All token-related views removed - Keycloak handles all authentication
# from users.main_views import CustomTokenObtainPairView

urlpatterns = [
    # Add public API endpoints here (tenant management, etc.)
    path('api/public/', include('users.urls_public')),
    
    # Core user management - needed for frontend login/registration
    path('api/users/', include('users.urls')),
    
    # Include staff endpoints in public schema
    path('api/staff/', include('users.staff_urls')),
    
    # Validation endpoints (for staff portal)
    path('api/staff/validation/', include('energy.validation.urls')),
    
    # Authentication endpoints handled by Keycloak - no longer needed
    # path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 