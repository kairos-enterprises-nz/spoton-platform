"""
Tests for invoice services.
"""
import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock

from ..services import InvoiceLifecycleService
from ..models import Invoice, InvoiceLine
from ...billing.models import Bill, BillLineItem, BillingRun
from users.models import User, Tenant


class InvoiceLifecycleServiceTest(TestCase):
    """Test cases for InvoiceLifecycleService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = InvoiceLifecycleService()
        
        # Create test tenant and users
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST",
            is_active=True
        )
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        
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
            status="issued"
        )
        
        # Create bill line item
        self.bill_line = BillLineItem.objects.create(
            bill=self.bill,
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
    
    def test_create_invoices_from_bills_success(self):
        """Test successful invoice creation from bills."""
        result = self.service.create_invoices_from_bills(
            bill_ids=[str(self.bill.id)],
            dry_run=False
        )
        
        # Verify result structure
        self.assertIn('invoices_created', result)
        self.assertIn('invoices_failed', result)
        self.assertIn('total_amount', result)
        self.assertIn('errors', result)
        
        # Verify invoice was created
        self.assertEqual(result['invoices_created'], 1)
        self.assertEqual(result['invoices_failed'], 0)
        
        # Verify invoice exists in database
        invoice = Invoice.objects.filter(bill=self.bill).first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.invoice_number, f"INV-{self.bill.bill_number}")
        self.assertEqual(invoice.status, "draft")
        self.assertEqual(invoice.total_amount, self.bill.total_amount)
        
        # Verify invoice lines were created
        invoice_lines = invoice.lines.all()
        self.assertEqual(invoice_lines.count(), 1)
        self.assertEqual(invoice_lines.first().description, "Broadband Service")
    
    def test_create_invoices_from_bills_dry_run(self):
        """Test invoice creation in dry run mode."""
        result = self.service.create_invoices_from_bills(
            bill_ids=[str(self.bill.id)],
            dry_run=True
        )
        
        # Should return simulated results
        self.assertEqual(result['invoices_created'], 1)
        self.assertEqual(result['invoices_failed'], 0)
        self.assertGreater(result['total_amount'], 0)
        
        # No actual invoices should be created
        invoice_count = Invoice.objects.filter(bill=self.bill).count()
        self.assertEqual(invoice_count, 0)
    
    def test_create_invoices_from_bills_invalid_status(self):
        """Test invoice creation from bills with invalid status."""
        # Change bill status to draft (not eligible for invoice creation)
        self.bill.status = "draft"
        self.bill.save()
        
        result = self.service.create_invoices_from_bills(
            bill_ids=[str(self.bill.id)],
            dry_run=False
        )
        
        # Should not create any invoices
        self.assertEqual(result['invoices_created'], 0)
        self.assertEqual(result['invoices_failed'], 0)
    
    def test_create_invoices_duplicate_prevention(self):
        """Test that duplicate invoices are not created."""
        # Create invoice first time
        result1 = self.service.create_invoices_from_bills(
            bill_ids=[str(self.bill.id)],
            dry_run=False
        )
        self.assertEqual(result1['invoices_created'], 1)
        
        # Try to create again
        result2 = self.service.create_invoices_from_bills(
            bill_ids=[str(self.bill.id)],
            dry_run=False
        )
        
        # Should not create duplicate
        self.assertEqual(result2['invoices_created'], 0)
        
        # Verify only one invoice exists
        invoice_count = Invoice.objects.filter(bill=self.bill).count()
        self.assertEqual(invoice_count, 1)
    
    def test_review_and_approve_invoices_success(self):
        """Test successful invoice review and approval."""
        # Create invoice first
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
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
        
        result = self.service.review_and_approve_invoices(
            invoice_ids=[str(invoice.id)],
            user=self.staff_user,
            approved=True
        )
        
        # Verify result
        self.assertEqual(result['reviewed_count'], 1)
        self.assertEqual(result['failed_count'], 0)
        self.assertEqual(len(result['errors']), 0)
        
        # Verify invoice status changed
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "review")
    
    def test_review_and_reject_invoices(self):
        """Test invoice rejection."""
        # Create invoice first
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
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
        
        result = self.service.review_and_approve_invoices(
            invoice_ids=[str(invoice.id)],
            user=self.staff_user,
            approved=False
        )
        
        # Verify result
        self.assertEqual(result['reviewed_count'], 1)
        self.assertEqual(result['failed_count'], 0)
        
        # Verify invoice status changed to cancelled
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "cancelled")
    
    def test_finalize_invoices_success(self):
        """Test successful invoice finalization."""
        # Create invoice in review status
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
            invoice_number="INV-001",
            status="review",
            payment_status="unpaid",
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00
        )
        
        result = self.service.finalize_invoices(
            invoice_ids=[str(invoice.id)],
            user=self.staff_user
        )
        
        # Verify result
        self.assertEqual(result['finalized_count'], 1)
        self.assertEqual(result['failed_count'], 0)
        
        # Verify invoice status and timestamp
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "finalized")
        self.assertIsNotNone(invoice.finalized_at)
    
    def test_finalize_invoices_invalid_status(self):
        """Test finalizing invoices with invalid status."""
        # Create invoice in draft status (not eligible for finalization)
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
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
        
        result = self.service.finalize_invoices(
            invoice_ids=[str(invoice.id)],
            user=self.staff_user
        )
        
        # Should not finalize any invoices
        self.assertEqual(result['finalized_count'], 0)
        self.assertEqual(result['failed_count'], 0)
        
        # Invoice status should remain unchanged
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "draft")
    
    @patch('finance.invoices.services.call_command')
    def test_generate_invoice_pdfs_success(self, mock_call_command):
        """Test successful PDF generation."""
        # Create finalized invoice
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
            invoice_number="INV-001",
            status="finalized",
            payment_status="unpaid",
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00,
            is_pdf_generated=False
        )
        
        # Mock successful PDF generation
        def mock_pdf_generation(*args, **kwargs):
            invoice.is_pdf_generated = True
            invoice.pdf_file_path = f"/app/media/invoices/{invoice.invoice_number}.pdf"
            invoice.save()
        
        mock_call_command.side_effect = mock_pdf_generation
        
        result = self.service.generate_invoice_pdfs(
            invoice_ids=[str(invoice.id)],
            dry_run=False
        )
        
        # Verify result
        self.assertEqual(result['pdfs_generated'], 1)
        self.assertEqual(result['pdfs_failed'], 0)
        
        # Verify PDF was marked as generated
        invoice.refresh_from_db()
        self.assertTrue(invoice.is_pdf_generated)
        self.assertIsNotNone(invoice.pdf_file_path)
    
    def test_generate_invoice_pdfs_dry_run(self):
        """Test PDF generation in dry run mode."""
        # Create finalized invoice
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
            invoice_number="INV-001",
            status="finalized",
            payment_status="unpaid",
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00,
            is_pdf_generated=False
        )
        
        result = self.service.generate_invoice_pdfs(
            invoice_ids=[str(invoice.id)],
            dry_run=True
        )
        
        # Should return simulated results
        self.assertEqual(result['pdfs_generated'], 1)
        self.assertEqual(result['pdfs_failed'], 0)
        
        # PDF should not actually be generated
        invoice.refresh_from_db()
        self.assertFalse(invoice.is_pdf_generated)
    
    @patch('finance.invoices.services.call_command')
    def test_send_invoice_emails_success(self, mock_call_command):
        """Test successful email sending."""
        # Create finalized invoice with PDF
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
            invoice_number="INV-001",
            status="finalized",
            payment_status="unpaid",
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=15.00,
            total_amount=115.00,
            amount_due=115.00,
            is_pdf_generated=True,
            is_emailed=False
        )
        
        # Mock successful email sending
        def mock_email_sending(*args, **kwargs):
            invoice.is_emailed = True
            invoice.save()
        
        mock_call_command.side_effect = mock_email_sending
        
        result = self.service.send_invoice_emails(
            invoice_ids=[str(invoice.id)],
            dry_run=False
        )
        
        # Verify result
        self.assertEqual(result['emails_sent'], 1)
        self.assertEqual(result['emails_failed'], 0)
        
        # Verify email was marked as sent
        invoice.refresh_from_db()
        self.assertTrue(invoice.is_emailed)
        self.assertEqual(invoice.status, "emailed")
        self.assertIsNotNone(invoice.emailed_at)
    
    def test_get_invoice_analytics(self):
        """Test getting invoice analytics."""
        # Create test invoices with different statuses
        Invoice.objects.create(
            tenant=self.tenant,
            bill=self.bill,
            customer=self.customer,
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
        
        analytics = self.service.get_invoice_analytics(tenant=self.tenant)
        
        # Verify analytics structure
        self.assertIn('total_invoices', analytics)
        self.assertIn('total_amount', analytics)
        self.assertIn('status_distribution', analytics)
        self.assertIn('payment_status_distribution', analytics)
        self.assertIn('service_breakdown', analytics)
        self.assertIn('monthly_trends', analytics)
        self.assertIn('generated_at', analytics)
        
        # Verify data
        self.assertEqual(analytics['total_invoices'], 1)
        self.assertGreater(analytics['total_amount'], 0)
        self.assertIsInstance(analytics['status_distribution'], dict)
        self.assertIsInstance(analytics['monthly_trends'], list)
    
    def test_create_invoice_from_bill_private_method(self):
        """Test the private method for creating invoice from bill."""
        invoice = self.service._create_invoice_from_bill(self.bill)
        
        # Verify invoice creation
        self.assertIsInstance(invoice, Invoice)
        self.assertEqual(invoice.bill, self.bill)
        self.assertEqual(invoice.customer, self.bill.customer)
        self.assertEqual(invoice.total_amount, self.bill.total_amount)
        self.assertEqual(invoice.invoice_number, f"INV-{self.bill.bill_number}")
        
        # Verify invoice lines were created
        invoice_lines = invoice.lines.all()
        self.assertEqual(invoice_lines.count(), 1)
        
        line = invoice_lines.first()
        self.assertEqual(line.description, self.bill_line.description)
        self.assertEqual(line.amount, self.bill_line.amount)
        self.assertEqual(line.service_type, self.bill_line.service_type)
