"""
Invoice management services for handling invoice lifecycle operations.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.db import transaction, models
from django.core.management import call_command
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Invoice, InvoiceLine
from ..billing.models import Bill, BillingRun
from users.models import User, Tenant

logger = logging.getLogger(__name__)


class InvoiceLifecycleService:
    """Manages the complete invoice lifecycle from draft to delivery."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_invoices_from_bills(self, bill_ids: List[str], dry_run: bool = False) -> Dict:
        """
        Create draft invoices from finalized bills.
        
        Args:
            bill_ids: List of bill IDs to create invoices from
            dry_run: Whether to perform a dry run
            
        Returns:
            Dict: Creation results with statistics
        """
        self.logger.info(f"Creating invoices from {len(bill_ids)} bills")
        
        results = {
            'invoices_created': 0,
            'invoices_failed': 0,
            'total_amount': 0,
            'errors': []
        }
        
        try:
            bills = Bill.objects.filter(
                id__in=bill_ids,
                status__in=['issued', 'pending']
            ).exclude(
                id__in=Invoice.objects.values_list('bill_id', flat=True)
            )
            
            if dry_run:
                results['invoices_created'] = bills.count()
                results['total_amount'] = sum(float(bill.total_amount) for bill in bills)
                self.logger.info(f"Dry run: would create {results['invoices_created']} invoices")
                return results
            
            with transaction.atomic():
                for bill in bills:
                    try:
                        invoice = self._create_invoice_from_bill(bill)
                        results['invoices_created'] += 1
                        results['total_amount'] += float(invoice.total_amount)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to create invoice from bill {bill.id}: {str(e)}")
                        results['invoices_failed'] += 1
                        results['errors'].append(f"Bill {bill.bill_number}: {str(e)}")
            
            self.logger.info(f"Created {results['invoices_created']} invoices")
            
        except Exception as e:
            self.logger.error(f"Failed to create invoices from bills: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def review_and_approve_invoices(self, invoice_ids: List[str], user: User, 
                                  approved: bool = True) -> Dict:
        """
        Review and approve/reject invoices.
        
        Args:
            invoice_ids: List of invoice IDs to review
            user: User performing the review
            approved: Whether invoices are approved
            
        Returns:
            Dict: Review results
        """
        self.logger.info(f"Reviewing {len(invoice_ids)} invoices (approved: {approved})")
        
        results = {
            'reviewed_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        try:
            with transaction.atomic():
                invoices = Invoice.objects.filter(
                    id__in=invoice_ids,
                    status='draft'
                )
                
                for invoice in invoices:
                    try:
                        invoice.status = 'review' if approved else 'cancelled'
                        invoice.save()
                        
                        # Log the review action
                        self.logger.info(f"Invoice {invoice.invoice_number} {'approved' if approved else 'rejected'} by {user.username}")
                        results['reviewed_count'] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to review invoice {invoice.id}: {str(e)}")
                        results['failed_count'] += 1
                        results['errors'].append(f"Invoice {invoice.invoice_number}: {str(e)}")
                
            self.logger.info(f"Reviewed {results['reviewed_count']} invoices")
            
        except Exception as e:
            self.logger.error(f"Failed to review invoices: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def finalize_invoices(self, invoice_ids: List[str], user: User) -> Dict:
        """
        Finalize reviewed invoices for delivery.
        
        Args:
            invoice_ids: List of invoice IDs to finalize
            user: User performing the action
            
        Returns:
            Dict: Finalization results
        """
        self.logger.info(f"Finalizing {len(invoice_ids)} invoices")
        
        results = {
            'finalized_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        try:
            with transaction.atomic():
                invoices = Invoice.objects.filter(
                    id__in=invoice_ids,
                    status='review'
                )
                
                for invoice in invoices:
                    try:
                        invoice.status = 'finalized'
                        invoice.finalized_at = timezone.now()
                        invoice.save()
                        
                        self.logger.info(f"Invoice {invoice.invoice_number} finalized by {user.username}")
                        results['finalized_count'] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to finalize invoice {invoice.id}: {str(e)}")
                        results['failed_count'] += 1
                        results['errors'].append(f"Invoice {invoice.invoice_number}: {str(e)}")
                
            self.logger.info(f"Finalized {results['finalized_count']} invoices")
            
        except Exception as e:
            self.logger.error(f"Failed to finalize invoices: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def generate_invoice_pdfs(self, invoice_ids: List[str], dry_run: bool = False) -> Dict:
        """
        Generate PDF files for finalized invoices.
        
        Args:
            invoice_ids: List of invoice IDs to generate PDFs for
            dry_run: Whether to perform a dry run
            
        Returns:
            Dict: PDF generation results
        """
        self.logger.info(f"Generating PDFs for {len(invoice_ids)} invoices")
        
        results = {
            'pdfs_generated': 0,
            'pdfs_failed': 0,
            'errors': []
        }
        
        try:
            invoices = Invoice.objects.filter(
                id__in=invoice_ids,
                status='finalized',
                is_pdf_generated=False
            )
            
            if dry_run:
                results['pdfs_generated'] = invoices.count()
                self.logger.info(f"Dry run: would generate {results['pdfs_generated']} PDFs")
                return results
            
            # Use management command for PDF generation
            call_command('generate_pdfs')
            
            # Check which PDFs were successfully generated
            for invoice in invoices:
                try:
                    invoice.refresh_from_db()
                    if invoice.is_pdf_generated:
                        results['pdfs_generated'] += 1
                    else:
                        results['pdfs_failed'] += 1
                        results['errors'].append(f"PDF generation failed for invoice {invoice.invoice_number}")
                        
                except Exception as e:
                    results['pdfs_failed'] += 1
                    results['errors'].append(f"Invoice {invoice.invoice_number}: {str(e)}")
            
            self.logger.info(f"Generated {results['pdfs_generated']} PDFs")
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDFs: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def send_invoice_emails(self, invoice_ids: List[str], dry_run: bool = False) -> Dict:
        """
        Send invoice emails to customers.
        
        Args:
            invoice_ids: List of invoice IDs to send emails for
            dry_run: Whether to perform a dry run
            
        Returns:
            Dict: Email sending results
        """
        self.logger.info(f"Sending emails for {len(invoice_ids)} invoices")
        
        results = {
            'emails_sent': 0,
            'emails_failed': 0,
            'errors': []
        }
        
        try:
            invoices = Invoice.objects.filter(
                id__in=invoice_ids,
                status='finalized',
                is_pdf_generated=True,
                is_emailed=False
            )
            
            if dry_run:
                results['emails_sent'] = invoices.count()
                self.logger.info(f"Dry run: would send {results['emails_sent']} emails")
                return results
            
            # Use management command for email sending
            call_command('send_invoice_emails', '--dry-run' if dry_run else '')
            
            # Check which emails were successfully sent
            for invoice in invoices:
                try:
                    invoice.refresh_from_db()
                    if invoice.is_emailed:
                        invoice.status = 'emailed'
                        invoice.emailed_at = timezone.now()
                        invoice.save()
                        results['emails_sent'] += 1
                    else:
                        results['emails_failed'] += 1
                        results['errors'].append(f"Email sending failed for invoice {invoice.invoice_number}")
                        
                except Exception as e:
                    results['emails_failed'] += 1
                    results['errors'].append(f"Invoice {invoice.invoice_number}: {str(e)}")
            
            self.logger.info(f"Sent {results['emails_sent']} emails")
            
        except Exception as e:
            self.logger.error(f"Failed to send emails: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def get_invoice_analytics(self, tenant: Optional[Tenant] = None, 
                            date_from: Optional[datetime] = None,
                            date_to: Optional[datetime] = None) -> Dict:
        """
        Get comprehensive invoice analytics and metrics.
        
        Args:
            tenant: Optional tenant for multi-tenancy
            date_from: Start date for analytics
            date_to: End date for analytics
            
        Returns:
            Dict: Analytics data
        """
        try:
            queryset = Invoice.objects.filter(tenant=tenant)
            
            if date_from:
                queryset = queryset.filter(issue_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(issue_date__lte=date_to)
            
            # Status distribution
            status_counts = {}
            for status, _ in Invoice.INVOICE_STATUS_CHOICES:
                status_counts[status] = queryset.filter(status=status).count()
            
            # Payment status distribution
            payment_status_counts = {}
            for status, _ in Invoice.PAYMENT_STATUS_CHOICES:
                payment_status_counts[status] = queryset.filter(payment_status=status).count()
            
            # Service type breakdown
            service_breakdown = queryset.values(
                'lines__service_type'
            ).annotate(
                count=models.Count('id'),
                total_amount=models.Sum('total_amount')
            )
            
            # Monthly trends (last 12 months)
            monthly_trends = []
            for i in range(12):
                month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
                month_end = month_start + timedelta(days=31)
                
                month_data = queryset.filter(
                    issue_date__gte=month_start,
                    issue_date__lt=month_end
                ).aggregate(
                    count=models.Count('id'),
                    total_amount=models.Sum('total_amount')
                )
                
                monthly_trends.append({
                    'month': month_start.strftime('%Y-%m'),
                    'count': month_data['count'] or 0,
                    'total_amount': float(month_data['total_amount'] or 0)
                })
            
            # Performance metrics
            avg_processing_time = queryset.filter(
                finalized_at__isnull=False
            ).aggregate(
                avg_time=models.Avg(
                    models.F('finalized_at') - models.F('created_at')
                )
            )['avg_time']
            
            analytics = {
                'total_invoices': queryset.count(),
                'total_amount': float(queryset.aggregate(
                    total=models.Sum('total_amount')
                )['total'] or 0),
                'status_distribution': status_counts,
                'payment_status_distribution': payment_status_counts,
                'service_breakdown': list(service_breakdown),
                'monthly_trends': monthly_trends,
                'avg_processing_time_hours': avg_processing_time.total_seconds() / 3600 if avg_processing_time else 0,
                'generated_at': timezone.now()
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get invoice analytics: {str(e)}")
            return {'error': str(e)}
    
    def _create_invoice_from_bill(self, bill: Bill) -> Invoice:
        """Create an invoice from a bill with all line items."""
        # Generate invoice number
        invoice_number = f"INV-{bill.bill_number}"
        
        # Create invoice
        invoice = Invoice.objects.create(
            tenant=bill.tenant,
            bill=bill,
            customer=bill.customer,
            invoice_number=invoice_number,
            status='draft',
            payment_status='unpaid',
            issue_date=bill.issue_date,
            due_date=bill.due_date,
            subtotal=bill.subtotal,
            tax_amount=bill.tax_amount,
            total_amount=bill.total_amount,
            amount_paid=bill.amount_paid,
            amount_due=bill.amount_due
        )
        
        # Create invoice lines from bill line items
        for bill_line in bill.line_items.all():
            InvoiceLine.objects.create(
                tenant=bill.tenant,
                invoice=invoice,
                description=bill_line.description,
                service_type=bill_line.service_type,
                quantity=bill_line.quantity,
                unit=bill_line.unit,
                unit_price=bill_line.unit_price,
                amount=bill_line.amount,
                service_period_start=bill_line.service_period_start,
                service_period_end=bill_line.service_period_end,
                is_taxable=bill_line.is_taxable,
                tax_rate=bill_line.tax_rate,
                tax_amount=bill_line.tax_amount,
                sort_order=bill_line.sort_order
            )
        
        return invoice


# Service instance for easy import
invoice_lifecycle_service = InvoiceLifecycleService()
