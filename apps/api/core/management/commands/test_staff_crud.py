"""
Test Staff CRUD Operations
Tests Create, Read, Update, Delete operations for all staff models
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.request import Request
from users.models import Tenant, Account, UserAccountRole
from users.staff_views import (
    TenantViewSet, StaffUserViewSet, AccountViewSet, 
    ServiceContractViewSet, ConnectionViewSet, PlanViewSet
)
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Test CRUD operations for all staff models'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== TESTING STAFF CRUD OPERATIONS ==='))
        
        # Get a super admin user for testing
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found for testing'))
            return
        
        # Test each model's CRUD operations
        self.test_tenant_crud(admin_user)
        self.test_user_crud(admin_user)
        self.test_account_crud(admin_user)
        self.test_contract_crud(admin_user)
        
        self.stdout.write(self.style.SUCCESS('\n=== CRUD TESTING COMPLETED ==='))

    def test_tenant_crud(self, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING TENANT CRUD ---'))
        
        try:
            factory = RequestFactory()
            
            # Test CREATE
            create_data = {
                'name': 'Test Energy Corp',
                'slug': 'test-energy-corp',
                'business_number': 'TEST123456',
                'contact_email': 'admin@test-energy.com',
                'contact_phone': '+64-9-123-4567',
                'timezone': 'Pacific/Auckland',
                'currency': 'NZD',
                'is_active': True
            }
            
            django_request = factory.post('/api/staff/tenants/', data=create_data)
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = TenantViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.action = 'create'
            
            try:
                response = viewset.create(request)
                self.stdout.write(f'✓ Tenant CREATE: {response.status_code}')
                if response.status_code == 201:
                    tenant_id = response.data['id']
                    self.stdout.write(f'  Created tenant ID: {tenant_id}')
                else:
                    self.stdout.write(f'  Error: {response.data}')
                    return
            except Exception as e:
                self.stdout.write(f'✗ Tenant CREATE error: {e}')
                return
            
            # Test READ
            django_request = factory.get(f'/api/staff/tenants/{tenant_id}/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = TenantViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': tenant_id}
            viewset.action = 'retrieve'
            
            try:
                response = viewset.retrieve(request, pk=tenant_id)
                self.stdout.write(f'✓ Tenant READ: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ Tenant READ error: {e}')
            
            # Test UPDATE
            update_data = {
                'name': 'Test Energy Corp Updated',
                'contact_phone': '+64-9-123-9999'
            }
            
            django_request = factory.patch(f'/api/staff/tenants/{tenant_id}/', data=update_data)
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = TenantViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': tenant_id}
            viewset.action = 'partial_update'
            
            try:
                response = viewset.partial_update(request, pk=tenant_id)
                self.stdout.write(f'✓ Tenant UPDATE: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ Tenant UPDATE error: {e}')
            
            # Test DELETE
            django_request = factory.delete(f'/api/staff/tenants/{tenant_id}/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = TenantViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': tenant_id}
            viewset.action = 'destroy'
            
            try:
                response = viewset.destroy(request, pk=tenant_id)
                self.stdout.write(f'✓ Tenant DELETE: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ Tenant DELETE error: {e}')
                
        except Exception as e:
            self.stdout.write(f'✗ Tenant CRUD test error: {e}')

    def test_user_crud(self, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING USER CRUD ---'))
        
        try:
            factory = RequestFactory()
            
            # Get a tenant for the user
            tenant = Tenant.objects.first()
            if not tenant:
                self.stdout.write('ℹ No tenant found for user testing')
                return
            
            # Test CREATE
            create_data = {
                'email': 'test.user@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'testpass123',
                'user_type': 'customer',
                'tenant_id': str(tenant.id),
                'is_active': True
            }
            
            django_request = factory.post('/api/staff/users/', data=create_data)
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = StaffUserViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.action = 'create'
            
            try:
                response = viewset.create(request)
                self.stdout.write(f'✓ User CREATE: {response.status_code}')
                if response.status_code == 201:
                    user_id = response.data['id']
                    self.stdout.write(f'  Created user ID: {user_id}')
                else:
                    self.stdout.write(f'  Error: {response.data}')
                    return
            except Exception as e:
                self.stdout.write(f'✗ User CREATE error: {e}')
                return
            
            # Test READ
            django_request = factory.get(f'/api/staff/users/{user_id}/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = StaffUserViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': user_id}
            viewset.action = 'retrieve'
            
            try:
                response = viewset.retrieve(request, pk=user_id)
                self.stdout.write(f'✓ User READ: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ User READ error: {e}')
            
            # Test UPDATE
            update_data = {
                'first_name': 'Updated Test',
                'department': 'Testing Department'
            }
            
            django_request = factory.patch(f'/api/staff/users/{user_id}/', data=update_data)
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = StaffUserViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': user_id}
            viewset.action = 'partial_update'
            
            try:
                response = viewset.partial_update(request, pk=user_id)
                self.stdout.write(f'✓ User UPDATE: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ User UPDATE error: {e}')
            
            # Test DELETE
            django_request = factory.delete(f'/api/staff/users/{user_id}/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = StaffUserViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': user_id}
            viewset.action = 'destroy'
            
            try:
                response = viewset.destroy(request, pk=user_id)
                self.stdout.write(f'✓ User DELETE: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ User DELETE error: {e}')
                
        except Exception as e:
            self.stdout.write(f'✗ User CRUD test error: {e}')

    def test_account_crud(self, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING ACCOUNT CRUD ---'))
        
        try:
            factory = RequestFactory()
            
            # Get a tenant and user for the account
            tenant = Tenant.objects.first()
            user = User.objects.filter(tenant=tenant, user_type='customer').first()
            if not tenant or not user:
                self.stdout.write('ℹ No tenant or user found for account testing')
                return
            
            # Test CREATE
            create_data = {
                'account_type': 'residential',
                'tenant_id': str(tenant.id),
                'primary_user_email': user.email,
                'billing_cycle': 'monthly',
                'billing_day': 1,
                'status': 'active'
            }
            
            django_request = factory.post('/api/staff/accounts/', data=create_data)
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = AccountViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.action = 'create'
            
            try:
                response = viewset.create(request)
                self.stdout.write(f'✓ Account CREATE: {response.status_code}')
                if response.status_code == 201:
                    account_id = response.data['id']
                    self.stdout.write(f'  Created account ID: {account_id}')
                else:
                    self.stdout.write(f'  Error: {response.data}')
                    return
            except Exception as e:
                self.stdout.write(f'✗ Account CREATE error: {e}')
                return
            
            # Test READ
            django_request = factory.get(f'/api/staff/accounts/{account_id}/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = AccountViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': account_id}
            viewset.action = 'retrieve'
            
            try:
                response = viewset.retrieve(request, pk=account_id)
                self.stdout.write(f'✓ Account READ: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ Account READ error: {e}')
            
            # Test UPDATE
            update_data = {
                'billing_day': 15,
                'status': 'suspended'
            }
            
            django_request = factory.patch(f'/api/staff/accounts/{account_id}/', data=update_data)
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = AccountViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': account_id}
            viewset.action = 'partial_update'
            
            try:
                response = viewset.partial_update(request, pk=account_id)
                self.stdout.write(f'✓ Account UPDATE: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ Account UPDATE error: {e}')
            
            # Test DELETE
            django_request = factory.delete(f'/api/staff/accounts/{account_id}/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = AccountViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = {'pk': account_id}
            viewset.action = 'destroy'
            
            try:
                response = viewset.destroy(request, pk=account_id)
                self.stdout.write(f'✓ Account DELETE: {response.status_code}')
            except Exception as e:
                self.stdout.write(f'✗ Account DELETE error: {e}')
                
        except Exception as e:
            self.stdout.write(f'✗ Account CRUD test error: {e}')

    def test_contract_crud(self, admin_user):
        self.stdout.write(self.style.WARNING('\n--- TESTING CONTRACT CRUD ---'))
        
        # Note: Contracts are complex due to tenant schemas
        # For now, just test if the endpoints respond properly
        try:
            factory = RequestFactory()
            
            # Test if we can access the contract list
            django_request = factory.get('/api/staff/contracts/')
            django_request.user = admin_user
            request = Request(django_request)
            request.user = admin_user
            
            viewset = ServiceContractViewSet()
            viewset.request = request
            viewset.format_kwarg = None
            
            queryset = viewset.get_queryset()
            self.stdout.write(f'✓ Contract LIST access: {len(queryset)} contracts found')
            
            if queryset and len(queryset) > 0:
                contract = queryset[0]
                
                # Test READ
                django_request = factory.get(f'/api/staff/contracts/{contract.id}/')
                django_request.user = admin_user
                request = Request(django_request)
                request.user = admin_user
                
                viewset = ServiceContractViewSet()
                viewset.request = request
                viewset.format_kwarg = None
                viewset.kwargs = {'pk': str(contract.id)}
                viewset.action = 'retrieve'
                
                try:
                    response = viewset.retrieve(request, pk=str(contract.id))
                    self.stdout.write(f'✓ Contract READ: {response.status_code}')
                except Exception as e:
                    self.stdout.write(f'✗ Contract READ error: {e}')
            else:
                self.stdout.write('ℹ No contracts found for testing')
                
        except Exception as e:
            self.stdout.write(f'✗ Contract CRUD test error: {e}') 