"""
Comprehensive End-to-End Tests for Tenant CRUD Operations
Tests all aspects of tenant management including permissions, API endpoints, and data integrity.
"""

import json
import uuid
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
# JWT tokens removed - using Keycloak authentication
from django.db import transaction
from django.core.exceptions import ValidationError

from users.models import Tenant, TenantUserRole
from users.staff_serializers import TenantListSerializer, TenantDetailSerializer, TenantCreateSerializer

User = get_user_model()


class TenantCRUDPermissionTests(APITestCase):
    """Test permission controls for tenant management"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create Admin group
        self.admin_group = Group.objects.create(name='Admin')
        
        # Create test users with different permission levels
        self.superuser = User.objects.create_user(
            email='superuser@test.com',
            password='testpass123',
            first_name='Super',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            first_name='Regular',
            last_name='User'
        )
        
        # Create test tenant
        self.test_tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            contact_email='contact@test-tenant.com',
            contact_phone='+64123456789',
            timezone='Pacific/Auckland',
            currency='NZD'
        )
        
        self.tenant_list_url = '/api/staff/tenants/'
        self.tenant_detail_url = f'/api/staff/tenants/{self.test_tenant.pk}/'
    
    def get_auth_header(self, user):
        """Get authorization header for user"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_superuser_can_access_tenant_management(self):
        """Test that superuser can access all tenant operations"""
        # List tenants
        response = self.client.get(self.tenant_list_url, **self.get_auth_header(self.superuser))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get tenant detail
        response = self.client.get(self.tenant_detail_url, **self.get_auth_header(self.superuser))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Create tenant
        create_data = {
            'name': 'New Tenant',
            'slug': 'new-tenant',
            'contact_email': 'contact@new-tenant.com',
            'contact_phone': '+64987654321',
            'timezone': 'Pacific/Auckland',
            'currency': 'NZD'
        }
        response = self.client.post(self.tenant_list_url, create_data, **self.get_auth_header(self.superuser))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Update tenant
        update_data = {'name': 'Updated Tenant Name'}
        response = self.client.patch(self.tenant_detail_url, update_data, **self.get_auth_header(self.superuser))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_user_can_access_tenant_management(self):
        """Test that admin group user can access all tenant operations"""
        # List tenants
        response = self.client.get(self.tenant_list_url, **self.get_auth_header(self.admin_user))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get tenant detail
        response = self.client.get(self.tenant_detail_url, **self.get_auth_header(self.admin_user))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Create tenant
        create_data = {
            'name': 'Admin Created Tenant',
            'slug': 'admin-created-tenant',
            'contact_email': 'contact@admin-tenant.com',
            'contact_phone': '+64555666777',
            'timezone': 'Pacific/Auckland',
            'currency': 'NZD'
        }
        response = self.client.post(self.tenant_list_url, create_data, **self.get_auth_header(self.admin_user))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_staff_user_cannot_access_tenant_management(self):
        """Test that regular staff user cannot access tenant operations"""
        # List tenants - should be forbidden
        response = self.client.get(self.tenant_list_url, **self.get_auth_header(self.staff_user))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Get tenant detail - should be forbidden
        response = self.client.get(self.tenant_detail_url, **self.get_auth_header(self.staff_user))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Create tenant - should be forbidden
        create_data = {
            'name': 'Unauthorized Tenant',
            'slug': 'unauthorized-tenant',
            'contact_email': 'contact@unauthorized.com'
        }
        response = self.client.post(self.tenant_list_url, create_data, **self.get_auth_header(self.staff_user))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_regular_user_cannot_access_tenant_management(self):
        """Test that regular user cannot access tenant operations"""
        # List tenants - should be forbidden
        response = self.client.get(self.tenant_list_url, **self.get_auth_header(self.regular_user))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Get tenant detail - should be forbidden
        response = self.client.get(self.tenant_detail_url, **self.get_auth_header(self.regular_user))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_cannot_access_tenant_management(self):
        """Test that unauthenticated user cannot access tenant operations"""
        # List tenants - should be unauthorized
        response = self.client.get(self.tenant_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Get tenant detail - should be unauthorized
        response = self.client.get(self.tenant_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TenantCRUDOperationsTests(APITestCase):
    """Test all CRUD operations for tenants"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin_group = Group.objects.create(name='Admin')
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )
        self.admin_user.groups.add(self.admin_group)
        
        # Set up authentication
        refresh = RefreshToken.for_user(self.admin_user)
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
        
        self.tenant_list_url = '/api/staff/tenants/'
    
    def test_create_tenant_success(self):
        """Test successful tenant creation"""
        tenant_data = {
            'name': 'Test Company Ltd',
            'slug': 'test-company',
            'contact_email': 'contact@testcompany.com',
            'contact_phone': '+64123456789',
            'business_number': 'BN123456789',
            'address': '123 Test Street, Auckland, New Zealand',
            'timezone': 'Pacific/Auckland',
            'currency': 'NZD',
            'service_limits': {
                'max_users': 100,
                'max_accounts': 500,
                'max_contracts': 1000
            },
            'is_active': True
        }
        
        response = self.client.post(self.tenant_list_url, tenant_data, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify tenant was created in database
        tenant = Tenant.objects.get(slug='test-company')
        self.assertEqual(tenant.name, 'Test Company Ltd')
        self.assertEqual(tenant.contact_email, 'contact@testcompany.com')
        self.assertEqual(tenant.currency, 'NZD')
        self.assertTrue(tenant.is_active)
        
        # Verify response data
        self.assertEqual(response.data['name'], 'Test Company Ltd')
        self.assertEqual(response.data['slug'], 'test-company')
        self.assertIn('id', response.data)
    
    def test_create_tenant_validation_errors(self):
        """Test tenant creation with validation errors"""
        # Missing required fields
        response = self.client.post(self.tenant_list_url, {}, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('slug', response.data)
        
        # Invalid email
        tenant_data = {
            'name': 'Test Company',
            'slug': 'test-company',
            'contact_email': 'invalid-email'
        }
        response = self.client.post(self.tenant_list_url, tenant_data, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('contact_email', response.data)
        
        # Duplicate slug
        Tenant.objects.create(
            name='Existing Tenant',
            slug='duplicate-slug',
            contact_email='existing@test.com'
        )
        
        tenant_data = {
            'name': 'New Tenant',
            'slug': 'duplicate-slug',
            'contact_email': 'new@test.com'
        }
        response = self.client.post(self.tenant_list_url, tenant_data, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('slug', response.data)
    
    def test_list_tenants_with_pagination(self):
        """Test listing tenants with pagination and filtering"""
        # Create multiple tenants
        for i in range(15):
            Tenant.objects.create(
                name=f'Tenant {i}',
                slug=f'tenant-{i}',
                contact_email=f'contact{i}@test.com',
                is_active=i % 2 == 0  # Alternating active/inactive
            )
        
        # Test basic listing
        response = self.client.get(self.tenant_list_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        
        # Test pagination
        response = self.client.get(f'{self.tenant_list_url}?page_size=5', **self.auth_headers)
        self.assertEqual(len(response.data['results']), 5)
        
        # Test filtering by active status
        response = self.client.get(f'{self.tenant_list_url}?is_active=true', **self.auth_headers)
        for tenant in response.data['results']:
            self.assertTrue(tenant['is_active'])
        
        # Test search
        response = self.client.get(f'{self.tenant_list_url}?search=Tenant 1', **self.auth_headers)
        self.assertTrue(any('Tenant 1' in tenant['name'] for tenant in response.data['results']))
    
    def test_retrieve_tenant_detail(self):
        """Test retrieving tenant details"""
        tenant = Tenant.objects.create(
            name='Detail Test Tenant',
            slug='detail-test',
            contact_email='detail@test.com',
            contact_phone='+64987654321',
            timezone='Pacific/Auckland',
            currency='NZD'
        )
        
        url = f'/api/staff/tenants/{tenant.pk}/'
        response = self.client.get(url, **self.auth_headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Detail Test Tenant')
        self.assertEqual(response.data['slug'], 'detail-test')
        self.assertEqual(response.data['contact_email'], 'detail@test.com')
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
    
    def test_update_tenant_partial(self):
        """Test partial update of tenant"""
        tenant = Tenant.objects.create(
            name='Original Name',
            slug='original-slug',
            contact_email='original@test.com'
        )
        
        url = f'/api/staff/tenants/{tenant.pk}/'
        update_data = {
            'name': 'Updated Name',
            'contact_phone': '+64111222333'
        }
        
        response = self.client.patch(url, update_data, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update in database
        tenant.refresh_from_db()
        self.assertEqual(tenant.name, 'Updated Name')
        self.assertEqual(tenant.contact_phone, '+64111222333')
        self.assertEqual(tenant.slug, 'original-slug')  # Should remain unchanged
    
    def test_update_tenant_full(self):
        """Test full update of tenant"""
        tenant = Tenant.objects.create(
            name='Original Name',
            slug='original-slug',
            contact_email='original@test.com'
        )
        
        url = f'/api/staff/tenants/{tenant.pk}/'
        update_data = {
            'name': 'Completely Updated Name',
            'slug': 'updated-slug',
            'contact_email': 'updated@test.com',
            'contact_phone': '+64999888777',
            'timezone': 'Pacific/Auckland',
            'currency': 'AUD',
            'is_active': False
        }
        
        response = self.client.put(url, update_data, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update in database
        tenant.refresh_from_db()
        self.assertEqual(tenant.name, 'Completely Updated Name')
        self.assertEqual(tenant.slug, 'updated-slug')
        self.assertEqual(tenant.currency, 'AUD')
        self.assertFalse(tenant.is_active)
    
    def test_delete_tenant(self):
        """Test tenant deletion"""
        tenant = Tenant.objects.create(
            name='To Be Deleted',
            slug='to-be-deleted',
            contact_email='delete@test.com'
        )
        
        url = f'/api/staff/tenants/{tenant.pk}/'
        response = self.client.delete(url, **self.auth_headers)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        with self.assertRaises(Tenant.DoesNotExist):
            Tenant.objects.get(pk=tenant.pk)


class TenantDataIntegrityTests(TransactionTestCase):
    """Test data integrity and constraint enforcement"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_group = Group.objects.create(name='Admin')
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        self.admin_user.groups.add(self.admin_group)
    
    def test_tenant_slug_uniqueness(self):
        """Test that tenant slugs must be unique"""
        Tenant.objects.create(
            name='First Tenant',
            slug='unique-slug',
            contact_email='first@test.com'
        )
        
        with self.assertRaises(Exception):  # Should raise IntegrityError
            Tenant.objects.create(
                name='Second Tenant',
                slug='unique-slug',  # Duplicate slug
                contact_email='second@test.com'
            )
    
    def test_tenant_user_role_relationships(self):
        """Test tenant user role relationships"""
        tenant = Tenant.objects.create(
            name='Role Test Tenant',
            slug='role-test',
            contact_email='role@test.com'
        )
        
        user = User.objects.create_user(
            email='roleuser@test.com',
            password='pass123'
        )
        
        # Create tenant user role
        role = TenantUserRole.objects.create(
            tenant=tenant,
            user=user,
            role='admin',
            can_manage_users=True,
            can_modify_settings=True
        )
        
        self.assertEqual(role.tenant, tenant)
        self.assertEqual(role.user, user)
        self.assertTrue(role.can_manage_users)
        self.assertTrue(role.can_modify_settings)
        
        # Test role permissions are set correctly for admin role
        self.assertTrue(role.can_access_billing)
        self.assertTrue(role.can_access_metering)
        self.assertTrue(role.can_manage_contracts)


class TenantSerializerTests(TestCase):
    """Test tenant serializers"""
    
    def test_tenant_list_serializer(self):
        """Test tenant list serializer"""
        tenant = Tenant.objects.create(
            name='Serializer Test Tenant',
            slug='serializer-test',
            contact_email='serializer@test.com',
            contact_phone='+64123456789'
        )
        
        serializer = TenantListSerializer(tenant)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Serializer Test Tenant')
        self.assertEqual(data['slug'], 'serializer-test')
        self.assertEqual(data['contact_email'], 'serializer@test.com')
        self.assertIn('id', data)
        self.assertIn('is_active', data)
        self.assertIn('created_at', data)
    
    def test_tenant_create_serializer_validation(self):
        """Test tenant create serializer validation"""
        # Valid data
        valid_data = {
            'name': 'Valid Tenant',
            'slug': 'valid-tenant',
            'contact_email': 'valid@test.com'
        }
        serializer = TenantCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid data - missing required fields
        invalid_data = {
            'name': 'Invalid Tenant'
            # Missing slug and contact_email
        }
        serializer = TenantCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('slug', serializer.errors)
        self.assertIn('contact_email', serializer.errors)
        
        # Invalid email format
        invalid_email_data = {
            'name': 'Invalid Email Tenant',
            'slug': 'invalid-email',
            'contact_email': 'not-an-email'
        }
        serializer = TenantCreateSerializer(data=invalid_email_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contact_email', serializer.errors)
    
    def test_tenant_detail_serializer(self):
        """Test tenant detail serializer with all fields"""
        tenant = Tenant.objects.create(
            name='Detail Serializer Test',
            slug='detail-serializer',
            contact_email='detail@test.com',
            contact_phone='+64987654321',
            business_number='BN987654321',
            address='456 Detail Street',
            timezone='Pacific/Auckland',
            currency='NZD',
            service_limits={'max_users': 50}
        )
        
        # Create a user role for this tenant
        user = User.objects.create_user(
            email='detailuser@test.com',
            password='pass123'
        )
        TenantUserRole.objects.create(
            tenant=tenant,
            user=user,
            role='staff'
        )
        
        serializer = TenantDetailSerializer(tenant)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Detail Serializer Test')
        self.assertEqual(data['business_number'], 'BN987654321')
        self.assertEqual(data['timezone'], 'Pacific/Auckland')
        self.assertEqual(data['currency'], 'NZD')
        self.assertIn('service_limits', data)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests([
        'users.tests.test_tenant_crud_e2e'
    ]) 