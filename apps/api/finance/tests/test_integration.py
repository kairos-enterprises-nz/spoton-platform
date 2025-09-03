"""
Integration tests for the complete billing workflow.
"""
import pytest
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from ..billing.models import Bill, BillLineItem, BillingRun
from ..billing.models_registry import ServiceRegistry
from ..invoices.models import Invoice, InvoiceLine
from ..billing.services import billing_service
from ..invoices.services import invoice_lifecycle_service
from users.models import User, Tenant


class BillingWorkflowIntegrationTest(TransactionTestCase):
    """Test the complete billing workflow from run creation to invoice delivery."""
    
    def setUp(self):
        """Set up test data for integration tests."""
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
        
        # Test period
        self.period_start = timezone.now() - timedelta(days=30)
        self.period_end = timezone.now() - timedelta(days=1)
    
    @patch('finance.billing.services.call_command')
    def test_complete_billing_workflow_dry_run(self, mock_call_command):
        """Test complete billing workflow in dry run mode."""
        # Step 1: Create billing run
        billing_run = billing_service.create_billing_run(
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            tenant=self.tenant,
            dry_run=True
        )
        
        self.assertIsInstance(billing_run, BillingRun)
        self.assertEqual(billing_run.status, "pending")
        
        # Step 2: Execute billing run (dry run)
        result = billing_service.execute_billing_run(billing_run, dry_run=True)
        
        self.assertTrue(result['dry_run'])
        self.assertGreater(result['bills_created'], 0)
        self.assertEqual(result['bills_failed'], 0)
        
        # Verify billing run status
        billing_run.refresh_from_db()
        self.assertEqual(billing_run.status, "completed")
        
        # Mock command should not be called in dry run
        mock_call_command.assert_not_called()
    
    def test_complete_billing_workflow_with_real_data(self):
        """Test complete workflow with actual bill and invoice creation."""
        # Create a test bill manually (simulating successful billing run)
        bill = Bill.objects.create(
            tenant=self.tenant,
            bill_number="BILL-TEST-001",
            customer=self.customer,
            period_start=self.period_start,
            period_end=self.period_end,
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
            bill=bill,
            description="Broadband Service",
            service_type="broadband",
            quantity=1,
            unit="month",
            unit_price=100.00,
            amount=100.00,
            is_taxable=True,
            tax_rate=0.15,
            tax_amount=15.00,
            sort_order=1
        )
        
        # Step 1: Create invoice from bill
        invoice_result = invoice_lifecycle_service.create_invoices_from_bills(
            bill_ids=[str(bill.id)],
            dry_run=False
        )
        
        self.assertEqual(invoice_result['invoices_created'], 1)
        self.assertEqual(invoice_result['invoices_failed'], 0)
        
        # Verify invoice was created
        invoice = Invoice.objects.filter(bill=bill).first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.status, "draft")
        self.assertEqual(invoice.total_amount, bill.total_amount)
        
        # Verify invoice lines
        invoice_lines = invoice.lines.all()
        self.assertEqual(invoice_lines.count(), 1)
        self.assertEqual(invoice_lines.first().description, "Broadband Service")
        
        # Step 2: Review and approve invoice
        review_result = invoice_lifecycle_service.review_and_approve_invoices(
            invoice_ids=[str(invoice.id)],
            user=self.staff_user,
            approved=True
        )
        
        self.assertEqual(review_result['reviewed_count'], 1)
        self.assertEqual(review_result['failed_count'], 0)
        
        # Verify invoice status
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "review")
        
        # Step 3: Finalize invoice
        finalize_result = invoice_lifecycle_service.finalize_invoices(
            invoice_ids=[str(invoice.id)],
            user=self.staff_user
        )
        
        self.assertEqual(finalize_result['finalized_count'], 1)
        self.assertEqual(finalize_result['failed_count'], 0)
        
        # Verify invoice status and timestamp
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "finalized")
        self.assertIsNotNone(invoice.finalized_at)
        
        # Step 4: Generate PDF (dry run)
        pdf_result = invoice_lifecycle_service.generate_invoice_pdfs(
            invoice_ids=[str(invoice.id)],
            dry_run=True
        )
        
        self.assertEqual(pdf_result['pdfs_generated'], 1)
        self.assertEqual(pdf_result['pdfs_failed'], 0)
        
        # Step 5: Send email (dry run)
        # First mark PDF as generated for email sending
        invoice.is_pdf_generated = True
        invoice.save()
        
        email_result = invoice_lifecycle_service.send_invoice_emails(
            invoice_ids=[str(invoice.id)],
            dry_run=True
        )
        
        self.assertEqual(email_result['emails_sent'], 1)
        self.assertEqual(email_result['emails_failed'], 0)
    
    def test_error_handling_in_workflow(self):
        """Test error handling throughout the workflow."""
        # Test 1: Invalid service type
        with self.assertRaises(ValidationError):
            billing_service.create_billing_run(
                service_type="invalid",
                period_start=self.period_start,
                period_end=self.period_end,
                tenant=self.tenant
            )
        
        # Test 2: Invalid date range
        with self.assertRaises(ValidationError):
            billing_service.create_billing_run(
                service_type="broadband",
                period_start=self.period_end,  # Start after end
                period_end=self.period_start,
                tenant=self.tenant
            )
        
        # Test 3: Invoice creation with invalid bill status
        bill = Bill.objects.create(
            tenant=self.tenant,
            bill_number="BILL-INVALID-001",
            customer=self.customer,
            period_start=self.period_start,
            period_end=self.period_end,
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00,
            status="draft"  # Invalid status for invoice creation
        )
        
        # Should not create invoice for draft bill
        result = invoice_lifecycle_service.create_invoices_from_bills(
            bill_ids=[str(bill.id)],
            dry_run=False
        )
        
        self.assertEqual(result['invoices_created'], 0)
        self.assertEqual(result['invoices_failed'], 0)
    
    def test_idempotency_in_workflow(self):
        """Test that operations are idempotent."""
        # Create billing run twice with same parameters
        run1 = billing_service.create_billing_run(
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            tenant=self.tenant
        )
        
        run2 = billing_service.create_billing_run(
            service_type="broadband",
            period_start=self.period_start,
            period_end=self.period_end,
            tenant=self.tenant
        )
        
        # Should return same billing run
        self.assertEqual(run1.id, run2.id)
        
        # Test invoice creation idempotency
        bill = Bill.objects.create(
            tenant=self.tenant,
            bill_number="BILL-IDEMPOTENT-001",
            customer=self.customer,
            period_start=self.period_start,
            period_end=self.period_end,
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00,
            status="issued"
        )
        
        # Create invoice first time
        result1 = invoice_lifecycle_service.create_invoices_from_bills(
            bill_ids=[str(bill.id)],
            dry_run=False
        )
        self.assertEqual(result1['invoices_created'], 1)
        
        # Try to create again - should not create duplicate
        result2 = invoice_lifecycle_service.create_invoices_from_bills(
            bill_ids=[str(bill.id)],
            dry_run=False
        )
        self.assertEqual(result2['invoices_created'], 0)
        
        # Verify only one invoice exists
        invoice_count = Invoice.objects.filter(bill=bill).count()
        self.assertEqual(invoice_count, 1)


class BillingAPIIntegrationTest(APITestCase):
    """Test the complete API workflow."""
    
    def setUp(self):
        """Set up test data for API integration tests."""
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
        ServiceRegistry.objects.create(
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
        self.client.force_authenticate(user=self.staff_user)
    
    def test_api_workflow_billing_run_creation_and_execution(self):
        """Test API workflow for billing run creation and execution."""
        # Step 1: Get dashboard stats
        dashboard_response = self.client.get('/api/finance/billing/runs/dashboard/')
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        
        initial_active_runs = dashboard_response.data['active_runs']
        
        # Step 2: Create billing run via API
        create_data = {
            'service_type': 'broadband',
            'period_start': (timezone.now() - timedelta(days=30)).isoformat(),
            'period_end': (timezone.now() - timedelta(days=1)).isoformat(),
            'dry_run': True,
            'execute_immediately': False
        }
        
        create_response = self.client.post('/api/finance/billing/runs/create_run/', create_data)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        
        billing_run_id = create_response.data['id']
        self.assertEqual(create_response.data['service_type'], 'broadband')
        
        # Step 3: Execute billing run via API
        execute_response = self.client.post(
            f'/api/finance/billing/runs/{billing_run_id}/execute/',
            {'dry_run': True}
        )
        self.assertEqual(execute_response.status_code, status.HTTP_200_OK)
        self.assertTrue(execute_response.data['dry_run'])
        self.assertGreater(execute_response.data['bills_created'], 0)
        
        # Step 4: Verify dashboard stats updated
        updated_dashboard_response = self.client.get('/api/finance/billing/runs/dashboard/')
        self.assertEqual(updated_dashboard_response.status_code, status.HTTP_200_OK)
        
        # Active runs might be the same since the run completed
        # But recent activity should be updated
        self.assertIsInstance(updated_dashboard_response.data['recent_activity'], list)
    
    def test_api_workflow_with_pagination(self):
        """Test API pagination and filtering."""
        # Create multiple billing runs
        for i in range(25):  # More than one page
            create_data = {
                'service_type': 'broadband',
                'period_start': (timezone.now() - timedelta(days=30+i)).isoformat(),
                'period_end': (timezone.now() - timedelta(days=1+i)).isoformat(),
                'dry_run': True,
                'execute_immediately': False
            }
            
            response = self.client.post('/api/finance/billing/runs/create_run/', create_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test pagination
        response = self.client.get('/api/finance/billing/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['results']), 20)  # Default page size
        
        # Test filtering
        filtered_response = self.client.get('/api/finance/billing/runs/', {
            'service_type': 'broadband',
            'status': 'pending'
        })
        self.assertEqual(filtered_response.status_code, status.HTTP_200_OK)
        
        # All results should match filter
        for run in filtered_response.data['results']:
            self.assertEqual(run['service_type'], 'broadband')
            self.assertEqual(run['status'], 'pending')


@pytest.mark.django_db
class BillingPerformanceIntegrationTest:
    """Performance tests for billing operations."""
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations."""
        # This would test bulk bill creation, invoice generation, etc.
        # For now, we'll create a placeholder
        assert True  # Placeholder for performance test
    
    def test_concurrent_billing_runs(self):
        """Test handling of concurrent billing runs."""
        # This would test concurrent access and race conditions
        assert True  # Placeholder for concurrency test
