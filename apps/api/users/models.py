import uuid
import random
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import date
import logging
from django.contrib.auth.models import AbstractUser
import secrets
from decouple import config

logger = logging.getLogger(__name__)

# ===========================
# MULTI-TENANCY SUPPORT MODEL
# ===========================

class Tenant(models.Model):
    """
    Multi-tenant support with client-based white-label branding.
    Each tenant represents a separate brand/utility company with its own Keycloak client.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Utility company name")
    slug = models.SlugField(unique=True, help_text="URL-safe identifier")
    subdomain = models.CharField(max_length=50, unique=True, help_text="Subdomain for this tenant")
    
    # Keycloak client-based tenancy within environment realms
    keycloak_client_id_uat = models.CharField(max_length=128, null=True, blank=True,
                                             help_text="Keycloak client ID for UAT environment",
                                             default='customer-uat-portal')
    keycloak_client_id_live = models.CharField(max_length=128, null=True, blank=True,
                                              help_text="Keycloak client ID for Live environment", 
                                              default='customer-live-portal')
    
    is_primary_brand = models.BooleanField(default=False, 
                                          help_text="True if this is the main SpotOn brand")
    
    REALM_MAPPING = {
        'uat': 'spoton-uat',
        'live': 'spoton-prod', 
        'staff': 'spoton-staff'
    }
    
    primary_domain = models.CharField(max_length=255, unique=True, null=True, blank=True,
                                     help_text="Primary domain for this tenant (e.g., brand.spoton.co.nz)")
    additional_domains = models.JSONField(default=list, blank=True,
                                         help_text="Additional domains for this tenant")
    
    branding_config = models.JSONField(default=dict, blank=True, help_text="React app branding configuration")
    
    business_number = models.CharField(max_length=50, blank=True, help_text="Business registration number")
    tax_number = models.CharField(max_length=50, blank=True, help_text="Tax identification number")
    
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    timezone = models.CharField(max_length=50, default='Pacific/Auckland')
    currency = models.CharField(max_length=3, default='NZD')
    
    service_limits = models.JSONField(
        default=dict,
        help_text="Service limits per user type (e.g., {'power': 3, 'broadband': 2})"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_tenant'
        ordering = ['name']

    def __str__(self):
        primary_indicator = " [PRIMARY]" if self.is_primary_brand else ""
        return f"{self.name}{primary_indicator}"

    def get_service_limit(self, service_type):
        default_limits = {'power': 3, 'broadband': 2, 'mobile': 5}
        return self.service_limits.get(service_type, default_limits.get(service_type, 1))
    
    def get_branding_config(self):
        spoton_default_config = {
            'theme': {
                'primary_color': '#2563eb', 'secondary_color': '#64748b', 'accent_color': '#0ea5e9',
                'background_color': '#ffffff', 'text_color': '#1e293b', 'border_color': '#e2e8f0'
            },
            'logos': {
                'main_logo': '/assets/spoton-logo.png', 'favicon': '/favicon.ico',
                'login_logo': '/assets/spoton-logo-light.png', 'header_logo': '/assets/spoton-logo-small.png'
            },
            'branding': {
                'company_name': 'SpotOn Energy', 'tagline': 'Your Energy Partner',
                'footer_text': '© 2024 SpotOn Energy. All rights reserved.',
                'support_email': 'support@spoton.co.nz', 'support_phone': '+64 9 123 4567'
            },
            'features': {
                'show_social_login': True, 'show_phone_verification': True,
                'enable_dark_mode': True, 'show_company_branding': True
            },
            'domains': { 'primary': self.primary_domain, 'additional': self.additional_domains },
            'keycloak': {
                'client_id_uat': self.keycloak_client_id_uat, 'client_id_live': self.keycloak_client_id_live,
                'realm_uat': 'spoton-uat', 'realm_live': 'spoton-prod'
            }
        }
        if self.is_primary_brand:
            if self.branding_config:
                allowed_overrides = ['theme', 'features']
                for key in allowed_overrides:
                    if key in self.branding_config:
                        spoton_default_config[key].update(self.branding_config[key])
            return spoton_default_config
        
        base_config = spoton_default_config.copy()
        base_config['branding'].update({
            'company_name': self.name, 'footer_text': f'© 2024 {self.name}. All rights reserved.',
            'support_email': self.contact_email or 'support@spoton.co.nz',
            'support_phone': self.contact_phone or '+64 9 123 4567'
        })
        if self.branding_config:
            self._deep_update(base_config, self.branding_config)
        return base_config
    
    def _deep_update(self, base_dict, update_dict):
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def matches_domain(self, domain):
        if self.primary_domain and domain == self.primary_domain:
            return True
        return domain in self.additional_domains
    
    @classmethod
    def get_by_domain(cls, domain):
        return cls.objects.filter(models.Q(primary_domain=domain) | models.Q(additional_domains__contains=[domain])).first()
    
    def get_client_id_for_environment(self, environment):
        if environment == 'uat': return self.keycloak_client_id_uat
        elif environment == 'live': return self.keycloak_client_id_live
        return None
    
    def get_realm_for_environment(self, environment):
        return self.REALM_MAPPING.get(environment, 'spoton-uat')
    
    @classmethod
    def get_by_client_id(cls, client_id, environment=None):
        if environment == 'uat':
            return cls.objects.filter(keycloak_client_id_uat=client_id).first()
        elif environment == 'live':
            return cls.objects.filter(keycloak_client_id_live=client_id).first()
        else:
            tenant = cls.objects.filter(keycloak_client_id_uat=client_id).first()
            if not tenant:
                tenant = cls.objects.filter(keycloak_client_id_live=client_id).first()
            return tenant
    
    def get_keycloak_config(self, environment='uat'):
        keycloak_base_url = config('KEYCLOAK_SERVER_URL', default='https://auth.spoton.co.nz')
        client_id = self.get_client_id_for_environment(environment)
        if not client_id:
            return None
        realm = self.get_realm_for_environment(environment)
        if environment == 'live':
            redirect_uri = 'https://live.spoton.co.nz/api/auth/keycloak/callback/'
        else:
            redirect_uri = 'https://uat.spoton.co.nz/api/auth/keycloak/callback/'
        
        client_secret = config(f'KEYCLOAK_CLIENT_SECRET_{environment.upper()}', default='')
        admin_username = config('KEYCLOAK_ADMIN_USERNAME', default='admin')
        admin_password = config('KEYCLOAK_ADMIN_PASSWORD', default='')
        admin_client_id = config('KEYCLOAK_ADMIN_CLIENT_ID', default='admin-cli')
        admin_client_secret = config('KEYCLOAK_ADMIN_CLIENT_SECRET', default='')

        logger.debug(f"[Tenant.get_keycloak_config] Admin Username: {admin_username}")
        logger.debug(f"[Tenant.get_keycloak_config] Admin Password: {'******' if admin_password else 'None'}")
        logger.debug(f"[Tenant.get_keycloak_config] Admin Client ID: {admin_client_id}")
        logger.debug(f"[Tenant.get_keycloak_config] Admin Client Secret: {'******' if admin_client_secret else 'None'}")
        
        return {
            'url': keycloak_base_url, 'realm': realm, 'client_id': client_id,
            'client_secret': client_secret, 'redirect_uri': redirect_uri, 'tenant_id': str(self.id),
            'tenant_name': self.name, 'environment': environment, 'admin_username': admin_username,
            'admin_password': admin_password, 'admin_client_id': admin_client_id, 'admin_client_secret': admin_client_secret,
        }

class UserManager(BaseUserManager):
    def create_user(self, keycloak_id, email=None, username=None, **extra_fields):
        """Create user with keycloak_id as the primary key (single ID architecture).

        Sanitizes incoming extra_fields to avoid unexpected keyword argument errors
        from legacy or external callers (e.g., 'is_onboarding_complete', 'mobile',
        'is_email_verified', 'is_mobile_verified').
        """
        if not keycloak_id:
            raise ValueError('Users must have a keycloak_id')
        
        # Use email as username if username not provided
        if not username:
            username = email or keycloak_id
            
        if not email:
            email = f"{keycloak_id}@example.com"  # Temporary email
        
        # Map legacy/external keys to model fields and drop unsupported keys
        key_map = {
            'mobile': 'phone',
            'is_email_verified': 'email_verified',
            'is_mobile_verified': 'phone_verified',
        }
        # Compute allowed field names for safety
        allowed_fields = {f.name for f in self.model._meta.get_fields() if hasattr(f, 'attname')}
        sanitized_fields = {}
        # Debug logging to catch unexpected fields during creation
        try:
            import logging
            logger = logging.getLogger(__name__)
            if extra_fields:
                logger.info(f"[UserManager.create_user] extra_fields received: {list(extra_fields.keys())}")
        except Exception:
            pass

        for k, v in (extra_fields or {}).items():
            mapped_key = key_map.get(k, k)
            if mapped_key in allowed_fields:
                sanitized_fields[mapped_key] = v
            else:
                # Silently ignore unknown fields like 'is_onboarding_complete'
                continue

        # Create model instance with sanitized fields only
        try:
            # Debug: log what we're about to create (keys only)
            try:
                logger.info(
                    f"[UserManager.create_user] creating with keys: base=['keycloak_id','username','email'] + {list(sanitized_fields.keys())}; "
                    f"allowed_has_onboarding={'is_onboarding_complete' in allowed_fields}"
                )
            except Exception:
                pass
            user = self.model(
                id=keycloak_id,  # Use keycloak_id as primary key directly
                **sanitized_fields
            )
        except TypeError as te:
            # Surface which keys might be causing issues
            try:
                logger = logging.getLogger(__name__)
                logger.exception(f"[UserManager.create_user] TypeError constructing User; sanitized_keys={list(sanitized_fields.keys())}")
            except Exception:
                pass
            raise
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    # Intercept generic create() usages to sanitize legacy fields too
    def create(self, **kwargs):  # type: ignore[override]
        import logging
        logger = logging.getLogger(__name__)
        # Drop legacy or unsupported keys if callers bypass create_user()
        for legacy_key in ['is_onboarding_complete', 'onboarding_complete']:
            if legacy_key in kwargs:
                logger.warning(f"[UserManager.create] Dropping unsupported kwarg '{legacy_key}' from create()")
                kwargs.pop(legacy_key, None)
        return super().create(**kwargs)
        
    def create_superuser(self, keycloak_id, email=None, username=None, **extra_fields):
        """Create superuser with keycloak_id"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(keycloak_id=keycloak_id, email=email, username=username, **extra_fields)
            
    def get_by_keycloak_id(self, keycloak_id):
        """Get user by keycloak_id - now uses primary key directly"""
        return self.get(id=keycloak_id)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Minimal Keycloak-first User model.
    Identity data (email, names, phone) is stored in Keycloak and accessed via UserCacheService.
    Django only stores what's needed for business logic and Django admin functionality.
    """
    
    def __init__(self, *args, **kwargs):
        # Defensive sanitization - drop any identity fields that should come from Keycloak
        import logging
        logger = logging.getLogger(__name__)

        # Drop identity fields that are now Keycloak-only
        identity_fields = [
            'email', 'email_verified', 'first_name', 'last_name', 
            'phone', 'phone_verified', 'username', 'mobile',
            'is_email_verified', 'is_mobile_verified', 'is_onboarding_complete', 'onboarding_complete'
        ]
        
        for field in identity_fields:
            if field in kwargs:
                logger.info(f"[User.__init__] Ignoring identity field '{field}' - use Keycloak/UserCacheService instead")
                kwargs.pop(field, None)

        # Compute allowed fields to strictly filter kwargs
        try:
            allowed_fields = {f.name for f in self._meta.get_fields() if hasattr(f, 'attname')}
        except Exception:
            allowed_fields = set()

        # Drop any remaining unsupported kwargs
        for key in list(kwargs.keys()):
            if key not in allowed_fields:
                logger.warning(f"[User.__init__] Dropping unknown kwarg '{key}' from constructor")
                kwargs.pop(key, None)
                
        super().__init__(*args, **kwargs)
    
    # PRIMARY KEY - Use Keycloak ID directly (true single ID architecture)
    id = models.CharField(max_length=64, primary_key=True, help_text="Keycloak subject identifier (sub claim)")
    
    # No separate keycloak_id field needed - id IS the Keycloak ID
    
    # DJANGO PERMISSIONS - Required for Django admin functionality
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # BUSINESS LOGIC FIELDS - Not stored in Keycloak
    keycloak_client_id = models.CharField(max_length=128, null=True, blank=True, help_text="Keycloak client ID for tenant context")
    preferred_tenant_slug = models.CharField(max_length=100, null=True, blank=True, help_text="User's preferred tenant slug")
    app_preferences = models.JSONField(default=dict, blank=True, help_text="User preferences specific to this application")
    
    # TIMESTAMPS - Ordered chronologically
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_keycloak_sync = models.DateTimeField(null=True, blank=True, help_text="Last time Keycloak data was synced")
    
    objects = UserManager()
    USERNAME_FIELD = 'id'  # Primary key is the Keycloak ID
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['id']  # Order by primary key (Keycloak ID)
        indexes = [
            # Primary key index is automatic, no need to explicitly create
            models.Index(fields=['is_active', 'is_staff'], name='users_user_permissions_idx'),
            models.Index(fields=['preferred_tenant_slug'], name='users_user_tenant_idx'),
            models.Index(fields=['last_keycloak_sync'], name='users_user_sync_idx'),
        ]
    
    def __str__(self):
        return f"User(id={self.id})"
    
    # Override AbstractBaseUser fields to disable them
    password = None  # Remove password field
    last_login = None  # Remove last_login field
    
    def set_password(self, raw_password):
        raise NotImplementedError("Password authentication disabled. Use Keycloak for authentication.")
        
    def check_password(self, raw_password):
        raise NotImplementedError("Password authentication disabled. Use Keycloak for authentication.")
    
    def get_cached_data(self):
        """
        Get user identity data from UserCacheService.
        This replaces the old sync methods - use this to get email, names, phone, etc.
        """
        try:
            from users.services import UserCacheService
            return UserCacheService.get_user_data(self.id)  # Single ID: id IS the Keycloak ID
        except Exception as e:
            logger.warning(f"Failed to get cached user data for {self.id}: {e}")
            return None
    
    def get_email(self):
        """Get user's email from Keycloak cache"""
        cached_data = self.get_cached_data()
        return cached_data.get('email', '') if cached_data else ''
    
    def get_first_name(self):
        """Get user's first name from Keycloak cache"""
        cached_data = self.get_cached_data()
        return cached_data.get('first_name', '') if cached_data else ''
    
    def get_last_name(self):
        """Get user's last name from Keycloak cache"""
        cached_data = self.get_cached_data()
        return cached_data.get('last_name', '') if cached_data else ''
    
    def get_full_name(self):
        """Get user's full name from Keycloak cache"""
        cached_data = self.get_cached_data()
        if cached_data:
            first_name = cached_data.get('first_name', '')
            last_name = cached_data.get('last_name', '')
            return f"{first_name} {last_name}".strip()
        return ''
    
    def get_phone(self):
        """Get user's phone from Keycloak cache"""
        cached_data = self.get_cached_data()
        return cached_data.get('phone', '') if cached_data else ''
    
    def is_phone_verified(self):
        """Check if user's phone is verified from Keycloak cache"""
        cached_data = self.get_cached_data()
        return cached_data.get('phone_verified', False) if cached_data else False
    
    def is_email_verified(self):
        """Check if user's email is verified from Keycloak cache"""
        cached_data = self.get_cached_data()
        return cached_data.get('email_verified', False) if cached_data else False
    
    def is_onboarding_complete(self):
        """Check if user's onboarding is complete from Keycloak cache"""
        cached_data = self.get_cached_data()
        return cached_data.get('is_onboarding_complete', False) if cached_data else False
    
    # Admin display methods
    def get_email_display(self):
        """Display method for Django admin"""
        return self.get_email() or 'No email'
    get_email_display.short_description = 'Email'
    
    def get_full_name_display(self):
        """Display method for Django admin"""
        return self.get_full_name() or 'No name'
    get_full_name_display.short_description = 'Full Name'
    
    def get_phone_display(self):
        """Display method for Django admin"""
        phone = self.get_phone()
        verified = self.is_phone_verified()
        status = " ✓" if verified else " ✗"
        return f"{phone}{status}" if phone else 'No phone'
    get_phone_display.short_description = 'Phone'
    
    def get_verification_status_display(self):
        """Display method for Django admin"""
        status = self.get_verification_status()
        email_status = "✓" if status.get('email_verified') else "✗"
        phone_status = "✓" if status.get('phone_verified') else "✗"
        return f"Email: {email_status}, Phone: {phone_status}"
    get_verification_status_display.short_description = 'Verification Status'
    
    def save(self, *args, **kwargs):
        """Override save - simplified since identity data is now in Keycloak only"""
        # Just save - no sync needed since identity data is cached from Keycloak
        super().save(*args, **kwargs)
        
    def get_tenant_roles(self, tenant=None):
        target_tenant = tenant or self.preferred_tenant
        if not target_tenant: return []
        return getattr(self, '_keycloak_roles', [])
        
    def has_client_role(self, role_name, client_id=None):
        """Check if user has a specific client role in Keycloak (to be implemented)"""
        return False
        
    def get_verification_status(self):
        """
        Get verification status from Keycloak cache.
        Returns dict with email_verified and phone_verified status.
        """
        cached_data = self.get_cached_data()
        if cached_data:
            return {
                'email_verified': cached_data.get('email_verified', False),
                'phone_verified': cached_data.get('phone_verified', False),
                'mobile_verified': cached_data.get('phone_verified', False)  # Alias for backward compatibility
            }
        return {
            'email_verified': False,
            'phone_verified': False,
            'mobile_verified': False
        }
    
    def update_sync_timestamp(self):
        """
        Update the last Keycloak sync timestamp.
        This is used by middleware to track when user data was last accessed.
        Identity data is now stored in Keycloak only and accessed via UserCacheService.
        """
        from django.utils import timezone
        self.last_keycloak_sync = timezone.now()
        self.save(update_fields=['last_keycloak_sync', 'updated_at'])
        logger.debug(f"[User.update_sync_timestamp] Updated sync timestamp for {self.id}")
    
    def sync_from_keycloak(self, keycloak_user_data):
        """
        Legacy method for backward compatibility.
        Now just updates the sync timestamp since identity data is in Keycloak only.
        """
        logger.info(f"[User.sync_from_keycloak] Legacy sync method called for {self.id} - updating timestamp only")
        
        # Only sync the is_active status since that affects Django permissions
        is_active = keycloak_user_data.get('enabled', True)
        updated_fields = []
        
        if self.is_active != is_active:
            self.is_active = is_active
            updated_fields.append('is_active')
        
        # Always update the sync timestamp
        from django.utils import timezone
        self.last_keycloak_sync = timezone.now()
        updated_fields.extend(['last_keycloak_sync', 'updated_at'])
        
        if updated_fields:
            self.save(update_fields=updated_fields)
            logger.info(f"[User.sync_from_keycloak] Updated user {self.id}: {updated_fields}")
    
    def check_keycloak_sync_status(self):
        """
        Check if this user's data is in sync with Keycloak.
        Returns dict with sync status and any discrepancies found.
        """
        if not self.id:
            return {
                'is_synced': False,
                'issues': ['No user ID set'],
                'last_sync': self.last_keycloak_sync
            }
        
        try:
            from django.conf import settings
            from .keycloak_admin import KeycloakAdminService
            
            # Get tenant and environment
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                return {
                    'is_synced': False,
                    'issues': ['No primary tenant found'],
                    'last_sync': self.last_keycloak_sync
                }
            
            environment = getattr(settings, 'ENVIRONMENT', 'uat')
            realm = f'spoton-{environment}'
            kc_admin = KeycloakAdminService(realm=realm)
            
            # Get user from Keycloak
            admin = kc_admin._get_admin_client()
            kc_user = admin.get_user(self.id)
            
            if not kc_user:
                return {
                    'is_synced': False,
                    'issues': ['User not found in Keycloak'],
                    'last_sync': self.last_keycloak_sync
                }
            
            issues = []
            
            # Check email verification
            kc_email_verified = kc_user.get('emailVerified', False)
            if self.email_verified != kc_email_verified:
                issues.append(f'email_verified mismatch: Django={self.email_verified}, Keycloak={kc_email_verified}')
            
            # Check phone attributes
            kc_attributes = kc_user.get('attributes', {})
            
            # Check phone number
            kc_phone = ''
            if 'phone' in kc_attributes and kc_attributes['phone']:
                kc_phone = kc_attributes['phone'][0] if isinstance(kc_attributes['phone'], list) else str(kc_attributes['phone'])
            
            if self.phone != kc_phone:
                issues.append(f'phone mismatch: Django="{self.phone}", Keycloak="{kc_phone}"')
            
            # Check phone verification
            kc_phone_verified = False
            if 'phone_verified' in kc_attributes:
                phone_verified_attr = kc_attributes['phone_verified']
                if isinstance(phone_verified_attr, list) and phone_verified_attr:
                    kc_phone_verified = str(phone_verified_attr[0]).lower() == 'true'
                else:
                    kc_phone_verified = str(phone_verified_attr).lower() == 'true'
            
            if self.phone_verified != kc_phone_verified:
                issues.append(f'phone_verified mismatch: Django={self.phone_verified}, Keycloak={kc_phone_verified}')
            
            # Check for legacy attributes
            legacy_keys = []
            for key in ['phone_number', 'mobile', 'phoneVerified']:
                if key in kc_attributes:
                    legacy_keys.append(key)
            
            if legacy_keys:
                issues.append(f'Legacy attribute keys found: {", ".join(legacy_keys)}')
            
            return {
                'is_synced': len(issues) == 0,
                'issues': issues,
                'last_sync': self.last_keycloak_sync,
                'keycloak_data': {
                    'email_verified': kc_email_verified,
                    'phone': kc_phone,
                    'phone_verified': kc_phone_verified,
                    'legacy_keys': legacy_keys
                }
            }
            
        except Exception as e:
            return {
                'is_synced': False,
                'issues': [f'Error checking Keycloak sync: {e}'],
                'last_sync': self.last_keycloak_sync
            }
        
    class Meta:
        db_table = 'users_user'
        # Primary key index is automatic, other business logic indexes
        indexes = [
            models.Index(fields=['preferred_tenant_slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_keycloak_sync']),
        ]

class VersionedModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True, null=True, blank=True)
    valid_from = models.DateField(default=date.today, db_index=True)
    valid_to = models.DateField(null=True, blank=True, db_index=True)
    source = models.CharField(max_length=50, default='user', choices=[
        ('user', 'User Input'), ('import', 'Data Import'), ('api', 'API Integration'),
        ('admin', 'Admin Override'), ('system', 'System Generated'), ('migration', 'Data Migration'),
    ])
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_created", editable=False)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_updated", editable=False)
    updated_reason = models.CharField(max_length=255, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [models.Index(fields=['tenant', 'valid_from', 'valid_to']), models.Index(fields=['created_at'])]

    def is_active(self):
        today = date.today()
        return self.valid_from <= today and (self.valid_to is None or self.valid_to >= today)

    def clean(self):
        if self.valid_to and self.valid_from >= self.valid_to:
            raise ValidationError("valid_from must be before valid_to")

class VersionedManager(models.Manager):
    def active(self, tenant=None):
        today = date.today()
        queryset = self.filter(valid_from__lte=today, valid_to__isnull=True) | self.filter(valid_from__lte=today, valid_to__gte=today)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset
    
    def history(self, tenant=None):
        today = date.today()
        queryset = self.filter(valid_to__lt=today)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset
    
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)
    
    def at_date(self, date_val, tenant=None):
        queryset = self.filter(valid_from__lte=date_val, valid_to__isnull=True) | self.filter(valid_from__lte=date_val, valid_to__gte=date_val)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset

def versioned_update(model_class, filter_kwargs, new_data, user=None, reason="", source="user"):
    try:
        current = model_class.objects.active().get(**filter_kwargs)
        current.valid_to = date.today()
        current.save()
        
        new_record_data = {
            field.name: getattr(current, field.name) for field in current._meta.fields if field.name not in ['id', 'created_at', 'updated_at']
        }
        new_record_data.update(new_data)
        new_record_data.update({
            'valid_from': date.today(), 'valid_to': None, 'updated_by': user,
            'updated_reason': reason, 'source': source
        })
        new_record = model_class.objects.create(**new_record_data)
        return current, new_record
    except model_class.DoesNotExist:
        raise ValueError(f"No active record found matching {filter_kwargs}")

SERVICE_TYPE_CHOICES = [('power', 'Electricity'), ('broadband', 'Broadband Internet'), ('mobile', 'Mobile Service')]

class UserServiceContract(VersionedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    connection_id = models.CharField(max_length=100)
    contract_name = models.CharField(max_length=100)
    contract_terms = models.TextField()
    signed_at = models.DateField()
    is_signed = models.BooleanField(default=False)
    objects = VersionedManager()

    class Meta:
        db_table = 'users_userservicecontract'
        unique_together = ('tenant', 'user', 'connection_id', 'valid_from')
        indexes = [models.Index(fields=['tenant', 'user', 'service_type']), models.Index(fields=['connection_id'])]

    def __str__(self):
        return f"{self.user.id} - {self.service_type} ({self.connection_id})"

    def clean(self):
        super().clean()
        if self.valid_to and self.valid_from >= self.valid_to:
            raise ValidationError("valid_from must be before valid_to")

class OTP(models.Model):
    identifier = models.CharField(max_length=255)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, choices=[
        ('signup', 'Signup'), ('login', 'Login'), ('password_reset', 'Password Reset'),
    ], default='signup')
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta: db_table = 'users_otp'
    def __str__(self): return f"OTP {self.code} for {self.identifier} ({self.purpose})"
    def is_expired(self): return timezone.now() > self.expires_at

class UserChangeLog(models.Model):
    FIELD_CHOICES = [("email", "Email"), ("mobile", "Mobile")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="change_logs")
    field_changed = models.CharField(max_length=50, choices=FIELD_CHOICES)
    old_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="changed_users")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta: db_table = 'users_userchangelog'
    def __str__(self): return f"{self.user.id} - {self.field_changed} changed from '{self.old_value}' to '{self.new_value}'"

class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=50, unique=True)
    account_number_int = models.PositiveIntegerField(unique=True, null=True, blank=True)
    account_type = models.CharField(max_length=20, choices=[('residential', 'Residential'), ('commercial', 'Commercial'), ('industrial', 'Industrial')])
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive'), ('suspended', 'Suspended')], default='active')
    billing_address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True, related_name='billing_accounts')
    BILLING_CYCLE_CHOICES = [('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('bi_monthly', 'Bi-Monthly'), ('annual', 'Annual')]
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    billing_day = models.IntegerField(default=1, help_text="Day of month for billing")
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="accounts_created")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'users_account'
        indexes = [
            models.Index(fields=['tenant', 'account_number']), models.Index(fields=['account_type']),
            models.Index(fields=['status']), models.Index(fields=['valid_from', 'valid_to']),
        ]
    
    def __str__(self): return f"{self.account_number} ({self.account_type})"
    
    def save(self, *args, **kwargs):
        if not self.account_number:
            acc_num, acc_int = self.generate_account_number()
            self.account_number = acc_num
            self.account_number_int = acc_int
        super().save(*args, **kwargs)
    
    def delete(self, using=None, keep_parents=False):
        from django.db import transaction
        account_number = self.account_number
        account_id = str(self.id)
        try:
            super().delete(using=using, keep_parents=keep_parents)
            print(f"Successfully deleted account {account_number}")
            return
        except Exception as e:
            if "does not exist" not in str(e): raise e
            print(f"Warning: Some related tables don't exist, using direct deletion for account {account_number}: {e}")
        try:
            transaction.rollback()
            with transaction.atomic():
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM users_useraccountrole WHERE account_id = %s", [account_id])
                    try:
                        cursor.execute("DELETE FROM contracts_contractservice WHERE contract_id IN (SELECT id FROM contracts_servicecontract WHERE account_id = %s)", [account_id])
                        cursor.execute("DELETE FROM contracts_contractamendment WHERE contract_id IN (SELECT id FROM contracts_servicecontract WHERE account_id = %s)", [account_id])
                        cursor.execute("DELETE FROM contracts_contractdocument WHERE contract_id IN (SELECT id FROM contracts_servicecontract WHERE account_id = %s)", [account_id])
                        cursor.execute("DELETE FROM contracts_electricitycontract WHERE account_id = %s", [account_id])
                        cursor.execute("DELETE FROM contracts_broadbandcontract WHERE account_id = %s", [account_id])
                        cursor.execute("DELETE FROM contracts_mobilecontract WHERE account_id = %s", [account_id])
                        cursor.execute("DELETE FROM contracts_servicecontract WHERE account_id = %s", [account_id])
                    except Exception as contract_error:
                        print(f"Warning: Some contract tables may not exist: {contract_error}")
                    cursor.execute("DELETE FROM users_account WHERE id = %s", [account_id])
                    print(f"Successfully force-deleted account {account_number}")
        except Exception as final_error:
            print(f"Failed to delete account {account_number}: {final_error}")
            raise final_error
    
    @staticmethod
    def generate_account_number():
        from django.db.models import Max
        from django.db import transaction
        with transaction.atomic():
            last_int = Account.objects.filter(account_number_int__isnull=False).aggregate(Max('account_number_int'))['account_number_int__max']
            next_number = 1 if last_int is None else last_int + 1
            max_attempts, attempts = 100, 0
            while attempts < max_attempts:
                formatted = f"ACC{next_number:06d}"
                if not Account.objects.filter(account_number=formatted).exists():
                    return formatted, next_number
                next_number += 1
                attempts += 1
            raise ValueError("Unable to generate unique account number after 100 attempts")

class UserAccountRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_roles')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='user_roles')
    ROLE_CHOICES = [('primary', 'Primary User'), ('owner', 'Owner'), ('authorized', 'Authorized User'), ('viewer', 'Viewer')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    can_manage_services = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_billing = models.BooleanField(default=False)
    can_view_usage = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="account_roles_created")

    class Meta:
        db_table = 'users_useraccountrole'
        unique_together = ('user', 'account', 'role', 'valid_from')
        indexes = [
            models.Index(fields=['tenant', 'account', 'role']), models.Index(fields=['user', 'role']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]

    def __str__(self):
        return f"{self.user.id} - {self.account.account_number} ({self.role})"

    def clean(self):
        if self.role == 'primary':
            existing_primary = UserAccountRole.objects.filter(
                account=self.account, role='primary', valid_from__lte=self.valid_from, valid_to__isnull=True
            ).exclude(id=self.id).first()
            if existing_primary:
                raise ValidationError(f"Account {self.account.account_number} already has a primary user: {existing_primary.user.id}")

    def save(self, *args, **kwargs):
        self.clean()
        if self.role in ['primary', 'owner']:
            self.can_manage_services, self.can_manage_users, self.can_manage_billing, self.can_view_usage = True, True, True, True
        elif self.role == 'authorized':
            self.can_manage_services, self.can_view_usage = True, True
        elif self.role == 'viewer':
            self.can_view_usage = True
        super().save(*args, **kwargs)

class TenantUserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='user_roles')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_roles')
    ROLE_CHOICES = [
        ('staff', 'Staff Member'), ('admin', 'Tenant Administrator'), ('billing_manager', 'Billing Manager'),
        ('support', 'Support Representative'), ('viewer', 'Read-Only Access'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    can_manage_users = models.BooleanField(default=False)
    can_modify_settings = models.BooleanField(default=False)
    can_access_billing = models.BooleanField(default=False)
    can_access_metering = models.BooleanField(default=False)
    can_manage_contracts = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_tenantuserrole'
        unique_together = ('tenant', 'user', 'role')
        indexes = [models.Index(fields=['tenant', 'user']), models.Index(fields=['role'])]
    
    def __str__(self):
        return f"{self.user.id} - {self.tenant.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        if self.role == 'admin':
            self.can_manage_users, self.can_modify_settings, self.can_access_billing, self.can_access_metering, self.can_manage_contracts = True, True, True, True, True
        elif self.role == 'billing_manager':
            self.can_access_billing = True
        elif self.role == 'support':
            self.can_access_metering, self.can_manage_contracts = True, True
        super().save(*args, **kwargs)

class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="tenant_addresses")
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True)
    suburb = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='New Zealand')
    ADDRESS_TYPE_CHOICES = [
        ('service', 'Service Address'), ('billing', 'Billing Address'),
        ('postal', 'Postal Address'), ('legal', 'Legal Address'),
    ]
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES)
    is_primary = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_address'
        indexes = [models.Index(fields=['tenant']), models.Index(fields=['postal_code'])]

    def __str__(self): return f"{self.address_line1}, {self.city}"

class UserTenantRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'), ('staff', 'Staff'), ('customer', 'Customer')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_usertenantrole'
        unique_together = ('tenant', 'user', 'role')
        indexes = [models.Index(fields=['tenant', 'role'])]
    
    def __str__(self):
        return f"{self.user.id} - {self.tenant.name} ({self.role})"

class APIToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True, default=secrets.token_hex)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='api_token', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key

class OnboardingProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_progress')
    current_step = models.CharField(max_length=100, blank=True, default='')
    step_data = models.JSONField(default=dict, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'web_support_onboardingprogress'

    def __str__(self):
        return f"OnboardingProgress({self.user})"

    def sync_to_keycloak(self):
        """Sync onboarding progress to Keycloak user attributes"""
        try:
            from users.keycloak_admin import KeycloakAdminService
            
            kc_admin = KeycloakAdminService()
            
            success = kc_admin.update_user(
                self.user.id,
                attributes={
                    'is_onboarding_complete': str(self.is_completed).lower(),
                    'onboarding_step': self.current_step or '',
                    'onboarding_data': str(self.step_data) if self.step_data else '{}'
                }
            )
            
            if success:
                from users.services.user_cache_service import UserCacheService
                UserCacheService.invalidate_user_cache(self.user.id)
                
            return success
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to sync onboarding progress to Keycloak for user {self.user.id}: {e}")
            return False

    def save(self, *args, **kwargs):
        """Override save to sync to Keycloak"""
        super().save(*args, **kwargs)
        self.sync_to_keycloak()
