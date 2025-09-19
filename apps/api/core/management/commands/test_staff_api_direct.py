"""
Test Staff API Direct Calls
Simulates the staff API calls to verify the backend logic works correctly
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from users.staff_views import StaffUserViewSet, AccountViewSet, ServiceContractViewSet
from users.models import Tenant

User = get_user_model()

class Command(BaseCommand):
    help = 'Test staff API calls directly'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== TESTING STAFF API DIRECT CALLS ==='))
        
        # Create a mock request
        factory = RequestFactory()
        
        # Test contracts endpoint
        self.test_contracts_endpoint(factory)
        
        # Test user contracts
        self.test_user_contracts(factory)
        
        # Test account contracts
        self.test_account_contracts(factory)
        
        self.stdout.write(self.style.SUCCESS('\n=== ALL TESTS COMPLETED ==='))

    def test_contracts_endpoint(self, factory):
        self.stdout.write(self.style.WARNING('\n--- TESTING CONTRACTS ENDPOINT ---'))
        
        # Create a mock request with no tenant selection (super admin)
        request = factory.get('/api/staff/contracts/')
        request.user = User.objects.filter(is_superuser=True).first()
        
        # Create the viewset and test
        viewset = ServiceContractViewSet()
        viewset.request = request
        
        try:
            queryset = viewset.get_queryset()
            self.stdout.write(f'Contracts found: {len(queryset)}')
            
            # Test with specific tenant
            tenant = Tenant.objects.first()
            request.GET = {'tenant': str(tenant.id)}
            viewset.request = request
            
            queryset_filtered = viewset.get_queryset()
            self.stdout.write(f'Contracts for tenant {tenant.name}: {len(queryset_filtered)}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def test_user_contracts(self, factory):
        self.stdout.write(self.style.WARNING('\n--- TESTING USER CONTRACTS ---'))
        
        # Get a user with contracts
        user = User.objects.filter(tenant__isnull=False).first()
        if not user:
            self.stdout.write('No users with tenants found')
            return
            
        self.stdout.write(f'Testing user: {user.email} (Tenant: {user.tenant.name})')
        
        # Create mock request
        request = factory.get(f'/api/staff/users/{user.id}/contracts/')
        request.user = User.objects.filter(is_superuser=True).first()
        request.GET = {}
        
        # Create viewset and test
        viewset = StaffUserViewSet()
        viewset.request = request
        viewset.kwargs = {'pk': str(user.id)}
        
        try:
            response = viewset.contracts(request, pk=str(user.id))
            self.stdout.write(f'User contracts response: {response.status_code}')
            if hasattr(response, 'data'):
                self.stdout.write(f'Contracts count: {len(response.data)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def test_account_contracts(self, factory):
        self.stdout.write(self.style.WARNING('\n--- TESTING ACCOUNT CONTRACTS ---'))
        
        from users.models import Account
        
        # Get an account with contracts
        account = Account.objects.filter(tenant__isnull=False).first()
        if not account:
            self.stdout.write('No accounts found')
            return
            
        self.stdout.write(f'Testing account: {account.account_number} (Tenant: {account.tenant.name})')
        
        # Create mock request
        request = factory.get(f'/api/staff/accounts/{account.id}/contracts/')
        request.user = User.objects.filter(is_superuser=True).first()
        request.GET = {}
        
        # Create viewset and test
        viewset = AccountViewSet()
        viewset.request = request
        viewset.kwargs = {'pk': str(account.id)}
        
        try:
            response = viewset.contracts(request, pk=str(account.id))
            self.stdout.write(f'Account contracts response: {response.status_code}')
            if hasattr(response, 'data'):
                self.stdout.write(f'Contracts count: {len(response.data)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}')) 