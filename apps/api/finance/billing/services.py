"""
Billing orchestration services for managing the complete billing workflow.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from django.db import transaction, models
from django.core.management import call_command
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Bill, BillLineItem, BillingRun, BillingCycle
from .models_registry import ServiceRegistry
from ..invoices.models import Invoice, InvoiceLine
from users.models import User, Tenant

logger = logging.getLogger(__name__)


class BillingOrchestrationService:
    """Orchestrates the complete billing workflow with proper error handling and logging."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_billing_run(self, service_type: str, period_start: datetime, 
                          period_end: datetime, tenant: Optional[Tenant] = None,
                          dry_run: bool = False) -> BillingRun:
        """
        Create and prepare a billing run with proper validation.
        
        Args:
            service_type: The service type (electricity, broadband, mobile)
            period_start: Start of billing period
            period_end: End of billing period
            tenant: Optional tenant for multi-tenancy
            dry_run: Whether this is a dry run (no actual changes)
            
        Returns:
            BillingRun: Created billing run instance
            
        Raises:
            ValidationError: If parameters are invalid
            ValueError: If service registry not found
        """
        self.logger.info(f"Creating billing run for {service_type} from {period_start} to {period_end}")
        
        # Validate inputs
        self._validate_billing_run_params(service_type, period_start, period_end)
        
        # Check if service is registered and active
        service_registry = ServiceRegistry.objects.filter(
            service_code=service_type, 
            is_active=True,
            tenant=tenant
        ).first()
        
        if not service_registry:
            raise ValueError(f"No active service registry found for {service_type}")
        
        # Check for existing billing run in the same period
        existing_run = BillingRun.objects.filter(
            tenant=tenant,
            service_type=service_type,
            period_start=period_start,
            period_end=period_end,
            status__in=['pending', 'running', 'completed']
        ).first()
        
        if existing_run:
            self.logger.warning(f"Existing billing run found: {existing_run.id}")
            return existing_run
        
        # Create billing run
        run_name = f"{service_type.title()} Billing - {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        if dry_run:
            run_name += " (DRY RUN)"
            
        billing_run = BillingRun.objects.create(
            tenant=tenant,
            run_name=run_name,
            service_type=service_type,
            period_start=period_start,
            period_end=period_end,
            run_date=timezone.now(),
            status='pending',
            idempotency_key=f"{tenant.id if tenant else 'global'}|{service_type}|{period_start.isoformat()}|{period_end.isoformat()}"
        )
        
        self.logger.info(f"Created billing run: {billing_run.id}")
        return billing_run
    
    def execute_billing_run(self, billing_run: BillingRun, dry_run: bool = False) -> Dict:
        """
        Execute a billing run with comprehensive error handling and progress tracking.
        
        Args:
            billing_run: The billing run to execute
            dry_run: Whether to perform a dry run
            
        Returns:
            Dict: Execution results with statistics
        """
        self.logger.info(f"Executing billing run: {billing_run.id}")
        
        if billing_run.status not in ['pending', 'failed']:
            raise ValidationError(f"Cannot execute billing run in status: {billing_run.status}")
        
        results = {
            'billing_run_id': str(billing_run.id),
            'service_type': billing_run.service_type,
            'period_start': billing_run.period_start,
            'period_end': billing_run.period_end,
            'dry_run': dry_run,
            'started_at': timezone.now(),
            'bills_created': 0,
            'bills_failed': 0,
            'total_amount': 0,
            'errors': []
        }
        
        try:
            # Update status to running
            billing_run.status = 'running'
            billing_run.started_at = timezone.now()
            billing_run.save()
            
            # Calculate bills for the service and period
            bills_result = self.calculate_bills_for_service(
                billing_run.service_type,
                billing_run.period_start,
                billing_run.period_end,
                billing_run.tenant,
                dry_run
            )
            
            results.update(bills_result)
            
            # Update billing run with results
            billing_run.bills_generated = results['bills_created']
            billing_run.bills_failed = results['bills_failed']
            billing_run.total_billed_amount = results['total_amount']
            billing_run.status = 'completed' if results['bills_failed'] == 0 else 'failed'
            billing_run.completed_at = timezone.now()
            billing_run.error_log = '\n'.join(results['errors']) if results['errors'] else ''
            billing_run.save()
            
            results['completed_at'] = billing_run.completed_at
            results['status'] = billing_run.status
            
            self.logger.info(f"Billing run {billing_run.id} completed with {results['bills_created']} bills created")
            
        except Exception as e:
            self.logger.error(f"Billing run {billing_run.id} failed: {str(e)}")
            billing_run.status = 'failed'
            billing_run.completed_at = timezone.now()
            billing_run.error_log = str(e)
            billing_run.save()
            results['status'] = 'failed'
            results['errors'].append(str(e))
            raise
        
        return results
    
    def calculate_bills_for_service(self, service_type: str, period_start: datetime,
                                  period_end: datetime, tenant: Optional[Tenant] = None,
                                  dry_run: bool = False) -> Dict:
        """
        Calculate bills for a specific service and period using the service handler.
        
        Args:
            service_type: Service type to calculate bills for
            period_start: Start of billing period
            period_end: End of billing period
            tenant: Optional tenant for multi-tenancy
            dry_run: Whether to perform a dry run
            
        Returns:
            Dict: Calculation results with statistics
        """
        self.logger.info(f"Calculating bills for {service_type} from {period_start} to {period_end}")
        
        # Get service registry
        service_registry = ServiceRegistry.objects.filter(
            service_code=service_type,
            is_active=True,
            tenant=tenant
        ).first()
        
        if not service_registry:
            raise ValueError(f"No active service registry found for {service_type}")
        
        results = {
            'bills_created': 0,
            'bills_failed': 0,
            'total_amount': 0,
            'errors': []
        }
        
        try:
            # Use management command to calculate bills
            if dry_run:
                self.logger.info("Performing dry run - no bills will be created")
                # For dry run, we simulate the process
                results['bills_created'] = 3  # Simulated count
                results['total_amount'] = 500.00  # Simulated amount
            else:
                # Call the existing management command
                call_command(
                    'calculate_bills',
                    service=service_type,
                    date=period_start.date().isoformat()
                )
                
                # Count the bills created in this period
                bills_count = Bill.objects.filter(
                    tenant=tenant,
                    period_start__gte=period_start,
                    period_end__lte=period_end,
                    status='draft'
                ).count()
                
                total_amount = Bill.objects.filter(
                    tenant=tenant,
                    period_start__gte=period_start,
                    period_end__lte=period_end,
                    status='draft'
                ).aggregate(total=models.Sum('total_amount'))['total'] or 0
                
                results['bills_created'] = bills_count
                results['total_amount'] = float(total_amount)
                
        except Exception as e:
            self.logger.error(f"Failed to calculate bills for {service_type}: {str(e)}")
            results['bills_failed'] = 1
            results['errors'].append(str(e))
            raise
        
        return results
    
    def get_billing_dashboard_stats(self, tenant: Optional[Tenant] = None) -> Dict:
        """
        Get comprehensive dashboard statistics for billing operations.
        
        Args:
            tenant: Optional tenant for multi-tenancy
            
        Returns:
            Dict: Dashboard statistics
        """
        stats = {}
        
        try:
            # Active billing runs
            active_runs = BillingRun.objects.filter(
                tenant=tenant,
                status__in=['pending', 'running']
            ).count()
            
            # Pending bills
            pending_bills = Bill.objects.filter(
                tenant=tenant,
                status='draft'
            ).count()
            
            # Recent activity (last 24 hours)
            yesterday = timezone.now() - timedelta(days=1)
            recent_runs = BillingRun.objects.filter(
                tenant=tenant,
                created_at__gte=yesterday
            ).order_by('-created_at')[:10]
            
            recent_activity = []
            for run in recent_runs:
                recent_activity.append({
                    'id': str(run.id),
                    'service_type': run.service_type,
                    'status': run.status,
                    'created_at': run.created_at,
                    'bills_generated': run.bills_generated,
                    'total_amount': float(run.total_billed_amount)
                })
            
            # Service status
            service_status = {}
            for service_type in ['electricity', 'broadband', 'mobile']:
                last_run = BillingRun.objects.filter(
                    tenant=tenant,
                    service_type=service_type
                ).order_by('-created_at').first()
                
                service_status[service_type] = {
                    'last_run': last_run.created_at if last_run else None,
                    'last_status': last_run.status if last_run else 'never_run',
                    'is_healthy': last_run.status == 'completed' if last_run else False
                }
            
            stats = {
                'active_runs': active_runs,
                'pending_bills': pending_bills,
                'recent_activity': recent_activity,
                'service_status': service_status,
                'last_updated': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard stats: {str(e)}")
            stats = {
                'error': str(e),
                'last_updated': timezone.now()
            }
        
        return stats
    
    def _validate_billing_run_params(self, service_type: str, period_start: datetime, period_end: datetime):
        """Validate billing run parameters."""
        if service_type not in ['electricity', 'broadband', 'mobile']:
            raise ValidationError(f"Invalid service type: {service_type}")
        
        if period_start >= period_end:
            raise ValidationError("Period start must be before period end")
        
        if period_end > timezone.now():
            raise ValidationError("Period end cannot be in the future")
        
        # Check if period is reasonable (not more than 1 year)
        if (period_end - period_start).days > 365:
            raise ValidationError("Billing period cannot exceed 365 days")


class InvoiceManagementService:
    """Manages invoice lifecycle operations with proper error handling."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_invoices_from_bills(self, billing_run_id: str, dry_run: bool = False) -> Dict:
        """
        Generate draft invoices from calculated bills.
        
        Args:
            billing_run_id: ID of the billing run
            dry_run: Whether to perform a dry run
            
        Returns:
            Dict: Generation results with statistics
        """
        self.logger.info(f"Generating invoices for billing run: {billing_run_id}")
        
        results = {
            'billing_run_id': billing_run_id,
            'invoices_created': 0,
            'invoices_failed': 0,
            'total_amount': 0,
            'errors': []
        }
        
        try:
            billing_run = BillingRun.objects.get(id=billing_run_id)
            
            # Get bills from this billing run that don't have invoices
            bills = Bill.objects.filter(
                tenant=billing_run.tenant,
                period_start=billing_run.period_start,
                period_end=billing_run.period_end,
                status='draft'
            ).exclude(
                id__in=Invoice.objects.values_list('bill_id', flat=True)
            )
            
            if dry_run:
                self.logger.info(f"Dry run: would create {bills.count()} invoices")
                results['invoices_created'] = bills.count()
                results['total_amount'] = sum(float(bill.total_amount) for bill in bills)
                return results
            
            # Generate invoices using management command
            call_command('generate_draft_invoices')
            
            # Count created invoices
            invoices = Invoice.objects.filter(
                bill__in=bills,
                status='draft'
            )
            
            results['invoices_created'] = invoices.count()
            results['total_amount'] = sum(float(inv.total_amount) for inv in invoices)
            
            self.logger.info(f"Generated {results['invoices_created']} invoices")
            
        except Exception as e:
            self.logger.error(f"Failed to generate invoices: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def finalize_invoices(self, invoice_ids: List[str], user: User) -> Dict:
        """
        Finalize invoices and prepare for delivery.
        
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
                    status='draft'
                )
                
                for invoice in invoices:
                    try:
                        invoice.status = 'finalized'
                        invoice.finalized_at = timezone.now()
                        invoice.save()
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
    
    def generate_pdfs(self, invoice_ids: List[str], dry_run: bool = False) -> Dict:
        """
        Generate PDFs for invoices with progress tracking.
        
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
            if dry_run:
                self.logger.info("Dry run: would generate PDFs")
                results['pdfs_generated'] = len(invoice_ids)
                return results
            
            # Use management command for PDF generation
            call_command('generate_pdfs')
            
            # Update results based on successful PDF generation
            invoices = Invoice.objects.filter(
                id__in=invoice_ids,
                is_pdf_generated=True
            )
            
            results['pdfs_generated'] = invoices.count()
            results['pdfs_failed'] = len(invoice_ids) - results['pdfs_generated']
            
            self.logger.info(f"Generated {results['pdfs_generated']} PDFs")
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDFs: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def send_invoice_emails(self, invoice_ids: List[str], dry_run: bool = False) -> Dict:
        """
        Send invoice emails with delivery tracking.
        
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
            if dry_run:
                self.logger.info("Dry run: would send emails")
                results['emails_sent'] = len(invoice_ids)
                return results
            
            # Use management command for email sending
            call_command('send_invoice_emails', '--dry-run' if dry_run else '')
            
            # Update results based on successful email sending
            invoices = Invoice.objects.filter(
                id__in=invoice_ids,
                is_emailed=True
            )
            
            results['emails_sent'] = invoices.count()
            results['emails_failed'] = len(invoice_ids) - results['emails_sent']
            
            self.logger.info(f"Sent {results['emails_sent']} emails")
            
        except Exception as e:
            self.logger.error(f"Failed to send emails: {str(e)}")
            results['errors'].append(str(e))
            raise
        
        return results
    
    def get_invoice_status_summary(self, tenant: Optional[Tenant] = None, filters: Optional[Dict] = None) -> Dict:
        """
        Get summary of invoice statuses for dashboard.
        
        Args:
            tenant: Optional tenant for multi-tenancy
            filters: Optional filters to apply
            
        Returns:
            Dict: Invoice status summary
        """
        try:
            queryset = Invoice.objects.filter(tenant=tenant)
            
            if filters:
                if filters.get('service_type'):
                    queryset = queryset.filter(lines__service_type=filters['service_type'])
                if filters.get('date_from'):
                    queryset = queryset.filter(issue_date__gte=filters['date_from'])
                if filters.get('date_to'):
                    queryset = queryset.filter(issue_date__lte=filters['date_to'])
            
            # Status breakdown
            status_counts = {}
            for status, _ in Invoice.INVOICE_STATUS_CHOICES:
                status_counts[status] = queryset.filter(status=status).count()
            
            # Payment status breakdown
            payment_status_counts = {}
            for status, _ in Invoice.PAYMENT_STATUS_CHOICES:
                payment_status_counts[status] = queryset.filter(payment_status=status).count()
            
            # Total amounts
            total_amount = queryset.aggregate(
                total=models.Sum('total_amount')
            )['total'] or 0
            
            summary = {
                'total_invoices': queryset.count(),
                'status_breakdown': status_counts,
                'payment_status_breakdown': payment_status_counts,
                'total_amount': float(total_amount),
                'last_updated': timezone.now()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get invoice status summary: {str(e)}")
            return {'error': str(e)}


# Service instances for easy import
billing_service = BillingOrchestrationService()
invoice_service = InvoiceManagementService()
