"""
Django management command to set up Keycloak realms for SpotOn Energy.
This command configures realms, clients, and groups for the SSO system.

Usage: python manage.py setup_keycloak_realms
"""

from django.core.management.base import BaseCommand
from core.utils.environment import get_redirect_uris, get_web_origins
from django.conf import settings
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up Keycloak realms, clients, and groups for SpotOn Energy SSO'

    def __init__(self):
        super().__init__()
        # Use direct HTTP connection to Keycloak container for setup
        self.keycloak_url = 'http://172.18.0.4:8080'
        self.admin_username = 'admin'
        self.admin_password = 'spoton_keycloak_admin_2024'
        self.access_token = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            # Get admin access token
            self.stdout.write('🔑 Getting Keycloak admin access token...')
            self.get_admin_token()
            
            # Create realms
            self.stdout.write('🏗️ Setting up Keycloak realms...')
            self.setup_realms()
            
            # Create clients for each realm
            self.stdout.write('🔧 Setting up clients...')
            self.setup_clients()
            
            # Create groups and roles
            self.stdout.write('👥 Setting up groups and roles...')
            self.setup_groups_and_roles()
            
            self.stdout.write(self.style.SUCCESS('✅ Keycloak setup completed successfully!'))
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('1. Run: python manage.py migrate_users_to_keycloak')
            self.stdout.write('2. Test authentication with hybrid mode')
            self.stdout.write('3. Configure service clients with the generated secrets')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Setup failed: {str(e)}'))
            logger.exception('Keycloak setup failed')

    def get_admin_token(self):
        """Get admin access token for Keycloak API calls"""
        url = f'{self.keycloak_url}/realms/master/protocol/openid-connect/token'
        data = {
            'client_id': 'admin-cli',
            'username': self.admin_username,
            'password': self.admin_password,
            'grant_type': 'password'
        }
        
        response = requests.post(url, data=data, verify=False)
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
                self.stdout.write(f'  [DRY RUN] Data: {json.dumps(data, indent=2)}')
            return {'status': 'dry_run'}
        
        if method == 'GET':
            response = requests.get(url, headers=headers, verify=False)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, verify=False)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data, verify=False)
        
        return {
            'status_code': response.status_code,
            'data': response.json() if response.content else None,
            'text': response.text
        }

    def setup_realms(self):
        """Create the three main realms"""
        realms = [
            {
                'realm': 'spoton-customers',
                'displayName': 'SpotOn Energy Customers',
                'enabled': True,
                'registrationAllowed': True,
                'registrationEmailAsUsername': True,
                'rememberMe': True,
                'verifyEmail': True,
                'loginWithEmailAllowed': True,
                'duplicateEmailsAllowed': False,
                'resetPasswordAllowed': True,
                'editUsernameAllowed': False,
                'bruteForceProtected': True,
                'permanentLockout': False,
                'maxFailureWaitSeconds': 900,
                'minimumQuickLoginWaitSeconds': 60,
                'waitIncrementSeconds': 60,
                'quickLoginCheckMilliSeconds': 1000,
                'maxDeltaTimeSeconds': 43200,
                'failureFactor': 30
            },
            {
                'realm': 'spoton-staff',
                'displayName': 'SpotOn Energy Staff Portal',
                'enabled': True,
                'registrationAllowed': False,  # Staff users created by admin
                'registrationEmailAsUsername': True,
                'rememberMe': True,
                'verifyEmail': True,
                'loginWithEmailAllowed': True,
                'duplicateEmailsAllowed': False,
                'resetPasswordAllowed': True,
                'editUsernameAllowed': False,
                'bruteForceProtected': True,
                'permanentLockout': False,
                'maxFailureWaitSeconds': 900,
                'minimumQuickLoginWaitSeconds': 60,
                'waitIncrementSeconds': 60,
                'quickLoginCheckMilliSeconds': 1000,
                'maxDeltaTimeSeconds': 43200,
                'failureFactor': 30
            },
            {
                'realm': 'spoton-system',
                'displayName': 'SpotOn Energy System Services',
                'enabled': True,
                'registrationAllowed': False,  # Service accounts only
                'registrationEmailAsUsername': False,
                'rememberMe': False,
                'verifyEmail': False,
                'loginWithEmailAllowed': False,
                'duplicateEmailsAllowed': True,
                'resetPasswordAllowed': False,
                'editUsernameAllowed': False,
                'bruteForceProtected': True
            }
        ]
        
        for realm_config in realms:
            realm_name = realm_config['realm']
            self.stdout.write(f'  Creating realm: {realm_name}')
            
            # Check if realm exists
            result = self.api_request('GET', f'/realms/{realm_name}')
            if result.get('status_code') == 200:
                self.stdout.write(f'    ⚠️  Realm {realm_name} already exists, updating...')
                self.api_request('PUT', f'/realms/{realm_name}', realm_config)
            else:
                result = self.api_request('POST', '/realms', realm_config)
                if result.get('status_code') == 201 or result.get('status') == 'dry_run':
                    self.stdout.write(f'    ✅ Realm {realm_name} created')
                else:
                    self.stdout.write(f'    ❌ Failed to create realm {realm_name}: {result.get("text")}')

    def setup_clients(self):
        """Create clients for each service in appropriate realms"""
        clients_config = {
            'spoton-customers': [
                {
                    'clientId': 'customer-live-portal',
                    'name': 'Customer Live Portal',
                    'description': 'Production customer portal',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': True,  # Enable ROPC
                    'serviceAccountsEnabled': False,
                    'redirectUris': get_redirect_uris('web'),
                    'webOrigins': get_web_origins('web'),
                    'attributes': {
                        'pkce.code.challenge.method': 'S256'
                    }
                },
                {
                    'clientId': 'customer-uat-portal',
                    'name': 'Customer UAT Portal',
                    'description': 'UAT customer portal',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': True,  # Enable ROPC
                    'serviceAccountsEnabled': False,
                    'redirectUris': get_redirect_uris('web'),
                    'webOrigins': get_web_origins('web'),
                    'attributes': {
                        'pkce.code.challenge.method': 'S256'
                    }
                }
            ],
            'spoton-staff': [
                {
                    'clientId': 'staff-portal',
                    'name': 'Staff Management Portal',
                    'description': 'Staff and admin interface',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': False,
                    'redirectUris': ['https://staff.spoton.co.nz/*'],
                    'webOrigins': ['https://staff.spoton.co.nz']
                },
                {
                    'clientId': 'grafana',
                    'name': 'Grafana Monitoring',
                    'description': 'Grafana dashboard access',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': False,
                    'redirectUris': ['https://grafana.spoton.co.nz/login/generic_oauth'],
                    'webOrigins': ['https://grafana.spoton.co.nz']
                },
                {
                    'clientId': 'wiki',
                    'name': 'Wiki.js Documentation',
                    'description': 'Documentation wiki access',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': False,
                    'redirectUris': ['https://wiki.spoton.co.nz/*'],
                    'webOrigins': ['https://wiki.spoton.co.nz']
                },
                {
                    'clientId': 'gitea',
                    'name': 'Gitea Repository',
                    'description': 'Git repository access',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': False,
                    'redirectUris': ['https://git.spoton.co.nz/*'],
                    'webOrigins': ['https://git.spoton.co.nz']
                },
                {
                    'clientId': 'pgadmin',
                    'name': 'pgAdmin Database Manager',
                    'description': 'Database administration',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': False,
                    'redirectUris': ['https://pgadmin.spoton.co.nz/*'],
                    'webOrigins': ['https://pgadmin.spoton.co.nz']
                }
            ],
            'spoton-system': [
                {
                    'clientId': 'airflow-live',
                    'name': 'Airflow Live',
                    'description': 'Production workflow management',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': True,
                    'redirectUris': ['https://airflow-live.spoton.co.nz/*'],
                    'webOrigins': ['https://airflow-live.spoton.co.nz']
                },
                {
                    'clientId': 'airflow-uat',
                    'name': 'Airflow UAT',
                    'description': 'UAT workflow management',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': True,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': True,
                    'redirectUris': ['https://airflow-uat.spoton.co.nz/*'],
                    'webOrigins': ['https://airflow-uat.spoton.co.nz']
                },
                {
                    'clientId': 'backend-api',
                    'name': 'Django Backend API',
                    'description': 'Backend API service account',
                    'enabled': True,
                    'clientAuthenticatorType': 'client-secret',
                    'publicClient': False,
                    'standardFlowEnabled': False,
                    'directAccessGrantsEnabled': False,
                    'serviceAccountsEnabled': True,
                    'redirectUris': [],
                    'webOrigins': []
                }
            ]
        }
        
        for realm_name, clients in clients_config.items():
            self.stdout.write(f'  Setting up clients for realm: {realm_name}')
            
            for client_config in clients:
                client_id = client_config['clientId']
                self.stdout.write(f'    Creating client: {client_id}')
                
                result = self.api_request('POST', f'/realms/{realm_name}/clients', client_config)
                if result.get('status_code') == 201 or result.get('status') == 'dry_run':
                    self.stdout.write(f'      ✅ Client {client_id} created')
                    
                    # Add custom claims mappers for customer portal clients
                    if client_id in ['customer-live-portal', 'customer-uat-portal']:
                        self.setup_custom_claims_mappers(realm_name, client_id)
                elif 'already exists' in result.get('text', ''):
                    self.stdout.write(f'      ⚠️  Client {client_id} already exists, updating mappers...')
                    
                    # Add custom claims mappers for existing customer portal clients
                    if client_id in ['customer-live-portal', 'customer-uat-portal']:
                        self.setup_custom_claims_mappers(realm_name, client_id)
                else:
                    self.stdout.write(f'      ❌ Failed to create client {client_id}: {result.get("text")}')

    def setup_custom_claims_mappers(self, realm_name, client_id):
        """Add custom protocol mappers for tenant context"""
        self.stdout.write(f'      Adding custom claims mappers for {client_id}')
        
        # First, get the client's internal ID
        clients_result = self.api_request('GET', f'/realms/{realm_name}/clients?clientId={client_id}')
        if clients_result.get('status_code') != 200:
            self.stdout.write(f'      ❌ Failed to get client ID for {client_id}')
            return
            
        clients_data = clients_result.get('data', [])
        if not clients_data:
            self.stdout.write(f'      ❌ Client {client_id} not found')
            return
            
        internal_client_id = clients_data[0]['id']
        
        # Define custom claims mappers
        mappers = [
            {
                'name': 'tenant-id-mapper',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-hardcoded-claim-mapper',
                'config': {
                    'claim.name': 'tenant_id',
                    'claim.value': 'spoton',
                    'jsonType.label': 'String',
                    'id.token.claim': 'true',
                    'access.token.claim': 'true',
                    'userinfo.token.claim': 'true'
                }
            },
            {
                'name': 'environment-mapper',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-hardcoded-claim-mapper',
                'config': {
                    'claim.name': 'environment',
                    'claim.value': 'live' if 'live' in client_id else 'uat',
                    'jsonType.label': 'String',
                    'id.token.claim': 'true',
                    'access.token.claim': 'true',
                    'userinfo.token.claim': 'true'
                }
            },
            {
                'name': 'client-context-mapper',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-hardcoded-claim-mapper',
                'config': {
                    'claim.name': 'client_context',
                    'claim.value': client_id,
                    'jsonType.label': 'String',
                    'id.token.claim': 'true',
                    'access.token.claim': 'true',
                    'userinfo.token.claim': 'true'
                }
            }
        ]
        
        # Create each mapper
        for mapper in mappers:
            # Check if mapper already exists
            existing_mappers_result = self.api_request(
                'GET', 
                f'/realms/{realm_name}/clients/{internal_client_id}/protocol-mappers/models'
            )
            
            mapper_exists = False
            if existing_mappers_result.get('status_code') == 200:
                existing_mappers = existing_mappers_result.get('data', [])
                for existing_mapper in existing_mappers:
                    if existing_mapper.get('name') == mapper['name']:
                        mapper_exists = True
                        # Update existing mapper
                        mapper_id = existing_mapper['id']
                        update_result = self.api_request(
                            'PUT',
                            f'/realms/{realm_name}/clients/{internal_client_id}/protocol-mappers/models/{mapper_id}',
                            mapper
                        )
                        if update_result.get('status_code') == 204 or update_result.get('status') == 'dry_run':
                            self.stdout.write(f'        ✅ Mapper {mapper["name"]} updated')
                        else:
                            self.stdout.write(f'        ❌ Failed to update mapper {mapper["name"]}: {update_result.get("text")}')
                        break
            
            if not mapper_exists:
                # Create new mapper
                result = self.api_request(
                    'POST', 
                    f'/realms/{realm_name}/clients/{internal_client_id}/protocol-mappers/models',
                    mapper
                )
                if result.get('status_code') == 201 or result.get('status') == 'dry_run':
                    self.stdout.write(f'        ✅ Mapper {mapper["name"]} created')
                else:
                    self.stdout.write(f'        ❌ Failed to create mapper {mapper["name"]}: {result.get("text")}')

    def setup_groups_and_roles(self):
        """Create groups and roles for each realm"""
        groups_config = {
            'spoton-customers': [
                {'name': 'customers', 'path': '/customers'},
                {'name': 'premium-customers', 'path': '/premium-customers'},
                {'name': 'beta-testers', 'path': '/beta-testers'}
            ],
            'spoton-staff': [
                {'name': 'staff-support', 'path': '/staff-support'},
                {'name': 'staff-billing', 'path': '/staff-billing'},
                {'name': 'staff-technical', 'path': '/staff-technical'},
                {'name': 'staff-admin', 'path': '/staff-admin'},
                {'name': 'staff-super-admin', 'path': '/staff-super-admin'}
            ],
            'spoton-system': [
                {'name': 'service-accounts', 'path': '/service-accounts'},
                {'name': 'monitoring-services', 'path': '/monitoring-services'},
                {'name': 'etl-services', 'path': '/etl-services'}
            ]
        }
        
        for realm_name, groups in groups_config.items():
            self.stdout.write(f'  Setting up groups for realm: {realm_name}')
            
            for group_config in groups:
                group_name = group_config['name']
                self.stdout.write(f'    Creating group: {group_name}')
                
                result = self.api_request('POST', f'/realms/{realm_name}/groups', group_config)
                if result.get('status_code') == 201 or result.get('status') == 'dry_run':
                    self.stdout.write(f'      ✅ Group {group_name} created')
                else:
                    self.stdout.write(f'      ❌ Failed to create group {group_name}: {result.get("text")}') 