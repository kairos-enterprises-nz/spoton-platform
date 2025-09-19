from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
import random

from users.models import Tenant, User, Account, UserAccountRole, Address


class Command(BaseCommand):
    help = 'Create sample data with correct relationship hierarchy in public schema: tenant->users->accounts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data with correct relationships...'))
        
        with transaction.atomic():
            # Step 1: Get existing tenants or create new ones
            tenants = self.get_or_create_tenants()
            
            # Step 2: Create Users for each tenant
            users = self.create_users(tenants)
            
            # Step 3: Create Accounts with primary users
            accounts = self.create_accounts(tenants, users)
            
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.print_summary()

    def get_or_create_tenants(self):
        self.stdout.write('Getting or creating tenants...')
        tenants = []
        
        # Check if tenants already exist
        existing_tenants = list(Tenant.objects.all())
        if existing_tenants:
            self.stdout.write(f'  Found {len(existing_tenants)} existing tenants')
            return existing_tenants
        
        tenant_data = [
            {
                'name': 'ACME Energy Solutions',
                'slug': 'acme-energy',
                'business_number': '12345678901',
                'contact_email': 'admin@acme-energy.co.nz',
                'contact_phone': '+64 9 123 4567',
                'address': '123 Queen Street, Auckland 1010, New Zealand'
            },
            {
                'name': 'Stellar Utilities Ltd',
                'slug': 'stellar-utilities',
                'business_number': '98765432109',
                'contact_email': 'admin@stellar-utilities.co.nz',
                'contact_phone': '+64 4 987 6543',
                'address': '456 Lambton Quay, Wellington 6011, New Zealand'
            }
        ]
        
        for data in tenant_data:
            tenant, created = Tenant.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            tenants.append(tenant)
            if created:
                self.stdout.write(f'  Created tenant: {tenant.name}')
        
        return tenants

    def create_users(self, tenants):
        self.stdout.write('Creating users...')
        users = []
        
        # Create admin users for each tenant
        for tenant in tenants:
            admin_email = tenant.contact_email
            admin_user, created = User.objects.get_or_create(
                email=admin_email,
                defaults={
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'tenant': tenant,
                    'user_type': 'staff',
                    'is_staff': True,
                    'is_active': True,
                    'is_verified': True
                }
            )
            users.append(admin_user)
            if created:
                self.stdout.write(f'  Created admin user: {admin_user.email}')
        
        # Create residential customers for each tenant
        customer_data = [
            ('john.smith@email.com', 'John', 'Smith'),
            ('mary.jones@email.com', 'Mary', 'Jones'),
            ('david.brown@email.com', 'David', 'Brown'),
            ('sarah.wilson@email.com', 'Sarah', 'Wilson'),
            ('mike.taylor@email.com', 'Mike', 'Taylor'),
            ('alice.johnson@email.com', 'Alice', 'Johnson'),
            ('bob.williams@email.com', 'Bob', 'Williams'),
            ('emma.davis@email.com', 'Emma', 'Davis'),
        ]
        
        for tenant in tenants:
            for email, first_name, last_name in customer_data:
                # Make email unique per tenant
                tenant_email = f"{first_name.lower()}.{last_name.lower()}@{tenant.slug}.co.nz"
                user, created = User.objects.get_or_create(
                    email=tenant_email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'tenant': tenant,
                        'user_type': 'residential',
                        'is_active': True,
                        'is_verified': True
                    }
                )
                users.append(user)
                if created:
                    self.stdout.write(f'  Created customer: {user.email}')
        
        return users

    def create_accounts(self, tenants, users):
        self.stdout.write('Creating accounts with primary users...')
        accounts = []
        
        # Get residential users for each tenant
        for tenant in tenants:
            tenant_users = [u for u in users if u.tenant == tenant and u.user_type == 'residential']
            
            # Create multiple accounts per tenant
            for i, user in enumerate(tenant_users[:6]):  # Create 6 accounts per tenant
                account = Account.objects.create(
                    tenant=tenant,
                    account_number=f"{tenant.slug.upper()}-ACC-{str(i+1).zfill(4)}",
                    account_type='residential',
                    status='active',
                    billing_cycle='monthly',
                    billing_day=1,
                    created_by=user
                )
                
                # Create primary user role
                UserAccountRole.objects.create(
                    tenant=tenant,
                    user=user,
                    account=account,
                    role='primary',
                    can_manage_services=True,
                    can_manage_users=True,
                    can_manage_billing=True,
                    can_view_usage=True,
                    created_by=user
                )
                
                accounts.append(account)
                self.stdout.write(f'  Created account: {account.account_number} (Primary: {user.email})')
                
                # Add some additional users to some accounts
                if i < 2 and len(tenant_users) > i + 3:  # Add additional users to first 2 accounts
                    additional_user = tenant_users[i + 3]
                    UserAccountRole.objects.create(
                        tenant=tenant,
                        user=additional_user,
                        account=account,
                        role='authorized',
                        can_manage_services=False,
                        can_manage_users=False,
                        can_manage_billing=False,
                        can_view_usage=True,
                        created_by=user
                    )
                    self.stdout.write(f'    Added authorized user: {additional_user.email}')
        
        return accounts

    def print_summary(self):
        self.stdout.write(self.style.SUCCESS('\n=== SAMPLE DATA SUMMARY ==='))
        
        tenant_count = Tenant.objects.count()
        user_count = User.objects.count()
        account_count = Account.objects.count()
        role_count = UserAccountRole.objects.count()
        
        self.stdout.write(f'Tenants: {tenant_count}')
        self.stdout.write(f'Users: {user_count}')
        self.stdout.write(f'Accounts: {account_count}')
        self.stdout.write(f'User-Account Roles: {role_count}')
        
        self.stdout.write(self.style.SUCCESS('\nRelationship hierarchy implemented:'))
        self.stdout.write('✅ Tenant → Users (public schema)')
        self.stdout.write('✅ User → Accounts (primary user required, additional users supported)')
        self.stdout.write('✅ All models have tenant for multi-tenancy')
        self.stdout.write('✅ All models have temporal tracking')
        self.stdout.write('✅ UserAccountRole enforces primary user constraint')
        
        # Print detailed breakdown
        self.stdout.write(self.style.SUCCESS('\n=== DETAILED BREAKDOWN ==='))
        for tenant in Tenant.objects.all():
            tenant_users = User.objects.filter(tenant=tenant).count()
            tenant_accounts = Account.objects.filter(tenant=tenant).count()
            primary_roles = UserAccountRole.objects.filter(tenant=tenant, role='primary').count()
            authorized_roles = UserAccountRole.objects.filter(tenant=tenant, role='authorized').count()
            
            self.stdout.write(f'{tenant.name}:')
            self.stdout.write(f'  Users: {tenant_users}')
            self.stdout.write(f'  Accounts: {tenant_accounts}')
            self.stdout.write(f'  Primary roles: {primary_roles}')
            self.stdout.write(f'  Authorized roles: {authorized_roles}')
            
        self.stdout.write(self.style.SUCCESS('\n=== NEXT STEPS ==='))
        self.stdout.write('To complete the relationship hierarchy:')
        self.stdout.write('1. Migrate tenant schemas to create contracts/connections tables')
        self.stdout.write('2. Create contracts linked to accounts')
        self.stdout.write('3. Create connections linked to contracts')
        self.stdout.write('4. Create plan assignments linked to connections')
        self.stdout.write('5. Update frontend to display correct relationship flow') 