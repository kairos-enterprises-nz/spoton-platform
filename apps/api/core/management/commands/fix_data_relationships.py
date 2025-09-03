from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context, get_tenant_model
from users.models import User, Account, Tenant, UserAccountRole
from core.contracts.models import ServiceContract
from decimal import Decimal
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Fix data relationships: tenant->user->account->contract->connection->plan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating the records',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be created'))
        
        self.stdout.write('🔧 Fixing Data Relationships...')
        
        # Get tenant clients
        Client = get_tenant_model()
        tenant_clients = Client.objects.exclude(schema_name='public')
        
        for client in tenant_clients:
            self.stdout.write(f"\n🏢 Processing tenant: {client.name} ({client.schema_name})")
            
            with schema_context(client.schema_name):
                self.fix_tenant_relationships(client, dry_run)
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('DRY RUN completed - no changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('Data relationships fixed successfully'))

    def fix_tenant_relationships(self, client, dry_run):
        """Fix relationships for a specific tenant"""
        
        # Step 1: Fix User-Account relationships (multiple users per account)
        self.fix_user_account_relationships(client, dry_run)
        
        # Step 2: Fix Contract-Connection relationships (one contract per service)
        self.fix_contract_connection_relationships(client, dry_run)
        
        # Step 3: Fix Connection-Plan relationships (one plan per connection)
        self.fix_connection_plan_relationships(client, dry_run)

    def fix_user_account_relationships(self, client, dry_run):
        """Ensure multiple users can be under one account with proper roles"""
        self.stdout.write(f"  👥 Fixing User-Account relationships...")
        
        # Get tenant
        tenant = Tenant.objects.filter(name=client.name).first()
        if not tenant:
            self.stdout.write(f"    ❌ Tenant not found: {client.name}")
            return
        
        # Get all accounts for this tenant
        accounts = Account.objects.filter(tenant=tenant)
        
        for account in accounts:
            # Get existing user roles for this account
            existing_roles = UserAccountRole.objects.filter(account=account)
            
            if existing_roles.count() == 0:
                # No users assigned to this account - this shouldn't happen
                self.stdout.write(f"    ⚠️  Account {account.account_number} has no users")
                continue
            
            # Check if we have an owner
            owner_role = existing_roles.filter(role='owner').first()
            if not owner_role:
                # Make the first user the owner
                first_role = existing_roles.first()
                if not dry_run:
                    first_role.role = 'owner'
                    first_role.save()
                self.stdout.write(f"    ✅ Set {first_role.user.email} as owner of {account.account_number}")
            
            # Add additional family members if account has less than 2 users
            if existing_roles.count() < 2:
                additional_users = self.create_additional_users(tenant, account, dry_run)
                self.stdout.write(f"    ➕ Added {additional_users} additional users to {account.account_number}")

    def create_additional_users(self, tenant, account, dry_run):
        """Create additional family members for an account"""
        family_members = [
            {'first_name': 'Jane', 'last_name': 'Smith', 'role': 'member'},
            {'first_name': 'Tom', 'last_name': 'Smith', 'role': 'member'},
        ]
        
        created_count = 0
        
        for member in family_members:
            if created_count >= 1:  # Limit to 1 additional user per account
                break
                
            email = f"{member['first_name'].lower()}.{member['last_name'].lower()}@{account.account_number.lower().replace('#', '').replace('-', '')}.com"
            
            # Check if user already exists
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                continue  # Skip if user already exists
            
            if not dry_run:
                # Create user
                # Create with strict field set to avoid legacy kwargs in environments with old data
                user = User.objects.create(
                    email=email,
                    first_name=member['first_name'],
                    last_name=member['last_name'],
                    user_type='customer',
                    tenant=tenant,
                    is_active=True
                )
                
                # Create account user role
                UserAccountRole.objects.create(
                    account=account,
                    user=user,
                    role=member['role'],
                    tenant=tenant
                )
                
                created_count += 1
            else:
                created_count += 1
        
        return created_count

    def fix_contract_connection_relationships(self, client, dry_run):
        """Implement one contract per service type per account (best practice)"""
        self.stdout.write(f"  📄 Fixing Contract-Connection relationships...")
        
        # Get tenant
        tenant = Tenant.objects.filter(name=client.name).first()
        if not tenant:
            return
        
        # Get all accounts
        accounts = Account.objects.filter(tenant=tenant)
        
        for account in accounts:
            # Group contracts by service type
            contracts_by_service = {}
            contracts = ServiceContract.objects.filter(account=account)
            
            for contract in contracts:
                service_type = contract.contract_type
                if service_type not in contracts_by_service:
                    contracts_by_service[service_type] = []
                contracts_by_service[service_type].append(contract)
            
            # Ensure one contract per service type
            for service_type, service_contracts in contracts_by_service.items():
                if len(service_contracts) > 1:
                    # Keep the first contract, mark others as terminated
                    primary_contract = service_contracts[0]
                    for contract in service_contracts[1:]:
                        if not dry_run:
                            contract.status = 'terminated'
                            contract.end_date = datetime.now()
                            contract.save()
                        self.stdout.write(f"    🔄 Terminated duplicate {service_type} contract: {contract.contract_number}")
                
                # Ensure each contract has a connection
                primary_contract = service_contracts[0]
                self.ensure_contract_has_connection(primary_contract, dry_run)

    def ensure_contract_has_connection(self, contract, dry_run):
        """Ensure each contract has exactly one connection"""
        try:
            from energy.connections.models import Connection
            
            # Check if contract already has a connection
            existing_connections = Connection.objects.filter(
                account=contract.account,
                service_type=contract.contract_type
            )
            
            if existing_connections.count() == 0:
                # Create connection for this contract
                if not dry_run:
                    connection_data = self.generate_connection_for_contract(contract)
                    Connection.objects.create(**connection_data)
                self.stdout.write(f"    ➕ Created connection for contract: {contract.contract_number}")
            elif existing_connections.count() > 1:
                # Keep first connection, remove others
                primary_connection = existing_connections.first()
                for conn in existing_connections[1:]:
                    if not dry_run:
                        conn.delete()
                self.stdout.write(f"    🔄 Removed duplicate connections for contract: {contract.contract_number}")
                
        except ImportError:
            self.stdout.write(f"    ⚠️  Connection model not available")

    def generate_connection_for_contract(self, contract):
        """Generate connection data for a contract"""
        service_type = contract.contract_type
        
        base_data = {
            'tenant': contract.tenant,
            'account': contract.account,
            'service_type': service_type,
            'status': 'active',
            'activation_date': contract.start_date or datetime.now(),
            'metadata': {
                'contract_reference': contract.contract_number,
                'plan_name': contract.service_name,
                'plan_details': contract.special_conditions
            }
        }
        
        # Add service-specific identifiers
        if service_type == 'electricity':
            icp_code = f'{random.randint(1000000000000, 9999999999999)}'
            base_data.update({
                'connection_identifier': icp_code,
                'icp_code': icp_code,
                'gxp_code': f'GXP{random.randint(100, 999)}',
                'network_code': f'NET{random.randint(10, 99)}',
            })
        elif service_type == 'broadband':
            ont_serial = f'ONT{random.randint(1000000, 9999999)}'
            base_data.update({
                'connection_identifier': ont_serial,
                'ont_serial': ont_serial,
                'circuit_id': f'CIR{random.randint(100000, 999999)}',
                'connection_type': 'fibre',
            })
        elif service_type == 'mobile':
            mobile_number = f'021{random.randint(1000000, 9999999)}'
            base_data.update({
                'connection_identifier': mobile_number,
                'mobile_number': mobile_number,
                'sim_id': f'SIM{random.randint(10000000000000000000, 99999999999999999999)}',
                'imei': f'{random.randint(100000000000000, 999999999999999)}',
            })
        
        return base_data

    def fix_connection_plan_relationships(self, client, dry_run):
        """Link each connection to an appropriate plan based on service type and region"""
        self.stdout.write(f"  🎯 Fixing Connection-Plan relationships...")
        
        try:
            from energy.connections.models import Connection
            from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan
            
            connections = Connection.objects.all()
            
            for connection in connections:
                plan = self.get_appropriate_plan_for_connection(connection)
                if plan:
                    # Update connection metadata with plan information
                    if not dry_run:
                        connection.metadata.update({
                            'assigned_plan_id': plan['id'],
                            'assigned_plan_name': plan['name'],
                            'assigned_plan_type': plan['service_type'],
                            'monthly_charge': plan['monthly_charge'],
                            'plan_features': plan['features']
                        })
                        connection.save()
                    self.stdout.write(f"    🔗 Linked {connection.connection_identifier} to plan: {plan['name']}")
                
        except ImportError:
            self.stdout.write(f"    ⚠️  Connection or Plan models not available")

    def get_appropriate_plan_for_connection(self, connection):
        """Get appropriate plan based on service type and region"""
        service_type = connection.service_type
        
        try:
            if service_type == 'electricity':
                from web_support.public_pricing.models import ElectricityPlan
                plans = ElectricityPlan.objects.filter(is_active=True)
                if plans.exists():
                    plan = random.choice(plans)
                    return {
                        'id': f'ele-{plan.plan_id}',
                        'name': plan.name,
                        'service_type': 'electricity',
                        'monthly_charge': float(plan.base_rate),
                        'features': [f'{plan.plan_type.title()} Plan', plan.city.title()]
                    }
            
            elif service_type == 'broadband':
                from web_support.public_pricing.models import BroadbandPlan
                plans = BroadbandPlan.objects.filter(is_active=True)
                if plans.exists():
                    plan = random.choice(plans)
                    return {
                        'id': f'bb-{plan.plan_id}',
                        'name': plan.name,
                        'service_type': 'broadband',
                        'monthly_charge': float(plan.monthly_charge),
                        'features': [f'{plan.plan_type.title()} Plan', plan.data_allowance]
                    }
            
            elif service_type == 'mobile':
                from web_support.public_pricing.models import MobilePlan
                plans = MobilePlan.objects.filter(is_active=True)
                if plans.exists():
                    plan = random.choice(plans)
                    return {
                        'id': f'mob-{plan.plan_id}',
                        'name': plan.name,
                        'service_type': 'mobile',
                        'monthly_charge': float(plan.monthly_charge),
                        'features': [plan.data_allowance, plan.minutes, plan.texts]
                    }
        
        except ImportError:
            pass
        
        return None 