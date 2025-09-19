from django.contrib.auth.models import AnonymousUser

class VirtualUser:
    """
    A virtual user object that mimics the Django User model but is populated
    from Keycloak token claims. This allows for a gradual phase-out of the
    database-backed User model.
    """
    def __init__(self, token_claims):
        self.id = token_claims.get('sub')
        self.pk = self.id
        self.username = token_claims.get('preferred_username')
        self.email = token_claims.get('email')
        self.first_name = token_claims.get('given_name')
        self.last_name = token_claims.get('family_name')
        self.is_staff = 'staff' in token_claims.get('realm_access', {}).get('roles', [])
        self.is_active = token_claims.get('active', True)
        self.is_superuser = False  # Superuser status should be managed carefully
        
        # Store all claims for reference
        self.token_claims = token_claims
        
        # Will be set by the authentication backend
        self.profile = None

    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_anonymous(self):
        return False
        
    def get_username(self):
        return self.username or self.email or self.id
        
    def __str__(self):
        return self.get_username()
        
    def has_perm(self, perm, obj=None):
        """
        Check if the user has a specific permission.
        Simplistic implementation based on staff status.
        """
        if self.is_superuser:
            return True
            
        # Check Keycloak roles
        if 'realm_access' in self.token_claims:
            roles = self.token_claims['realm_access'].get('roles', [])
            
            # Map permissions to roles
            # This is a simplistic implementation - you may want to expand this
            if perm.startswith('users.'):
                return 'manage-users' in roles
            if perm.startswith('admin.'):
                return 'admin' in roles
                
        return self.is_staff
        
    def has_perms(self, perm_list, obj=None):
        """
        Check if the user has all specified permissions.
        """
        return all(self.has_perm(perm, obj) for perm in perm_list)
        
    def has_module_perms(self, app_label):
        """
        Check if the user has any permission for the given app label.
        """
        if self.is_superuser:
            return True
            
        # Check Keycloak roles
        if 'realm_access' in self.token_claims:
            roles = self.token_claims['realm_access'].get('roles', [])
            
            # Staff can access all modules
            if 'staff' in roles:
                return True
                
            # App-specific roles
            if app_label == 'users' and 'manage-users' in roles:
                return True
                
        return False
        
    def get_all_permissions(self):
        """
        Get all permissions for this user.
        """
        if not self.token_claims:
            return set()
            
        permissions = set()
        
        # Convert Keycloak roles to Django-style permissions
        if 'realm_access' in self.token_claims:
            roles = self.token_claims['realm_access'].get('roles', [])
            
            # Map roles to permissions
            role_to_perm = {
                'admin': {'admin.access', 'admin.change'},
                'manage-users': {'users.add_user', 'users.change_user', 'users.view_user'},
                'view-users': {'users.view_user'},
                'staff': {'staff.access'},
            }
            
            for role, perms in role_to_perm.items():
                if role in roles:
                    permissions.update(perms)
                    
        return permissions


class AnonymousVirtualUser(AnonymousUser):
    """
    An anonymous user class compatible with VirtualUser.
    """
    def __init__(self):
        super().__init__()
        self.profile = None 