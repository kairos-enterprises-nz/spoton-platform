"""
Django management command to migrate existing users to Keycloak.
This command exports Django users and imports them into appropriate Keycloak realms.

Usage: python manage.py migrate_users_to_keycloak
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import requests
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate existing Django users to Keycloak realms'

    def __init__(self):
        super().__init__()
        self.keycloak_url = getattr(settings, 'KEYCLOAK_BASE_URL', 'https://auth.spoton.co.nz')
        self.admin_username = 'admin'
        self.admin_password = 'spoton_keycloak_admin_2024'
        self.access_token = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually migrating',
        )
        parser.add_argument(
            '--user-type',
            choices=['staff', 'customers', 'all'],
            default='all',
            help='Migrate only specific user types',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of users to migrate in each batch',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.user_type = options['user_type']
        self.batch_size = options['batch_size']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            # Get admin access token
            self.stdout.write('🔑 Getting Keycloak admin access token...')
            self.get_admin_token()
            
            # Get user statistics
            self.stdout.write('📊 Analyzing users to migrate...')
            self.analyze_users()
            
            # Migrate users
            self.stdout.write('👥 Migrating users to Keycloak...')
            self.migrate_users()
            
            self.stdout.write(self.style.SUCCESS('✅ User migration completed successfully!'))
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('1. Test login with migrated users')
            self.stdout.write('2. Enable hybrid authentication mode')
            self.stdout.write('3. Configure frontend for OIDC support')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Migration failed: {str(e)}'))
            logger.exception('User migration failed')

    def get_admin_token(self):
        """Get admin access token for Keycloak API calls"""
        url = f'{self.keycloak_url}/realms/master/protocol/openid-connect/token'
        data = {
            'client_id': 'admin-cli',
            'username': self.admin_username,
            'password': self.admin_password,
            'grant_type': 'password'
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            self.stdout.write('  ✅ Admin token obtained')
        else:
            raise Exception(f'Failed to get admin token: {response.text}')

    def api_request(self, method, endpoint, data=None):
        """Make authenticated API request to Keycloak"""
        url = f'{self.keycloak_url}/admin{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        if self.dry_run:
            self.stdout.write(f'  [DRY RUN] {method} {endpoint}')
            if data:
                self.stdout.write(f'  [DRY RUN] Data: {json.dumps(data, indent=2)[:200]}...')
            return {'status': 'dry_run'}
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        
        return {
            'status_code': response.status_code,
            'data': response.json() if response.content else None,
            'text': response.text
        }

    def analyze_users(self):
        """Analyze existing users and show migration statistics"""
        users = User.objects.all()
        
        # Count users by type
        staff_users = users.filter(is_staff=True)
        customer_users = users.filter(is_staff=False)
        
        # Count by user_type field
        residential_users = users.filter(user_type='residential')
        commercial_users = users.filter(user_type='commercial')
        internal_users = users.filter(user_type='internal')
        staff_type_users = users.filter(user_type='staff')
        
        self.stdout.write('  📊 User Analysis:')
        self.stdout.write(f'    Total users: {users.count()}')
        self.stdout.write(f'    Staff users (is_staff=True): {staff_users.count()}')
        self.stdout.write(f'    Customer users (is_staff=False): {customer_users.count()}')
        self.stdout.write('')
        self.stdout.write('  📋 By user_type field:')
        self.stdout.write(f'    Residential: {residential_users.count()}')
        self.stdout.write(f'    Commercial: {commercial_users.count()}')
        self.stdout.write(f'    Internal: {internal_users.count()}')
        self.stdout.write(f'    Staff: {staff_type_users.count()}')
        self.stdout.write('')
        
        # Show realm mapping
        self.stdout.write('  🏗️ Realm Mapping:')
        self.stdout.write(f'    spoton-staff realm: {staff_users.count()} users')
        self.stdout.write(f'    spoton-customers realm: {customer_users.count()} users')
        self.stdout.write('')

    def migrate_users(self):
        """Migrate users to appropriate Keycloak realms"""
        users_query = User.objects.all()
        
        # Filter by user type if specified
        if self.user_type == 'staff':
            users_query = users_query.filter(is_staff=True)
        elif self.user_type == 'customers':
            users_query = users_query.filter(is_staff=False)
        
        users = list(users_query)
        total_users = len(users)
        
        self.stdout.write(f'  Migrating {total_users} users...')
        
        # Process users in batches
        for i in range(0, total_users, self.batch_size):
            batch = users[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_users + self.batch_size - 1) // self.batch_size
            
            self.stdout.write(f'  Processing batch {batch_num}/{total_batches} ({len(batch)} users)...')
            
            for user in batch:
                self.migrate_single_user(user)

    def migrate_single_user(self, user):
        """Migrate a single user to the appropriate Keycloak realm"""
        # Determine target realm
        if user.is_staff:
            realm = 'spoton-staff'
            groups = self.get_staff_groups(user)
        else:
            realm = 'spoton-customers'
            groups = self.get_customer_groups(user)
        
        # Create user data for Keycloak
        keycloak_user = {
            'username': user.email,
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'enabled': user.is_active,
            'emailVerified': user.is_email_verified,
            'attributes': {
                'django_user_id': [str(user.id)],
                'user_number': [user.user_number] if user.user_number else [],
                'user_type': [user.user_type],
                'department': [user.department] if user.department else [],
                'job_title': [user.job_title] if user.job_title else [],
                'tenant_id': [str(user.tenant.id)] if user.tenant else [],
                'tenant_name': [user.tenant.name] if user.tenant else [],
            },
            'groups': groups,
            # Don't migrate passwords - users will need to reset
            'requiredActions': ['UPDATE_PASSWORD'] if not self.dry_run else []
        }
        
        self.stdout.write(f'    Migrating user: {user.email} → {realm}')
        
        # Create user in Keycloak
        result = self.api_request('POST', f'/realms/{realm}/users', keycloak_user)
        
        if result.get('status_code') == 201 or result.get('status') == 'dry_run':
            self.stdout.write(f'      ✅ User {user.email} migrated successfully')
            
            # If not dry run, get the created user ID and assign to groups
            if not self.dry_run and result.get('status_code') == 201:
                self.assign_user_to_groups(realm, user.email, groups)
                
        elif result.get('status_code') == 409:
            self.stdout.write(f'      ⚠️  User {user.email} already exists in {realm}')
            # Update existing user
            self.update_existing_user(realm, user.email, keycloak_user)
        else:
            self.stdout.write(f'      ❌ Failed to migrate {user.email}: {result.get("text")}')

    def get_staff_groups(self, user):
        """Get appropriate Keycloak groups for staff user"""
        groups = []
        
        # Map Django groups to Keycloak groups
        django_groups = user.groups.values_list('name', flat=True)
        
        group_mapping = {
            'Admin': 'staff-admin',
            'Super Admin': 'staff-super-admin',
            'Technical Staff': 'staff-technical',
            'Billing Staff': 'staff-billing',
            'Support Staff': 'staff-support'
        }
        
        for django_group in django_groups:
            keycloak_group = group_mapping.get(django_group)
            if keycloak_group:
                groups.append(keycloak_group)
        
        # Default group for staff
        if not groups:
            if user.is_superuser:
                groups.append('staff-super-admin')
            else:
                groups.append('staff-support')  # Default staff group
        
        return groups

    def get_customer_groups(self, user):
        """Get appropriate Keycloak groups for customer user"""
        groups = ['customers']  # Default group for all customers
        
        # Add premium group if applicable (you can customize this logic)
        if user.user_type == 'commercial':
            groups.append('premium-customers')
        
        return groups

    def assign_user_to_groups(self, realm, email, groups):
        """Assign user to Keycloak groups"""
        if not groups:
            return
        
        # First, get the user ID
        result = self.api_request('GET', f'/realms/{realm}/users?email={email}')
        if result.get('status_code') != 200 or not result.get('data'):
            self.stdout.write(f'      ❌ Could not find user {email} for group assignment')
            return
        
        user_id = result['data'][0]['id']
        
        # Get available groups
        groups_result = self.api_request('GET', f'/realms/{realm}/groups')
        if groups_result.get('status_code') != 200:
            self.stdout.write(f'      ❌ Could not fetch groups for realm {realm}')
            return
        
        available_groups = {g['name']: g['id'] for g in groups_result['data']}
        
        # Assign user to each group
        for group_name in groups:
            if group_name in available_groups:
                group_id = available_groups[group_name]
                result = self.api_request('PUT', f'/realms/{realm}/users/{user_id}/groups/{group_id}')
                if result.get('status_code') == 204:
                    self.stdout.write(f'        ✅ Added to group: {group_name}')
                else:
                    self.stdout.write(f'        ❌ Failed to add to group {group_name}')
            else:
                self.stdout.write(f'        ⚠️  Group {group_name} not found in realm')

    def update_existing_user(self, realm, email, user_data):
        """Update existing user in Keycloak"""
        # Get existing user
        result = self.api_request('GET', f'/realms/{realm}/users?email={email}')
        if result.get('status_code') != 200 or not result.get('data'):
            return
        
        existing_user = result['data'][0]
        user_id = existing_user['id']
        
        # Update user data (merge with existing)
        update_data = {
            'firstName': user_data['firstName'],
            'lastName': user_data['lastName'],
            'enabled': user_data['enabled'],
            'emailVerified': user_data['emailVerified'],
            'attributes': {**existing_user.get('attributes', {}), **user_data['attributes']}
        }
        
        result = self.api_request('PUT', f'/realms/{realm}/users/{user_id}', update_data)
        if result.get('status_code') == 204 or result.get('status') == 'dry_run':
            self.stdout.write(f'      ✅ Updated existing user {email}')
            
            # Update group assignments
            if not self.dry_run:
                self.assign_user_to_groups(realm, email, user_data['groups'])
        else:
            self.stdout.write(f'      ❌ Failed to update user {email}: {result.get("text")}') 