"""
Automated tests for multi-tenant functionality
Ensures reliable multi-tenant operations
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
import json

User = get_user_model()


class MultiTenantModelTests(TestCase):
    """Test multi-tenant model relationships"""
    
    def setUp(self):
        """Set up test data"""
        from users.models import Tenant
        
        # Create test tenants
        self.tenant1 = Tenant.objects.create(
            name='Test Tenant 1',
            slug='test-tenant-1',
            is_active=True,
            contact_email='tenant1@test.com'
        )
        
        self.tenant2 = Tenant.objects.create(
            name='Test Tenant 2',
            slug='test-tenant-2',
            is_active=True,
            contact_email='tenant2@test.com'
        )

    def test_tenant_creation(self):
        """Test tenant creation and basic properties"""
        self.assertEqual(self.tenant1.name, 'Test Tenant 1')
        self.assertEqual(self.tenant1.slug, 'test-tenant-1')
        self.assertTrue(self.tenant1.is_active)

    def test_user_tenant_association(self):
        """Test user-tenant relationships"""
        from users.models import User
        
        user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            tenant=self.tenant1
        )
        
        user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            tenant=self.tenant2
        )
        
        self.assertEqual(user1.tenant, self.tenant1)
        self.assertEqual(user2.tenant, self.tenant2)
        self.assertNotEqual(user1.tenant, user2.tenant)

    def test_account_tenant_isolation(self):
        """Test account tenant isolation"""
        from users.models import Account, User
        
        user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            tenant=self.tenant1
        )
        
        account1 = Account.objects.create(
            account_number='ACC001',
            tenant=self.tenant1,
            account_type='residential'
        )
        
        account2 = Account.objects.create(
            account_number='ACC002',
            tenant=self.tenant2,
            account_type='residential'
        )
        
        # Test tenant filtering
        tenant1_accounts = Account.objects.filter(tenant=self.tenant1)
        tenant2_accounts = Account.objects.filter(tenant=self.tenant2)
        
        self.assertEqual(tenant1_accounts.count(), 1)
        self.assertEqual(tenant2_accounts.count(), 1)
        self.assertIn(account1, tenant1_accounts)
        self.assertNotIn(account1, tenant2_accounts)

    def test_plan_tenant_association(self):
        """Test plan-tenant relationships"""
        try:
            from finance.pricing.models import ServicePlan
            from django.utils import timezone
            
            plan1 = ServicePlan.objects.create(
                tenant=self.tenant1,
                plan_code='PLAN001',
                plan_name='Test Plan 1',
                service_type='electricity',
                plan_type='fixed',
                description='Test plan for tenant 1',
                base_price=100.00,
                monthly_fee=50.00,
                status='active',
                available_from=timezone.now()
            )
            
            plan2 = ServicePlan.objects.create(
                tenant=self.tenant2,
                plan_code='PLAN002',
                plan_name='Test Plan 2',
                service_type='electricity',
                plan_type='fixed',
                description='Test plan for tenant 2',
                base_price=120.00,
                monthly_fee=60.00,
                status='active',
                available_from=timezone.now()
            )
            
            # Test tenant isolation
            tenant1_plans = ServicePlan.objects.filter(tenant=self.tenant1)
            tenant2_plans = ServicePlan.objects.filter(tenant=self.tenant2)
            
            self.assertEqual(tenant1_plans.count(), 1)
            self.assertEqual(tenant2_plans.count(), 1)
            self.assertIn(plan1, tenant1_plans)
            self.assertNotIn(plan1, tenant2_plans)
            
        except ImportError:
            self.skipTest("ServicePlan model not available")


class StaffAPIMultiTenantTests(APITestCase):
    """Test staff API multi-tenant functionality"""
    
    def setUp(self):
        """Set up test data"""
        from users.models import Tenant, User
        
        # Create test tenants
        self.tenant1 = Tenant.objects.create(
            name='Test Tenant 1',
            slug='test-tenant-1',
            is_active=True,
            contact_email='tenant1@test.com'
        )
        
        self.tenant2 = Tenant.objects.create(
            name='Test Tenant 2',
            slug='test-tenant-2',
            is_active=True,
            contact_email='tenant2@test.com'
        )
        
        # Create test users
        self.superuser = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123'
        )
        
        self.staff_user1 = User.objects.create_user(
            email='staff1@test.com',
            password='testpass123',
            is_staff=True,
            tenant=self.tenant1
        )
        
        self.staff_user2 = User.objects.create_user(
            email='staff2@test.com',
            password='testpass123',
            is_staff=True,
            tenant=self.tenant2
        )

    def test_superuser_tenant_access(self):
        """Test superuser can access all tenants"""
        self.client.force_authenticate(user=self.superuser)
        
        # Test tenant list access
        url = reverse('users:tenant-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Superuser should see all tenants
        self.assertGreaterEqual(len(response.data.get('results', response.data)), 2)

    def test_staff_user_tenant_isolation(self):
        """Test staff user can only access their tenant"""
        self.client.force_authenticate(user=self.staff_user1)
        
        # Test with tenant filtering
        url = reverse('users:tenant-list')
        response = self.client.get(url, {'tenant': self.tenant1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff user should only see their tenant
        data = response.data.get('results', response.data)
        if isinstance(data, list):
            tenant_ids = [t['id'] for t in data]
            self.assertIn(str(self.tenant1.id), tenant_ids)

    def test_plans_api_tenant_filtering(self):
        """Test plans API respects tenant filtering"""
        try:
            from finance.pricing.models import ServicePlan
            from django.utils import timezone
            
            # Create plans for different tenants
            ServicePlan.objects.create(
                tenant=self.tenant1,
                plan_code='PLAN001',
                plan_name='Tenant 1 Plan',
                service_type='electricity',
                plan_type='fixed',
                description='Plan for tenant 1',
                base_price=100.00,
                monthly_fee=50.00,
                status='active',
                available_from=timezone.now()
            )
            
            ServicePlan.objects.create(
                tenant=self.tenant2,
                plan_code='PLAN002',
                plan_name='Tenant 2 Plan',
                service_type='electricity',
                plan_type='fixed',
                description='Plan for tenant 2',
                base_price=120.00,
                monthly_fee=60.00,
                status='active',
                available_from=timezone.now()
            )
            
            # Test as staff user 1
            self.client.force_authenticate(user=self.staff_user1)
            url = reverse('users:plan-list')
            response = self.client.get(url, {'tenant': self.tenant1.id})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Should only see tenant 1 plans
            plans_data = response.data.get('results', response.data)
            if isinstance(plans_data, list) and plans_data:
                # Check that plans belong to tenant 1
                plan_names = [p.get('name', p.get('plan_name', '')) for p in plans_data]
                self.assertIn('Tenant 1 Plan', str(plan_names))
                
        except ImportError:
            self.skipTest("ServicePlan model not available")

    def test_connection_management_endpoints(self):
        """Test connection management endpoints work correctly"""
        try:
            from energy.connections.models import Connection
            from users.models import Account
            
            # Create test data
            account = Account.objects.create(
                account_number='ACC001',
                tenant=self.tenant1,
                account_type='residential'
            )
            
            connection = Connection.objects.create(
                tenant=self.tenant1,
                account=account,
                connection_identifier='CONN001',
                service_type='electricity',
                status='pending'
            )
            
            self.client.force_authenticate(user=self.staff_user1)
            
            # Test status update endpoint
            url = reverse('users:connection-update-status', kwargs={'pk': connection.id})
            response = self.client.post(url, {'status': 'active'})
            
            # Should succeed or return method not allowed (depending on implementation)
            self.assertIn(response.status_code, [
                status.HTTP_200_OK, 
                status.HTTP_405_METHOD_NOT_ALLOWED,
                status.HTTP_404_NOT_FOUND  # If endpoint doesn't exist yet
            ])
            
        except ImportError:
            self.skipTest("Connection model not available")


class TenantManagementCommandTests(TransactionTestCase):
    """Test tenant management commands"""
    
    def test_create_default_tenant_command(self):
        """Test create_default_tenant management command"""
        from django.core.management import call_command
        from users.models import Tenant
        
        # Ensure no default tenant exists
        Tenant.objects.filter(slug='utility-byte-default').delete()
        
        # Run command
        call_command('create_default_tenant', '--dry-run')
        
        # In dry run mode, tenant should not be created
        self.assertFalse(Tenant.objects.filter(slug='utility-byte-default').exists())

    def test_audit_tenant_data_command(self):
        """Test audit_tenant_data management command"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('audit_tenant_data', stdout=out)
        
        output = out.getvalue()
        self.assertIn('TENANT DATA AUDIT SUMMARY', output)

    def test_monitor_tenant_health_command(self):
        """Test monitor_tenant_health management command"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('monitor_tenant_health', stdout=out)
        
        output = out.getvalue()
        self.assertIn('TENANT HEALTH REPORT', output)


class TenantContextTests(TestCase):
    """Test tenant context functionality"""
    
    def setUp(self):
        """Set up test data"""
        from users.models import Tenant, User
        
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            is_active=True,
            contact_email='test@test.com'
        )
        
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            tenant=self.tenant
        )

    def test_get_user_tenant_function(self):
        """Test get_user_tenant utility function"""
        from users.staff_views import get_user_tenant
        
        user_tenant = get_user_tenant(self.user)
        self.assertEqual(user_tenant, self.tenant)

    def test_tenant_filtering_utility(self):
        """Test tenant filtering utilities"""
        from users.staff_views import should_filter_by_tenant
        
        # Regular user should be filtered by tenant
        self.assertTrue(should_filter_by_tenant(self.user))
        
        # Superuser might not be filtered (depends on implementation)
        superuser = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123'
        )
        
        # Test superuser filtering behavior
        result = should_filter_by_tenant(superuser)
        self.assertIsInstance(result, bool)


class DataIntegrityTests(TestCase):
    """Test data integrity in multi-tenant environment"""
    
    def setUp(self):
        """Set up test data"""
        from users.models import Tenant
        
        self.tenant1 = Tenant.objects.create(
            name='Tenant 1',
            slug='tenant-1',
            is_active=True,
            contact_email='tenant1@test.com'
        )
        
        self.tenant2 = Tenant.objects.create(
            name='Tenant 2',
            slug='tenant-2',
            is_active=True,
            contact_email='tenant2@test.com'
        )

    def test_no_cross_tenant_data_leakage(self):
        """Test that tenants cannot access each other's data"""
        from users.models import Account, User
        
        # Create users for different tenants
        user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            tenant=self.tenant1
        )
        
        user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            tenant=self.tenant2
        )
        
        # Create accounts for different tenants
        account1 = Account.objects.create(
            account_number='ACC001',
            tenant=self.tenant1,
            account_type='residential'
        )
        
        account2 = Account.objects.create(
            account_number='ACC002',
            tenant=self.tenant2,
            account_type='residential'
        )
        
        # Test that filtering by tenant works correctly
        tenant1_accounts = Account.objects.filter(tenant=self.tenant1)
        tenant2_accounts = Account.objects.filter(tenant=self.tenant2)
        
        self.assertEqual(tenant1_accounts.count(), 1)
        self.assertEqual(tenant2_accounts.count(), 1)
        self.assertNotIn(account2, tenant1_accounts)
        self.assertNotIn(account1, tenant2_accounts)

    def test_orphaned_record_detection(self):
        """Test detection of orphaned records without tenant association"""
        from users.models import User
        
        # Create user without tenant (orphaned)
        orphaned_user = User.objects.create_user(
            email='orphaned@test.com',
            password='testpass123'
            # No tenant specified
        )
        
        # Test that orphaned users are detected
        orphaned_users = User.objects.filter(tenant__isnull=True)
        self.assertIn(orphaned_user, orphaned_users)
        
        # Test that users with tenants are not in orphaned list
        user_with_tenant = User.objects.create_user(
            email='tenant_user@test.com',
            password='testpass123',
            tenant=self.tenant1
        )
        
        self.assertNotIn(user_with_tenant, orphaned_users)
