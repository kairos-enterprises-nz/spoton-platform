"""
Test command to verify staff API endpoints work correctly
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient
# JWT tokens removed - using Keycloak authentication
from users.models import Tenant

User = get_user_model()

class Command(BaseCommand):
    help = 'Test staff API endpoints for CRUD operations'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, help='Tenant ID to test with')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Staff API endpoints...'))
        
        # Get or create a staff user
        staff_user = self.get_or_create_staff_user()
        
        # Create API client with authentication
        client = APIClient()
        refresh = RefreshToken.for_user(staff_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Test tenant filtering
        tenant_id = options.get('tenant')
        if tenant_id:
            self.test_with_tenant_filter(client, tenant_id)
        else:
            self.test_without_tenant_filter(client)
        
        self.stdout.write(self.style.SUCCESS('Staff API testing completed!'))

    def get_or_create_staff_user(self):
        """Get or create a staff user for testing"""
        try:
            # Try to get an existing staff user
            staff_user = User.objects.filter(is_staff=True, is_active=True).first()
            if staff_user:
                self.stdout.write(f'Using existing staff user: {staff_user.email}')
                return staff_user
            
            # Create a new staff user
            staff_user = User.objects.create_user(
                email='test-staff@example.com',
                password='testpass123',
                first_name='Test',
                last_name='Staff',
                is_staff=True,
                is_active=True
            )
            self.stdout.write(f'Created new staff user: {staff_user.email}')
            return staff_user
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create staff user: {e}'))
            raise

    def test_with_tenant_filter(self, client, tenant_id):
        """Test API endpoints with tenant filtering"""
        self.stdout.write(f'Testing with tenant filter: {tenant_id}')
        
        endpoints = [
            (f'/api/staff/accounts/?tenant={tenant_id}', 'Accounts (filtered)'),
            (f'/api/staff/users/?tenant={tenant_id}', 'Users (filtered)'),
            (f'/api/staff/contracts/?tenant={tenant_id}', 'Contracts (filtered)'),
            (f'/api/staff/connections/?tenant={tenant_id}', 'Connections (filtered)'),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = client.get(endpoint)
                if hasattr(response, 'data'):
                    results_count = len(response.data.get("results", []))
                    self.stdout.write(f'{name}: {response.status_code} - {results_count} results')
                else:
                    self.stdout.write(f'{name}: {response.status_code} - No data attribute')
                    if hasattr(response, 'content'):
                        content = response.content.decode('utf-8')[:200]
                        self.stdout.write(f'  Content: {content}...')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'{name}: Error - {e}'))

    def test_without_tenant_filter(self, client):
        """Test API endpoints without tenant filtering"""
        self.stdout.write('Testing without tenant filter')
        
        endpoints = [
            ('/api/staff/tenants/', 'Tenants'),
            ('/api/staff/accounts/', 'Accounts'),
            ('/api/staff/users/', 'Users'),
            ('/api/staff/contracts/', 'Contracts'),
            ('/api/staff/connections/', 'Connections'),
            ('/api/staff/plans/', 'Plans'),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = client.get(endpoint)
                if hasattr(response, 'data'):
                    results_count = len(response.data.get("results", []))
                    self.stdout.write(f'{name}: {response.status_code} - {results_count} results')
                else:
                    self.stdout.write(f'{name}: {response.status_code} - No data attribute')
                    if hasattr(response, 'content'):
                        content = response.content.decode('utf-8')[:200]
                        self.stdout.write(f'  Content: {content}...')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'{name}: Error - {e}'))

    def test_account_crud(self, client, tenant_id):
        """Test account CRUD operations"""
        self.stdout.write('Testing Account CRUD operations...')
        
        # Create account
        account_data = {
            'account_number': 'TEST001',
            'account_type': 'residential',
            'tenant': tenant_id,
            'status': 'active'
        }
        response = client.post('/api/staff/accounts/', account_data)
        self.stdout.write(f'Create Account: {response.status_code}')
        
        if response.status_code == 201:
            account_id = response.data['id']
            
            # Read account
            response = client.get(f'/api/staff/accounts/{account_id}/')
            self.stdout.write(f'Read Account: {response.status_code}')
            
            # Update account
            update_data = {'status': 'inactive'}
            response = client.patch(f'/api/staff/accounts/{account_id}/', update_data)
            self.stdout.write(f'Update Account: {response.status_code}')
            
            # Delete account
            response = client.delete(f'/api/staff/accounts/{account_id}/')
            self.stdout.write(f'Delete Account: {response.status_code}')
        else:
            self.stdout.write(self.style.ERROR(f'Failed to create account: {response.data}')) 