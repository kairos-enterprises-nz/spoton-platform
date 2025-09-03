# verification/management/commands/import_csv.py

## To import the csv file. From Project Root Folder
## docker compose exec backend bash
## python manage.py import_csv web_support/address_plans/management/data/nz-addresses.csv --tenant default
## docker compose exec backend python manage.py import_csv web_support/address_plans/management/data/nz-addresses.csv --tenant default


import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web_support.address_plans.models import Address
from users.models import Tenant

class Command(BaseCommand):
    help = 'Import address data from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file to import')
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant slug to associate addresses with (default: "default")',
            default='default'
        )
        parser.add_argument(
            '--shared',
            action='store_true',
            help='Mark addresses as shared across all tenants'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch (default: 1000)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        tenant_slug = options['tenant']
        is_shared = options['shared']
        batch_size = options['batch_size']

        # Get the tenant
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
            self.stdout.write(f"Using tenant: {tenant.name} ({tenant.slug})")
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant with slug '{tenant_slug}' does not exist. Available tenants: {', '.join(Tenant.objects.values_list('slug', flat=True))}")

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Get the field names from the CSV
                fieldnames = reader.fieldnames
                if not fieldnames:
                    raise CommandError("CSV file appears to be empty or has no headers")
                
                self.stdout.write(f"CSV fields: {', '.join(fieldnames)}")
                
                # Process in batches
                addresses_to_create = []
                total_processed = 0
                total_created = 0
                
                for row in reader:
                    # Convert empty strings to None for numeric fields
                    for field in ['gd2000_xcoord', 'gd2000_ycoord', 'shape_X', 'shape_Y']:
                        if field in row and row[field] == '':
                            row[field] = None
                        elif field in row and row[field]:
                            try:
                                row[field] = float(row[field])
                            except ValueError:
                                row[field] = None
                    
                    # Convert address_id and change_id to integers
                    for field in ['address_id', 'change_id']:
                        if field in row and row[field]:
                            try:
                                row[field] = int(row[field])
                            except ValueError:
                                self.stdout.write(self.style.WARNING(f"Invalid {field} value: {row[field]}"))
                                continue
                    
                    # Create address object
                    address = Address(
                        address_id=row.get('address_id'),
                        source_dataset=row.get('source_dataset', ''),
                        change_id=row.get('change_id'),
                        full_address_number=row.get('full_address_number', ''),
                        full_road_name=row.get('full_road_name', ''),
                        full_address=row.get('full_address', ''),
                        territorial_authority=row.get('territorial_authority', ''),
                        unit_type=row.get('unit_type', ''),
                        unit_value=row.get('unit_value', ''),
                        level_type=row.get('level_type', ''),
                        level_value=row.get('level_value', ''),
                        address_number_prefix=row.get('address_number_prefix', ''),
                        address_number=row.get('address_number', ''),
                        address_number_suffix=row.get('address_number_suffix', ''),
                        address_number_high=row.get('address_number_high', ''),
                        road_name_prefix=row.get('road_name_prefix', ''),
                        road_name=row.get('road_name', ''),
                        road_type_name=row.get('road_type_name', ''),
                        road_suffix=row.get('road_suffix', ''),
                        water_name=row.get('water_name', ''),
                        water_body_name=row.get('water_body_name', ''),
                        suburb_locality=row.get('suburb_locality', ''),
                        town_city=row.get('town_city', ''),
                        address_class=row.get('address_class', ''),
                        address_lifecycle=row.get('address_lifecycle', ''),
                        gd2000_xcoord=row.get('gd2000_xcoord'),
                        gd2000_ycoord=row.get('gd2000_ycoord'),
                        road_name_ascii=row.get('road_name_ascii', ''),
                        water_name_ascii=row.get('water_name_ascii', ''),
                        water_body_name_ascii=row.get('water_body_name_ascii', ''),
                        suburb_locality_ascii=row.get('suburb_locality_ascii', ''),
                        town_city_ascii=row.get('town_city_ascii', ''),
                        full_road_name_ascii=row.get('full_road_name_ascii', ''),
                        full_address_ascii=row.get('full_address_ascii', ''),
                        shape_X=row.get('shape_X'),
                        shape_Y=row.get('shape_Y'),
                    )
                    
                    addresses_to_create.append(address)
                    total_processed += 1
                    
                    # Process batch
                    if len(addresses_to_create) >= batch_size:
                        created_count = self.create_batch(addresses_to_create)
                        total_created += created_count
                        addresses_to_create = []
                        self.stdout.write(f"Processed {total_processed} records, created {total_created} addresses")
                
                # Process remaining addresses
                if addresses_to_create:
                    created_count = self.create_batch(addresses_to_create)
                    total_created += created_count
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed {total_processed} records, created {total_created} addresses for tenant {tenant.name}'
                    )
                )
                
        except FileNotFoundError:
            raise CommandError(f"CSV file '{csv_file}' not found")
        except Exception as e:
            raise CommandError(f"Error importing data: {str(e)}")

    def create_batch(self, addresses):
        """Create a batch of addresses with proper error handling"""
        try:
            with transaction.atomic():
                # Use bulk_create with ignore_conflicts to handle duplicates
                created_addresses = Address.objects.bulk_create(
                    addresses,
                    ignore_conflicts=True,
                    batch_size=500
                )
                return len(created_addresses)
        except Exception as e:
            # If bulk create fails, try individual creates to identify problematic records
            self.stdout.write(self.style.WARNING(f"Bulk create failed: {e}. Trying individual creates..."))
            created_count = 0
            for address in addresses:
                try:
                    # Check if address already exists
                    if not Address.objects.filter(
                        address_id=address.address_id,
                        source_dataset=address.source_dataset
                    ).exists():
                        address.save()
                        created_count += 1
                except Exception as individual_error:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Failed to create address {address.address_id}: {individual_error}"
                        )
                    )
            return created_count

