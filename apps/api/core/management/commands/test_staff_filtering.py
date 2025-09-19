"""
Test Staff Filtering Logic
Debug why main views return 0 items but relationships work fine
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Tenant, Account
from users.staff_views import get_selected_tenant_from_request, get_user_tenant, should_filter_by_tenant
from django.test import RequestFactory
from rest_framework.request import Request

User = get_user_model()

class Command(BaseCommand):
    help = 'Test staff filtering logic'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== TESTING STAFF FILTERING LOGIC ==='))
        
        # Get a super admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found'))
            return
            
        self.stdout.write(f'Testing with admin user: {admin_user.email}')
        self.stdout.write(f'Admin is_superuser: {admin_user.is_superuser}')
        self.stdout.write(f'Admin tenant: {admin_user.tenant}')
        
        # Test filtering functions
        factory = RequestFactory()
        django_request = factory.get('/api/staff/users/')
        django_request.user = admin_user
        request = Request(django_request)
        
        # Test helper functions
        selected_tenant = get_selected_tenant_from_request(request)
        user_tenant = get_user_tenant(admin_user)
        should_filter = should_filter_by_tenant(admin_user)
        
        self.stdout.write(f'Selected tenant from request: {selected_tenant}')
        self.stdout.write(f'User tenant: {user_tenant}')
        self.stdout.write(f'Should filter by tenant: {should_filter}')
        
        # Test actual data counts
        total_users = User.objects.count()
        total_accounts = Account.objects.count()
        total_tenants = Tenant.objects.count()
        
        self.stdout.write(f'\nDatabase counts:')
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Total accounts: {total_accounts}')
        self.stdout.write(f'Total tenants: {total_tenants}')
        
        # Test user filtering logic
        self.stdout.write(f'\nUser filtering logic:')
        base_query = User.objects.select_related('tenant').prefetch_related('account_roles__account')
        
        if selected_tenant:
            filtered_users = base_query.filter(tenant=selected_tenant)
            self.stdout.write(f'Users filtered by selected tenant: {filtered_users.count()}')
        elif should_filter:
            if user_tenant:
                filtered_users = base_query.filter(tenant=user_tenant)
                self.stdout.write(f'Users filtered by user tenant: {filtered_users.count()}')
            else:
                filtered_users = base_query.none()
                self.stdout.write(f'No tenant assigned - empty queryset: {filtered_users.count()}')
        else:
            filtered_users = base_query.all()
            self.stdout.write(f'Super admin - all users: {filtered_users.count()}')
        
        # Test account filtering logic
        self.stdout.write(f'\nAccount filtering logic:')
        base_query = Account.objects.select_related('tenant')
        
        if selected_tenant:
            filtered_accounts = base_query.filter(tenant=selected_tenant)
            self.stdout.write(f'Accounts filtered by selected tenant: {filtered_accounts.count()}')
        elif should_filter:
            if user_tenant:
                filtered_accounts = base_query.filter(tenant=user_tenant)
                self.stdout.write(f'Accounts filtered by user tenant: {filtered_accounts.count()}')
            else:
                filtered_accounts = base_query.none()
                self.stdout.write(f'No tenant assigned - empty queryset: {filtered_accounts.count()}')
        else:
            filtered_accounts = base_query.all()
            self.stdout.write(f'Super admin - all accounts: {filtered_accounts.count()}')
        
        # Show some sample data
        self.stdout.write(f'\nSample users:')
        for user in User.objects.all()[:5]:
            self.stdout.write(f'  {user.email} - tenant: {user.tenant}')
            
        self.stdout.write(f'\nSample accounts:')
        for account in Account.objects.all()[:5]:
            self.stdout.write(f'  {account.account_number} - tenant: {account.tenant}') 