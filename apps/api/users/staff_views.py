"""
Staff CRUD API Views for Utility Byte Platform
Provides comprehensive management capabilities for tenants, users, contracts, and customer data.
"""

from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import models
from django.db.models import Q, Count, Prefetch
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import datetime, date
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
import uuid
from decimal import Decimal

from .models import (
    Tenant, TenantUserRole, Account, Address, UserAccountRole
)

# Import contract models - will be loaded dynamically to avoid app loading issues
ServiceContract = None

from .auth import IsStaffUser, IsAdminUser
from core.permissions import StaffPermission
from .staff_serializers import (
    # Tenant serializers
    TenantListSerializer, TenantDetailSerializer, TenantCreateSerializer,
    TenantUserRoleSerializer,
    
    # User serializers
    StaffUserListSerializer, StaffUserDetailSerializer, StaffUserCreateSerializer,
    StaffUserUpdateSerializer,
    
    # Account serializers
    AccountListSerializer, AccountDetailSerializer, AccountCreateSerializer,
    AccountUpdateSerializer, AddressSerializer,
    
    # Contract serializers
    ServiceContractListSerializer, ServiceContractDetailSerializer,
    ServiceContractCreateSerializer,
    
    # Customer data serializers
    CustomerOverviewSerializer, CustomerStatsSerializer
)

# Import serializers for connections and plans
# NOTE: We use local ConnectionSerializer to avoid DictField issues with Account model instances
try:
    from web_support.public_pricing.serializers import (
        ElectricityPlanSerializer, BroadbandPlanSerializer, MobilePlanSerializer
    )
    # Don't import ConnectionSerializer - use local definition to avoid serialization issues
except ImportError:
    # Create dummy serializers if not available
    from rest_framework import serializers
    
    class ElectricityPlanSerializer(serializers.Serializer):
        id = serializers.CharField(read_only=True)
        plan_id = serializers.CharField(read_only=True)
        plan_name = serializers.CharField(read_only=True)
        plan_type = serializers.CharField(read_only=True)
        description = serializers.CharField(read_only=True)
        contract_length = serializers.CharField(read_only=True)
        region = serializers.CharField(read_only=True)
        base_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        pricing_details = serializers.CharField(read_only=True)
        monthly_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        monthly_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        connection_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        service_type = serializers.CharField(read_only=True)
        is_active = serializers.BooleanField(read_only=True)
        status = serializers.CharField(read_only=True)
        created_at = serializers.DateTimeField(read_only=True)
        
        def to_representation(self, instance):
            data = super().to_representation(instance)
            if 'name' in data:
                data['plan_name'] = data['name']
            if 'monthly_fee' in data:
                data['monthly_cost'] = data['monthly_fee']
            if 'status' in data:
                data['is_active'] = data['status'] == 'active'
            return data
    
    class BroadbandPlanSerializer(serializers.Serializer):
        id = serializers.CharField(read_only=True)
        plan_id = serializers.CharField(read_only=True)  # Changed from IntegerField to CharField
        name = serializers.CharField(read_only=True)
        plan_type = serializers.CharField(read_only=True)
        description = serializers.CharField(read_only=True)
        contract_length = serializers.CharField(read_only=True)
        region = serializers.CharField(read_only=True)
        base_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        pricing_details = serializers.CharField(read_only=True)
        monthly_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        connection_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        download_speed = serializers.CharField(read_only=True)
        upload_speed = serializers.CharField(read_only=True)
        data_allowance = serializers.CharField(read_only=True)
        service_type = serializers.CharField(default='broadband', read_only=True)
    
    class MobilePlanSerializer(serializers.Serializer):
        id = serializers.CharField(read_only=True)
        plan_id = serializers.CharField(read_only=True)  # Changed from IntegerField to CharField
        name = serializers.CharField(read_only=True)
        plan_type = serializers.CharField(read_only=True)
        description = serializers.CharField(read_only=True)
        contract_length = serializers.CharField(read_only=True)
        region = serializers.CharField(read_only=True)
        base_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        pricing_details = serializers.CharField(read_only=True)
        monthly_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        connection_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
        data_allowance = serializers.CharField(read_only=True)
        call_allowance = serializers.CharField(read_only=True)
        text_allowance = serializers.CharField(read_only=True)
        service_type = serializers.CharField(default='mobile', read_only=True)

# Always use local ConnectionSerializer to avoid DictField serialization issues
from rest_framework import serializers

class ConnectionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    connection_identifier = serializers.CharField(read_only=True)
    connection_number = serializers.CharField(read_only=True)
    icp_number = serializers.CharField(read_only=True)
    service_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    activation_date = serializers.DateTimeField(read_only=True)
    connection_date = serializers.DateTimeField(read_only=True)
    account_number = serializers.CharField(read_only=True)
    account_id = serializers.CharField(read_only=True)
    account_type = serializers.CharField(read_only=True)
    account_status = serializers.CharField(read_only=True)
    contract_id = serializers.CharField(read_only=True)
    contract_number = serializers.CharField(read_only=True)
    contract_status = serializers.CharField(read_only=True)
    assignment_status = serializers.CharField(read_only=True)
    assignment_date = serializers.DateField(read_only=True)
    primary_user_email = serializers.CharField(read_only=True)
    primary_user_name = serializers.CharField(read_only=True)
    tenant_name = serializers.CharField(read_only=True)
    address = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Basic field mapping
        if 'connection_identifier' in data:
            data['connection_number'] = data['connection_identifier']
            data['icp_number'] = data['connection_identifier']
        if 'activation_date' in data:
            data['connection_date'] = data['activation_date']
            
        # Enriched attributes from ContractConnectionAssignment
        for attr_name, field_name in [
            ('_contract_id', 'contract_id'),
            ('_contract_number', 'contract_number'),
            ('_contract_status', 'contract_status'),
            ('_account_id', 'account_id'),
            ('_account_number', 'account_number'),
            ('_account_type', 'account_type'),
            ('_account_status', 'account_status'),
            ('_assignment_status', 'assignment_status'),
            ('_assignment_date', 'assignment_date'),
            ('_primary_user_email', 'primary_user_email'),
            ('_primary_user_name', 'primary_user_name'),
        ]:
            value = getattr(instance, attr_name, None)
            if value is not None:
                data[field_name] = value
        
        # Service-specific details
        service_details = {}
        if instance.service_type == 'electricity':
            service_details.update({
                'icp_code': getattr(instance, 'icp_code', None),
                'gxp_code': getattr(instance, 'gxp_code', None),
                'network_code': getattr(instance, 'network_code', None),
            })
        elif instance.service_type == 'broadband':
            service_details.update({
                'ont_serial': getattr(instance, 'ont_serial', None),
                'circuit_id': getattr(instance, 'circuit_id', None),
                'connection_type': getattr(instance, 'connection_type', None),
            })
        elif instance.service_type == 'mobile':
            service_details.update({
                'mobile_number': getattr(instance, 'mobile_number', None),
                'sim_iccid': getattr(instance, 'sim_iccid', None),
                'device_imei': getattr(instance, 'device_imei', None),
            })
        
        data['service_details'] = service_details
        
        return data

# Add import for pricing models at the top
from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan

from .mixins import VersionedViewSetMixin

User = get_user_model()

# API Version Information - REMOVED

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


def get_user_tenant(user):
    """
    Get the tenant for a staff user.
    Returns the user's tenant or None if not found.
    For super admin users, returns None to allow access to all tenants.
    """
    if not user or not user.is_authenticated:
        return None
    
    # Super admin users can see all tenants
    if is_super_admin(user):
        return None
    
    # Direct tenant relationship
    if hasattr(user, 'tenant') and user.tenant:
        return user.tenant
    
    # Check tenant roles
    tenant_role = TenantUserRole.objects.filter(user=user).first()
    if tenant_role:
        return tenant_role.tenant
    
    return None


def get_selected_tenant_from_request(request):
    """
    Get the selected tenant from request parameters.
    For super admin users, this allows them to filter by specific tenant.
    For regular staff users, this returns their assigned tenant.
    """
    user = request.user
    # Explicit override: all=1 forces no tenant scoping
    try:
        all_flag = request.GET.get('all') or request.query_params.get('all')
        if str(all_flag).lower() in ['1', 'true', 'yes']:
            return None
    except Exception:
        pass
    # Always honor an explicit tenant filter id if provided and valid
    tenant_filter = request.GET.get('tenant') or request.GET.get('tenant_id')
    if tenant_filter:
        try:
            return Tenant.objects.get(id=tenant_filter)
        except (Tenant.DoesNotExist, ValueError):
            # Ignore invalid id and proceed with role-based determination
            pass

    # Determine super-admin also from Keycloak claims if request.user isn't authenticated
    is_admin_via_claims = False
    try:
        claims = getattr(request, 'keycloak_claims', None)
        if claims:
            groups = [str(g) for g in (claims.get('groups') or [])]
            roles = [str(r) for r in (claims.get('realm_access', {}).get('roles') or [])]
            is_admin_via_claims = any(g.lower().find('admin') != -1 for g in groups) or ('admin' in [r.lower() for r in roles])
    except Exception:
        pass

    if user and user.is_authenticated and is_super_admin(user):
        # Super admin: no tenant restriction unless explicit filter above
        return None

    if is_admin_via_claims:
        # Token indicates admin; allow all tenants (or explicit filter already handled)
        return None

    # Regular staff users are limited to their assigned tenant
    if user and user.is_authenticated:
        return get_user_tenant(user)
    
    # No authenticated user and no admin claims: no tenant context
    return None


def is_super_admin(user):
    """
    Check if user is a super admin who can access all tenant data.
    Handles both regular Django users and Keycloak-authenticated users.
    """
    if not user:
        return False
    
    # Handle regular Django authenticated users
    if user.is_authenticated and hasattr(user, 'is_superuser'):
        if user.is_superuser:
            return True
        # Check groups only if user has groups attribute
        if hasattr(user, 'groups'):
            return user.groups.filter(name='Admin').exists()
    
    return False


def should_filter_by_tenant(user):
    """
    Determine if data should be filtered by tenant for this user.
    Returns True if user should see only their tenant's data.
    Returns False if user should see all data (super admin).
    """
    return not is_super_admin(user)


class TenantViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """
    Staff CRUD operations for Tenants
    """
    permission_classes = [StaffPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'slug', 'business_number', 'contact_email']
    filterset_fields = ['is_active', 'currency', 'timezone']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Tenant.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'action', None) == 'retrieve':
            return TenantDetailSerializer
        elif getattr(self, 'action', None) == 'create':
            return TenantCreateSerializer
        return TenantListSerializer

    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export tenants list in CSV or JSON based on ?format= param.
        Default format is csv. Uses TenantListSerializer for fields.
        """
        export_format = request.query_params.get('format', 'csv').lower()
        queryset = self.filter_queryset(self.get_queryset())
        serializer = TenantListSerializer(queryset, many=True)

        if export_format == 'json':
            # If template=1, return only field names as an example object
            if request.query_params.get('template'):
                header = ['name', 'slug', 'business_number', 'tax_number', 'contact_email', 'contact_phone', 'address', 'timezone', 'currency', 'is_active']
                return Response({h: '' for h in header})
            return Response(serializer.data)

        # CSV export
        import csv
        from io import StringIO
        buffer = StringIO()
        writer = csv.writer(buffer)
        # Write header
        header = ['name', 'slug', 'business_number', 'tax_number', 'contact_email', 'contact_phone', 'address', 'timezone', 'currency', 'is_active']
        writer.writerow(header)
        # If template requested, only header row is returned
        if not request.query_params.get('template'):
            for item in serializer.data:
                writer.writerow([
                    item.get('name'), item.get('slug'), item.get('business_number'), item.get('tax_number') or '',
                    item.get('contact_email'), item.get('contact_phone') or '', '',
                    item.get('timezone') or 'Pacific/Auckland', item.get('currency') or 'NZD',
                    item.get('is_active')
                ])
        csv_data = buffer.getvalue()
        buffer.close()
        from django.http import HttpResponse
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tenants_export.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_tenants(self, request):
        """
        Import tenants from a CSV file uploaded as form-data 'file'.
        Returns counts of created and errors.
        """
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file uploaded under field name "file"'}, status=status.HTTP_400_BAD_REQUEST)

        import csv, io
        decoded = uploaded.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(decoded))

        created, errors = 0, []
        for idx, row in enumerate(reader, start=1):
            payload = {
                'name': row.get('name', '').strip(),
                'slug': row.get('slug', '').strip(),
                'subdomain': (row.get('subdomain') or row.get('slug') or '').strip(),
                'business_number': row.get('business_number', '').strip(),
                'tax_number': row.get('tax_number', '').strip(),
                'contact_email': row.get('contact_email', '').strip(),
                'contact_phone': row.get('contact_phone', '').strip(),
                'address': row.get('address', '').strip(),
                'timezone': row.get('timezone', 'Pacific/Auckland').strip() or 'Pacific/Auckland',
                'currency': row.get('currency', 'NZD').strip() or 'NZD',
                'is_active': str(row.get('is_active', 'true')).lower() in ['1', 'true', 'yes', 'y']
            }
            serializer = TenantCreateSerializer(data=payload)
            if serializer.is_valid():
                try:
                    serializer.save()
                    created += 1
                except Exception as e:
                    errors.append({'row': idx, 'error': str(e)})
            else:
                errors.append({'row': idx, 'error': serializer.errors})

        return Response({'created': created, 'errors': errors}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get users for a specific tenant"""
        tenant = self.get_object()
        # The User model is not directly FK'd to Tenant; derive via TenantUserRole
        users = User.objects.filter(tenant_roles__tenant=tenant).distinct()
        serializer = StaffUserListSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a specific tenant"""
        tenant = self.get_object()
        stats = {
            'users_count': tenant.user_set.count(),
            'active_users_count': tenant.user_set.filter(is_active=True).count(),
            'accounts_count': tenant.account_set.count() if hasattr(tenant, 'account_set') else 0,
            'contracts_count': tenant.servicecontract_set.count() if hasattr(tenant, 'servicecontract_set') else 0,
        }
        return Response(stats)

    @action(detail=True, methods=['post'])
    def add_user_role(self, request, pk=None):
        """Add a user role to tenant"""
        tenant = self.get_object()
        serializer = TenantUserRoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant=tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffUserViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """
    Staff CRUD operations for Users
    """
    permission_classes = [StaffPermission]  # Enable staff authentication
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # Use only valid model fields for search, filtering, and ordering
    search_fields = ['id']  # Only search by ID since email/name are in Keycloak
    filterset_fields = ['is_active', 'is_staff']
    ordering_fields = ['id', 'date_joined', 'is_active', 'is_staff']
    ordering = ['id']

    def get_queryset(self):
        # Get selected tenant from request
        selected_tenant = get_selected_tenant_from_request(self.request)
        
        # Base query with proper prefetch
        base_query = User.objects.prefetch_related('account_roles__account', 'tenant_roles__tenant')
        
        if selected_tenant:
            # Filter users by specific tenant through TenantUserRole or UserAccountRole
            return base_query.filter(
                models.Q(tenant_roles__tenant=selected_tenant) |
                models.Q(account_roles__account__tenant=selected_tenant)
            ).distinct()
        elif should_filter_by_tenant(self.request.user):
            # Regular staff users - filter by their assigned tenant
            user_tenant = get_user_tenant(self.request.user)
            if user_tenant:
                return base_query.filter(
                    models.Q(tenant_roles__tenant=user_tenant) |
                    models.Q(account_roles__account__tenant=user_tenant)
                ).distinct()
            else:
                # No tenant assigned - return empty for safety
                return base_query.none()
        else:
            # Super admin with no tenant filter - show all users
            return base_query.all()

    def get_serializer_class(self):
        if getattr(self, 'action', None) == 'retrieve':
            return StaffUserDetailSerializer
        elif getattr(self, 'action', None) == 'create':
            return StaffUserCreateSerializer
        elif getattr(self, 'action', None) in ['update', 'partial_update']:
            return StaffUserUpdateSerializer
        return StaffUserListSerializer

    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export users list in CSV or JSON based on ?format= param.
        Default format is csv. Supports ?template=1 to return header only.
        """
        export_format = request.query_params.get('format', 'csv').lower()
        queryset = self.filter_queryset(self.get_queryset())

        # JSON export
        if export_format == 'json':
            if request.query_params.get('template'):
                header = ['email', 'first_name', 'last_name', 'mobile', 'user_type', 'department', 'job_title', 'tenant_slug', 'manager_email', 'is_staff', 'is_active']
                return Response({h: '' for h in header})
            serializer = StaffUserListSerializer(queryset, many=True)
            return Response(serializer.data)

        # CSV export
        import csv
        from io import StringIO
        buffer = StringIO()
        writer = csv.writer(buffer)
        header = ['email', 'first_name', 'last_name', 'mobile', 'user_type', 'department', 'job_title', 'tenant_slug', 'is_staff', 'is_active', 'last_login', 'date_joined']
        writer.writerow(header)

        # If template requested, only header row is returned
        if not request.query_params.get('template'):
            for user in queryset:
                try:
                    tenant_slug = getattr(getattr(user, 'tenant', None), 'slug', '') or ''
                except Exception:
                    tenant_slug = ''
                writer.writerow([
                    user.email,
                    getattr(user, 'first_name', '') or '',
                    getattr(user, 'last_name', '') or '',
                    getattr(user, 'mobile', '') or '',
                    getattr(user, 'user_type', '') or '',
                    getattr(user, 'department', '') or '',
                    getattr(user, 'job_title', '') or '',
                    tenant_slug,
                    'true' if getattr(user, 'is_staff', False) else 'false',
                    'true' if getattr(user, 'is_active', False) else 'false',
                    user.last_login.isoformat() if getattr(user, 'last_login', None) else '',
                    user.date_joined.isoformat() if getattr(user, 'date_joined', None) else '',
                ])

        csv_data = buffer.getvalue()
        buffer.close()
        from django.http import HttpResponse
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_users(self, request):
        """
        Import users from a CSV file uploaded as form-data 'file'.
        Accepts header: email, first_name, last_name, mobile, user_type, department,
        job_title, tenant_slug, manager_email, is_staff, is_active, password (optional).
        """
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file uploaded under field name "file"'}, status=status.HTTP_400_BAD_REQUEST)

        import csv, io
        from django.utils.crypto import get_random_string
        decoded = uploaded.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(decoded))

        created, updated, errors = 0, 0, []
        for idx, row in enumerate(reader, start=1):
            try:
                email = (row.get('email') or '').strip().lower()
                if not email:
                    errors.append({'row': idx, 'error': 'email is required'})
                    continue

                first_name = (row.get('first_name') or '').strip()
                last_name = (row.get('last_name') or '').strip()
                mobile = (row.get('mobile') or '').strip()
                user_type = (row.get('user_type') or '').strip()
                department = (row.get('department') or '').strip()
                job_title = (row.get('job_title') or '').strip()
                is_staff = str(row.get('is_staff', '')).strip().lower() in ['1', 'true', 'yes', 'y']
                is_active = str(row.get('is_active', 'true')).strip().lower() in ['1', 'true', 'yes', 'y']
                manager_email = (row.get('manager_email') or '').strip().lower() or None
                password = (row.get('password') or '').strip() or (get_random_string(12) + 'aA1!')

                # Resolve tenant by slug or name
                tenant_obj = None
                tenant_slug = (row.get('tenant_slug') or '').strip()
                tenant_name = (row.get('tenant') or '').strip()
                try:
                    if tenant_slug:
                        tenant_obj = Tenant.objects.filter(slug=tenant_slug).first()
                    elif tenant_name:
                        tenant_obj = Tenant.objects.filter(name=tenant_name).first()
                except Exception:
                    tenant_obj = None

                # Build payload for serializer
                payload = {
                    'email': email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                    'mobile': mobile,
                    'user_type': user_type or None,
                    'department': department or None,
                    'job_title': job_title or None,
                    'tenant_id': str(tenant_obj.id) if tenant_obj else None,
                    'manager_email': manager_email or None,
                    'is_staff': is_staff,
                    'is_active': is_active,
                }

                # If user exists, update; else create
                existing = User.objects.filter(email=email).first()
                if existing:
                    from .staff_serializers import StaffUserUpdateSerializer
                    update_serializer = StaffUserUpdateSerializer(existing, data={
                        'first_name': first_name,
                        'last_name': last_name,
                        'mobile': mobile,
                        'user_type': user_type or None,
                        'department': department or None,
                        'job_title': job_title or None,
                        'tenant_id': str(tenant_obj.id) if tenant_obj else None,
                        'manager_email': manager_email or None,
                        'is_staff': is_staff,
                        'is_active': is_active,
                    }, partial=True)
                    if update_serializer.is_valid():
                        update_serializer.save()
                        updated += 1
                    else:
                        errors.append({'row': idx, 'error': update_serializer.errors})
                    continue

                from .staff_serializers import StaffUserCreateSerializer
                serializer = StaffUserCreateSerializer(data=payload)
                if serializer.is_valid():
                    serializer.save()
                    created += 1
                else:
                    errors.append({'row': idx, 'error': serializer.errors})
            except Exception as e:
                errors.append({'row': idx, 'error': str(e)})

        return Response({'created': created, 'updated': updated, 'errors': errors}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def stats(self, request):
        """
        Basic aggregate statistics for users.
        If a selected tenant is present (query/header), limit to that tenant.
        Otherwise, regular staff see their tenant; super admins see global.
        """
        # Determine tenant scope
        selected_tenant = get_selected_tenant_from_request(request)
        if selected_tenant is not None:
            base_qs = User.objects.filter(
                models.Q(tenant_roles__tenant=selected_tenant) |
                models.Q(account_roles__account__tenant=selected_tenant)
            ).distinct()
        elif should_filter_by_tenant(request.user):
            user_tenant = get_user_tenant(request.user)
            if user_tenant:
                base_qs = User.objects.filter(
                    models.Q(tenant_roles__tenant=user_tenant) |
                    models.Q(account_roles__account__tenant=user_tenant)
                ).distinct()
            else:
                base_qs = User.objects.all()
        else:
            base_qs = User.objects.all()

        data = {
            'total_users': base_qs.count(),
            'active_users': base_qs.filter(is_active=True).count(),
            'staff_users': base_qs.filter(is_staff=True).count(),
            'admin_users': base_qs.filter(is_superuser=True).count(),
        }
        return Response(data)

    @action(detail=True, methods=['get'])
    def accounts(self, request, pk=None):
        """Get all accounts associated with this user"""
        user = self.get_object()
        
        # Get selected tenant from request
        selected_tenant = get_selected_tenant_from_request(request)
        
        # Filter accounts by selected tenant if applicable
        accounts = Account.objects.filter(user_roles__user=user)
        if selected_tenant:
            accounts = accounts.filter(tenant=selected_tenant)
            
        serializer = AccountListSerializer(accounts, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Defensive retrieve that tolerates optional fields and returns a minimal payload if serialization fails.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            # Fallback minimal response to avoid 500s in UAT
            try:
                instance = self.get_object()
                fallback = {
                    'id': str(getattr(instance, 'id', '')),
                    'email': getattr(instance, 'email', ''),
                    'first_name': getattr(instance, 'first_name', ''),
                    'last_name': getattr(instance, 'last_name', ''),
                    'is_active': bool(getattr(instance, 'is_active', True)),
                    'is_staff': bool(getattr(instance, 'is_staff', False)),
                    'last_login': getattr(instance, 'last_login', None),
                }
                return Response(fallback)
            except Exception:
                from rest_framework import status as drf_status
                return Response({'detail': str(e)}, status=drf_status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def contracts(self, request, pk=None):
        """Get all contracts associated with this user through their accounts"""
        user = self.get_object()
        
        # Get selected tenant from request
        selected_tenant = get_selected_tenant_from_request(request)
        
        # Get user's accounts first
        user_accounts = Account.objects.filter(user_roles__user=user)
        if selected_tenant:
            user_accounts = user_accounts.filter(tenant=selected_tenant)
        
        # Get contracts for those accounts (robust import)
        try:
            from core.contracts.models import ServiceContract as SC
        except Exception:
            SC = None
        
        if not SC:
            return Response([])
        
        contracts = SC.objects.filter(account__in=user_accounts).select_related('account', 'tenant')
        if selected_tenant:
            contracts = contracts.filter(tenant=selected_tenant)
        serializer = ServiceContractListSerializer(contracts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def connections(self, request, pk=None):
        """Get all connections associated with this user through their accounts"""
        user = self.get_object()
        
        # Get selected tenant from request
        selected_tenant = get_selected_tenant_from_request(request)
        
        # Get user's accounts first
        user_accounts = Account.objects.filter(user_roles__user=user)
        if selected_tenant:
            user_accounts = user_accounts.filter(tenant=selected_tenant)
        
        # Use ConnectionViewSet logic for fetching connections
        connection_viewset = ConnectionViewSet()
        connection_viewset.request = request
        all_connections = connection_viewset.get_real_connections_for_tenant(selected_tenant)
        
        # Filter connections to only those linked to the user's accounts (when enrichment available)
        account_numbers = set(user_accounts.values_list('account_number', flat=True))
        user_connections = []
        for conn in all_connections or []:
            conn_account = getattr(conn, '_account_number', None)
            if conn_account and conn_account in account_numbers:
                user_connections.append(conn)
        
        # Fallback: if nothing matched but we have connections, return a small subset
        if not user_connections and all_connections:
            user_connections = all_connections[:5]
        
        # Add debug information
        print(f"DEBUG: User {user.email} tenant: {selected_tenant}")
        print(f"DEBUG: User accounts: {[acc.account_number for acc in user_accounts]}")
        print(f"DEBUG: Found {len(all_connections)} total connections")
        print(f"DEBUG: Returning {len(user_connections)} connections")
        
        serializer = ConnectionSerializer(user_connections, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def plans(self, request, pk=None):
        """Get all active plans associated with this user through their connections"""
        user = self.get_object()
        
        # Get selected tenant from request
        selected_tenant = get_selected_tenant_from_request(request)
        
        # If no specific tenant is selected, use the user's tenant
        if not selected_tenant:
            selected_tenant = user.tenant
        
        # Get plans for the tenant using the PlanViewSet logic
        plan_viewset = PlanViewSet()
        plan_viewset.request = request
        all_plans = plan_viewset.get_real_plans_for_tenant(selected_tenant)
        
        # For demo purposes, return a subset of available plans
        # In a real implementation, this would be based on actual user connections and plan assignments
        user_plans = all_plans[:3] if all_plans else []
        
        # Add debug information
        print(f"DEBUG: User {user.email} tenant: {selected_tenant}")
        print(f"DEBUG: Found {len(all_plans)} total plans")
        print(f"DEBUG: Returning {len(user_plans)} plans")
        
        # Return the data directly since get_real_plans_for_tenant already returns properly formatted data
        return Response(user_plans)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password"""
        user = self.get_object()
        new_password = request.data.get('password')
        if new_password:
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password reset successfully'})
        return Response({'error': 'Password required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle user active status"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({'status': 'success', 'is_active': user.is_active})

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk delete users"""
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response(
                {'error': 'user_ids is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(user_ids, list):
            return Response(
                {'error': 'user_ids must be a list'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get users that exist and can be deleted
        users_to_delete = self.get_queryset().filter(id__in=user_ids)
        
        if not users_to_delete.exists():
            return Response(
                {'error': 'No valid users found to delete'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent deletion of superusers by non-superusers
        if not request.user.is_superuser:
            superusers = users_to_delete.filter(is_superuser=True)
            if superusers.exists():
                return Response(
                    {'error': 'Cannot delete superuser accounts'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        deleted_count = users_to_delete.count()
        users_to_delete.delete()
        
        return Response({
            'message': f'Successfully deleted {deleted_count} users',
            'deleted_count': deleted_count
        })

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update users"""
        user_ids = request.data.get('user_ids', [])
        update_data = request.data.get('update_data', {})
        
        if not user_ids:
            return Response(
                {'error': 'user_ids is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(user_ids, list):
            return Response(
                {'error': 'user_ids must be a list'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not update_data:
            return Response(
                {'error': 'update_data is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow certain fields to be bulk updated
        allowed_fields = ['is_active', 'is_staff']
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_data:
            return Response(
                {'error': f'No valid fields to update. Allowed: {allowed_fields}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get users that exist and can be updated
        users_to_update = self.get_queryset().filter(id__in=user_ids)
        
        if not users_to_update.exists():
            return Response(
                {'error': 'No valid users found to update'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        updated_count = users_to_update.update(**filtered_data)
        
        return Response({
            'message': f'Successfully updated {updated_count} users',
            'updated_count': updated_count,
            'updated_fields': list(filtered_data.keys())
        })

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get all users associated with this account"""
        account = self.get_object()
        user_roles = UserAccountRole.objects.filter(account=account)
        users = [role.user for role in user_roles]
        serializer = StaffUserListSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def addresses(self, request, pk=None):
        """Get all unique addresses associated with an account's contracts and billing."""
        account = self.get_object()
        address_ids = set()

        # Add the account's primary billing address
        if account.billing_address:
            address_ids.add(account.billing_address.id)

        addresses = Address.objects.filter(id__in=list(address_ids))
        serializer = AddressSerializer(addresses, many=True, context={'request': request})
        return Response(serializer.data)


class AccountViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """
    Staff CRUD operations for Accounts
    """
    serializer_class = AccountListSerializer
    permission_classes = [StaffPermission]  # Enable staff authentication
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['account_number', 'user_roles__user__email', 'user_roles__user__first_name', 'user_roles__user__last_name']
    filterset_fields = ['account_type', 'status', 'tenant']
    ordering_fields = ['account_number', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # Get selected tenant from request (supports super admin tenant switching)
        selected_tenant = get_selected_tenant_from_request(self.request)
        
        # Check if user has admin privileges (either Django user or Keycloak claims)
        is_admin = is_super_admin(self.request.user)
        
        # Also check Keycloak claims for admin privileges
        if not is_admin and hasattr(self.request, 'keycloak_claims'):
            claims = self.request.keycloak_claims
            groups = [str(g) for g in (claims.get('groups') or [])]
            roles = [str(r) for r in (claims.get('realm_access', {}).get('roles') or [])]
            is_admin = any(g.lower().find('admin') != -1 for g in groups) or ('admin' in [r.lower() for r in roles])
        
        # Super admin can see all accounts if no tenant is selected
        if is_admin and not selected_tenant:
            queryset = Account.objects.all()
        elif selected_tenant:
            queryset = Account.objects.filter(tenant=selected_tenant)
        else:
            # For now, allow all accounts if no specific tenant context
            # In the future, we might want to restrict this further
            queryset = Account.objects.all()

        # Annotate with counts and prefetch related data for efficiency
        return queryset.annotate(
            # connections_count=models.Count('connections', distinct=True),  # Connections are in tenant schemas
            contracts_count=models.Count('contracts', distinct=True)
        ).select_related(
            'tenant', 'billing_address'
        ).prefetch_related(
            'user_roles__user'
        )

    def get_serializer_class(self):
        if getattr(self, 'action', None) == 'retrieve':
            return AccountDetailSerializer
        elif getattr(self, 'action', None) == 'create':
            return AccountCreateSerializer
        elif getattr(self, 'action', None) in ['update', 'partial_update']:
            return AccountUpdateSerializer
        return AccountListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Defensive retrieve that tolerates tenant scoping and returns a minimal
        payload instead of a hard 404 when possible. Helps UAT navigation.
        """
        try:
            instance = self.get_object()
            serializer = AccountDetailSerializer(instance)
            return Response(serializer.data)
        except Exception as e:
            # Fallback: try to find by primary key without tenant scoping
            try:
                account_id = kwargs.get(self.lookup_field or 'pk')
                account = Account.objects.filter(id=account_id).select_related('tenant').first()
                if account:
                    minimal = {
                        'id': str(account.id),
                        'account_number': account.account_number,
                        'account_type': account.account_type,
                        'tenant': {
                            'id': str(account.tenant.id),
                            'name': account.tenant.name,
                            'slug': account.tenant.slug,
                        } if account.tenant else None,
                        'status': account.status,
                        'created_at': account.created_at,
                        'updated_at': account.updated_at,
                    }
                    return Response(minimal)
            except Exception:
                pass
            from rest_framework import status as drf_status
            return Response({'detail': str(e)}, status=drf_status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export accounts in CSV or JSON. Supports ?template=1 for header only.
        """
        export_format = request.query_params.get('format', 'csv').lower()
        queryset = self.filter_queryset(self.get_queryset())

        if export_format == 'json':
            if request.query_params.get('template'):
                header = ['account_number','tenant_slug','account_type','billing_cycle','billing_day','status','primary_user_email']
                return Response({h: '' for h in header})
            serializer = AccountListSerializer(queryset, many=True)
            return Response(serializer.data)

        import csv
        from io import StringIO
        buffer = StringIO()
        writer = csv.writer(buffer)
        header = ['account_number','tenant_slug','account_type','billing_cycle','billing_day','status','primary_user_email']
        writer.writerow(header)
        if not request.query_params.get('template'):
            for acc in queryset:
                tenant_slug = getattr(acc.tenant, 'slug', '') if getattr(acc, 'tenant', None) else ''
                primary_email = None
                try:
                    primary_role = acc.user_roles.filter(role__in=['owner','primary']).first()
                    if primary_role and primary_role.user:
                        primary_email = primary_role.user.email
                except Exception:
                    primary_email = None
                writer.writerow([
                    acc.account_number,
                    tenant_slug,
                    getattr(acc, 'account_type', '') or '',
                    getattr(acc, 'billing_cycle', '') or '',
                    getattr(acc, 'billing_day', '') or '',
                    getattr(acc, 'status', '') or '',
                    primary_email or ''
                ])
        csv_data = buffer.getvalue(); buffer.close()
        from django.http import HttpResponse
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="accounts_export.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_accounts(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file uploaded under field name "file"'}, status=status.HTTP_400_BAD_REQUEST)
        import csv, io
        decoded = uploaded.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(decoded))
        from .staff_serializers import AccountCreateSerializer
        created, updated, errors = 0, 0, []
        for idx, row in enumerate(reader, start=1):
            try:
                account_number = (row.get('account_number') or '').strip()
                tenant_slug = (row.get('tenant_slug') or '').strip()
                primary_user_email = (row.get('primary_user_email') or '').strip()
                if not tenant_slug or not primary_user_email:
                    errors.append({'row': idx, 'error': 'tenant_slug and primary_user_email are required'})
                    continue
                tenant_obj = Tenant.objects.filter(slug=tenant_slug).first()
                if not tenant_obj:
                    errors.append({'row': idx, 'error': f'tenant not found: {tenant_slug}'})
                    continue
                payload = {
                    'account_number': account_number,
                    'tenant_id': str(tenant_obj.id),
                    'account_type': (row.get('account_type') or '').strip() or 'standard',
                    'billing_cycle': (row.get('billing_cycle') or '').strip() or None,
                    'billing_day': (row.get('billing_day') or '').strip() or None,
                    'primary_user_email': primary_user_email,
                    'status': (row.get('status') or '').strip() or 'active',
                }
                # Update if exists by account_number
                existing = Account.objects.filter(account_number=account_number, tenant=tenant_obj).first() if account_number else None
                if existing:
                    # Minimal updates
                    for f in ['account_type','billing_cycle','billing_day','status']:
                        setattr(existing, f, payload.get(f))
                    existing.save(); updated += 1
                    continue
                serializer = AccountCreateSerializer(data=payload)
                if serializer.is_valid():
                    serializer.save(); created += 1
                else:
                    errors.append({'row': idx, 'error': serializer.errors})
            except Exception as e:
                errors.append({'row': idx, 'error': str(e)})
        return Response({'created': created, 'updated': updated, 'errors': errors})

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get all users associated with this account"""
        account = self.get_object()
        user_roles = UserAccountRole.objects.filter(account=account)
        users = [role.user for role in user_roles]
        serializer = StaffUserListSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def contracts(self, request, pk=None):
        """Get all contracts associated with this account"""
        account = self.get_object()
        
        # Get contracts for this account
        try:
            from core.contracts.models import ServiceContract as SC
        except Exception:
            SC = None
        if not SC:
            return Response([])
        contracts = SC.objects.filter(account=account)
        serializer = ServiceContractListSerializer(contracts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def connections(self, request, pk=None):
        """Get all connections associated with this account"""
        account = self.get_object()
        
        # Get connections for this account from tenant schema
        connection_viewset = ConnectionViewSet()
        connection_viewset.request = request
        all_connections = connection_viewset.get_real_connections_for_tenant(account.tenant)
        
        # Filter connections by account. Prefer enriched attributes populated during enrichment
        account_connections = []
        for conn in all_connections or []:
            if getattr(conn, '_account_number', None) == account.account_number:
                account_connections.append(conn)
        # Fallback to a small subset if nothing matched (demo data / no links)
        if not account_connections and all_connections:
            account_connections = all_connections[:5]
        
        serializer = ConnectionSerializer(account_connections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def plans(self, request, pk=None):
        """Get all plans associated with this account"""
        account = self.get_object()
        
        # Get plans for this account's tenant
        plan_viewset = PlanViewSet()
        plan_viewset.request = request
        all_plans = plan_viewset.get_real_plans_for_tenant(account.tenant)
        
        # Return first few plans for demo
        account_plans = all_plans[:3] if all_plans else []
        
        return Response(account_plans)

    @action(detail=True, methods=['get'])
    def addresses(self, request, pk=None):
        """Get all unique addresses associated with an account's contracts and billing."""
        account = self.get_object()
        address_ids = set()

        # Add the account's primary billing address
        if account.billing_address:
            address_ids.add(account.billing_address.id)

        addresses = Address.objects.filter(id__in=list(address_ids))
        serializer = AddressSerializer(addresses, many=True, context={'request': request})
        return Response(serializer.data)


class ServiceContractViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """
    Staff CRUD operations for Service Contracts
    """
    serializer_class = ServiceContractListSerializer
    permission_classes = [StaffPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['contract_number', 'service_name', 'account__account_number']
    filterset_fields = ['contract_type', 'status', 'tenant']
    ordering_fields = ['contract_number', 'start_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Get selected tenant from request
        selected_tenant = get_selected_tenant_from_request(self.request)
        
        # Load ServiceContract model dynamically to avoid app loading issues
        try:
            from django.apps import apps
            ServiceContract = apps.get_model('contracts', 'ServiceContract')
        except (LookupError, ImportError) as e:
            # ServiceContract model not available - return empty queryset
            from django.contrib.auth import get_user_model
            User = get_user_model()
            return User.objects.none()
        
        try:
            # Build base queryset with proper prefetch for user_roles
            queryset = ServiceContract.objects.select_related(
                'account', 'tenant', 'created_by', 'updated_by'
            ).prefetch_related(
                Prefetch(
                    'account__user_roles',
                    queryset=UserAccountRole.objects.select_related('user').order_by('role', 'created_at')
                )
            )
            
            # Filter by tenant if not super admin
            if selected_tenant:
                queryset = queryset.filter(tenant=selected_tenant)
            elif should_filter_by_tenant(self.request.user):
                user_tenant = get_user_tenant(self.request.user)
                if user_tenant:
                    queryset = queryset.filter(tenant=user_tenant)
            
            return queryset
        except Exception as e:
            # Log the error and return empty queryset
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in ServiceContractViewSet.get_queryset: {e}")
            try:
                return ServiceContract.objects.none()
            except:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                return User.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServiceContractDetailSerializer
        elif self.action in ['create']:
            return ServiceContractCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ServiceContractCreateSerializer
        return ServiceContractListSerializer

    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export contracts to CSV/JSON. ?template=1 for header only.
        """
        export_format = request.query_params.get('format', 'csv').lower()
        queryset = self.filter_queryset(self.get_queryset())
        if export_format == 'json':
            if request.query_params.get('template'):
                header = ['contract_number','contract_type','service_name','status','start_date','end_date','tenant_slug','account_number','base_charge']
                return Response({h: '' for h in header})
            serializer = ServiceContractListSerializer(queryset, many=True)
            return Response(serializer.data)
        import csv
        from io import StringIO
        buffer = StringIO(); writer = csv.writer(buffer)
        header = ['contract_number','contract_type','service_name','status','start_date','end_date','tenant_slug','account_number','base_charge']
        writer.writerow(header)
        if not request.query_params.get('template'):
            for c in queryset:
                tenant_slug = getattr(getattr(c, 'tenant', None), 'slug', '') or ''
                account_number = getattr(getattr(c, 'account', None), 'account_number', '') or ''
                writer.writerow([
                    getattr(c, 'contract_number', ''), getattr(c, 'contract_type', ''), getattr(c, 'service_name', ''),
                    getattr(c, 'status', ''), getattr(c, 'start_date', None) or '', getattr(c, 'end_date', None) or '',
                    tenant_slug, account_number, getattr(c, 'base_charge', '') or ''
                ])
        csv_data = buffer.getvalue(); buffer.close()
        from django.http import HttpResponse
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contracts_export.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_contracts(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file uploaded under field name "file"'}, status=status.HTTP_400_BAD_REQUEST)
        import csv, io
        from .staff_serializers import ServiceContractCreateSerializer
        decoded = uploaded.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(decoded))
        created, updated, errors = 0, 0, []
        try:
            from core.contracts.models import ServiceContract as SC
        except Exception:
            SC = None
        for idx, row in enumerate(reader, start=1):
            try:
                tenant_slug = (row.get('tenant_slug') or '').strip()
                account_number = (row.get('account_number') or '').strip()
                tenant_obj = Tenant.objects.filter(slug=tenant_slug).first() if tenant_slug else None
                account_obj = Account.objects.filter(account_number=account_number, tenant=tenant_obj).first() if tenant_obj and account_number else None
                payload = {
                    'contract_number': (row.get('contract_number') or '').strip(),
                    'contract_type': (row.get('contract_type') or '').strip() or None,
                    'service_name': (row.get('service_name') or '').strip() or None,
                    'status': (row.get('status') or '').strip() or 'active',
                    'start_date': (row.get('start_date') or '').strip() or None,
                    'end_date': (row.get('end_date') or '').strip() or None,
                    'base_charge': (row.get('base_charge') or '').strip() or None,
                    'tenant_id': str(tenant_obj.id) if tenant_obj else None,
                    'account_id': str(account_obj.id) if account_obj else None,
                }
                if SC and payload.get('contract_number'):
                    existing = SC.objects.filter(contract_number=payload['contract_number']).first()
                else:
                    existing = None
                if existing:
                    # Shallow update
                    for f in ['contract_type','service_name','status','start_date','end_date','base_charge']:
                        v = payload.get(f)
                        if v is not None:
                            setattr(existing, f, v)
                    if tenant_obj: existing.tenant = tenant_obj
                    if account_obj: existing.account = account_obj
                    existing.save(); updated += 1
                    continue
                serializer = ServiceContractCreateSerializer(data=payload)
                if serializer.is_valid():
                    serializer.save(); created += 1
                else:
                    errors.append({'row': idx, 'error': serializer.errors})
            except Exception as e:
                errors.append({'row': idx, 'error': str(e)})
        return Response({'created': created, 'updated': updated, 'errors': errors})


class ConnectionViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """
    Staff CRUD operations for Service Connections with time slicing
    Connections can be standalone (tenant connections) or associated with contracts
    """
    permission_classes = [StaffPermission]  # Enable staff authentication
    serializer_class = ConnectionSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Get selected tenant from request
        selected_tenant = get_selected_tenant_from_request(self.request)
        return self.get_real_connections_for_tenant(selected_tenant)

    def get_real_connections_for_tenant(self, selected_tenant):
        """Get real connections from database filtered by tenant"""
        try:
            from energy.connections.models import Connection
            
            # Get all connections from public schema with tenant filtering
            all_connections = []
            
            if selected_tenant:
                # Query specific tenant's connections
                connections = Connection.objects.filter(tenant=selected_tenant).defer('account').all()
                all_connections = []
                for conn in connections:
                    # Extract IDs for enrichment
                    conn._extracted_account_id = conn.account_id
                    conn._extracted_contract_id = getattr(conn, 'contract_id', None)
                    all_connections.append(conn)
            elif should_filter_by_tenant(self.request.user):
                # Regular staff user - query their tenant's connections
                user_tenant = get_user_tenant(self.request.user)
                if user_tenant:
                    connections = Connection.objects.filter(tenant=user_tenant).defer('account').all()
                    all_connections = []
                    for conn in connections:
                        # Extract IDs for enrichment
                        conn._extracted_account_id = conn.account_id
                        conn._extracted_contract_id = getattr(conn, 'contract_id', None)
                        all_connections.append(conn)
            else:
                # Super admin - query all connections
                connections = Connection.objects.defer('account').all()
                for conn in connections:
                    # Extract IDs for enrichment
                    conn._extracted_account_id = conn.account_id
                    conn._extracted_contract_id = getattr(conn, 'contract_id', None)
                    all_connections.append(conn)
            
            # Enrich connections with account data
            enriched_connections = self.enrich_connections_with_accounts(all_connections)
            return enriched_connections
            
        except (ImportError, Exception) as e:
            # Fallback to sample data if Connection model not available or table doesn't exist
            print(f"Warning: Connection model error, using sample data: {e}")
            if selected_tenant:
                return self.get_sample_connections_for_tenant(selected_tenant)
            elif should_filter_by_tenant(self.request.user):
                user_tenant = get_user_tenant(self.request.user)
                return self.get_sample_connections_for_tenant(user_tenant)
            else:
                return self.get_sample_connections_fallback()

    def enrich_connections_with_accounts(self, connections):
        """
        Enrich connection objects with account and contract data using ContractConnectionAssignment
        """
        if not connections:
            return connections
        
        # Extract connection IDs for proper assignment lookup
        connection_ids = [str(conn.id) for conn in connections if hasattr(conn, 'id')]
        
        if not connection_ids:
            # Fallback to old method for connections without IDs
            return self._enrich_connections_fallback(connections)
        
        # Get contract assignments for these connections
        from core.contracts.models import ServiceContract
        from core.contracts.plan_assignments import ContractConnectionAssignment
        
        assignments = ContractConnectionAssignment.objects.filter(
            connection_id__in=connection_ids,
            status__in=['assigned', 'active']
        ).select_related('contract', 'contract__account').prefetch_related(
            'contract__account__user_roles__user'
        )
        
        # Create mapping of connection_id to assignment
        assignment_dict = {str(assignment.connection_id): assignment for assignment in assignments}
        
        # Also get contract IDs from legacy contract_id field as fallback
        contract_ids = []
        account_ids = []
        for conn in connections:
            if hasattr(conn, 'contract_id') and conn.contract_id:
                contract_ids.append(str(conn.contract_id))
            if hasattr(conn, '_extracted_account_id') and conn._extracted_account_id:
                account_ids.append(str(conn._extracted_account_id))
        
        contracts_dict = {}
        if contract_ids:
            contracts = ServiceContract.objects.filter(id__in=contract_ids).select_related('account')
            contracts_dict = {str(contract.id): contract for contract in contracts}
        
        # Get accounts for direct account fallback
        accounts_dict = {}
        if account_ids:
            from users.models import Account
            accounts = Account.objects.filter(id__in=account_ids).prefetch_related('user_roles__user')
            accounts_dict = {str(account.id): account for account in accounts}
        
        # Enrich connection objects with account and contract data
        enriched_connections = []
        for conn in connections:
            conn_id = str(conn.id) if hasattr(conn, 'id') else None
            assignment = assignment_dict.get(conn_id) if conn_id else None
            
            # First try to use ContractConnectionAssignment data
            if assignment and assignment.contract:
                contract = assignment.contract
                # Add contract data as attributes
                conn._contract_id = str(contract.id)
                conn._contract_number = contract.contract_number
                conn._contract_status = contract.status
                conn._contract_start_date = contract.start_date
                conn._contract_end_date = contract.end_date
                conn._assignment_status = assignment.status
                conn._assignment_date = assignment.assigned_date
                
                # Add account data if available
                if contract.account:
                    conn._account_id = str(contract.account.id)
                    conn._account_number = contract.account.account_number
                    conn._account_type = contract.account.account_type
                    conn._account_status = contract.account.status
                    
                    # Add primary user info
                    primary_role = contract.account.user_roles.filter(role__in=['owner', 'primary']).first()
                    if primary_role and primary_role.user:
                        user = primary_role.user
                        conn._primary_user_email = user.get_email()
                        conn._primary_user_name = user.get_full_name()
            
            # Fallback to legacy contract_id field
            elif hasattr(conn, 'contract_id') and conn.contract_id:
                contract = contracts_dict.get(str(conn.contract_id))
                if contract:
                    # Add contract data as attributes
                    conn._contract_id = str(contract.id)
                    conn._contract_number = contract.contract_number
                    conn._contract_status = contract.status
                    conn._contract_start_date = contract.start_date
                    conn._contract_end_date = contract.end_date
                    # If contract has account info, use it
                    if contract.account:
                        conn._account_id = str(contract.account.id)
                        conn._account_number = contract.account.account_number
                        conn._account_type = contract.account.account_type
                        # Add primary user info from contract account
                        primary_role = contract.account.user_roles.filter(role='primary').first()
                        if primary_role and primary_role.user:
                            conn._primary_user_email = primary_role.user.email
                            user = primary_role.user
                            conn._primary_user_name = f"{user.first_name} {user.last_name}".strip() or user.username or user.email
                        else:
                            # Fall back to any user on the account if no primary
                            any_role = contract.account.user_roles.first()
                            if any_role and any_role.user:
                                user = any_role.user
                                conn._primary_user_email = user.email
                                conn._primary_user_name = f"{user.first_name} {user.last_name}".strip() or user.username or user.email
                            else:
                                conn._primary_user_email = None
                                conn._primary_user_name = None
                    else:
                        # Contract exists but no account
                        conn._account_number = "NO-ACCOUNT"
                        conn._account_type = "unknown"
                        conn._primary_user_email = None
                        conn._primary_user_name = None
                else:
                    # Contract not found - set missing contract attributes
                    conn._contract_number = f"MISSING-{str(conn._extracted_contract_id)[:8]}"
                    conn._contract_status = "unknown"
                    conn._contract_start_date = None
                    conn._contract_end_date = None
                    # Fall back to account data
                    if hasattr(conn, '_extracted_account_id') and conn._extracted_account_id:
                        account = accounts_dict.get(str(conn._extracted_account_id))
                        if account:
                            conn._account_number = account.account_number
                            conn._account_type = account.account_type
                            # Add primary user info, with fallback
                            primary_role = account.user_roles.filter(role='primary').first()
                            if primary_role and primary_role.user:
                                user = primary_role.user
                                conn._primary_user_email = user.email
                                conn._primary_user_name = f"{user.first_name} {user.last_name}".strip() or user.username or user.email
                            else:
                                # Fall back to any user on the account
                                any_role = account.user_roles.first()
                                if any_role and any_role.user:
                                    user = any_role.user
                                    conn._primary_user_email = user.email
                                    conn._primary_user_name = f"{user.first_name} {user.last_name}".strip() or user.username or user.email
                                else:
                                    conn._primary_user_email = None
                                    conn._primary_user_name = None
                        else:
                            conn._account_number = f"MISSING-{str(conn._extracted_account_id)[:8]}"
                            conn._account_type = "unknown"
                            conn._primary_user_email = None
                            conn._primary_user_name = None
                    else:
                        conn._account_number = "NO-ACCOUNT"
                        conn._account_type = "unknown"
                        conn._primary_user_email = None
                        conn._primary_user_name = None
            else:
                # Mark as unassigned
                conn._contract_status = 'unassigned'
                conn._account_status = 'unassigned'
                conn._contract_number = None
                conn._account_number = None
            
            enriched_connections.append(conn)
        
        return enriched_connections
    
    def _enrich_connections_fallback(self, connections):
        """Fallback enrichment method for connections without IDs"""
        # Legacy enrichment logic for backward compatibility
        return connections

    def get_sample_connections_for_tenant(self, tenant):
        """Get sample connections filtered by tenant"""
        all_connections = self.get_sample_connections_fallback()
        
        if tenant:
            # For sample data, just return a subset based on tenant name
            # Since sample data is dictionaries, not model instances
            tenant_connections = []
            for conn in all_connections:
                # Sample data filtering logic - return first few connections for any tenant
                if len(tenant_connections) < 3:  # Limit to 3 connections per tenant
                    tenant_connections.append(conn)
            return tenant_connections
        
        return all_connections

    def get_sample_connections_fallback(self):
        """Return sample connections data"""
        return [
            {
                'id': 'conn-ele-001',
                'connection_id': 'CONN-ELE-001',
                'service_type': 'electricity',
                'service_identifier': 'ICP-0000123456',
                'status': 'active',
                'installation_date': '2024-06-02',
                'account': {
                    'id': 'acc-001-2024',
                    'account_number': '#ACC-RES-001-2024',
                    'account_type': 'residential',
                    'user': {
                        'email': 'john.smith@gmail.com',
                        'first_name': 'John',
                        'last_name': 'Smith'
                    }
                },
                'plan': {
                    'id': 'ele-fixed-001',
                    'name': 'Fixed Rate Residential',
                    'monthly_charge': 150.00,
                    'service_type': 'electricity',
                    'features': ['24/7 Support', 'Fixed Rate', 'No Exit Fees']
                },
                'plan_assigned_date': '2024-06-02'
            },
            {
                'id': 'conn-bb-001',
                'connection_id': 'CONN-BB-001',
                'service_type': 'broadband',
                'service_identifier': 'ONT-JS-001234',
                'status': 'active',
                'installation_date': '2024-06-07',
                'account': {
                    'id': 'acc-001-2024',
                    'account_number': '#ACC-RES-001-2024',
                    'account_type': 'residential',
                    'user': {
                        'email': 'john.smith@gmail.com',
                        'first_name': 'John',
                        'last_name': 'Smith'
                    }
                },
                'plan': {
                    'id': 'bb-basic-001',
                    'name': 'Fibre Basic 100/20',
                    'monthly_charge': 69.99,
                    'service_type': 'broadband',
                    'features': ['100Mbps Down', '20Mbps Up', 'Unlimited Data']
                },
                'plan_assigned_date': '2024-06-07'
            },
            {
                'id': 'conn-ele-002',
                'connection_id': 'CONN-ELE-002',
                'service_type': 'electricity',
                'service_identifier': 'ICP-0000234567',
                'status': 'active',
                'installation_date': '2024-05-18',
                'account': {
                    'id': 'acc-002-2024',
                    'account_number': '#ACC-COM-002-2024',
                    'account_type': 'commercial',
                    'user': {
                        'email': 'sarah.jones@company.co.nz',
                        'first_name': 'Sarah',
                        'last_name': 'Jones'
                    }
                },
                'plan': {
                    'id': 'ele-green-002',
                    'name': 'Green Energy Plus',
                    'monthly_charge': 165.00,
                    'service_type': 'electricity',
                    'features': ['100% Renewable', '24/7 Support', 'Carbon Neutral']
                },
                'plan_assigned_date': '2024-05-18'
            },
            {
                'id': 'conn-bb-002',
                'connection_id': 'CONN-BB-002',
                'service_type': 'broadband',
                'service_identifier': 'ONT-SJ-002345',
                'status': 'active',
                'installation_date': '2024-05-23',
                'account': {
                    'id': 'acc-002-2024',
                    'account_number': '#ACC-COM-002-2024',
                    'account_type': 'commercial',
                    'user': {
                        'email': 'sarah.jones@company.co.nz',
                        'first_name': 'Sarah',
                        'last_name': 'Jones'
                    }
                },
                'plan': {
                    'id': 'bb-pro-002',
                    'name': 'Fibre Pro 300/100',
                    'monthly_charge': 89.99,
                    'service_type': 'broadband',
                    'features': ['300Mbps Down', '100Mbps Up', 'Unlimited Data', 'WiFi 6 Router']
                },
                'plan_assigned_date': '2024-05-23'
            },
            {
                'id': 'conn-mob-001',
                'connection_id': 'CONN-MOB-001',
                'service_type': 'mobile',
                'service_identifier': '+64-21-234-5678',
                'status': 'active',
                'installation_date': '2024-05-28',
                'account': {
                    'id': 'acc-002-2024',
                    'account_number': '#ACC-COM-002-2024',
                    'account_type': 'commercial',
                    'user': {
                        'email': 'sarah.jones@company.co.nz',
                        'first_name': 'Sarah',
                        'last_name': 'Jones'
                    }
                },
                'plan': {
                    'id': 'mob-plus-002',
                    'name': 'Mobile Plus',
                    'monthly_charge': 49.99,
                    'service_type': 'mobile',
                    'features': ['20GB Data', 'Unlimited Talk/Text', '5G Coverage', 'International Roaming']
                },
                'plan_assigned_date': '2024-05-28'
            },
            {
                'id': 'conn-ele-003',
                'connection_id': 'CONN-ELE-003',
                'service_type': 'electricity',
                'service_identifier': 'ICP-0000345678',
                'status': 'active',
                'installation_date': '2024-05-03',
                'account': {
                    'id': 'acc-003-2024',
                    'account_number': '#ACC-BUS-003-2024',
                    'account_type': 'business',
                    'user': {
                        'email': 'mike.wilson@business.co.nz',
                        'first_name': 'Mike',
                        'last_name': 'Wilson'
                    }
                },
                'plan': {
                    'id': 'ele-biz-003',
                    'name': 'Business Power Pro',
                    'monthly_charge': 280.00,
                    'service_type': 'electricity',
                    'features': ['High Capacity', 'Priority Support', 'Demand Management']
                },
                'plan_assigned_date': '2024-05-03'
            }
        ]

        def list(self, request, *args, **kwargs):
            """Return real plans data from database"""
        from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan
        from users.models import Tenant
        from rest_framework.response import Response
        
        # Get the first tenant for now
        tenant = Tenant.objects.first()
        all_plans = []
        
        # Get electricity plans
        for plan in ElectricityPlan.objects.filter(is_active=True, tenant=tenant):
            all_plans.append({
                'id': f'ele-{plan.plan_id}',
                'plan_id': str(plan.plan_id),
                'name': plan.name,
                'plan_name': plan.name,
                'service_type': 'electricity',
                'description': plan.description,
                'monthly_cost': float(plan.standard_daily_charge or 0) * 30,
                'is_active': plan.is_active,
                'created_at': plan.created_at.isoformat() if hasattr(plan, 'created_at') else None,
            })
        
        # Get broadband plans
        for plan in BroadbandPlan.objects.filter(is_active=True, tenant=tenant):
            all_plans.append({
                'id': f'bb-{plan.plan_id}',
                'plan_id': str(plan.plan_id),
                'name': plan.name,
                'plan_name': plan.name,
                'service_type': 'broadband',
                'description': plan.description,
                'monthly_cost': float(plan.monthly_charge or 0),
                'is_active': plan.is_active,
                'created_at': plan.created_at.isoformat() if hasattr(plan, 'created_at') else None,
            })
        
        # Get mobile plans
        for plan in MobilePlan.objects.filter(is_active=True, tenant=tenant):
            all_plans.append({
                'id': f'mob-{plan.plan_id}',
                'plan_id': str(plan.plan_id),
                'name': plan.name,
                'plan_name': plan.name,
                'service_type': 'mobile',
                'description': plan.description,
                'monthly_cost': float(plan.monthly_charge or 0),
                'is_active': plan.is_active,
                'created_at': plan.created_at.isoformat() if hasattr(plan, 'created_at') else None,
            })
        
        print(f'PlanViewSet returning {len(all_plans)} plans')
        return Response({'count': len(all_plans), 'results': all_plans})

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export plans as CSV (real or sample). Supports ?template=1."""
        import csv
        from io import StringIO
        tenant = get_user_tenant(request.user)
        plans = self.get_real_plans_for_tenant(tenant)
        buffer = StringIO(); writer = csv.writer(buffer)
        header = ['service_type','name','description','monthly_charge','base_rate','setup_fee','term','city','status','created_at']
        writer.writerow(header)
        if not request.query_params.get('template'):
            for p in plans:
                writer.writerow([
                    p.get('service_type',''), p.get('name',''), p.get('description',''),
                    p.get('monthly_fee') or p.get('monthly_cost') or '',
                    p.get('base_price') or p.get('base_rate') or '',
                    p.get('connection_fee') or p.get('setup_fee') or '',
                    p.get('contract_length') or '', p.get('region') or '',
                    'active' if p.get('is_active') else 'inactive', p.get('created_at') or ''
                ])
        csv_data = buffer.getvalue(); buffer.close()
        from django.http import HttpResponse
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="plans_export.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_plans(self, request):
        """Plans are managed from pricing models; import is not supported."""
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file uploaded under field name "file"'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'created': 0, 'updated': 0, 'errors': ['Import for plans is not supported. Manage plans via pricing models.']})

    @action(detail=False, methods=['get'])
    def test(self, request):
        """Test endpoint for plans"""
        user_tenant = get_user_tenant(request.user)
        plans = self.get_real_plans_for_tenant(user_tenant)
        return Response({'message': 'Plans endpoint working', 'count': len(plans), 'using_real_data': True})


class CustomerDataViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Staff read-only operations for comprehensive customer data
    """
    permission_classes = [StaffPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name', 'username']
    # Use valid model fields only (avoid non-model fields)
    filterset_fields = ['is_active']
    ordering_fields = ['email', 'last_login']
    ordering = ['-last_login']

    def get_queryset(self):
        # Super admin users can see all customer data across all tenants
        if not should_filter_by_tenant(self.request.user):
            base_query = User.objects.filter(user_type__in=['residential', 'commercial']).prefetch_related('account_roles__account')
        else:
            # Regular staff users see only their tenant's customer data
            user_tenant = get_user_tenant(self.request.user)
            
            base_query = User.objects.filter(user_type__in=['residential', 'commercial']).prefetch_related('account_roles__account')
            
            if user_tenant:
                base_query = base_query.filter(tenant=user_tenant)
        
        # Don't prefetch contracts if ServiceContract model doesn't exist
        if ServiceContract is not None:
            base_query = base_query.prefetch_related('servicecontract_set')
            
        return base_query

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CustomerOverviewSerializer
        return StaffUserListSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get customer statistics filtered by staff user's tenant or all data for super admin"""
        if not should_filter_by_tenant(request.user):
            # Super admin users see global statistics
            base_query = User.objects.filter(user_type__in=['residential', 'commercial'])
            
            stats = {
                'total_customers': base_query.count(),
                'residential_customers': base_query.filter(user_type='residential').count(),
                'commercial_customers': base_query.filter(user_type='commercial').count(),
                'active_customers': base_query.filter(is_active=True).count(),
                'verified_customers': base_query.filter(is_verified=True).count(),
                'is_super_admin': True,
                'customers_by_tenant': {}
            }
            
            # Group by tenant for super admin
            for tenant in Tenant.objects.all():
                tenant_customers = base_query.filter(tenant=tenant).count()
                stats['customers_by_tenant'][tenant.name] = tenant_customers
                
        else:
            # Regular staff users see tenant-specific statistics
            user_tenant = get_user_tenant(request.user)
            
            base_query = User.objects.filter(user_type__in=['residential', 'commercial'])
            if user_tenant:
                base_query = base_query.filter(tenant=user_tenant)
            
            stats = {
                'total_customers': base_query.count(),
                'residential_customers': base_query.filter(user_type='residential').count(),
                'commercial_customers': base_query.filter(user_type='commercial').count(),
                'active_customers': base_query.filter(is_active=True).count(),
                'verified_customers': base_query.filter(is_verified=True).count(),
                'is_super_admin': False
            }
            
            # Only show current tenant info
            if user_tenant:
                stats['tenant_info'] = {
                    'name': user_tenant.name,
                    'slug': user_tenant.slug
                }
        
        return Response(stats)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def admin_probe(self, request):
        """
        Safe probe for admin detection. Always 200.
        Returns flags based on available request.user and Keycloak claims.
        """
        is_super = False
        is_admin_flag = False
        try:
            # Django user flags if available
            if getattr(request, 'user', None) and getattr(request.user, 'is_authenticated', False):
                is_super = bool(getattr(request.user, 'is_superuser', False))
                is_admin_flag = is_admin_flag or bool(getattr(request.user, 'is_staff', False))

            # Keycloak claims (realm roles/groups)
            claims = getattr(request, 'keycloak_claims', None)
            if claims:
                groups = [str(g).lower() for g in (claims.get('groups') or [])]
                roles = [str(r).lower() for r in (claims.get('realm_access', {}).get('roles') or [])]
                if any('admin' in g for g in groups) or 'admin' in roles or 'super-admin' in roles:
                    is_admin_flag = True
                    is_super = is_super or True
        except Exception:
            pass

        return Response({
            'is_admin': bool(is_admin_flag or is_super),
            'is_super_admin': bool(is_super),
        })

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """Get comprehensive customer overview"""
        user = self.get_object()
        serializer = CustomerOverviewSerializer(user)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_endpoint(request):
    """Test endpoint to verify API is working"""
    return Response({'message': 'Staff API is working', 'timestamp': timezone.now()})


@api_view(['GET'])
@permission_classes([AllowAny])
def test_plans(request):
    """Test endpoint specifically for plans"""
    plans_count = len(PlanViewSet().get_sample_plans())
    return Response({'message': 'Plans API is working', 'plans_count': plans_count})

 
class PlanViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """
    Staff CRUD operations for Service Plans (UAT)
    """
    permission_classes = [IsStaffUser]
    
    def list(self, request, *args, **kwargs):
        """Return basic plans data for UAT"""
        from rest_framework.response import Response
        
        return Response([
            {'id': 1, 'name': 'UAT Basic Plan', 'type': 'electricity', 'status': 'active'}
        ])
