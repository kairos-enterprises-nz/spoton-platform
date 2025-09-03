from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from users.models import Tenant, Account, Address, TenantUserRole
from datetime import datetime, timedelta, date
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for all staff portal pages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up existing data before creating sample data',
        )

    def handle(self, *args, **options):
        self.stdout.write("🎯 Creating Sample Data for Staff Portal")
        self.stdout.write("=" * 50)
        
        self.created_data = {
            'tenants': [],
            'users': [],
            'accounts': [],
            'addresses': []
        }
        
        try:
            with transaction.atomic():
                if options['cleanup']:
                    self.cleanup_database()
                
                self.create_tenants()
                self.create_users()
                self.create_addresses()
                self.create_accounts()
                
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write(self.style.SUCCESS("🎉 Sample data creation completed successfully!"))
                self.stdout.write("=" * 50)
                
                # Print summary
                self.stdout.write("\n📊 Data Summary:")
                for data_type, items in self.created_data.items():
                    if items:
                        self.stdout.write(f"  {data_type.capitalize()}: {len(items)}")
                
                self.stdout.write("\n🔐 Login Information:")
                self.stdout.write("  Superuser: admin / admin123")
                self.stdout.write("  Sample Users:")
                for user in self.created_data['users']:
                    self.stdout.write(f"    {user.email} / password123")
                
                self.stdout.write("\n🌐 Staff Portal URLs:")
                self.stdout.write("  Tenants: https://192.168.1.107:5174/staff/tenants")
                self.stdout.write("  Users: https://192.168.1.107:5174/staff/users")
                self.stdout.write("  Accounts: https://192.168.1.107:5174/staff/accounts")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating sample data: {e}"))
            import traceback
            traceback.print_exc()
            raise

    def cleanup_database(self):
        """Clean up existing data while preserving superuser"""
        self.stdout.write("🧹 Cleaning up existing data...")
        
        # Get superuser before cleanup
        superuser = User.objects.filter(is_superuser=True).first()
        
        # Delete in proper order to avoid foreign key constraints
        self.stdout.write("  Deleting accounts...")
        Account.objects.all().delete()
        
        self.stdout.write("  Deleting addresses...")
        Address.objects.all().delete()
        
        self.stdout.write("  Deleting tenant user roles...")
        TenantUserRole.objects.all().delete()
        
        self.stdout.write("  Deleting non-superuser users...")
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write("  Deleting tenants...")
        Tenant.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS("✅ Database cleanup completed"))
        
        if superuser:
            self.stdout.write(f"✅ Preserved superuser: {superuser.email}")
        else:
            self.stdout.write(self.style.WARNING("⚠️  No superuser found to preserve"))

    def create_tenants(self):
        """Create sample tenants"""
        self.stdout.write("🏢 Creating sample tenants...")
        
        tenant_data = [
            {
                'name': 'ACME Energy Solutions',
                'slug': 'acme-energy',
                'contact_email': 'admin@acme-energy.com',
                'contact_phone': '+64 9 123 4567',
                'address': '123 Queen Street, Auckland Central, Auckland 1010',
                'business_number': 'BN123456789',
                'tax_number': 'TAX987654321',
                'is_active': True,
                'timezone': 'Pacific/Auckland',
                'currency': 'NZD'
            },
            {
                'name': 'Stellar Utilities Ltd',
                'slug': 'stellar-utilities',
                'contact_email': 'admin@stellar-utilities.com',
                'contact_phone': '+64 4 987 6543',
                'address': '456 Lambton Quay, Wellington Central, Wellington 6011',
                'business_number': 'BN987654321',
                'tax_number': 'TAX123456789',
                'is_active': True,
                'timezone': 'Pacific/Auckland',
                'currency': 'NZD'
            }
        ]
        
        for data in tenant_data:
            tenant = Tenant.objects.create(**data)
            self.created_data['tenants'].append(tenant)
            self.stdout.write(f"  ✅ Created tenant: {tenant.name}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(self.created_data['tenants'])} tenants"))

    def create_users(self):
        """Create sample users for each tenant"""
        self.stdout.write("👥 Creating sample users...")
        
        user_data = [
            # Users for ACME Energy Solutions
            {
                'email': 'alice.brown@gmail.com',
                'first_name': 'Alice',
                'last_name': 'Brown',
                'mobile': '+64 21 123 4567',
                'is_active': True,
                'is_staff': False,
                'user_type': 'residential',
                'tenant': self.created_data['tenants'][0],
                'address_line1': '123 Queen Street',
                'address_line2': 'Apartment 5A',
                'city': 'Auckland',
                'postal_code': '1010',
                'region': 'Auckland'
            },
            {
                'email': 'bob.wilson@outlook.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'mobile': '+64 21 234 5678',
                'is_active': True,
                'is_staff': False,
                'user_type': 'residential',
                'tenant': self.created_data['tenants'][0],
                'address_line1': '456 Ponsonby Road',
                'city': 'Auckland',
                'postal_code': '1011',
                'region': 'Auckland'
            },
            # Users for Stellar Utilities Ltd
            {
                'email': 'carol.davis@yahoo.com',
                'first_name': 'Carol',
                'last_name': 'Davis',
                'mobile': '+64 21 345 6789',
                'is_active': True,
                'is_staff': False,
                'user_type': 'residential',
                'tenant': self.created_data['tenants'][1],
                'address_line1': '789 Lambton Quay',
                'city': 'Wellington',
                'postal_code': '6011',
                'region': 'Wellington'
            },
            {
                'email': 'david.taylor@gmail.com',
                'first_name': 'David',
                'last_name': 'Taylor',
                'mobile': '+64 21 456 7890',
                'is_active': True,
                'is_staff': False,
                'user_type': 'commercial',
                'tenant': self.created_data['tenants'][1],
                'address_line1': '321 Cashel Street',
                'city': 'Christchurch',
                'postal_code': '8011',
                'region': 'Canterbury'
            }
        ]
        
        for data in user_data:
            tenant = data.pop('tenant')
            
            # Create user
            user = User.objects.create_user(
                username=data['email'],
                password='password123',
                **data
            )
            
            # Set tenant relationship
            user.tenant = tenant
            user.save()
            
            # Create tenant user role
            TenantUserRole.objects.create(
                user=user,
                tenant=tenant,
                role='staff',
                can_access_billing=True,
                can_access_metering=True
            )
            
            self.created_data['users'].append(user)
            self.stdout.write(f"  ✅ Created user: {user.first_name} {user.last_name} ({user.email})")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(self.created_data['users'])} users"))

    def create_addresses(self):
        """Create sample addresses"""
        self.stdout.write("📍 Creating sample addresses...")
        
        address_data = [
            {
                'address_line1': '123 Queen Street',
                'address_line2': 'Apartment 5A',
                'city': 'Auckland',
                'suburb': 'Auckland Central',
                'postal_code': '1010',
                'region': 'Auckland',
                'country': 'New Zealand',
                'address_type': 'service',
                'is_primary': True,
                'tenant': self.created_data['tenants'][0]
            },
            {
                'address_line1': '456 Ponsonby Road',
                'city': 'Auckland',
                'suburb': 'Ponsonby',
                'postal_code': '1011',
                'region': 'Auckland',
                'country': 'New Zealand',
                'address_type': 'service',
                'is_primary': True,
                'tenant': self.created_data['tenants'][0]
            },
            {
                'address_line1': '789 Lambton Quay',
                'city': 'Wellington',
                'suburb': 'Wellington Central',
                'postal_code': '6011',
                'region': 'Wellington',
                'country': 'New Zealand',
                'address_type': 'service',
                'is_primary': True,
                'tenant': self.created_data['tenants'][1]
            },
            {
                'address_line1': '321 Cashel Street',
                'city': 'Christchurch',
                'suburb': 'Christchurch Central',
                'postal_code': '8011',
                'region': 'Canterbury',
                'country': 'New Zealand',
                'address_type': 'service',
                'is_primary': True,
                'tenant': self.created_data['tenants'][1]
            }
        ]
        
        for data in address_data:
            address = Address.objects.create(**data)
            self.created_data['addresses'].append(address)
            self.stdout.write(f"  ✅ Created address: {address.address_line1}, {address.city}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(self.created_data['addresses'])} addresses"))

    def create_accounts(self):
        """Create sample accounts"""
        self.stdout.write("🏦 Creating sample accounts...")
        
        account_data = [
            {
                'account_number': 'ACC000001',
                'account_type': 'residential',
                'status': 'active',
                'primary_user': self.created_data['users'][0],
                'tenant': self.created_data['tenants'][0],
                'billing_cycle': 'monthly',
                'billing_day': 1,
                'billing_address': self.created_data['addresses'][0]
            },
            {
                'account_number': 'ACC000002',
                'account_type': 'residential',
                'status': 'active',
                'primary_user': self.created_data['users'][1],
                'tenant': self.created_data['tenants'][0],
                'billing_cycle': 'monthly',
                'billing_day': 15,
                'billing_address': self.created_data['addresses'][1]
            },
            {
                'account_number': 'ACC000003',
                'account_type': 'commercial',
                'status': 'active',
                'primary_user': self.created_data['users'][2],
                'tenant': self.created_data['tenants'][1],
                'billing_cycle': 'monthly',
                'billing_day': 1,
                'billing_address': self.created_data['addresses'][2]
            },
            {
                'account_number': 'ACC000004',
                'account_type': 'residential',
                'status': 'active',
                'primary_user': self.created_data['users'][3],
                'tenant': self.created_data['tenants'][1],
                'billing_cycle': 'monthly',
                'billing_day': 15,
                'billing_address': self.created_data['addresses'][3]
            }
        ]
        
        for data in account_data:
            account = Account.objects.create(**data)
            self.created_data['accounts'].append(account)
            self.stdout.write(f"  ✅ Created account: {account.account_number} for {account.primary_user.first_name} {account.primary_user.last_name}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(self.created_data['accounts'])} accounts")) 