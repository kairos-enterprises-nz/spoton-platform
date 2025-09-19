from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context, get_tenant_model
from core.contracts.models import ServiceContract
from decimal import Decimal
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Create service connections for the existing contracts'

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
        
        # Get tenant clients to work with
        Client = get_tenant_model()
        tenant_clients = Client.objects.exclude(schema_name='public')
        
        for client in tenant_clients:
            self.stdout.write(f"\nProcessing tenant: {client.name} ({client.schema_name})")
            
            with schema_context(client.schema_name):
                self.create_connections_for_tenant(client, dry_run)
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('DRY RUN completed - no changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('Service connections creation completed successfully'))

    def create_connections_for_tenant(self, client, dry_run):
        """Create connections for a specific tenant"""
        try:
            # Import Connection model - check if it exists
            from energy.connections.models import Connection
        except ImportError:
            self.stdout.write(self.style.ERROR(f'Connection model not found for tenant {client.name}'))
            return
        
        # Get active contracts for this tenant
        active_contracts = ServiceContract.objects.filter(
            status__in=['active', 'pending']
        ).select_related('customer', 'account')
        
        if not active_contracts.exists():
            self.stdout.write(self.style.WARNING(f'No active contracts found for tenant {client.name}'))
            return
        
        connections_created = 0
        
        for contract in active_contracts:
            # Generate connection data based on contract type
            service_type = contract.contract_type
            connection_data = self.generate_connection_data(contract, service_type, client)
            
            if not dry_run:
                try:
                    connection = Connection.objects.create(**connection_data)
                    connections_created += 1
                    self.stdout.write(f"Created connection: {connection.connection_identifier} for contract {contract.contract_number}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to create connection for contract {contract.contract_number}: {e}"))
            else:
                connections_created += 1
                self.stdout.write(f"Would create connection: {connection_data['connection_identifier']} for contract {contract.contract_number}")
        
        self.stdout.write(f"Total connections {'would be created' if dry_run else 'created'} for {client.name}: {connections_created}")

    def generate_connection_data(self, contract, service_type, client):
        """Generate connection data based on contract and service type"""
        base_data = {
            'tenant': contract.tenant,
            'account': contract.account,
            'service_type': service_type,
            'status': random.choice(['active', 'pending', 'switching']),
            'activation_date': datetime.now() - timedelta(days=random.randint(1, 15)),
            'metadata': {
                'contract_reference': contract.contract_number,
                'monthly_charge': str(contract.special_conditions.get('monthly_charge', 0)),
                'plan_name': contract.service_name,
                'plan_details': contract.special_conditions
            }
        }
        
        # Add service-specific data
        if service_type == 'electricity':
            icp_code = f'{random.randint(1000000000000, 9999999999999)}'
            base_data.update({
                'connection_identifier': icp_code,
                'icp_code': icp_code,
                'gxp_code': f'GXP{random.randint(100, 999)}',
                'network_code': f'NET{random.randint(10, 99)}',
                'metadata': {
                    **base_data['metadata'],
                    'meter_number': f'ELE{random.randint(1000000, 9999999)}',
                    'meter_type': random.choice(['smart', 'basic', 'prepaid']),
                    'supply_voltage': '230V',
                    'supply_phases': random.choice([1, 3]),
                    'tariff_type': contract.special_conditions.get('plan_type', 'fixed'),
                    'daily_charge': str(contract.special_conditions.get('daily_charge', 0)),
                    'unit_rate': str(contract.special_conditions.get('variable_charge', 0)),
                    'network_area': contract.special_conditions.get('city', 'auckland'),
                }
            })
        elif service_type == 'broadband':
            ont_serial = f'ONT{random.randint(1000000, 9999999)}'
            base_data.update({
                'connection_identifier': ont_serial,
                'ont_serial': ont_serial,
                'circuit_id': f'CIR{random.randint(100000, 999999)}',
                'connection_type': contract.special_conditions.get('plan_type', 'fibre'),
                'metadata': {
                    **base_data['metadata'],
                    'service_number': f'BB{random.randint(100000, 999999)}',
                    'download_speed': contract.special_conditions.get('download_speed', '100 Mbps'),
                    'upload_speed': contract.special_conditions.get('upload_speed', '20 Mbps'),
                    'data_allowance': contract.special_conditions.get('data_allowance', 'Unlimited'),
                    'router_provided': True,
                    'static_ip': False,
                    'network_area': contract.special_conditions.get('city', 'auckland'),
                }
            })
        elif service_type == 'mobile':
            mobile_number = f'021{random.randint(1000000, 9999999)}'
            base_data.update({
                'connection_identifier': mobile_number,
                'mobile_number': mobile_number,
                'sim_id': f'SIM{random.randint(10000000000000000000, 99999999999999999999)}',
                'imei': f'{random.randint(100000000000000, 999999999999999)}',
                'metadata': {
                    **base_data['metadata'],
                    'plan_type': contract.special_conditions.get('plan_type', 'postpaid'),
                    'data_allowance': contract.special_conditions.get('data_allowance', '20GB'),
                    'voice_minutes': contract.special_conditions.get('minutes', 'Unlimited'),
                    'text_messages': contract.special_conditions.get('texts', 'Unlimited'),
                    'network_type': '5G',
                    'roaming_enabled': True,
                }
            })
        
        return base_data

    def generate_address(self):
        """Generate a random NZ address"""
        streets = ['Queen Street', 'King Street', 'Main Road', 'High Street', 'Park Avenue', 'Victoria Street']
        suburbs = ['Auckland Central', 'Newmarket', 'Ponsonby', 'Parnell', 'Mount Eden', 'Remuera']
        
        return f"{random.randint(1, 999)} {random.choice(streets)}, {random.choice(suburbs)}, Auckland 1010" 