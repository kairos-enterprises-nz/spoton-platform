"""
Comprehensive Staff API Endpoints Audit
Tests all endpoints, relationships, and data integrity across the staff portal
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django_tenants.utils import schema_context, get_tenant_model
from users.models import Tenant, Account, UserAccountRole
from users.staff_views import (
    TenantViewSet, StaffUserViewSet, AccountViewSet, 
    ServiceContractViewSet, ConnectionViewSet, PlanViewSet,
    get_selected_tenant_from_request, should_filter_by_tenant
)
from rest_framework.request import Request

User = get_user_model()

class Command(BaseCommand):
    help = 'Comprehensive audit of all staff API endpoints'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== STAFF API ENDPOINTS AUDIT ==='))
        
        # Create mock request factory
        factory = RequestFactory()
        
        # Get a super admin user for testing
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found for testing'))
            return
        
        # Test each endpoint category
        self.test_tenant_endpoints(factory, admin_user)
        self.test_user_endpoints(factory, admin_user)
        self.test_account_endpoints(factory, admin_user)
        self.test_contract_endpoints(factory, admin_user)
        self.test_connection_endpoints(factory, admin_user)
        self.test_plan_endpoints(factory, admin_user)
        
        # Test specific relationships
        self.test_user_relationships(factory, admin_user)
        self.test_account_relationships(factory, admin_user)
        
        self.stdout.write(self.style.SUCCESS('\n=== AUDIT COMPLETED ==='))

    def test_tenant_endpoints(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING TENANT ENDPOINTS ---'))
        
        try:
            # Test tenant list
            django_request = factory.get('/api/staff/tenants/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user  # DRF Request doesn't auto-copy user
            viewset = TenantViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            
            queryset = viewset.get_queryset()
            self.stdout.write(f'✓ Tenants list: {queryset.count()} items')
            
            # Test tenant detail
            if queryset.exists():
                tenant = queryset.first()
                django_request = factory.get(f'/api/staff/tenants/{tenant.id}/')
                django_request.user = admin_user
                request = Request(django_request)
                request.user = admin_user  # DRF Request doesn't auto-copy user
                viewset = TenantViewSet()
                viewset.request = request
                viewset.format_kwarg = None
                viewset.kwargs = {'pk': str(tenant.id)}
                viewset.action = 'retrieve'
                
                try:
                    response = viewset.retrieve(request, pk=str(tenant.id))
                    self.stdout.write(f'✓ Tenant detail: {response.status_code}')
                except Exception as e:
                    self.stdout.write(f'✗ Tenant detail error: {e}')
                    
                # Test tenant users
                try:
                    response = viewset.users(request, pk=str(tenant.id))
                    self.stdout.write(f'✓ Tenant users: {response.status_code}')
                except Exception as e:
                    self.stdout.write(f'✗ Tenant users error: {e}')
                    
        except Exception as e:
            self.stdout.write(f'✗ Tenant endpoints error: {e}')

    def test_user_endpoints(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING USER ENDPOINTS ---'))
        
        try:
            # Test user list
            django_request = factory.get('/api/staff/users/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user  # DRF Request doesn't auto-copy user
            viewset = StaffUserViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            
            queryset = viewset.get_queryset()
            self.stdout.write(f'✓ Users list: {queryset.count()} items')
            
            # Test user detail
            if queryset.exists():
                user = queryset.first()
                self.stdout.write(f'  Testing user: {user.email}')
                
                # Test user detail view
                django_request = factory.get(f'/api/staff/users/{user.id}/')
                django_request.user = admin_user
                request = Request(django_request)
                request.user = admin_user  # DRF Request doesn't auto-copy user
                viewset = StaffUserViewSet()
                viewset.request = request
                viewset.format_kwarg = None
                viewset.kwargs = {'pk': str(user.id)}
                viewset.action = 'retrieve'
                
                try:
                    response = viewset.retrieve(request, pk=str(user.id))
                    self.stdout.write(f'✓ User detail: {response.status_code}')
                    
                    # Check if user_number is in response
                    if hasattr(response, 'data') and 'user_number' in response.data:
                        self.stdout.write(f'✓ User number present: {response.data["user_number"]}')
                    else:
                        self.stdout.write('✗ User number missing from response')
                        
                except Exception as e:
                    self.stdout.write(f'✗ User detail error: {e}')
                    
        except Exception as e:
            self.stdout.write(f'✗ User endpoints error: {e}')

    def test_account_endpoints(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING ACCOUNT ENDPOINTS ---'))
        
        try:
            # Test account list
            django_request = factory.get('/api/staff/accounts/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user  # DRF Request doesn't auto-copy user
            viewset = AccountViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            
            queryset = viewset.get_queryset()
            self.stdout.write(f'✓ Accounts list: {queryset.count()} items')
            
            # Test account detail
            if queryset.exists():
                account = queryset.first()
                self.stdout.write(f'  Testing account: {account.account_number}')
                
                django_request = factory.get(f'/api/staff/accounts/{account.id}/')
                django_request.user = admin_user
                request = Request(django_request)
                request.user = admin_user  # DRF Request doesn't auto-copy user
                viewset = AccountViewSet()
                viewset.request = request
                viewset.format_kwarg = None
                viewset.kwargs = {'pk': str(account.id)}
                viewset.action = 'retrieve'
                
                try:
                    response = viewset.retrieve(request, pk=str(account.id))
                    self.stdout.write(f'✓ Account detail: {response.status_code}')
                except Exception as e:
                    self.stdout.write(f'✗ Account detail error: {e}')
                    
        except Exception as e:
            self.stdout.write(f'✗ Account endpoints error: {e}')

    def test_contract_endpoints(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING CONTRACT ENDPOINTS ---'))
        
        try:
            # Test contract list
            django_request = factory.get('/api/staff/contracts/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user  # DRF Request doesn't auto-copy user
            viewset = ServiceContractViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            
            queryset = viewset.get_queryset()
            self.stdout.write(f'✓ Contracts list: {len(queryset)} items')
            
            # Test contract detail if any exist
            if queryset and len(queryset) > 0:
                contract = queryset[0]
                self.stdout.write(f'  Testing contract: {contract.contract_number}')
                
                django_request = factory.get(f'/api/staff/contracts/{contract.id}/')
                django_request.user = admin_user
                request = Request(django_request)
                request.user = admin_user  # DRF Request doesn't auto-copy user
                viewset = ServiceContractViewSet()
                viewset.request = request
                viewset.format_kwarg = None
                viewset.kwargs = {'pk': str(contract.id)}
                viewset.action = 'retrieve'
                
                try:
                    response = viewset.retrieve(request, pk=str(contract.id))
                    self.stdout.write(f'✓ Contract detail: {response.status_code}')
                except Exception as e:
                    self.stdout.write(f'✗ Contract detail error: {e}')
            else:
                self.stdout.write('ℹ No contracts found for detail testing')
                    
        except Exception as e:
            self.stdout.write(f'✗ Contract endpoints error: {e}')

    def test_connection_endpoints(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING CONNECTION ENDPOINTS ---'))
        
        try:
            # Test connection list
            request = factory.get('/api/staff/connections/')
            request.user = admin_user
            request.query_params = {}
            viewset = ConnectionViewSet()
            viewset.request = request
            
            queryset = viewset.get_queryset()
            self.stdout.write(f'✓ Connections list: {len(queryset)} items')
            
            # Check if connections are real models or sample data
            if queryset and len(queryset) > 0:
                connection = queryset[0]
                if hasattr(connection, 'id') and hasattr(connection, 'save'):
                    self.stdout.write('✓ Connections are real database models')
                else:
                    self.stdout.write('⚠ Connections are sample data (not real models)')
                    
        except Exception as e:
            self.stdout.write(f'✗ Connection endpoints error: {e}')

    def test_plan_endpoints(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING PLAN ENDPOINTS ---'))
        
        try:
            # Test plan list
            request = factory.get('/api/staff/plans/')
            request.user = admin_user
            request.query_params = {}
            viewset = PlanViewSet()
            viewset.request = request
            
            queryset = viewset.get_queryset()
            self.stdout.write(f'✓ Plans list: {len(queryset)} items')
            
        except Exception as e:
            self.stdout.write(f'✗ Plan endpoints error: {e}')

    def test_user_relationships(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING USER RELATIONSHIPS ---'))
        
        try:
            # Get a user with relationships
            user = User.objects.filter(tenant__isnull=False).first()
            if not user:
                self.stdout.write('ℹ No users with tenants found')
                return
                
            self.stdout.write(f'Testing relationships for user: {user.email}')
            
            # Test user accounts
            request = factory.get(f'/api/staff/users/{user.id}/accounts/')
            request.user = admin_user
            request.query_params = {}
            viewset = StaffUserViewSet()
            viewset.request = request
            viewset.kwargs = {'pk': str(user.id)}
            
            try:
                response = viewset.accounts(request, pk=str(user.id))
                self.stdout.write(f'✓ User accounts: {response.status_code}')
                if hasattr(response, 'data'):
                    self.stdout.write(f'  Accounts found: {len(response.data)}')
            except Exception as e:
                self.stdout.write(f'✗ User accounts error: {e}')
                
            # Test user contracts
            try:
                response = viewset.contracts(request, pk=str(user.id))
                self.stdout.write(f'✓ User contracts: {response.status_code}')
                if hasattr(response, 'data'):
                    self.stdout.write(f'  Contracts found: {len(response.data)}')
            except Exception as e:
                self.stdout.write(f'✗ User contracts error: {e}')
                
        except Exception as e:
            self.stdout.write(f'✗ User relationships error: {e}')

    def test_account_relationships(self, factory, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING ACCOUNT RELATIONSHIPS ---'))
        
        try:
            # Get an account with relationships
            account = Account.objects.first()
            if not account:
                self.stdout.write('ℹ No accounts found')
                return
                
            self.stdout.write(f'Testing relationships for account: {account.account_number}')
            
            # Test account users
            request = factory.get(f'/api/staff/accounts/{account.id}/users/')
            request.user = admin_user
            request.query_params = {}
            viewset = AccountViewSet()
            viewset.request = request
            viewset.kwargs = {'pk': str(account.id)}
            
            try:
                response = viewset.users(request, pk=str(account.id))
                self.stdout.write(f'✓ Account users: {response.status_code}')
                if hasattr(response, 'data'):
                    self.stdout.write(f'  Users found: {len(response.data)}')
            except Exception as e:
                self.stdout.write(f'✗ Account users error: {e}')
                
            # Test account contracts
            try:
                response = viewset.contracts(request, pk=str(account.id))
                self.stdout.write(f'✓ Account contracts: {response.status_code}')
                if hasattr(response, 'data'):
                    self.stdout.write(f'  Contracts found: {len(response.data)}')
            except Exception as e:
                self.stdout.write(f'✗ Account contracts error: {e}')
                
            # Test account addresses
            try:
                response = viewset.addresses(request, pk=str(account.id))
                self.stdout.write(f'✓ Account addresses: {response.status_code}')
                if hasattr(response, 'data'):
                    self.stdout.write(f'  Addresses found: {len(response.data)}')
            except Exception as e:
                self.stdout.write(f'✗ Account addresses error: {e}')
                
        except Exception as e:
            self.stdout.write(f'✗ Account relationships error: {e}') 