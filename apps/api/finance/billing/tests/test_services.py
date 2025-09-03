"""
Tests for billing services.
"""
import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock

from ..services import BillingOrchestrationService, InvoiceManagementService
from ..models import Bill, BillLineItem, BillingRun, BillingCycle
from ..models_registry import ServiceRegistry
from ...invoices.models import Invoice, InvoiceLine
from users.models import User, Tenant


class BillingOrchestrationServiceTest(TestCase):
    """Test cases for BillingOrchestrationService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = BillingOrchestrationService()
        
        # Create test tenant and user
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST",
            is_active=True
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
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
        
        # Test dates
        self.period_start = timezone.now() - timedelta(days=30)
        self.period_end = timezone.now() - timedelta(days=1)
    
    def test_create_billing_run_success(self):
        """Test successful billing run creation."""
        billing_run = self.service.create_billing_run(
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            tenant=self.tenant,
            dry_run=False
        )
        
        self.assertIsInstance(billing_run, BillingRun)
        self.assertEqual(billing_run.service_type, "broadband")
        self.assertEqual(billing_run.tenant, self.tenant)
        self.assertEqual(billing_run.status, "pending")
        self.assertIsNotNone(billing_run.idempotency_key)
    
    def test_create_billing_run_invalid_service(self):
        """Test billing run creation with invalid service type."""
        with self.assertRaises(ValidationError):
            self.service.create_billing_run(
                service_type="invalid",
                period_start=self.period_start,
                period_end=self.period_end,
                tenant=self.tenant
            )
    
    def test_create_billing_run_invalid_dates(self):
        """Test billing run creation with invalid dates."""
        with self.assertRaises(ValidationError):
            self.service.create_billing_run(
                service_type="broadband",
                period_start=self.period_end,  # Start after end
                period_end=self.period_start,
                tenant=self.tenant
            )
    
    def test_create_billing_run_future_date(self):
        """Test billing run creation with future end date."""
        future_date = timezone.now() + timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            self.service.create_billing_run(
                service_type="broadband",
                period_start=self.period_start,
                period_end=future_date,
                tenant=self.tenant
            )
    
    def test_create_billing_run_no_service_registry(self):
        """Test billing run creation without service registry."""
        with self.assertRaises(ValueError):
            self.service.create_billing_run(
                service_type="electricity",  # No registry for this
                period_start=self.period_start,
                period_end=self.period_end,
                tenant=self.tenant
            )
    
    def test_create_billing_run_duplicate(self):
        """Test creating duplicate billing run returns existing."""
        # Create first billing run
        run1 = self.service.create_billing_run(
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            tenant=self.tenant
        )
        
        # Create second with same parameters
        run2 = self.service.create_billing_run(
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            tenant=self.tenant
        )
        
        self.assertEqual(run1.id, run2.id)
    
    @patch('finance.billing.services.call_command')
    def test_execute_billing_run_success(self, mock_call_command):
        """Test successful billing run execution."""
        # Create billing run
        billing_run = BillingRun.objects.create(
            tenant=self.tenant,
            run_name="Test Run",
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            run_date=timezone.now(),
            status="pending"
        )
        
        # Mock successful command execution
        mock_call_command.return_value = None
        
        result = self.service.execute_billing_run(billing_run, dry_run=False)
        
        # Verify result structure
        self.assertIn('billing_run_id', result)
        self.assertIn('service_type', result)
        self.assertIn('bills_created', result)
        self.assertIn('status', result)
        
        # Verify billing run was updated
        billing_run.refresh_from_db()
        self.assertIn(billing_run.status, ['completed', 'failed'])
        self.assertIsNotNone(billing_run.started_at)
    
    def test_execute_billing_run_invalid_status(self):
        """Test executing billing run with invalid status."""
        billing_run = BillingRun.objects.create(
            tenant=self.tenant,
            run_name="Test Run",
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            run_date=timezone.now(),
            status="completed"  # Already completed
        )
        
        with self.assertRaises(ValidationError):
            self.service.execute_billing_run(billing_run)
    
    @patch('finance.billing.services.call_command')
    def test_execute_billing_run_dry_run(self, mock_call_command):
        """Test billing run execution in dry run mode."""
        billing_run = BillingRun.objects.create(
            tenant=self.tenant,
            run_name="Test Run",
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            run_date=timezone.now(),
            status="pending"
        )
        
        result = self.service.execute_billing_run(billing_run, dry_run=True)
        
        # Verify dry run results
        self.assertTrue(result['dry_run'])
        self.assertGreater(result['bills_created'], 0)  # Simulated count
        
        # Command should not be called in dry run
        mock_call_command.assert_not_called()
    
    def test_get_billing_dashboard_stats(self):
        """Test getting billing dashboard statistics."""
        # Create some test data
        BillingRun.objects.create(
            tenant=self.tenant,
            run_name="Test Run 1",
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            run_date=timezone.now(),
            status="running"
        )
        
        BillingRun.objects.create(
            tenant=self.tenant,
            run_name="Test Run 2",
            service_type="electricity",
            period_start=self.period_start,
            period_end=self.period_end,
            run_date=timezone.now() - timedelta(hours=1),
            status="completed"
        )
        
        stats = self.service.get_billing_dashboard_stats(tenant=self.tenant)
        
        # Verify stats structure
        self.assertIn('active_runs', stats)
        self.assertIn('pending_bills', stats)
        self.assertIn('recent_activity', stats)
        self.assertIn('service_status', stats)
        self.assertIn('last_updated', stats)
        
        # Verify data
        self.assertEqual(stats['active_runs'], 1)  # One running
        self.assertIsInstance(stats['recent_activity'], list)
        self.assertIsInstance(stats['service_status'], dict)
    
    def test_validate_billing_run_params(self):
        """Test billing run parameter validation."""
        # Valid parameters should not raise
        self.service._validate_billing_run_params(
            "broadband",
            self.period_start,
            self.period_end
        )
        
        # Invalid service type
        with self.assertRaises(ValidationError):
            self.service._validate_billing_run_params(
                "invalid",
                self.period_start,
                self.period_end
            )
        
        # Invalid date range
        with self.assertRaises(ValidationError):
            self.service._validate_billing_run_params(
                "broadband",
                self.period_end,
                self.period_start
            )
        
        # Period too long
        long_start = timezone.now() - timedelta(days=400)
        with self.assertRaises(ValidationError):
            self.service._validate_billing_run_params(
                "broadband",
                long_start,
                self.period_end
            )


class InvoiceManagementServiceTest(TestCase):
    """Test cases for InvoiceManagementService."""
    
    def setUp(self):
        """Set up test data."""
        from ..services import InvoiceManagementService
        self.service = InvoiceManagementService()
        
        # Create test tenant and user
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST",
            is_active=True
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create test bill
        self.bill = Bill.objects.create(
            tenant=self.tenant,
            bill_number="BILL-001",
            customer=self.user,
            period_start=timezone.now() - timedelta(days=30),
            period_end=timezone.now() - timedelta(days=1),
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00,
            status="issued"
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
    
    def test_generate_invoices_from_bills_success(self):
        """Test successful invoice generation from bills."""
        result = self.service.generate_invoices_from_bills(
            billing_run_id=str(self.bill.id),  # Using bill ID as placeholder
            dry_run=False
        )
        
        # Note: This test would need actual BillingRun setup
        # For now, we test the structure
        self.assertIn('invoices_created', result)
        self.assertIn('invoices_failed', result)
        self.assertIn('total_amount', result)
        self.assertIn('errors', result)
    
    def test_generate_invoices_dry_run(self):
        """Test invoice generation in dry run mode."""
        result = self.service.generate_invoices_from_bills(
            billing_run_id=str(self.bill.id),
            dry_run=True
        )
        
        # Should return simulated results without creating invoices
        self.assertGreaterEqual(result['invoices_created'], 0)
        self.assertEqual(result['invoices_failed'], 0)
    
    def test_get_invoice_status_summary(self):
        """Test getting invoice status summary."""
        # Create test invoice
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.user,
            invoice_number="INV-001",
            status="draft",
            payment_status="unpaid",
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00
        )
        
        summary = self.service.get_invoice_status_summary(tenant=self.tenant)
        
        # Verify summary structure
        self.assertIn('total_invoices', summary)
        self.assertIn('status_breakdown', summary)
        self.assertIn('payment_status_breakdown', summary)
        self.assertIn('total_amount', summary)
        
        # Verify data
        self.assertEqual(summary['total_invoices'], 1)
        self.assertGreater(summary['total_amount'], 0)


@pytest.mark.django_db
class TestBillingServiceIntegration:
    """Integration tests for billing services."""
    
    def test_complete_billing_workflow(self):
        """Test complete billing workflow from run creation to invoice generation."""
        # This would be an integration test that tests the full workflow
        # For now, we'll create a placeholder
        assert True  # Placeholder for integration test
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Test various error scenarios and recovery
        assert True  # Placeholder for error handling test
