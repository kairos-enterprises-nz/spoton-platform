"""
Test Staff API Relationships
Tests all the relationships between tenants, users, accounts, contracts, and connections
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context, get_tenant_model
from users.models import Tenant, Account, UserAccountRole
from core.contracts.models import ServiceContract

User = get_user_model()

class Command(BaseCommand):
    help = 'Test all staff API relationships'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== TESTING STAFF API RELATIONSHIPS ==='))
        
        # Test tenant relationships
        self.test_tenants()
        
        # Test user relationships  
        self.test_users()
        
        # Test account relationships
        self.test_accounts()
        
        # Test contract relationships
        self.test_contracts()
        
        self.stdout.write(self.style.SUCCESS('\n=== ALL TESTS COMPLETED ==='))

    def test_tenants(self):
        self.stdout.write(self.style.WARNING('\n--- TESTING TENANTS ---'))
        
        tenants = Tenant.objects.all()
        self.stdout.write(f'Total tenants: {tenants.count()}')
        
        for tenant in tenants:
            self.stdout.write(f'  - {tenant.name} (ID: {tenant.id})')
            
            # Test tenant users
            users = User.objects.filter(tenant=tenant)
            self.stdout.write(f'    Users: {users.count()}')
            
            # Test tenant accounts
            accounts = Account.objects.filter(tenant=tenant)
            self.stdout.write(f'    Accounts: {accounts.count()}')

    def test_users(self):
        self.stdout.write(self.style.WARNING('\n--- TESTING USERS ---'))
        
        users = User.objects.all()
        self.stdout.write(f'Total users: {users.count()}')
        
        for user in users[:5]:  # Test first 5 users
            self.stdout.write(f'  - {user.email} (Tenant: {user.tenant.name if user.tenant else "None"})')
            
            # Test user accounts
            user_roles = UserAccountRole.objects.filter(user=user)
            accounts = [role.account for role in user_roles if role.account]
            self.stdout.write(f'    Accounts: {len(accounts)}')
            
            # Test user contracts in tenant schemas
            contracts_count = 0
            if user.tenant:
                Client = get_tenant_model()
                tenant_client = Client.objects.filter(business_tenant=user.tenant).first()
                if tenant_client:
                    with schema_context(tenant_client.schema_name):
                        contracts = ServiceContract.objects.filter(customer=user)
                        contracts_count = contracts.count()
            self.stdout.write(f'    Contracts: {contracts_count}')

    def test_accounts(self):
        self.stdout.write(self.style.WARNING('\n--- TESTING ACCOUNTS ---'))
        
        accounts = Account.objects.all()
        self.stdout.write(f'Total accounts: {accounts.count()}')
        
        for account in accounts[:5]:  # Test first 5 accounts
            self.stdout.write(f'  - {account.account_number} (Tenant: {account.tenant.name if account.tenant else "None"})')
            
            # Test account users
            user_roles = account.user_roles.all()
            self.stdout.write(f'    Users: {user_roles.count()}')
            
            # Test account contracts in tenant schemas
            contracts_count = 0
            if account.tenant:
                Client = get_tenant_model()
                tenant_client = Client.objects.filter(business_tenant=account.tenant).first()
                if tenant_client:
                    with schema_context(tenant_client.schema_name):
                        contracts = ServiceContract.objects.filter(account=account)
                        contracts_count = contracts.count()
            self.stdout.write(f'    Contracts: {contracts_count}')

    def test_contracts(self):
        self.stdout.write(self.style.WARNING('\n--- TESTING CONTRACTS ---'))
        
        Client = get_tenant_model()
        total_contracts = 0
        
        for client in Client.objects.exclude(schema_name='public'):
            self.stdout.write(f'  Schema: {client.schema_name}')
            with schema_context(client.schema_name):
                contracts = ServiceContract.objects.all()
                schema_count = contracts.count()
                total_contracts += schema_count
                self.stdout.write(f'    Contracts: {schema_count}')
                
                # Test contract relationships
                for contract in contracts[:3]:  # Test first 3 contracts
                    self.stdout.write(f'      - {contract.contract_number}')
                    self.stdout.write(f'        Customer: {contract.customer.email if contract.customer else "None"}')
                    self.stdout.write(f'        Account: {contract.account.account_number if contract.account else "None"}')
                    self.stdout.write(f'        Tenant: {contract.tenant.name if contract.tenant else "None"}')
        
        self.stdout.write(f'Total contracts across all schemas: {total_contracts}')

    def test_api_endpoints(self):
        """Test that API endpoints would work (simulated)"""
        self.stdout.write(self.style.WARNING('\n--- TESTING API ENDPOINT LOGIC ---'))
        
        # Test user contracts endpoint logic
        user = User.objects.first()
        if user and user.tenant:
            Client = get_tenant_model()
            tenant_client = Client.objects.filter(business_tenant=user.tenant).first()
            if tenant_client:
                with schema_context(tenant_client.schema_name):
                    contracts = ServiceContract.objects.filter(customer=user)
                    self.stdout.write(f'User {user.email} contracts: {contracts.count()}')
        
        # Test account contracts endpoint logic  
        account = Account.objects.first()
        if account and account.tenant:
            Client = get_tenant_model()
            tenant_client = Client.objects.filter(business_tenant=account.tenant).first()
            if tenant_client:
                with schema_context(tenant_client.schema_name):
                    contracts = ServiceContract.objects.filter(account=account)
                    self.stdout.write(f'Account {account.account_number} contracts: {contracts.count()}') 