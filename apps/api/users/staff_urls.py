"""
Staff URL Configuration with API Versioning
Provides versioned API endpoints for staff operations
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .staff_views import (
    TenantViewSet, StaffUserViewSet, AccountViewSet,
    ServiceContractViewSet, ConnectionViewSet, PlanViewSet,
    CustomerDataViewSet, test_endpoint, test_plans
)
from .views import ProfileView

app_name = 'users'

# A single router for all staff API endpoints
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'users', StaffUserViewSet, basename='user')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'contracts', ServiceContractViewSet, basename='contract')
router.register(r'connections', ConnectionViewSet, basename='connection')
router.register(r'plans', PlanViewSet, basename='plan')

router.register(r'customers', CustomerDataViewSet, basename='customer')

# Application-level URL patterns
urlpatterns = [

    # Profile endpoint for authenticated staff
    path('profile/', ProfileView.as_view(), name='staff-profile'),
    
    # Version 1 of the API
    path('v1/', include(router.urls)),
    
    # Legacy endpoints (no version prefix) for backward compatibility
    path('', include(router.urls)),
    
    # Validation endpoints (for frontend compatibility)
    path('validation/', include('energy.validation.urls')),
    
    # Test endpoints
    path('test/', test_endpoint, name='staff-test'),
    path('test/plans/', test_plans, name='staff-test-plans'),
]

"""
Staff API Endpoints Documentation:

TENANTS:
- GET    /api/staff/tenants/                    - List all tenants
- POST   /api/staff/tenants/                    - Create new tenant
- GET    /api/staff/tenants/{id}/               - Get tenant details
- PUT    /api/staff/tenants/{id}/               - Update tenant
- PATCH  /api/staff/tenants/{id}/               - Partial update tenant
- DELETE /api/staff/tenants/{id}/               - Delete tenant
- GET    /api/staff/tenants/{id}/users/         - Get tenant users
- GET    /api/staff/tenants/{id}/stats/         - Get tenant statistics
- POST   /api/staff/tenants/{id}/add_user_role/ - Add user role to tenant

USERS:
- GET    /api/staff/users/                      - List all users
- POST   /api/staff/users/                      - Create new user
- GET    /api/staff/users/{id}/                 - Get user details
- PUT    /api/staff/users/{id}/                 - Update user
- PATCH  /api/staff/users/{id}/                 - Partial update user
- DELETE /api/staff/users/{id}/                 - Delete user
- GET    /api/staff/users/{id}/accounts/        - Get user accounts
- GET    /api/staff/users/{id}/contracts/       - Get user contracts
- POST   /api/staff/users/{id}/reset_password/  - Reset user password
- POST   /api/staff/users/{id}/toggle_active/   - Toggle user active status

ACCOUNTS:
- GET    /api/staff/accounts/                   - List all accounts
- POST   /api/staff/accounts/                   - Create new account
- GET    /api/staff/accounts/{id}/              - Get account details
- PUT    /api/staff/accounts/{id}/              - Update account
- PATCH  /api/staff/accounts/{id}/              - Partial update account
- DELETE /api/staff/accounts/{id}/              - Delete account
- GET    /api/staff/accounts/{id}/users/        - Get account users
- GET    /api/staff/accounts/{id}/addresses/    - Get account addresses
- POST   /api/staff/accounts/{id}/add_address/  - Add address to account
- GET    /api/staff/accounts/{id}/contracts/    - Get account contracts

CONTRACTS:
- GET    /api/staff/contracts/                  - List all contracts
- POST   /api/staff/contracts/                  - Create new contract
- GET    /api/staff/contracts/{id}/             - Get contract details
- PUT    /api/staff/contracts/{id}/             - Update contract
- PATCH  /api/staff/contracts/{id}/             - Partial update contract
- DELETE /api/staff/contracts/{id}/             - Delete contract
- GET    /api/staff/contracts/electricity/      - List electricity contracts
- GET    /api/staff/contracts/broadband/        - List broadband contracts
- GET    /api/staff/contracts/mobile/           - List mobile contracts
- POST   /api/staff/contracts/{id}/change_status/ - Change contract status

CUSTOMERS:
- GET    /api/staff/customers/                  - List all customers
- GET    /api/staff/customers/{id}/             - Get customer details
- GET    /api/staff/customers/stats/            - Get customer statistics
- GET    /api/staff/customers/{id}/overview/    - Get customer overview

FILTERING AND SEARCH:
All list endpoints support:
- ?search=<term>          - Search across relevant fields
- ?ordering=<field>       - Order by field (prefix with - for desc)
- ?page=<num>            - Pagination
- ?page_size=<num>       - Items per page (max 100)
- Various filter parameters specific to each model

AUTHENTICATION:
All endpoints require staff authentication via JWT token:
Authorization: Bearer <token>

PERMISSIONS:
- All endpoints require IsStaffUser permission
- Some operations may require additional tenant-specific permissions
- Superusers have access to all operations across all tenants
""" 