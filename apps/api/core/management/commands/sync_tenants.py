"""
Sync existing Tenant models with django-tenants Client models.
This bridges your existing tenant system with django-tenants schema isolation.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import Tenant

class Command(BaseCommand):
    help = 'Sync existing Tenant models with django-tenants Client models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--create-domains',
            action='store_true',
            help='Create domain mappings for tenants',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.stdout.write(
            self.style.SUCCESS('Syncing existing tenants with django-tenants...')
        )

        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            self._sync_tenants()
            
            if options['create_domains']:
                self._create_domains()
            
            self.stdout.write(
                self.style.SUCCESS('Tenant sync completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Sync failed: {str(e)}')
            )
            raise

    def _sync_tenants(self):
        """Sync existing Tenant models with Client models"""
        self.stdout.write('Syncing tenant models...')
        
        existing_tenants = Tenant.objects.all()
        synced_count = 0
        created_count = 0
        
        for tenant in existing_tenants:
            # Check if Client already exists for this tenant
            try:
                client = Client.objects.get(business_tenant=tenant)
                self.stdout.write(f'  ✓ Client already exists for: {tenant.name}')
                synced_count += 1
            except Client.DoesNotExist:
                # Create new Client for this tenant
                if not self.dry_run:
                    client = Client.objects.create(
                        schema_name=tenant.slug,  # Use slug as schema name
                        name=tenant.name,
                        description=f"Schema for {tenant.name}",
                        business_tenant=tenant
                    )
                    self.stdout.write(f'  ✓ Created Client for: {tenant.name} (schema: {tenant.slug})')
                    created_count += 1
                else:
                    self.stdout.write(f'  → Would create Client for: {tenant.name} (schema: {tenant.slug})')
                    created_count += 1
        
        self.stdout.write(f'Tenant sync results:')
        self.stdout.write(f'  - Existing: {synced_count}')
        self.stdout.write(f'  - Created: {created_count}')

    def _create_domains(self):
        """Create domain mappings for tenants"""
        self.stdout.write('Creating domain mappings...')
        
        clients = Client.objects.all()
        domain_count = 0
        
        for client in clients:
            # Create default domain for each client
            domain_name = f"{client.schema_name}.localhost"
            
            try:
                domain = Domain.objects.get(domain=domain_name)
                self.stdout.write(f'  ✓ Domain already exists: {domain_name}')
            except Domain.DoesNotExist:
                if not self.dry_run:
                    domain = Domain.objects.create(
                        domain=domain_name,
                        tenant=client,
                        is_primary=True
                    )
                    self.stdout.write(f'  ✓ Created domain: {domain_name}')
                    domain_count += 1
                else:
                    self.stdout.write(f'  → Would create domain: {domain_name}')
                    domain_count += 1
        
        self.stdout.write(f'Created {domain_count} domain mappings')

    def _verify_sync(self):
        """Verify the sync was successful"""
        self.stdout.write('Verifying sync...')
        
        # Check that all tenants have corresponding clients
        tenants_without_clients = Tenant.objects.filter(schema_client__isnull=True)
        if tenants_without_clients.exists():
            self.stdout.write(
                self.style.WARNING(f'Found {tenants_without_clients.count()} tenants without clients')
            )
            for tenant in tenants_without_clients:
                self.stdout.write(f'  - {tenant.name} (slug: {tenant.slug})')
        else:
            self.stdout.write('✓ All tenants have corresponding clients')
        
        # Check that all clients have business tenants
        clients_without_tenants = Client.objects.filter(business_tenant__isnull=True)
        if clients_without_tenants.exists():
            self.stdout.write(
                self.style.WARNING(f'Found {clients_without_tenants.count()} clients without business tenants')
            )
            for client in clients_without_tenants:
                self.stdout.write(f'  - {client.name} (schema: {client.schema_name})')
        else:
            self.stdout.write('✓ All clients have business tenants') 