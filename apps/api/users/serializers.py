from rest_framework import serializers
from django.contrib.auth import get_user_model
# JWT serializer removed - using Keycloak for authentication
from django.utils import timezone
from .models import Tenant, UserServiceContract, versioned_update, OnboardingProgress

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive user serializer for returning complete user context after authentication.
    Combines Django user data with cached Keycloak identity data.
    """
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()  # Legacy field for compatibility
    mobile = serializers.SerializerMethodField()  # Normalized field
    phone_verified = serializers.SerializerMethodField()  # Legacy field for compatibility  
    mobile_verified = serializers.SerializerMethodField()  # Normalized field
    email_verified = serializers.SerializerMethodField()
    is_onboarding_complete = serializers.SerializerMethodField()
    registration_method = serializers.SerializerMethodField()
    social_provider = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone', 'mobile',
            'phone_verified', 'mobile_verified', 'email_verified', 'is_onboarding_complete',
            'is_staff', 'registration_method', 'social_provider'
        ]

    def get_user_cache(self, obj):
        if not hasattr(obj, '_user_cache'):
            # Cache the user data on the object to avoid multiple lookups
            obj._user_cache = obj.get_cached_data() or {}
        return obj._user_cache

    def get_email(self, obj):
        return self.get_user_cache(obj).get('email', '')

    def get_first_name(self, obj):
        return self.get_user_cache(obj).get('first_name', '')

    def get_last_name(self, obj):
        return self.get_user_cache(obj).get('last_name', '')

    def get_phone(self, obj):
        # Legacy field - return mobile data for backward compatibility
        return self.get_user_cache(obj).get('phone', '')
    
    def get_mobile(self, obj):
        # Normalized field - primary mobile field
        return self.get_user_cache(obj).get('phone', '')  # UserCacheService stores mobile data in 'phone' field

    def get_phone_verified(self, obj):
        # Legacy field - return mobile_verified for backward compatibility
        return self.get_user_cache(obj).get('phone_verified', False)
    
    def get_mobile_verified(self, obj):
        # Normalized field - primary mobile verification field
        # FIXED: UserCacheService._extract_phone_verified() normalizes mobile_verified -> phone_verified in cache
        return self.get_user_cache(obj).get('phone_verified', False)

    def get_email_verified(self, obj):
        return self.get_user_cache(obj).get('email_verified', False)

    def get_registration_method(self, obj):
        return self.get_user_cache(obj).get('registration_method', 'email')

    def get_social_provider(self, obj):
        return self.get_user_cache(obj).get('social_provider', None)

    def get_is_onboarding_complete(self, obj):
        try:
            progress = OnboardingProgress.objects.filter(user=obj).first()
            return progress.is_completed if progress else False
        except OnboardingProgress.DoesNotExist:
            return False

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'identifier', 'user_number', 'email', 'mobile',
            'first_name', 'last_name', 'user_type',
            'is_email_verified', 'is_mobile_verified',
            'is_active'
        ]
        read_only_fields = ['id', 'identifier', 'user_number', 'is_active']



class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=[('residential', 'Residential'), ('commercial', 'Commercial')])

    class Meta:
        model = User
        fields = ['email', 'mobile', 'first_name', 'last_name', 'password', 'user_type']

    def create(self, validated_data):
        is_email_verified = self.context.get('is_email_verified', False)
        is_mobile_verified = self.context.get('is_mobile_verified', False)
        is_verified = self.context.get('is_verified', False)
        is_active = self.context.get('is_active', False)

        user = User.objects.create_user(
            email=validated_data['email'],
            mobile=validated_data['mobile'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            user_type=validated_data['user_type'],
        )

        # Manually set fields that are not part of create_user()
        user.is_email_verified = is_email_verified
        user.is_mobile_verified = is_mobile_verified
        user.is_verified = is_verified
        user.is_active = is_active
        user.save()

        return user



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data['email']
        password = data['password']
        
        # In Keycloak-first approach, authentication should go through Keycloak
        # This serializer should not be used for password-based login
        # Instead, redirect to Keycloak authentication
        raise serializers.ValidationError({
            "non_field_errors": "Password-based login is disabled. Please use Keycloak authentication."
        })


class LoginOTPRequestSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['email', 'mobile'])
    value = serializers.CharField()

    def validate(self, data):
        method = data['method']
        value = data['value']

        filter_kwargs = {method: value}
        user = User.objects.filter(**filter_kwargs).first()

        if not user:
            raise serializers.ValidationError({method: "No account found with this value."})
        if not user.is_active:
            raise serializers.ValidationError({method: "Account is inactive."})

        data['user'] = user
        return data


class LoginOTPVerifySerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['email', 'mobile'])
    value = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        method = data['method']
        value = data['value']
        otp = data['otp']

        user = User.objects.filter(**{method: value}).first()
        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        token_field = f"{method}_verification_token"
        sent_at_field = f"{method}_verification_sent_at"

        # Check token and expiry
        if getattr(user, token_field) != otp:
            raise serializers.ValidationError({"otp": "Incorrect OTP."})
        if getattr(user, sent_at_field) and (timezone.now() - getattr(user, sent_at_field)).seconds > 300:
            raise serializers.ValidationError({"otp": "OTP expired."})

        # Optional: mark verified
        if method == 'email':
            user.is_email_verified = True
        else:
            user.is_mobile_verified = True

        setattr(user, token_field, None)
        setattr(user, sent_at_field, None)

        user.save()
        return {"user": user}


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Use Keycloak-first approach to check if user exists
        try:
            from .models import Tenant
            from .keycloak_user_service import KeycloakUserService
            from django.conf import settings
            
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if tenant:
                environment = getattr(settings, 'ENVIRONMENT', 'uat')
                keycloak_service = KeycloakUserService(tenant=tenant, environment=environment)
                keycloak_user = keycloak_service.get_user_by_email(value)
                
                if not keycloak_user:
                    raise serializers.ValidationError("No user found with this email.")
            else:
                raise serializers.ValidationError("Service configuration error.")
                
        except Exception as e:
            raise serializers.ValidationError("Unable to validate email at this time.")
            
        return value



class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'mobile', 'first_name', 'last_name']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        changed_by = request.user if request and request.user.is_authenticated else None

        old_email = instance.email
        old_mobile = instance.mobile

        new_email = validated_data.get('email', old_email)
        new_mobile = validated_data.get('mobile', old_mobile)

        if new_email != old_email:
            UserChangeLog.objects.create(
                user=instance,
                field_changed='email',
                old_value=old_email,
                new_value=new_email,
                changed_by=changed_by
            )
            instance.email = new_email
            instance.is_email_verified = False
            instance.is_verified = False

        if new_mobile != old_mobile:
            UserChangeLog.objects.create(
                user=instance,
                field_changed='mobile',
                old_value=old_mobile,
                new_value=new_mobile,
                changed_by=changed_by
            )
            instance.mobile = new_mobile
            instance.is_mobile_verified = False
            instance.is_verified = False

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

# CustomTokenObtainPairSerializer removed - using Keycloak authentication only

class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model"""
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'business_number', 'tax_number',
            'contact_email', 'contact_phone', 'address', 'timezone',
            'currency', 'service_limits', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Enhanced user profile serializer with tenant information for unified login"""
    tenant = TenantSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    manager = serializers.SerializerMethodField()
    team_members = serializers.SerializerMethodField()
    groups = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'user_number', 'user_type', 'department', 'job_title',
            'tenant', 'manager', 'team_members', 'groups',
            'is_active', 'is_staff', 'is_superuser', 'is_verified'
        ]
        read_only_fields = [
            'id', 'user_number', 'full_name', 'tenant', 'manager',
            'team_members', 'groups', 'is_superuser'
        ]
    
    def get_manager(self, obj):
        if obj.manager:
            return {
                'id': str(obj.manager.id),
                'name': obj.manager.full_name,
                'email': obj.manager.email,
                'department': obj.manager.department
            }
        return None
    
    def get_team_members(self, obj):
        team_members = obj.team_members.filter(is_active=True)
        return [
            {
                'id': str(member.id),
                'name': member.full_name,
                'email': member.email,
                'department': member.department,
                'job_title': member.job_title
            }
            for member in team_members
        ]


class UserServiceContractSerializer(serializers.ModelSerializer):
    """Enhanced service contract serializer with versioning"""
    user = serializers.StringRelatedField(read_only=True)
    tenant = TenantSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = UserServiceContract
        fields = [
            'id', 'tenant', 'user', 'service_type', 'connection_id',
            'contract_name', 'contract_terms', 'signed_at', 'is_signed',
            'valid_from', 'valid_to', 'is_active', 'source',
            'created_by', 'updated_by', 'updated_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant', 'user', 'valid_from', 'valid_to',
            'created_by', 'updated_by', 'updated_reason',
            'created_at', 'updated_at'
        ]
    
    def get_is_active(self, obj):
        return obj.is_active()


class CreateUserServiceContractSerializer(serializers.Serializer):
    """Serializer for creating new service contracts"""
    service_type = serializers.ChoiceField(
        choices=[('power', 'Power'), ('broadband', 'Broadband'), ('mobile', 'Mobile')]
    )
    connection_id = serializers.CharField(max_length=100)
    contract_name = serializers.CharField(max_length=100)
    contract_terms = serializers.CharField()
    is_signed = serializers.BooleanField(default=True)
    
    def create(self, validated_data):
        user = self.context['request'].user
        tenant = user.get_tenant()
        
        if not tenant:
            raise serializers.ValidationError("User must be assigned to a tenant")
        
        # Use versioned update to create new contract
        filter_kwargs = {
            'tenant': tenant,
            'user': user,
            'service_type': validated_data['service_type'],
            'connection_id': validated_data['connection_id']
        }
        
        update_data = {
            'contract_name': validated_data['contract_name'],
            'contract_terms': validated_data['contract_terms'],
            'signed_at': validated_data.get('signed_at', timezone.now().date()),
            'is_signed': validated_data.get('is_signed', True),
        }
        
        contract = versioned_update(
            UserServiceContract,
            filter_kwargs,
            update_data,
            user=user,
            reason="New service contract created via API",
            source='api'
        )
        
        return contract


class UpdateUserServiceContractSerializer(serializers.Serializer):
    """Serializer for updating service contracts with versioning"""
    contract_name = serializers.CharField(max_length=100, required=False)
    contract_terms = serializers.CharField(required=False)
    is_signed = serializers.BooleanField(required=False)
    update_reason = serializers.CharField(max_length=255, required=False)
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        update_reason = validated_data.pop('update_reason', 'Contract updated via API')
        
        # Use versioned update to create new version
        filter_kwargs = {
            'tenant': instance.tenant,
            'user': instance.user,
            'service_type': instance.service_type,
            'connection_id': instance.connection_id
        }
        
        # Only include fields that were actually provided
        update_data = {}
        for field in ['contract_name', 'contract_terms', 'is_signed']:
            if field in validated_data:
                update_data[field] = validated_data[field]
        
        # Keep existing values for fields not being updated
        if 'contract_name' not in update_data:
            update_data['contract_name'] = instance.contract_name
        if 'contract_terms' not in update_data:
            update_data['contract_terms'] = instance.contract_terms
        if 'is_signed' not in update_data:
            update_data['is_signed'] = instance.is_signed
        
        # Always keep the original signed_at date
        update_data['signed_at'] = instance.signed_at
        
        new_contract = versioned_update(
            UserServiceContract,
            filter_kwargs,
            update_data,
            user=user,
            reason=update_reason,
            source='api'
        )
        
        return new_contract


class TenantStatsSerializer(serializers.Serializer):
    """Serializer for tenant statistics"""
    tenant = TenantSerializer(read_only=True)
    users = serializers.DictField(read_only=True)
    contracts = serializers.DictField(read_only=True)
    energy_data = serializers.DictField(read_only=True, required=False)
    
    class Meta:
        fields = ['tenant', 'users', 'contracts', 'energy_data']
