"""
Comprehensive tenant data audit command
Analyzes database state and identifies multi-tenancy issues
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
import json
from collections import defaultdict


class Command(BaseCommand):
    help = 'Audit tenant data associations and identify multi-tenancy issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='summary',
            choices=['summary', 'detailed', 'json'],
            help='Output format (default: summary)'
        )
        parser.add_argument(
            '--fix-suggestions',
            action='store_true',
            help='Include fix suggestions in output'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Starting Tenant Data Audit...'))
        
        audit_results = {
            'tenants': self.audit_tenants(),
            'users': self.audit_users(),
            'accounts': self.audit_accounts(),
            'contracts': self.audit_contracts(),
            'connections': self.audit_connections(),
            'plans': self.audit_plans(),
            'relationships': self.audit_relationships(),
            'orphaned_records': self.find_orphaned_records(),
            'summary': {}
        }
        
        # Generate summary
        audit_results['summary'] = self.generate_summary(audit_results)
        
        # Output results
        if options['format'] == 'json':
            self.stdout.write(json.dumps(audit_results, indent=2, default=str))
        elif options['format'] == 'detailed':
            self.output_detailed_report(audit_results)
        else:
            self.output_summary_report(audit_results)
        
        if options['fix_suggestions']:
            self.output_fix_suggestions(audit_results)

    def audit_tenants(self):
        """Audit tenant data"""
        try:
            from users.models import Tenant
            tenants = Tenant.objects.all()
            
            tenant_data = []
            for tenant in tenants:
                tenant_data.append({
                    'id': tenant.id,
                    'name': tenant.name,
                    'slug': tenant.slug,
                    'is_active': tenant.is_active,
                    'created_at': tenant.created_at
                })
            
            return {
                'count': len(tenant_data),
                'tenants': tenant_data,
                'has_default': any(t['slug'] == 'utility-byte-default' for t in tenant_data)
            }
        except Exception as e:
            return {'error': str(e), 'count': 0, 'tenants': []}

    def audit_users(self):
        """Audit user-tenant associations"""
        try:
            from users.models import User
            users = User.objects.all().select_related('tenant')
            
            user_data = {
                'total_users': users.count(),
                'users_with_tenant': users.filter(tenant__isnull=False).count(),
                'users_without_tenant': users.filter(tenant__isnull=True).count(),
                'superusers': users.filter(is_superuser=True).count(),
                'by_tenant': defaultdict(int)
            }
            
            for user in users:
                if user.tenant:
                    user_data['by_tenant'][user.tenant.slug] += 1
                else:
                    user_data['by_tenant']['NO_TENANT'] += 1
            
            return user_data
        except Exception as e:
            return {'error': str(e)}

    def audit_accounts(self):
        """Audit account-tenant associations"""
        try:
            from users.models import Account
            accounts = Account.objects.all().select_related('tenant')
            
            account_data = {
                'total_accounts': accounts.count(),
                'accounts_with_tenant': accounts.filter(tenant__isnull=False).count(),
                'accounts_without_tenant': accounts.filter(tenant__isnull=True).count(),
                'by_tenant': defaultdict(int)
            }
            
            for account in accounts:
                if account.tenant:
                    account_data['by_tenant'][account.tenant.slug] += 1
                else:
                    account_data['by_tenant']['NO_TENANT'] += 1
            
            return account_data
        except Exception as e:
            return {'error': str(e)}

    def audit_contracts(self):
        """Audit contract-tenant associations"""
        try:
            from core.contracts.models import ServiceContract
            contracts = ServiceContract.objects.all().select_related('tenant')
            
            contract_data = {
                'total_contracts': contracts.count(),
                'contracts_with_tenant': contracts.filter(tenant__isnull=False).count(),
                'contracts_without_tenant': contracts.filter(tenant__isnull=True).count(),
                'by_tenant': defaultdict(int),
                'by_status': defaultdict(int)
            }
            
            for contract in contracts:
                if contract.tenant:
                    contract_data['by_tenant'][contract.tenant.slug] += 1
                else:
                    contract_data['by_tenant']['NO_TENANT'] += 1
                contract_data['by_status'][contract.status] += 1
            
            return contract_data
        except Exception as e:
            return {'error': str(e)}

    def audit_connections(self):
        """Audit connection-tenant associations"""
        try:
            from energy.connections.models import Connection
            connections = Connection.objects.all().select_related('tenant')
            
            connection_data = {
                'total_connections': connections.count(),
                'connections_with_tenant': connections.filter(tenant__isnull=False).count(),
                'connections_without_tenant': connections.filter(tenant__isnull=True).count(),
                'by_tenant': defaultdict(int),
                'by_service_type': defaultdict(int),
                'by_status': defaultdict(int)
            }
            
            for connection in connections:
                if connection.tenant:
                    connection_data['by_tenant'][connection.tenant.slug] += 1
                else:
                    connection_data['by_tenant']['NO_TENANT'] += 1
                connection_data['by_service_type'][connection.service_type or 'UNKNOWN'] += 1
                connection_data['by_status'][connection.status or 'UNKNOWN'] += 1
            
            return connection_data
        except Exception as e:
            return {'error': str(e)}

    def audit_plans(self):
        """Audit plans - CRITICAL: This is why we see 0 plans"""
        try:
            # Try multiple potential plan model locations
            plan_models = []
            
            # Common locations for plan models
            potential_models = [
                'finance.pricing.models.Plan',
                'core.models.Plan', 
                'energy.models.Plan',
                'users.models.Plan',
                'pricing.models.Plan'
            ]
            
            plan_data = {
                'models_found': [],
                'models_not_found': [],
                'total_plans': 0,
                'plans_by_model': {},
                'critical_issue': 'INVESTIGATING_PLAN_MODEL_LOCATION'
            }
            
            for model_path in potential_models:
                try:
                    app_label, model_name = model_path.split('.')[-2], model_path.split('.')[-1]
                    model = apps.get_model(app_label, model_name)
                    plans = model.objects.all()
                    
                    plan_data['models_found'].append(model_path)
                    plan_data['plans_by_model'][model_path] = {
                        'count': plans.count(),
                        'has_tenant_field': hasattr(model, 'tenant'),
                        'sample_fields': [f.name for f in model._meta.fields][:10]
                    }
                    plan_data['total_plans'] += plans.count()
                    
                except Exception:
                    plan_data['models_not_found'].append(model_path)
            
            # Also check if there are any models with 'plan' in the name
            all_models = apps.get_models()
            plan_like_models = [
                model for model in all_models 
                if 'plan' in model.__name__.lower()
            ]
            
            plan_data['plan_like_models'] = [
                f"{model._meta.app_label}.{model.__name__}" 
                for model in plan_like_models
            ]
            
            return plan_data
        except Exception as e:
            return {'error': str(e), 'critical_issue': 'PLAN_MODEL_ACCESS_ERROR'}

    def audit_relationships(self):
        """Audit key relationships"""
        relationships = {
            'account_user_roles': self.count_relationships('users.models.UserAccountRole'),
            'contract_assignments': self.count_relationships('core.contracts.plan_assignments.ContractConnectionAssignment'),
            'account_contracts': self.audit_account_contract_relationships(),
            'connection_contracts': self.audit_connection_contract_relationships()
        }
        return relationships

    def count_relationships(self, model_path):
        """Count records for a specific relationship model"""
        try:
            app_label = model_path.split('.')[0]
            model_name = model_path.split('.')[-1]
            model = apps.get_model(app_label, model_name)
            return {
                'count': model.objects.count(),
                'model_exists': True
            }
        except Exception as e:
            return {
                'count': 0,
                'model_exists': False,
                'error': str(e)
            }

    def audit_account_contract_relationships(self):
        """Check account-contract relationships"""
        try:
            from users.models import Account
            from core.contracts.models import ServiceContract
            
            accounts_with_contracts = Account.objects.filter(
                servicecontract__isnull=False
            ).distinct().count()
            
            contracts_with_accounts = ServiceContract.objects.filter(
                account__isnull=False
            ).count()
            
            return {
                'accounts_with_contracts': accounts_with_contracts,
                'contracts_with_accounts': contracts_with_accounts,
                'total_accounts': Account.objects.count(),
                'total_contracts': ServiceContract.objects.count()
            }
        except Exception as e:
            return {'error': str(e)}

    def audit_connection_contract_relationships(self):
        """Check connection-contract relationships"""
        try:
            from energy.connections.models import Connection
            from core.contracts.models import ServiceContract
            
            connections_with_contract_id = Connection.objects.filter(
                contract_id__isnull=False
            ).count()
            
            connections_with_assignments = 0
            try:
                from core.contracts.plan_assignments import ContractConnectionAssignment
                connections_with_assignments = ContractConnectionAssignment.objects.count()
            except:
                pass
            
            return {
                'connections_with_contract_id': connections_with_contract_id,
                'connections_with_assignments': connections_with_assignments,
                'total_connections': Connection.objects.count()
            }
        except Exception as e:
            return {'error': str(e)}

    def find_orphaned_records(self):
        """Find records without proper tenant associations"""
        orphaned = {
            'users_without_tenant': [],
            'accounts_without_tenant': [],
            'contracts_without_tenant': [],
            'connections_without_tenant': []
        }
        
        try:
            from users.models import User, Account
            from core.contracts.models import ServiceContract
            from energy.connections.models import Connection
            
            # Find orphaned users
            orphaned_users = User.objects.filter(tenant__isnull=True)
            orphaned['users_without_tenant'] = [
                {'id': u.id, 'email': u.email, 'is_superuser': u.is_superuser}
                for u in orphaned_users[:10]  # Limit to first 10
            ]
            
            # Find orphaned accounts
            orphaned_accounts = Account.objects.filter(tenant__isnull=True)
            orphaned['accounts_without_tenant'] = [
                {'id': a.id, 'account_number': a.account_number}
                for a in orphaned_accounts[:10]
            ]
            
            # Find orphaned contracts
            orphaned_contracts = ServiceContract.objects.filter(tenant__isnull=True)
            orphaned['contracts_without_tenant'] = [
                {'id': c.id, 'contract_number': c.contract_number}
                for c in orphaned_contracts[:10]
            ]
            
            # Find orphaned connections
            orphaned_connections = Connection.objects.filter(tenant__isnull=True)
            orphaned['connections_without_tenant'] = [
                {'id': c.id, 'connection_identifier': c.connection_identifier}
                for c in orphaned_connections[:10]
            ]
            
        except Exception as e:
            orphaned['error'] = str(e)
        
        return orphaned

    def generate_summary(self, audit_results):
        """Generate audit summary"""
        summary = {
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check for critical issues
        if audit_results.get('plans', {}).get('total_plans', 0) == 0:
            summary['critical_issues'].append('NO_PLANS_FOUND - This explains why staff portal shows 0 plans')
        
        if audit_results.get('tenants', {}).get('count', 0) == 0:
            summary['critical_issues'].append('NO_TENANTS_FOUND - Multi-tenancy not set up')
        
        # Check for warnings
        users_without_tenant = audit_results.get('users', {}).get('users_without_tenant', 0)
        if users_without_tenant > 0:
            summary['warnings'].append(f"{users_without_tenant} users without tenant association")
        
        accounts_without_tenant = audit_results.get('accounts', {}).get('accounts_without_tenant', 0)
        if accounts_without_tenant > 0:
            summary['warnings'].append(f"{accounts_without_tenant} accounts without tenant association")
        
        return summary

    def output_summary_report(self, audit_results):
        """Output summary report"""
        self.stdout.write(self.style.SUCCESS('\n📊 TENANT DATA AUDIT SUMMARY'))
        self.stdout.write('=' * 50)
        
        # Tenants
        tenants = audit_results['tenants']
        self.stdout.write(f"🏢 Tenants: {tenants['count']} found")
        if tenants['count'] > 0:
            for tenant in tenants['tenants']:
                self.stdout.write(f"  • {tenant['name']} ({tenant['slug']}) - {'Active' if tenant['is_active'] else 'Inactive'}")
        
        # Critical Issues
        summary = audit_results['summary']
        if summary['critical_issues']:
            self.stdout.write(self.style.ERROR('\n🚨 CRITICAL ISSUES:'))
            for issue in summary['critical_issues']:
                self.stdout.write(self.style.ERROR(f"  • {issue}"))
        
        # Plans (Critical)
        plans = audit_results['plans']
        self.stdout.write(f"\n📋 Plans: {plans['total_plans']} found")
        if plans['total_plans'] == 0:
            self.stdout.write(self.style.ERROR("  ❌ NO PLANS FOUND - This is why staff portal shows 0 plans!"))
            self.stdout.write("  📍 Plan models searched:")
            for model in plans['models_not_found']:
                self.stdout.write(f"    • {model} - Not found")
        
        # Data counts
        self.stdout.write(f"\n📊 Data Summary:")
        
        users = audit_results.get('users', {})
        if 'error' in users:
            self.stdout.write(f"  • Users: ERROR - {users['error']}")
        else:
            self.stdout.write(f"  • Users: {users.get('total_users', 0)} ({users.get('users_without_tenant', 0)} without tenant)")
        
        accounts = audit_results.get('accounts', {})
        if 'error' in accounts:
            self.stdout.write(f"  • Accounts: ERROR - {accounts['error']}")
        else:
            self.stdout.write(f"  • Accounts: {accounts.get('total_accounts', 0)} ({accounts.get('accounts_without_tenant', 0)} without tenant)")
        
        contracts = audit_results.get('contracts', {})
        if 'error' in contracts:
            self.stdout.write(f"  • Contracts: ERROR - {contracts['error']}")
        else:
            self.stdout.write(f"  • Contracts: {contracts.get('total_contracts', 0)} ({contracts.get('contracts_without_tenant', 0)} without tenant)")
        
        connections = audit_results.get('connections', {})
        if 'error' in connections:
            self.stdout.write(f"  • Connections: ERROR - {connections['error']}")
        else:
            self.stdout.write(f"  • Connections: {connections.get('total_connections', 0)} ({connections.get('connections_without_tenant', 0)} without tenant)")

    def output_detailed_report(self, audit_results):
        """Output detailed report"""
        self.output_summary_report(audit_results)
        
        self.stdout.write(self.style.SUCCESS('\n📋 DETAILED BREAKDOWN'))
        self.stdout.write('=' * 50)
        
        # Users by tenant
        users = audit_results['users']
        self.stdout.write('\n👥 Users by Tenant:')
        for tenant_slug, count in users['by_tenant'].items():
            self.stdout.write(f"  • {tenant_slug}: {count} users")
        
        # Accounts by tenant
        accounts = audit_results['accounts']
        self.stdout.write('\n💳 Accounts by Tenant:')
        for tenant_slug, count in accounts['by_tenant'].items():
            self.stdout.write(f"  • {tenant_slug}: {count} accounts")
        
        # Relationships
        relationships = audit_results['relationships']
        self.stdout.write('\n🔗 Relationships:')
        self.stdout.write(f"  • Account-User Roles: {relationships['account_user_roles']['count']}")
        self.stdout.write(f"  • Contract Assignments: {relationships['contract_assignments']['count']}")

    def output_fix_suggestions(self, audit_results):
        """Output fix suggestions"""
        self.stdout.write(self.style.WARNING('\n🔧 FIX SUGGESTIONS'))
        self.stdout.write('=' * 50)
        
        if audit_results['plans']['total_plans'] == 0:
            self.stdout.write(self.style.ERROR('\n1. CRITICAL: Create Plans'))
            self.stdout.write('   Run: python manage.py create_sample_plans')
            self.stdout.write('   This will fix the "0 plans" issue in staff portal')
        
        if audit_results['tenants']['count'] == 0:
            self.stdout.write(self.style.ERROR('\n2. CRITICAL: Create Tenants'))
            self.stdout.write('   Run: python manage.py create_default_tenant')
        
        if audit_results['users']['users_without_tenant'] > 0:
            self.stdout.write(self.style.WARNING('\n3. Associate Users with Tenants'))
            self.stdout.write('   Run: python manage.py fix_tenant_associations --model=users')
        
        if audit_results['accounts']['accounts_without_tenant'] > 0:
            self.stdout.write(self.style.WARNING('\n4. Associate Accounts with Tenants'))
            self.stdout.write('   Run: python manage.py fix_tenant_associations --model=accounts')
        
        self.stdout.write('\n✅ After running fixes, re-run this audit to verify improvements')
