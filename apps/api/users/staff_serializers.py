"""
Staff Serializers for Utility Byte Platform
Provides serializers for staff CRUD operations on tenants, users, contracts, and customer data.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import uuid

from .models import (
    Tenant, TenantUserRole, Account, Address, UserAccountRole
)

# Import contract models
try:
    from core.contracts.models import ServiceContract
except ImportError:
    ServiceContract = None

User = get_user_model()


# =============================================================================
# TENANT SERIALIZERS
# =============================================================================

class TenantListSerializer(serializers.ModelSerializer):
    """Serializer for tenant list view"""
    users_count = serializers.SerializerMethodField()
    active_users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'business_number', 'contact_email',
            'contact_phone', 'timezone', 'currency', 'is_active',
            'users_count', 'active_users_count', 'created_at', 'updated_at'
        ]
    
    def get_users_count(self, obj):
        try:
            return obj.user_roles.count()
        except Exception:
            return 0
    
    def get_active_users_count(self, obj):
        try:
            return obj.user_roles.filter(user__is_active=True).count()
        except Exception:
            return 0


class TenantDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for tenant"""
    users_count = serializers.SerializerMethodField()
    # Back-compat fields expected by some frontend builds
    user_count = serializers.SerializerMethodField()
    active_users = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()
    accounts_count = serializers.SerializerMethodField()
    contracts_count = serializers.SerializerMethodField()
    user_roles = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'business_number', 'tax_number',
            'contact_email', 'contact_phone', 'address', 'timezone',
            'currency', 'service_limits', 'is_active',
            'users_count', 'user_count', 'active_users', 'staff_count', 'accounts_count', 'contracts_count',
            'user_roles', 'created_at', 'updated_at'
        ]
    
    def get_users_count(self, obj):
        """
        Count users associated to this tenant via explicit relations.
        The User model does not have a direct ForeignKey to Tenant,
        so we must count through TenantUserRole.
        """
        try:
            return obj.user_roles.count()
        except Exception:
            return 0

    # Aliases for older frontend fields
    def get_user_count(self, obj):
        return self.get_users_count(obj)
    
    def get_active_users(self, obj):
        try:
            return obj.user_roles.filter(user__is_active=True).count()
        except Exception:
            return 0
    
    def get_staff_count(self, obj):
        """
        Count staff users associated to this tenant via TenantUserRole.
        """
        try:
            return obj.user_roles.filter(user__is_staff=True).count()
        except Exception:
            return 0
    
    def get_accounts_count(self, obj):
        try:
            return obj.accounts.count()
        except Exception:
            return 0
    
    def get_contracts_count(self, obj):
        return 0
    
    def get_user_roles(self, obj):
        roles = obj.user_roles.select_related('user').all()
        return [
            {
                'id': str(role.id),
                'user': {
                    'id': str(role.user.id),
                    'email': role.user.email,
                    'full_name': f"{role.user.first_name} {role.user.last_name}".strip() or role.user.username or role.user.email,
                },
                'role': role.role,
                'permissions': {
                    'can_manage_users': role.can_manage_users,
                    'can_modify_settings': role.can_modify_settings,
                    'can_access_billing': role.can_access_billing,
                    'can_access_metering': role.can_access_metering,
                    'can_manage_contracts': role.can_manage_contracts,
                }
            }
            for role in roles
        ]


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tenants"""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'slug', 'subdomain', 'business_number', 'tax_number',
            'contact_email', 'contact_phone', 'address', 'timezone',
            'currency', 'service_limits', 'is_active'
        ]
    
    def validate_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A tenant with this slug already exists.")
        return value

    def validate_subdomain(self, value):
        if not value:
            return value
        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("A tenant with this subdomain already exists.")
        return value

    def create(self, validated_data):
        # Auto-fill subdomain from slug if missing
        subdomain = validated_data.get('subdomain')
        if not subdomain:
            slug = validated_data.get('slug') or ''
            validated_data['subdomain'] = slug[:50]
        return super().create(validated_data)


class TenantUserRoleSerializer(serializers.ModelSerializer):
    """Serializer for tenant user roles"""
    user_email = serializers.EmailField(write_only=True)
    user_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = TenantUserRole
        fields = [
            'id', 'user_email', 'user_details', 'role',
            'can_manage_users', 'can_modify_settings', 'can_access_billing',
            'can_access_metering', 'can_manage_contracts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_details(self, obj):
        return {
            'id': str(obj.user.id),
            'email': obj.user.email,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username or obj.user.email,
        }
    
    def validate_user_email(self, value):
        try:
            user = User.objects.get(email=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
    
    def create(self, validated_data):
        user = validated_data.pop('user_email')
        validated_data['user'] = user
        return super().create(validated_data)


# =============================================================================
# USER SERIALIZERS
# =============================================================================

class StaffUserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view with Keycloak identity data"""
    # Add Keycloak identity fields using SerializerMethodField
    email = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()
    account_number = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name', 'phone',
            'account_number', 'email_verified', 'phone_verified',
            'is_active', 'is_staff', 'date_joined', 'last_keycloak_sync'
        ]
    
    def get_email(self, obj):
        """Get email from Keycloak cache"""
        return obj.get_email()
    
    def get_full_name(self, obj):
        """Get full name from Keycloak cache"""
        return obj.get_full_name()
    
    def get_first_name(self, obj):
        """Get first name from Keycloak cache"""
        return obj.get_first_name()
    
    def get_last_name(self, obj):
        """Get last name from Keycloak cache"""
        return obj.get_last_name()
    
    def get_phone(self, obj):
        """Get phone from Keycloak cache"""
        return obj.get_phone()
    
    def get_email_verified(self, obj):
        """Get email verification status from Keycloak cache"""
        return obj.get_verification_status().get('email_verified', False)
    
    def get_phone_verified(self, obj):
        """Get phone verification status from Keycloak cache"""
        return obj.get_verification_status().get('phone_verified', False)
    
    def get_account_number(self, obj):
        """Get primary account number for this user"""
        try:
            # Get the first account associated with this user
            from .models import UserAccountRole
            account_role = UserAccountRole.objects.filter(user=obj).first()
            if account_role and account_role.account:
                return account_role.account.account_number
            return None
        except Exception:
            return None
    
    def get_accounts_count(self, obj):
        return obj.account_roles.count()

    def get_tenant_name(self, obj):
        # Direct tenant FK if present
        try:
            if getattr(obj, 'tenant', None):
                return obj.tenant.name
        except Exception:
            pass
        # Derive from tenant roles
        try:
            role = obj.tenant_roles.select_related('tenant').first()
            if role and role.tenant:
                return role.tenant.name
        except Exception:
            pass
        # Derive from accounts' tenant
        try:
            role = obj.account_roles.select_related('account__tenant').first()
            if role and getattr(role, 'account', None) and getattr(role.account, 'tenant', None):
                return role.account.tenant.name
        except Exception:
            pass
        return None


class StaffUserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user with Keycloak identity data"""
    # Computed/derived fields to avoid referencing non-model fields
    identifier = serializers.SerializerMethodField()
    user_number = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    # Keycloak identity fields
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()

    tenant = serializers.SerializerMethodField()
    groups = serializers.StringRelatedField(many=True, read_only=True)
    account_roles = serializers.SerializerMethodField()
    tenant_roles = serializers.SerializerMethodField()
    
    # Relationship counts for the detail view
    accounts_count = serializers.SerializerMethodField()
    contracts_count = serializers.SerializerMethodField()
    connections_count = serializers.SerializerMethodField()
    plans_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'identifier', 'user_number', 'email', 'phone',
            'first_name', 'last_name', 'full_name', 'tenant',
            'groups', 'account_roles', 'tenant_roles',
            'accounts_count', 'contracts_count', 'connections_count', 'plans_count',
            'is_active', 'is_staff', 'is_superuser', 'email_verified',
            'phone_verified', 'last_keycloak_sync',
            'last_login'
        ]

    def get_identifier(self, obj):
        # Use primary key (Keycloak ID) as the stable identifier
        return obj.id

    def get_user_number(self, obj):
        # Derive a simple display number from UUID for UI friendliness
        try:
            return str(getattr(obj, 'id', ''))[:8]
        except Exception:
            return None

    def get_last_login(self, obj):
        # Enhanced last login detection with multiple fallback methods
        
        # Method 1: Use last_keycloak_sync as primary indicator
        last_sync = getattr(obj, 'last_keycloak_sync', None)
        if last_sync:
            return last_sync
        
        # Method 2: Fall back to updated_at if recently updated
        updated_at = getattr(obj, 'updated_at', None)
        if updated_at:
            # Only use updated_at if it's recent (within last 30 days)
            from django.utils import timezone
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            if updated_at > thirty_days_ago:
                return updated_at
        
        # Method 3: Fall back to created_at for new users
        created_at = getattr(obj, 'created_at', None)
        if created_at:
            return created_at
        
        # Method 4: Return None if no login information available
        return None
    
    def get_email(self, obj):
        """Get email from Keycloak cache"""
        return obj.get_email()
    
    def get_phone(self, obj):
        """Get phone from Keycloak cache"""
        return obj.get_phone()
    
    def get_first_name(self, obj):
        """Get first name from Keycloak cache"""
        return obj.get_first_name()
    
    def get_last_name(self, obj):
        """Get last name from Keycloak cache"""
        return obj.get_last_name()
    
    def get_full_name(self, obj):
        """Get full name from Keycloak cache"""
        return obj.get_full_name()
    
    def get_email_verified(self, obj):
        """Get email verification status from Keycloak cache"""
        return obj.get_verification_status().get('email_verified', False)
    
    def get_phone_verified(self, obj):
        """Get phone verification status from Keycloak cache"""
        return obj.get_verification_status().get('phone_verified', False)

    def get_tenant(self, obj):
        # Enhanced tenant detection with multiple fallback methods
        tenant = None
        
        # Method 1: Try TenantUserRole (tenant_roles)
        try:
            tenant_role = obj.tenant_roles.select_related('tenant').first()
            if tenant_role and tenant_role.tenant:
                tenant = tenant_role.tenant
        except Exception:
            pass
        
        # Method 2: Try UserTenantRole (if exists)
        if not tenant:
            try:
                user_tenant_role = getattr(obj, 'usertenantrole_set', None)
                if user_tenant_role:
                    role = user_tenant_role.select_related('tenant').first()
                    if role and role.tenant:
                        tenant = role.tenant
            except Exception:
                pass
        
        # Method 3: Fall back to UserAccountRole
        if not tenant:
            try:
                account_role = obj.account_roles.select_related('account__tenant').first()
                if account_role and account_role.account and account_role.account.tenant:
                    tenant = account_role.account.tenant
            except Exception:
                pass
        
        # Method 4: Try direct tenant FK if model has it
        if not tenant:
            try:
                if hasattr(obj, 'tenant') and obj.tenant:
                    tenant = obj.tenant
            except Exception:
                pass
        
        # Method 5: Look for default tenant if user has no associations
        if not tenant:
            try:
                from users.models import Tenant
                default_tenant = Tenant.objects.filter(slug='utility-byte-default').first()
                if default_tenant:
                    tenant = default_tenant
            except Exception:
                pass
        
        if tenant:
            return {
                'id': str(tenant.id),
                'name': tenant.name,
                'slug': tenant.slug,
            }
        
        # Debug information for troubleshooting
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"No tenant found for user {obj.id}. Tenant roles: {obj.tenant_roles.count()}, Account roles: {obj.account_roles.count()}")
        
        return None
    
    def get_account_roles(self, obj):
        return [
            {
                'id': str(role.id),
                'account_number': role.account.account_number,
                'role': role.role,
                'permissions': {
                    'can_manage_services': role.can_manage_services,
                    'can_manage_users': role.can_manage_users,
                    'can_manage_billing': role.can_manage_billing,
                    'can_view_usage': role.can_view_usage,
                }
            }
            for role in obj.account_roles.select_related('account').all()
        ]
    
    def get_tenant_roles(self, obj):
        return [
            {
                'id': str(role.id),
                'tenant_name': role.tenant.name,
                'role': role.role,
                'permissions': {
                    'can_manage_users': role.can_manage_users,
                    'can_modify_settings': role.can_modify_settings,
                    'can_access_billing': role.can_access_billing,
                    'can_access_metering': role.can_access_metering,
                    'can_manage_contracts': role.can_manage_contracts,
                }
            }
            for role in obj.tenant_roles.select_related('tenant').all()
        ]

    def get_accounts_count(self, obj):
        """Get the count of accounts associated with this user"""
        from users.models import Account
        return Account.objects.filter(user_roles__user=obj).distinct().count()
    
    def get_contracts_count(self, obj):
        """Get the count of contracts associated with this user through their accounts"""
        try:
            from core.contracts.models import ServiceContract
            from users.models import Account
            user_accounts = Account.objects.filter(user_roles__user=obj).distinct()
            return ServiceContract.objects.filter(account__in=user_accounts).count()
        except Exception:
            return 0
    
    def get_connections_count(self, obj):
        """Get the count of connections associated with this user through their contracts"""
        try:
            from users.models import Account
            from core.contracts.models import ServiceContract
            from core.contracts.plan_assignments import ContractConnectionAssignment
            
            user_accounts = Account.objects.filter(user_roles__user=obj).distinct()
            user_contracts = ServiceContract.objects.filter(account__in=user_accounts)
            return ContractConnectionAssignment.objects.filter(contract__in=user_contracts).count()
        except Exception:
            return 0
    
    def get_plans_count(self, obj):
        """Get the count of plans assigned to this user through their contracts"""
        try:
            from users.models import Account
            from core.contracts.models import ServiceContract
            from core.contracts.plan_assignments import ContractPlanAssignment
            
            user_accounts = Account.objects.filter(user_roles__user=obj).distinct()
            user_contracts = ServiceContract.objects.filter(account__in=user_accounts)
            return ContractPlanAssignment.objects.filter(contract__in=user_contracts).count()
        except Exception:
            return 0


class StaffUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    password = serializers.CharField(write_only=True)
    tenant_id = serializers.UUIDField(required=False)

    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'phone',
            'tenant_id', 'is_active', 'is_staff'
        ]
    
    def validate_tenant_id(self, value):
        if value:
            try:
                return Tenant.objects.get(id=value)
            except Tenant.DoesNotExist:
                raise serializers.ValidationError("Tenant does not exist.")
        return None
    
    def validate_manager_email(self, value):
        if value:
            try:
                return User.objects.get(email=value, is_staff=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("Manager with this email does not exist or is not staff.")
        return None
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        tenant = validated_data.pop('tenant_id', None)
        manager = validated_data.pop('manager_email', None)
        # Generate a local keycloak_id for staff-created users in UAT
        generated_kid = str(uuid.uuid4())
        # Prepare fields for create_user, remapping and dropping unsupported keys
        create_fields = {k: v for k, v in validated_data.items() if k != 'password'}
        # Map mobile -> phone (model field)
        if 'mobile' in create_fields:
            create_fields['phone'] = create_fields.pop('mobile')
        # Drop non-model fields to avoid unexpected kwarg errors
        for drop_key in ['user_type', 'department', 'job_title']:
            create_fields.pop(drop_key, None)
        from django.db import IntegrityError
        try:
            user = User.objects.create_user(keycloak_id=generated_kid, email=validated_data.get('email'), **create_fields)
        except IntegrityError:
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        except TypeError as te:
            # Provide clearer feedback if unexpected fields slip through
            raise serializers.ValidationError({'detail': f'Invalid field(s) in request: {str(te)}'})
        except Exception as e:
            raise serializers.ValidationError({'detail': str(e)})
        # We cannot set Django password (disabled). Ignore password locally.
        # Persist minimal relations
        if tenant:
            try:
                from .models import TenantUserRole
                # Use valid role per choices: 'staff' for staff users, else 'viewer'
                role_value = 'staff' if bool(validated_data.get('is_staff')) else 'viewer'
                TenantUserRole.objects.get_or_create(tenant=tenant, user=user, defaults={'role': role_value})
            except Exception:
                pass
        # Manager relation not present on model; skip assigning
        user.save()
        return user


class StaffUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    tenant_id = serializers.UUIDField(required=False)

    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone', 'tenant_id',
            'is_active', 'is_staff'
        ]
    
    def validate_tenant_id(self, value):
        if value:
            try:
                return Tenant.objects.get(id=value)
            except Tenant.DoesNotExist:
                raise serializers.ValidationError("Tenant does not exist.")
        return None
    
    def validate_manager_email(self, value):
        if value:
            try:
                return User.objects.get(email=value, is_staff=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("Manager with this email does not exist or is not staff.")
        return None
    
    def update(self, instance, validated_data):
        tenant = validated_data.pop('tenant_id', None)
        manager = validated_data.pop('manager_email', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if tenant is not None:
            instance.tenant = tenant
        if manager is not None:
            instance.manager = manager
            
        instance.save()
        return instance


# =============================================================================
# ACCOUNT SERIALIZERS
# =============================================================================

class AccountListSerializer(serializers.ModelSerializer):
    """Serializer for account list view - parent entity without child details"""
    tenant = serializers.SerializerMethodField()
    primary_user = serializers.SerializerMethodField()
    connections_count = serializers.SerializerMethodField()
    contracts_count = serializers.IntegerField(read_only=True)
    address = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'account_type', 'tenant', 'primary_user',
            'billing_cycle', 'billing_day', 'status', 'connections_count', 
            'contracts_count', 'address', 'created_at'
        ]
    
    def get_tenant(self, obj):
        if obj.tenant:
            return {
                'id': str(obj.tenant.id),
                'name': obj.tenant.name,
            }
        return None
    
    def get_primary_user(self, obj):
        """Get primary user for the account using Keycloak data"""
        primary_role = obj.user_roles.filter(role__in=['owner', 'primary']).first()
        if primary_role:
            user = primary_role.user
            email = user.get_email()
            first_name = user.get_first_name()
            last_name = user.get_last_name()
            full_name = user.get_full_name()
            phone = user.get_phone()
            
            return {
                'id': str(user.id),
                'email': email,
                'full_name': full_name or email or str(user.id)[:8],
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'mobile': phone,  # Alias for backward compatibility
            }
        return None
    
    def get_connections_count(self, obj):
        # Connections are in tenant schemas, so we can't easily count them
        # Return 0 for now - this could be calculated separately if needed
        return 0
    
    def get_address(self, obj):
        # Account has a billing_address field that links to Address model
        if obj.billing_address:
            return str(obj.billing_address)  # Uses Address.__str__ method
            
        return None


class AccountDetailSerializer(AccountListSerializer):
    """Detailed serializer for account"""
    tenant = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    user_roles = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()
    connections = serializers.SerializerMethodField()
    contracts = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'account_type', 'tenant',
            'billing_cycle', 'billing_day', 'status',
            'valid_from', 'valid_to', 'metadata', 'created_by',
            'user_roles', 'addresses', 'connections', 'contracts',
            'created_at', 'updated_at'
        ]
    
    def get_tenant(self, obj):
        return {
            'id': str(obj.tenant.id),
            'name': obj.tenant.name,
            'slug': obj.tenant.slug,
        }
    
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                'id': str(obj.created_by.id),
                'email': obj.created_by.email,
                'full_name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username or obj.created_by.email,
            }
        return None
    
    def get_user_roles(self, obj):
        return [
            {
                'id': str(role.id),
                'user': {
                    'id': str(role.user.id),
                    'email': role.user.email,
                    'full_name': f"{role.user.first_name} {role.user.last_name}".strip() or role.user.username or role.user.email,
                },
                'role': role.role,
                'permissions': {
                    'can_manage_services': role.can_manage_services,
                    'can_manage_users': role.can_manage_users,
                    'can_manage_billing': role.can_manage_billing,
                    'can_view_usage': role.can_view_usage,
                }
            }
            for role in obj.user_roles.select_related('user').all()
        ]
    
    def get_addresses(self, obj):
        if obj.billing_address:
            return AddressSerializer([obj.billing_address], many=True).data
        return []
    
    def get_connections(self, obj):
        return []
    
    def get_contracts(self, obj):
        return []


class AccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating accounts"""
    tenant_id = serializers.UUIDField()
    primary_user_email = serializers.EmailField(write_only=True)
    account_number = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'tenant_id', 'account_type', 'billing_cycle', 'billing_day',
            'primary_user_email', 'status', 'metadata'
        ]
    
    def validate_tenant_id(self, value):
        try:
            return Tenant.objects.get(id=value)
        except Tenant.DoesNotExist:
            raise serializers.ValidationError("Tenant does not exist.")
    
    def validate_primary_user_email(self, value):
        try:
            return User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
    
    def create(self, validated_data):
        tenant = validated_data.pop('tenant_id')
        primary_user = validated_data.pop('primary_user_email')
        
        # Create account (account_number will be auto-generated if not provided)
        account = Account.objects.create(tenant=tenant, **validated_data)
        
        # Create primary user role
        UserAccountRole.objects.create(
            tenant=tenant,
            user=primary_user,
            account=account,
            role='owner',  # Changed from 'primary' to 'owner' to match ROLE_CHOICES
            can_manage_services=True,
            can_manage_users=True,
            can_manage_billing=True,
            can_view_usage=True
        )
        
        return account


class AccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating accounts"""
    
    class Meta:
        model = Account
        fields = [
            'account_type', 'billing_cycle', 'billing_day',
            'status', 'metadata'
        ]


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for address details"""

    class Meta:
        model = Address
        fields = [
            'id', 'address_line1', 'address_line2', 'suburb', 'city',
            'region', 'postal_code', 'country', 'address_type',
            'is_primary', 'latitude', 'longitude', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# CONNECTION AND PLAN SERIALIZERS (Child Relationships)
# =============================================================================

class ConnectionListSerializer(serializers.Serializer):
    """Serializer for connection list view (child relationship)"""
    id = serializers.UUIDField()
    service_type = serializers.CharField()
    connection_identifier = serializers.CharField()
    status = serializers.CharField()
    
    # Service-specific fields
    icp_code = serializers.CharField(required=False, allow_null=True)
    mobile_number = serializers.CharField(required=False, allow_null=True)
    ont_serial = serializers.CharField(required=False, allow_null=True)
    
    # Plan information (if available)
    plan = serializers.SerializerMethodField()
    
    def get_plan(self, obj):
        """Get associated plan for this connection"""
        try:
            # Try to get plan based on service type
            if obj.get('service_type') == 'electricity':
                from web_support.public_pricing.models import ElectricityPlan
                # Look for plan associated with this connection
                # This is a simplified approach - in real implementation, 
                # you'd have a proper connection-to-plan relationship
                plan = ElectricityPlan.objects.filter(
                    city__icontains='wellington',  # Example city
                    is_active=True
                ).first()
                if plan:
                    return {
                        'id': str(plan.pricing_id),
                        'name': plan.name,
                        'plan_type': plan.plan_type,
                        'base_rate': float(plan.base_rate),
                        'monthly_charge': float(plan.monthly_charge) if hasattr(plan, 'monthly_charge') else None,
                    }
            elif obj.get('service_type') == 'broadband':
                from web_support.public_pricing.models import BroadbandPlan
                plan = BroadbandPlan.objects.filter(
                    city__icontains='wellington',  # Example city
                    is_active=True
                ).first()
                if plan:
                    return {
                        'id': str(plan.pricing_id),
                        'name': plan.name,
                        'plan_type': plan.plan_type,
                        'base_rate': float(plan.base_rate),
                        'download_speed': plan.download_speed,
                        'upload_speed': plan.upload_speed,
                        'data_allowance': plan.data_allowance,
                    }
            elif obj.get('service_type') == 'mobile':
                from web_support.public_pricing.models import MobilePlan
                plan = MobilePlan.objects.filter(is_active=True).first()
                if plan:
                    return {
                        'id': str(plan.pricing_id),
                        'name': plan.name,
                        'plan_type': plan.plan_type,
                        'base_rate': float(plan.base_rate),
                        'monthly_charge': float(plan.monthly_charge) if hasattr(plan, 'monthly_charge') else None,
                    }
        except ImportError:
            pass
        return None


class AccountConnectionSerializer(serializers.Serializer):
    """Detailed serializer for account connections"""
    id = serializers.UUIDField()
    service_type = serializers.CharField()
    connection_identifier = serializers.CharField()
    status = serializers.CharField()
    
    # Service address
    service_address = serializers.SerializerMethodField()
    
    # Service-specific details
    service_details = serializers.SerializerMethodField()
    
    # Associated plan
    plan = serializers.SerializerMethodField()
    
    def get_service_address(self, obj):
        """Get service address for this connection"""
        if hasattr(obj, 'service_address') and obj.service_address:
            addr = obj.service_address
            return {
                'id': str(addr.id),
                'address_line1': addr.address_line1,
                'city': addr.city,
                'postal_code': addr.postal_code,
            }
        return None
    
    def get_service_details(self, obj):
        """Get service-specific details"""
        details = {}
        if obj.service_type == 'electricity':
            details.update({
                'icp_code': obj.icp_code,
                'gxp_code': obj.gxp_code,
                'network_code': obj.network_code,
            })
        elif obj.service_type == 'broadband':
            details.update({
                'ont_serial': obj.ont_serial,
                'circuit_id': obj.circuit_id,
                'connection_type': obj.connection_type,
            })
        elif obj.service_type == 'mobile':
            details.update({
                'mobile_number': obj.mobile_number,
                'sim_id': obj.sim_id,
                'imei': obj.imei,
            })
        return details
    
    def get_plan(self, obj):
        """Get associated plan - same logic as ConnectionListSerializer"""
        # Reuse the plan logic from ConnectionListSerializer
        serializer = ConnectionListSerializer()
        return serializer.get_plan({
            'service_type': obj.service_type,
            'connection_identifier': obj.connection_identifier
        })


# =============================================================================
# CUSTOMER DATA SERIALIZERS
# =============================================================================

class CustomerOverviewSerializer(serializers.ModelSerializer):
    """Comprehensive customer overview serializer"""
    tenant = serializers.SerializerMethodField()
    accounts = serializers.SerializerMethodField()
    contracts = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'user_number',
            'user_type', 'mobile', 'tenant', 'is_active', 'is_verified',
            'accounts', 'contracts', 'addresses',
            'last_login'
        ]
    
    def get_tenant(self, obj):
        if obj.tenant:
            return {
                'id': str(obj.tenant.id),
                'name': obj.tenant.name,
            }
        return None
    
    def get_accounts(self, obj):
        return AccountListSerializer(obj.accounts.all(), many=True).data
    
    def get_contracts(self, obj):
        return []
    
    def get_addresses(self, obj):
        # Get addresses through accounts
        addresses = set()
        for account in obj.accounts.all():
            if account.billing_address:
                addresses.add(account.billing_address)
        return AddressSerializer(list(addresses), many=True).data


class CustomerStatsSerializer(serializers.Serializer):
    """Serializer for customer statistics"""
    total_customers = serializers.IntegerField()
    residential_customers = serializers.IntegerField()
    commercial_customers = serializers.IntegerField()
    active_customers = serializers.IntegerField()
    verified_customers = serializers.IntegerField()
    customers_by_tenant = serializers.DictField()


# =============================================================================
# CONTRACT SERIALIZERS
# =============================================================================

class ServiceContractListSerializer(serializers.ModelSerializer):
    """Serializer for service contract list view"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    customer_name = serializers.SerializerMethodField()
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    
    class Meta:
        model = ServiceContract
        fields = [
            'id', 'contract_number', 'contract_type', 'service_name',
            'status', 'start_date', 'end_date', 'tenant_name',
            'customer_name', 'account_number', 'base_charge',
            'created_at', 'updated_at'
        ]
    
    def get_customer_name(self, obj):
        """Get customer name from account's primary user"""
        if obj.account and hasattr(obj.account, 'user_roles'):
            # Get the primary user from account roles
            primary_role = obj.account.user_roles.filter(role__in=['primary', 'owner']).first()
            if primary_role and primary_role.user:
                user = primary_role.user
                # In Keycloak-first setup, user profile data is not stored in Django
                # Return user ID instead of name fields that don't exist
                return str(user.id)
            # Fallback to first user if no primary user
            first_role = obj.account.user_roles.first()
            if first_role and first_role.user:
                user = first_role.user
                return str(user.id)
        return None


class ServiceContractDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for service contract"""
    tenant = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceContract
        fields = [
            'id', 'contract_number', 'contract_type', 'service_name',
            'description', 'status', 'start_date', 'end_date',
            'billing_frequency', 'billing_day', 'base_charge',
            'deposit_required', 'credit_limit', 'valid_from', 'valid_to',
            'tenant', 'account', 'customer', 'created_by', 'updated_by',
            'metadata', 'created_at', 'updated_at'
        ]
    
    def get_tenant(self, obj):
        if obj.tenant:
            return {
                'id': str(obj.tenant.id),
                'name': obj.tenant.name,
                'slug': obj.tenant.slug,
            }
        return None
    
    def get_account(self, obj):
        if obj.account:
            return {
                'id': str(obj.account.id),
                'account_number': obj.account.account_number,
                'account_type': obj.account.account_type,
                'status': obj.account.status,
            }
        return None
    
    def get_customer(self, obj):
        """Get customer details from account's primary user"""
        if obj.account and hasattr(obj.account, 'user_roles'):
            # Get the primary user from account roles
            primary_role = obj.account.user_roles.filter(role__in=['primary', 'owner']).first()
            if primary_role and primary_role.user:
                user = primary_role.user
                return {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username or user.email,
                    'mobile': user.mobile,
                }
            # Fallback to first user if no primary user
            first_role = obj.account.user_roles.first()
            if first_role and first_role.user:
                user = first_role.user
                return {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username or user.email,
                    'mobile': user.mobile,
                }
        return None
    
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                'id': str(obj.created_by.id),
                'email': obj.created_by.email,
                'full_name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username or obj.created_by.email,
            }
        return None
    
    def get_updated_by(self, obj):
        if obj.updated_by:
            return {
                'id': str(obj.updated_by.id),
                'email': obj.updated_by.email,
                'full_name': f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.username or obj.updated_by.email,
            }
        return None


class ServiceContractCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating service contracts"""
    tenant_id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    
    class Meta:
        model = ServiceContract
        fields = [
            'contract_number', 'contract_type', 'service_name',
            'description', 'status', 'start_date', 'end_date',
            'billing_frequency', 'billing_day', 'base_charge',
            'deposit_required', 'credit_limit', 'tenant_id', 'account_id',
            'metadata'
        ]
    
    def validate_tenant_id(self, value):
        try:
            tenant = Tenant.objects.get(id=value)
            return tenant
        except Tenant.DoesNotExist:
            raise serializers.ValidationError("Tenant with this ID does not exist.")
    
    def validate_account_id(self, value):
        try:
            account = Account.objects.get(id=value)
            return account
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account with this ID does not exist.")
    
    def create(self, validated_data):
        tenant = validated_data.pop('tenant_id')
        account = validated_data.pop('account_id')
        validated_data['tenant'] = tenant
        validated_data['account'] = account
        
        # Set created_by if available in context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        return super().create(validated_data) 