"""
API views for invoice management.
"""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone

from .models import Invoice, InvoiceLine
from .serializers import (
    InvoiceSerializer, InvoiceListSerializer, InvoiceCreateSerializer,
    InvoiceActionSerializer, InvoiceAnalyticsSerializer, InvoicePDFSerializer,
    InvoiceEmailSerializer, BulkInvoiceActionResultSerializer
)
from .services import invoice_lifecycle_service
from core.permissions import StaffPermission

logger = logging.getLogger(__name__)


class InvoicePagination(PageNumberPagination):
    """Custom pagination for invoice endpoints."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsStaffUser(permissions.BasePermission):
    """Permission class for staff users only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing invoices."""
    
    queryset = Invoice.objects.all().order_by('-created_at')
    permission_classes = [StaffPermission]
    pagination_class = InvoicePagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_status', 'customer', 'tenant']
    search_fields = ['invoice_number', 'customer__username', 'customer__email']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Handle both authenticated users and Keycloak claims
        if hasattr(self.request.user, 'is_superuser') and self.request.user.is_superuser:
            # Superuser can see all data
            pass
        elif hasattr(self.request.user, 'tenants') and self.request.user.is_authenticated:
            # Regular authenticated user
            user_tenants = self.request.user.tenants.all()
            queryset = queryset.filter(tenant__in=user_tenants)
        else:
            # User authenticated via Keycloak claims - for now, show all data
            # In the future, we could extract tenant info from Keycloak claims
            pass
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def create_from_bills(self, request):
        """Create invoices from bills."""
        serializer = InvoiceCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                result = invoice_lifecycle_service.create_invoices_from_bills(
                    bill_ids=[str(bid) for bid in serializer.validated_data['bill_ids']],
                    dry_run=serializer.validated_data['dry_run']
                )
                return Response(result, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Failed to create invoices from bills: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on invoices."""
        serializer = InvoiceActionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                invoice_ids = [str(iid) for iid in serializer.validated_data['invoice_ids']]
                action = serializer.validated_data['action']
                dry_run = serializer.validated_data['dry_run']
                approved = serializer.validated_data.get('approved', True)
                
                start_time = timezone.now()
                
                if action == 'review':
                    result = invoice_lifecycle_service.review_and_approve_invoices(
                        invoice_ids=invoice_ids,
                        user=request.user,
                        approved=approved
                    )
                elif action == 'finalize':
                    result = invoice_lifecycle_service.finalize_invoices(
                        invoice_ids=invoice_ids,
                        user=request.user
                    )
                elif action == 'generate_pdf':
                    result = invoice_lifecycle_service.generate_invoice_pdfs(
                        invoice_ids=invoice_ids,
                        dry_run=dry_run
                    )
                elif action == 'send_email':
                    result = invoice_lifecycle_service.send_invoice_emails(
                        invoice_ids=invoice_ids,
                        dry_run=dry_run
                    )
                else:
                    return Response(
                        {'error': f'Action {action} not implemented'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                execution_time = (timezone.now() - start_time).total_seconds()
                
                # Format result for response
                bulk_result = {
                    'action': action,
                    'total_requested': len(invoice_ids),
                    'successful_count': result.get('finalized_count', result.get('reviewed_count', result.get('pdfs_generated', result.get('emails_sent', 0)))),
                    'failed_count': result.get('failed_count', result.get('pdfs_failed', result.get('emails_failed', 0))),
                    'errors': result.get('errors', []),
                    'processed_invoices': invoice_ids[:result.get('successful_count', 0)],
                    'failed_invoices': invoice_ids[result.get('successful_count', 0):],
                    'execution_time_seconds': execution_time,
                    'dry_run': dry_run
                }
                
                result_serializer = BulkInvoiceActionResultSerializer(bulk_result)
                return Response(result_serializer.data, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Bulk invoice action failed: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generate_pdfs(self, request):
        """Generate PDFs for invoices."""
        serializer = InvoicePDFSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                result = invoice_lifecycle_service.generate_invoice_pdfs(
                    invoice_ids=[str(iid) for iid in serializer.validated_data['invoice_ids']],
                    dry_run=request.data.get('dry_run', False)
                )
                return Response(result, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"PDF generation failed: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def send_emails(self, request):
        """Send invoice emails."""
        serializer = InvoiceEmailSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                result = invoice_lifecycle_service.send_invoice_emails(
                    invoice_ids=[str(iid) for iid in serializer.validated_data['invoice_ids']],
                    dry_run=request.data.get('dry_run', False)
                )
                return Response(result, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download invoice PDF."""
        invoice = self.get_object()
        
        if not invoice.is_pdf_generated or not invoice.pdf_file_path:
            return Response(
                {'error': 'PDF not available for this invoice'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # In a real implementation, you would read the PDF file and return it
            # For now, we'll return a placeholder response
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
            response.write(b'PDF content would be here')
            return response
            
        except Exception as e:
            logger.error(f"Failed to download PDF for invoice {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get invoice analytics."""
        try:
            # Get user's tenant
            tenant = None
            if not request.user.is_superuser:
                tenant = request.user.tenants.first()
            
            # Get date filters from query params
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            analytics = invoice_lifecycle_service.get_invoice_analytics(
                tenant=tenant,
                date_from=timezone.datetime.fromisoformat(date_from) if date_from else None,
                date_to=timezone.datetime.fromisoformat(date_to) if date_to else None
            )
            
            serializer = InvoiceAnalyticsSerializer(analytics)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get invoice analytics: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
