from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from users.models import UserChangeLog


class CustomUserAdmin(UserAdmin):
    """
    Admin interface for minimal Keycloak-first User model.
    Identity data (email, names, phone) is shown via cached methods from Keycloak.
    """
    model = User
    list_display = ('id', 'get_email_display', 'get_full_name_display', 'is_active', 'is_staff', 'preferred_tenant_slug', 'last_keycloak_sync')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'preferred_tenant_slug', 'created_at')
    search_fields = ('id',)  # Search by primary key (Keycloak ID)
    ordering = ('id',)

    fieldsets = (
        ('User ID', {
            'fields': ('id',),
            'description': 'Keycloak user ID (primary key) - identity data is cached from Keycloak'
        }),
        ('Cached Identity Data (Read-Only)', {
            'fields': ('get_email_display', 'get_full_name_display', 'get_phone_display', 'get_verification_status_display'),
            'description': 'User identity data from Keycloak cache (not stored in Django)'
        }),
        ('Django Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'Django-specific permissions and status'
        }),
        ('Business Logic', {
            'fields': ('preferred_tenant_slug', 'keycloak_client_id', 'app_preferences'),
            'description': 'Application-specific settings not stored in Keycloak'
        }),
        ('System Information', {
            'fields': ('date_joined', 'created_at', 'updated_at', 'last_keycloak_sync'),
            'description': 'System timestamps and sync tracking'
        }),
    )
    
    readonly_fields = ('id', 'created_at', 'updated_at', 'date_joined', 'last_keycloak_sync', 
                      'get_email_display', 'get_full_name_display', 'get_phone_display', 'get_verification_status_display')
    actions = ['refresh_cache']

    def get_readonly_fields(self, request, obj=None):
        """Make ID readonly for existing users"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('id',)
        return self.readonly_fields
    
    def refresh_cache(self, request, queryset):
        """Admin action to refresh Keycloak cache for selected users"""
        refreshed_count = 0
        for user in queryset:
            try:
                from users.services import UserCacheService
                UserCacheService.invalidate_user_cache(user.id)
                refreshed_count += 1
            except Exception as e:
                self.message_user(request, f"Failed to refresh cache for user {user.id}: {e}", level='ERROR')
        
        if refreshed_count > 0:
            self.message_user(request, f"Successfully refreshed cache for {refreshed_count} user(s).")
    
    refresh_cache.short_description = "Refresh Keycloak cache for selected users"

# Register your custom User model with the admin site
admin.site.register(User, CustomUserAdmin)


@admin.register(UserChangeLog)
class UserChangeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'field_changed', 'old_value', 'new_value', 'changed_by', 'timestamp')
    list_filter = ('field_changed', 'timestamp')
    search_fields = ('user__id', 'old_value', 'new_value', 'changed_by__id')
