"""
Create a new tenant with customizable parameters.
This command allows creating tenants for data import and testing purposes.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users.models import Tenant
import uuid


class Command(BaseCommand):
    help = 'Create a new tenant with customizable parameters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Tenant name (e.g., "SpotOn Energy")'
        )
        parser.add_argument(
            '--slug',
            type=str,
            required=True,
            help='Tenant slug (e.g., "spoton-energy")'
        )
        parser.add_argument(
            '--subdomain',
            type=str,
            help='Subdomain for tenant (defaults to slug)'
        )
        parser.add_argument(
            '--primary-domain',
            type=str,
            help='Primary domain (e.g., "spoton.co.nz")'
        )
        parser.add_argument(
            '--contact-email',
            type=str,
            help='Contact email for tenant'
        )
        parser.add_argument(
            '--contact-phone',
            type=str,
            help='Contact phone for tenant'
        )
        parser.add_argument(
            '--address',
            type=str,
            help='Physical address for tenant'
        )
        parser.add_argument(
            '--business-number',
            type=str,
            help='Business registration number'
        )
        parser.add_argument(
            '--tax-number',
            type=str,
            help='Tax identification number'
        )
        parser.add_argument(
            '--is-primary',
            action='store_true',
            help='Mark this tenant as the primary brand'
        )
        parser.add_argument(
            '--keycloak-client-uat',
            type=str,
            default='customer-uat-portal',
            help='Keycloak client ID for UAT environment'
        )
        parser.add_argument(
            '--keycloak-client-live',
            type=str,
            default='customer-live-portal',
            help='Keycloak client ID for Live environment'
        )
        parser.add_argument(
            '--timezone',
            type=str,
            default='Pacific/Auckland',
            help='Timezone for tenant'
        )
        parser.add_argument(
            '--currency',
            type=str,
            default='NZD',
            help='Currency code for tenant'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if tenant with same slug exists'
        )

    def handle(self, *args, **options):
        """Create a new tenant with the provided parameters"""
        
        # Extract required parameters
        name = options['name']
        slug = options['slug']
        subdomain = options.get('subdomain') or slug
        
        # Check if tenant already exists
        if Tenant.objects.filter(slug=slug).exists():
            if not options['force']:
                raise CommandError(
                    f'Tenant with slug "{slug}" already exists. Use --force to update it.'
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Updating existing tenant with slug "{slug}"')
                )

        try:
            with transaction.atomic():
                # Prepare tenant data
                tenant_data = {
                    'name': name,
                    'slug': slug,
                    'subdomain': subdomain,
                    'is_primary_brand': options.get('is_primary', False),
                    'keycloak_client_id_uat': options.get('keycloak_client_uat'),
                    'keycloak_client_id_live': options.get('keycloak_client_live'),
                    'timezone': options.get('timezone'),
                    'currency': options.get('currency'),
                    'is_active': True,
                }
                
                # Add optional fields if provided
                optional_fields = [
                    'primary_domain', 'contact_email', 'contact_phone', 
                    'address', 'business_number', 'tax_number'
                ]
                
                for field in optional_fields:
                    value = options.get(field.replace('_', '-'))
                    if value:
                        tenant_data[field] = value

                # Create or update tenant
                tenant, created = Tenant.objects.update_or_create(
                    slug=slug,
                    defaults=tenant_data
                )

                # Output result
                action = "Created" if created else "Updated"
                self.stdout.write(
                    self.style.SUCCESS(f'{action} tenant: {tenant.name} (slug: {tenant.slug})')
                )
                
                # Display tenant details
                self.stdout.write('\nTenant Details:')
                self.stdout.write(f'  ID: {tenant.id}')
                self.stdout.write(f'  Name: {tenant.name}')
                self.stdout.write(f'  Slug: {tenant.slug}')
                self.stdout.write(f'  Subdomain: {tenant.subdomain}')
                self.stdout.write(f'  Primary Brand: {tenant.is_primary_brand}')
                self.stdout.write(f'  Contact Email: {tenant.contact_email or "Not set"}')
                self.stdout.write(f'  Contact Phone: {tenant.contact_phone or "Not set"}')
                self.stdout.write(f'  Business Number: {tenant.business_number or "Not set"}')
                self.stdout.write(f'  Timezone: {tenant.timezone}')
                self.stdout.write(f'  Currency: {tenant.currency}')
                self.stdout.write(f'  Active: {tenant.is_active}')
                
                return tenant.slug

        except Exception as e:
            raise CommandError(f'Failed to create tenant: {str(e)}')