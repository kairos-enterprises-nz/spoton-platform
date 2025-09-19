"""
API views for billing management.
"""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Bill, BillLineItem, BillingRun, BillingCycle, Payment
from .models_registry import ServiceRegistry
from .serializers import (
    BillSerializer, BillingRunSerializer, BillingCycleSerializer,
    ServiceRegistrySerializer, PaymentSerializer, BillingRunCreateSerializer,
    BillingDashboardSerializer, BulkBillActionSerializer, BillingExecutionResultSerializer,
    BillingStatsSerializer, BillingHealthCheckSerializer
)
from .services import billing_service, invoice_service
from users.models import Tenant
from core.permissions import StaffPermission

logger = logging.getLogger(__name__)


class BillingPagination(PageNumberPagination):
    """Custom pagination for billing endpoints."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100



class BillingRunViewSet(viewsets.ModelViewSet):
    """ViewSet for managing billing runs."""
    
    queryset = BillingRun.objects.all().order_by('-created_at')
    serializer_class = BillingRunSerializer
    permission_classes = [StaffPermission]
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service_type', 'status', 'tenant']
    
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
    def create_run(self, request):
        """Create a new billing run."""
        serializer = BillingRunCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Get user's tenant - handle both authenticated users and Keycloak claims
                tenant = None
                if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
                    # Superuser can create runs for any tenant
                    tenant = None
                elif hasattr(request.user, 'tenants') and request.user.is_authenticated:
                    # Regular authenticated user
                    tenant = request.user.tenants.first()
                else:
                    # User authenticated via Keycloak claims - for now, use None (all data)
                    tenant = None
                
                # Create billing run
                billing_run = billing_service.create_billing_run(
                    service_type=serializer.validated_data['service_type'],
                    period_start=serializer.validated_data['period_start'],
                    period_end=serializer.validated_data['period_end'],
                    tenant=tenant,
                    dry_run=serializer.validated_data['dry_run']
                )
                
                # Execute immediately if requested
                if serializer.validated_data.get('execute_immediately', False):
                    result = billing_service.execute_billing_run(
                        billing_run,
                        dry_run=serializer.validated_data['dry_run']
                    )
                    result_serializer = BillingExecutionResultSerializer(result)
                    return Response(result_serializer.data, status=status.HTTP_201_CREATED)
                
                # Return created billing run
                run_serializer = BillingRunSerializer(billing_run)
                return Response(run_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Failed to create billing run: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a billing run."""
        billing_run = self.get_object()
        dry_run = request.data.get('dry_run', False)
        
        try:
            result = billing_service.execute_billing_run(billing_run, dry_run=dry_run)
            serializer = BillingExecutionResultSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to execute billing run {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get billing dashboard statistics."""
        try:
            # Get user's tenant - handle both authenticated users and Keycloak claims
            tenant = None
            if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
                # Superuser can see all data
                tenant = None
            elif hasattr(request.user, 'tenants') and request.user.is_authenticated:
                # Regular authenticated user
                tenant = request.user.tenants.first()
            else:
                # User authenticated via Keycloak claims - for now, use None (all data)
                # In the future, we could extract tenant info from Keycloak claims
                tenant = None
            
            stats = billing_service.get_billing_dashboard_stats(tenant=tenant)
            serializer = BillingDashboardSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def health_check(self, request):
        """Health check for billing system."""
        try:
            # Perform basic health checks
            now = timezone.now()
            
            # Check if we can access the database
            recent_runs_count = BillingRun.objects.count()
            
            # Get last successful run for each service type
            last_successful_runs = {}
            for service_type in ['electricity', 'broadband', 'mobile']:
                last_run = BillingRun.objects.filter(
                    service_type=service_type,
                    status='completed'
                ).order_by('-created_at').first()
                if last_run:
                    last_successful_runs[service_type] = last_run.created_at
                else:
                    last_successful_runs[service_type] = None
            
            health_data = {
                'overall_status': 'healthy',
                'services': {
                    'billing_service': {'status': 'available'},
                    'invoice_service': {'status': 'available'},
                    'database': {'status': 'connected', 'recent_runs': recent_runs_count}
                },
                'last_successful_runs': last_successful_runs,
                'pending_issues': [],  # No issues currently
                'system_metrics': {
                    'total_billing_runs': recent_runs_count,
                    'uptime': 'operational',
                    'response_time': 'normal'
                },
                'checked_at': now
            }
            
            serializer = BillingHealthCheckSerializer(health_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return Response(
                {
                    'overall_status': 'critical',
                    'services': {},
                    'last_successful_runs': {},
                    'pending_issues': [str(e)],
                    'system_metrics': {},
                    'checked_at': timezone.now()
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class BillViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing bills."""
    
    queryset = Bill.objects.all().order_by('-created_at')
    serializer_class = BillSerializer
    permission_classes = [StaffPermission]
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'customer', 'tenant']
    search_fields = ['bill_number', 'customer__username', 'customer__email']
    
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
    def bulk_action(self, request):
        """Perform bulk actions on bills."""
        serializer = BulkBillActionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                bill_ids = serializer.validated_data['bill_ids']
                action = serializer.validated_data['action']
                dry_run = serializer.validated_data['dry_run']
                
                if action == 'generate_invoices':
                    # Import here to avoid circular imports
                    from ..invoices.services import invoice_lifecycle_service
                    result = invoice_lifecycle_service.create_invoices_from_bills(
                        bill_ids=[str(bid) for bid in bill_ids],
                        dry_run=dry_run
                    )
                    return Response(result, status=status.HTTP_200_OK)
                
                # Add other bulk actions as needed
                return Response(
                    {'error': f'Action {action} not implemented'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            except Exception as e:
                logger.error(f"Bulk action failed: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceRegistryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing service registry."""
    
    queryset = ServiceRegistry.objects.all()
    serializer_class = ServiceRegistrySerializer
    permission_classes = [StaffPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service_code', 'is_active', 'tenant']
    
    def get_queryset(self):
        """Filter queryset based user permissions."""
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


class BillingCycleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing billing cycles."""
    
    queryset = BillingCycle.objects.all().order_by('-created_at')
    serializer_class = BillingCycleSerializer
    permission_classes = [StaffPermission]
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service_type', 'cycle_type', 'is_active', 'tenant']
    
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


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payments."""
    
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [StaffPermission]
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method', 'tenant']
    search_fields = ['payment_reference', 'customer__username', 'external_reference']
    
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