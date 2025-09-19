"""
Management command to fix connection relationships and establish proper contract assignments
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import Tenant, Account
from core.contracts.models import ServiceContract
from core.contracts.plan_assignments import ContractConnectionAssignment


class Command(BaseCommand):
    help = 'Fix connection relationships and establish proper contract assignments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant slug to process (optional, processes all if not specified)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        tenant_slug = options.get('tenant')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get tenants to process
        if tenant_slug:
            try:
                tenants = [Tenant.objects.get(slug=tenant_slug)]
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant with slug "{tenant_slug}" not found'))
                return
        else:
            tenants = Tenant.objects.all()
        
        total_processed = 0
        total_assigned = 0
        total_errors = 0
        
        for tenant in tenants:
            self.stdout.write(f'\nProcessing tenant: {tenant.name} ({tenant.slug})')
            
            try:
                # Import connection model
                from energy.connections.models import Connection
                
                # Get all connections for this tenant
                connections = Connection.objects.filter(tenant=tenant)
                tenant_processed = 0
                tenant_assigned = 0
                
                for connection in connections:
                    try:
                        with transaction.atomic():
                            # Check if connection has a contract_id but no assignment
                            if connection.contract_id:
                                # Check if assignment already exists
                                existing_assignment = ContractConnectionAssignment.objects.filter(
                                    connection_id=connection.id,
                                    tenant=tenant
                                ).first()
                                
                                if not existing_assignment:
                                    # Try to get the contract
                                    try:
                                        contract = ServiceContract.objects.get(
                                            id=connection.contract_id,
                                            tenant=tenant
                                        )
                                        
                                        if not dry_run:
                                            # Create the assignment
                                            assignment = ContractConnectionAssignment.objects.create(
                                                tenant=tenant,
                                                contract=contract,
                                                connection_id=connection.id,
                                                status='active' if connection.status == 'active' else 'assigned'
                                            )
                                            
                                            self.stdout.write(
                                                f'  ✅ Created assignment: Connection {connection.connection_identifier} → Contract {contract.contract_number}'
                                            )
                                        else:
                                            self.stdout.write(
                                                f'  [DRY RUN] Would create assignment: Connection {connection.connection_identifier} → Contract {contract.contract_number}'
                                            )
                                        
                                        tenant_assigned += 1
                                        
                                    except ServiceContract.DoesNotExist:
                                        self.stdout.write(
                                            self.style.WARNING(f'  ⚠️  Contract {connection.contract_id} not found for connection {connection.connection_identifier}')
                                        )
                                        
                                        # Clear invalid contract_id
                                        if not dry_run:
                                            connection.contract_id = None
                                            connection.save()
                                            
                                else:
                                    self.stdout.write(
                                        f'  ℹ️  Assignment already exists for connection {connection.connection_identifier}'
                                    )
                            
                            # Check if connection has account but no contract
                            elif connection.account_id:
                                # Try to find or create a contract for this account
                                try:
                                    account = Account.objects.get(id=connection.account_id, tenant=tenant)
                                    
                                    # Look for existing contract for this service type
                                    contract = ServiceContract.objects.filter(
                                        account=account,
                                        contract_type=connection.service_type,
                                        status__in=['active', 'draft', 'pending']
                                    ).first()
                                    
                                    if not contract and not dry_run:
                                        # Create a contract for this connection
                                        contract = ServiceContract.objects.create(
                                            tenant=tenant,
                                            account=account,
                                            contract_type=connection.service_type,
                                            service_name=f'{connection.service_type.title()} Service',
                                            contract_number=f'AUTO-{connection.service_type.upper()}-{account.account_number}',
                                            status='active',
                                            start_date=connection.created_at
                                        )
                                        
                                        self.stdout.write(
                                            f'  ✅ Created contract: {contract.contract_number} for account {account.account_number}'
                                        )
                                    
                                    if contract:
                                        # Update connection with contract_id
                                        if not dry_run:
                                            connection.contract_id = contract.id
                                            connection.save()
                                            
                                            # Create assignment
                                            assignment, created = ContractConnectionAssignment.objects.get_or_create(
                                                tenant=tenant,
                                                contract=contract,
                                                connection_id=connection.id,
                                                defaults={
                                                    'status': 'active' if connection.status == 'active' else 'assigned'
                                                }
                                            )
                                            
                                            if created:
                                                self.stdout.write(
                                                    f'  ✅ Created assignment: Connection {connection.connection_identifier} → Contract {contract.contract_number}'
                                                )
                                                tenant_assigned += 1
                                        else:
                                            self.stdout.write(
                                                f'  [DRY RUN] Would assign connection {connection.connection_identifier} to contract {contract.contract_number if contract else "NEW"}'
                                            )
                                            tenant_assigned += 1
                                    
                                except Account.DoesNotExist:
                                    self.stdout.write(
                                        self.style.WARNING(f'  ⚠️  Account {connection.account_id} not found for connection {connection.connection_identifier}')
                                    )
                                    
                                    # Clear invalid account_id
                                    if not dry_run:
                                        connection.account_id = None
                                        connection.save()
                            
                            tenant_processed += 1
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Error processing connection {connection.connection_identifier}: {str(e)}')
                        )
                        total_errors += 1
                
                self.stdout.write(
                    f'  Tenant summary: {tenant_processed} connections processed, {tenant_assigned} assignments created'
                )
                
                total_processed += tenant_processed
                total_assigned += tenant_assigned
                
            except ImportError:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Connection model not available for tenant {tenant.slug}')
                )
                continue
        
        # Final summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(f'Total connections processed: {total_processed}')
        self.stdout.write(f'Total assignments created: {total_assigned}')
        if total_errors > 0:
            self.stdout.write(self.style.ERROR(f'Total errors: {total_errors}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a dry run. Re-run without --dry-run to apply changes.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Connection relationship fixes completed!'))
