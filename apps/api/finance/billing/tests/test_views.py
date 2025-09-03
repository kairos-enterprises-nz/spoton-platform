"""
Tests for billing API views.
"""
import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from ..models import Bill, BillLineItem, BillingRun, BillingCycle
from ..models_registry import ServiceRegistry
from users.models import User, Tenant


class BillingRunViewSetTest(APITestCase):
    """Test cases for BillingRunViewSet."""
    
    def setUp(self):
        """Set up test data."""
        # Create test tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST",
            is_active=True
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        self.staff_user.tenants.add(self.tenant)
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="testpass123",
            is_staff=False
        )
        
        # Create service registry
        self.service_registry = ServiceRegistry.objects.create(
            tenant=self.tenant,
            service_code="broadband",
            name="Broadband",
            billing_type="prepaid",
            frequency="monthly",
            period="prepaid",
            billing_handler="finance.billing.handlers.broadband_handler.calculate_bill",
            is_active=True
        )
        
        # Create test billing run
        self.billing_run = BillingRun.objects.create(
            tenant=self.tenant,
            run_name="Test Billing Run",
            service_type="broadband",
            period_start=timezone.now() - timedelta(days=30),
            period_end=timezone.now() - timedelta(days=1),
            run_date=timezone.now(),
            status="pending"
        )
        
        self.client = APIClient()
    
    def test_list_billing_runs_staff_user(self):
        """Test listing billing runs as staff user."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('billingrun-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_billing_runs_regular_user(self):
        """Test listing billing runs as regular user (should be denied)."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('billingrun-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_billing_runs_unauthenticated(self):
        """Test listing billing runs without authentication."""
        url = reverse('billingrun-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_billing_run_success(self):
        """Test creating billing run successfully."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('billingrun-create-run')
        data = {
            'service_type': 'broadband',
            'period_start': (timezone.now() - timedelta(days=60)).isoformat(),
            'period_end': (timezone.now() - timedelta(days=31)).isoformat(),
            'dry_run': True,
            'execute_immediately': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['service_type'], 'broadband')
    
    def test_create_billing_run_invalid_data(self):
        """Test creating billing run with invalid data."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('billingrun-create-run')
        data = {
            'service_type': 'invalid',  # Invalid service type
            'period_start': timezone.now().isoformat(),
            'period_end': (timezone.now() - timedelta(days=1)).isoformat(),  # End before start
            'dry_run': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('finance.billing.views.billing_service.execute_billing_run')
    def test_execute_billing_run_success(self, mock_execute):
        """Test executing billing run successfully."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Mock successful execution
        mock_execute.return_value = {
            'billing_run_id': str(self.billing_run.id),
            'service_type': 'broadband',
            'status': 'completed',
            'bills_created': 5,
            'bills_failed': 0,
            'total_amount': 500.00,
            'started_at': timezone.now(),
            'completed_at': timezone.now(),
            'dry_run': False
        }
        
        url = reverse('billingrun-execute', kwargs={'pk': self.billing_run.id})
        data = {'dry_run': False}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['bills_created'], 5)
        mock_execute.assert_called_once()
    
    def test_execute_billing_run_not_found(self):
        """Test executing non-existent billing run."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('billingrun-execute', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        data = {'dry_run': False}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('finance.billing.views.billing_service.get_billing_dashboard_stats')
    def test_dashboard_stats(self, mock_get_stats):
        """Test getting dashboard statistics."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Mock dashboard stats
        mock_get_stats.return_value = {
            'active_runs': 2,
            'pending_bills': 10,
            'recent_activity': [],
            'service_status': {
                'broadband': {'last_run': timezone.now(), 'last_status': 'completed', 'is_healthy': True}
            },
            'last_updated': timezone.now()
        }
        
        url = reverse('billingrun-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_runs'], 2)
        self.assertEqual(response.data['pending_bills'], 10)
        mock_get_stats.assert_called_once()
    
    def test_dashboard_stats_error(self):
        """Test dashboard stats with service error."""
        self.client.force_authenticate(user=self.staff_user)
        
        with patch('finance.billing.views.billing_service.get_billing_dashboard_stats') as mock_get_stats:
            mock_get_stats.side_effect = Exception("Service error")
            
            url = reverse('billingrun-dashboard')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)


class BillViewSetTest(APITestCase):
    """Test cases for BillViewSet."""
    
    def setUp(self):
        """Set up test data."""
        # Create test tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST",
            is_active=True
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        self.staff_user.tenants.add(self.tenant)
        
        # Create customer user
        self.customer = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpass123"
        )
        
        # Create test bill
        self.bill = Bill.objects.create(
            tenant=self.tenant,
            bill_number="BILL-001",
            customer=self.customer,
            period_start=timezone.now() - timedelta(days=30),
            period_end=timezone.now() - timedelta(days=1),
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00,
            status="draft"
        )
        
        # Create bill line item
        BillLineItem.objects.create(
            bill=self.bill,
            description="Broadband Service",
            service_type="broadband",
            quantity=1,
            unit="month",
            unit_price=100.00,
            amount=100.00,
            is_taxable=True,
            tax_rate=0.15,
            tax_amount=15.00
        )
        
        self.client = APIClient()
    
    def test_list_bills_staff_user(self):
        """Test listing bills as staff user."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('bill-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_bill_with_line_items(self):
        """Test retrieving bill with line items."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('bill-detail', kwargs={'pk': self.bill.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bill_number'], 'BILL-001')
        self.assertIn('line_items', response.data)
        self.assertEqual(len(response.data['line_items']), 1)
    
    def test_filter_bills_by_status(self):
        """Test filtering bills by status."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('bill-list')
        response = self.client.get(url, {'status': 'draft'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test with non-matching filter
        response = self.client.get(url, {'status': 'paid'})
        self.assertEqual(len(response.data['results']), 0)
    
    def test_search_bills(self):
        """Test searching bills by bill number."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('bill-list')
        response = self.client.get(url, {'search': 'BILL-001'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test with non-matching search
        response = self.client.get(url, {'search': 'NONEXISTENT'})
        self.assertEqual(len(response.data['results']), 0)
    
    @patch('finance.invoices.services.invoice_lifecycle_service.create_invoices_from_bills')
    def test_bulk_action_generate_invoices(self, mock_create_invoices):
        """Test bulk action to generate invoices from bills."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Mock successful invoice creation
        mock_create_invoices.return_value = {
            'invoices_created': 1,
            'invoices_failed': 0,
            'total_amount': 115.00,
            'errors': []
        }
        
        url = reverse('bill-bulk-action')
        data = {
            'bill_ids': [str(self.bill.id)],
            'action': 'generate_invoices',
            'dry_run': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['invoices_created'], 1)
        mock_create_invoices.assert_called_once()
    
    def test_bulk_action_invalid_action(self):
        """Test bulk action with invalid action type."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('bill-bulk-action')
        data = {
            'bill_ids': [str(self.bill.id)],
            'action': 'invalid_action',
            'dry_run': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not implemented', response.data['error'])


class ServiceRegistryViewSetTest(APITestCase):
    """Test cases for ServiceRegistryViewSet."""
    
    def setUp(self):
        """Set up test data."""
        # Create test tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST",
            is_active=True
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        self.staff_user.tenants.add(self.tenant)
        
        # Create service registry
        self.service_registry = ServiceRegistry.objects.create(
            tenant=self.tenant,
            service_code="broadband",
            name="Broadband",
            billing_type="prepaid",
            frequency="monthly",
            period="prepaid",
            billing_handler="finance.billing.handlers.broadband_handler.calculate_bill",
            is_active=True
        )
        
        self.client = APIClient()
    
    def test_list_service_registry(self):
        """Test listing service registry entries."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('serviceregistry-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['service_code'], 'broadband')
    
    def test_create_service_registry(self):
        """Test creating service registry entry."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('serviceregistry-list')
        data = {
            'tenant': self.tenant.id,
            'service_code': 'electricity',
            'name': 'Electricity',
            'billing_type': 'postpaid',
            'frequency': 'weekly',
            'period': 'postpaid',
            'billing_handler': 'finance.billing.handlers.electricity_handler.calculate_bill',
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['service_code'], 'electricity')
    
    def test_update_service_registry(self):
        """Test updating service registry entry."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('serviceregistry-detail', kwargs={'pk': self.service_registry.id})
        data = {
            'tenant': self.tenant.id,
            'service_code': 'broadband',
            'name': 'Broadband Updated',
            'billing_type': 'prepaid',
            'frequency': 'monthly',
            'period': 'prepaid',
            'billing_handler': 'finance.billing.handlers.broadband_handler.calculate_bill',
            'is_active': False  # Deactivate
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Broadband Updated')
        self.assertEqual(response.data['is_active'], False)
    
    def test_filter_service_registry(self):
        """Test filtering service registry by service code."""
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse('serviceregistry-list')
        response = self.client.get(url, {'service_code': 'broadband'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test with non-matching filter
        response = self.client.get(url, {'service_code': 'mobile'})
        self.assertEqual(len(response.data), 0)
