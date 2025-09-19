"""
Monitor tenant data health and integrity
Long-term maintenance and monitoring tool
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from collections import defaultdict
import json


class Command(BaseCommand):
    help = 'Monitor tenant data health and send alerts for issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Send email alerts for critical issues'
        )
        parser.add_argument(
            '--alert-email',
            type=str,
            default='admin@spoton.co.nz',
            help='Email address to send alerts to'
        )
        parser.add_argument(
            '--threshold-orphaned',
            type=int,
            default=5,
            help='Alert threshold for orphaned records'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Monitoring Tenant Data Health...'))
        
        health_report = {
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': {},
            'recommendations': []
        }
        
        try:
            # Check tenant data health
            health_report['metrics']['tenants'] = self.check_tenant_health()
            health_report['metrics']['users'] = self.check_user_health()
            health_report['metrics']['accounts'] = self.check_account_health()
            health_report['metrics']['contracts'] = self.check_contract_health()
            health_report['metrics']['connections'] = self.check_connection_health()
            health_report['metrics']['plans'] = self.check_plan_health()
            
            # Analyze health metrics
            self.analyze_health(health_report, options)
            
            # Output report
            self.output_health_report(health_report)
            
            # Send alerts if needed
            if options['send_alerts'] and (health_report['issues'] or health_report['warnings']):
                self.send_health_alert(health_report, options['alert_email'])
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Health monitoring failed: {str(e)}'))
            health_report['status'] = 'error'
            health_report['issues'].append(f'Monitoring system error: {str(e)}')

    def check_tenant_health(self):
        """Check tenant-related health metrics"""
        try:
            from users.models import Tenant
            
            tenants = Tenant.objects.all()
            active_tenants = tenants.filter(is_active=True)
            
            return {
                'total_tenants': tenants.count(),
                'active_tenants': active_tenants.count(),
                'inactive_tenants': tenants.filter(is_active=False).count(),
                'has_default': tenants.filter(slug='utility-byte-default').exists()
            }
        except Exception as e:
            return {'error': str(e)}

    def check_user_health(self):
        """Check user-tenant association health"""
        try:
            from users.models import User
            
            users = User.objects.all()
            users_with_tenant = users.filter(tenant__isnull=False)
            users_without_tenant = users.filter(tenant__isnull=True)
            
            return {
                'total_users': users.count(),
                'users_with_tenant': users_with_tenant.count(),
                'users_without_tenant': users_without_tenant.count(),
                'orphaned_percentage': round((users_without_tenant.count() / max(users.count(), 1)) * 100, 2),
                'superusers': users.filter(is_superuser=True).count()
            }
        except Exception as e:
            return {'error': str(e)}

    def check_account_health(self):
        """Check account-tenant association health"""
        try:
            from users.models import Account
            
            accounts = Account.objects.all()
            accounts_with_tenant = accounts.filter(tenant__isnull=False)
            accounts_without_tenant = accounts.filter(tenant__isnull=True)
            
            return {
                'total_accounts': accounts.count(),
                'accounts_with_tenant': accounts_with_tenant.count(),
                'accounts_without_tenant': accounts_without_tenant.count(),
                'orphaned_percentage': round((accounts_without_tenant.count() / max(accounts.count(), 1)) * 100, 2)
            }
        except Exception as e:
            return {'error': str(e)}

    def check_contract_health(self):
        """Check contract-tenant association health"""
        try:
            from core.contracts.models import ServiceContract
            
            contracts = ServiceContract.objects.all()
            contracts_with_tenant = contracts.filter(tenant__isnull=False)
            contracts_without_tenant = contracts.filter(tenant__isnull=True)
            
            return {
                'total_contracts': contracts.count(),
                'contracts_with_tenant': contracts_with_tenant.count(),
                'contracts_without_tenant': contracts_without_tenant.count(),
                'orphaned_percentage': round((contracts_without_tenant.count() / max(contracts.count(), 1)) * 100, 2),
                'active_contracts': contracts.filter(status='active').count()
            }
        except Exception as e:
            return {'error': str(e)}

    def check_connection_health(self):
        """Check connection-tenant association health"""
        try:
            from energy.connections.models import Connection
            
            connections = Connection.objects.all()
            connections_with_tenant = connections.filter(tenant__isnull=False)
            connections_without_tenant = connections.filter(tenant__isnull=True)
            
            return {
                'total_connections': connections.count(),
                'connections_with_tenant': connections_with_tenant.count(),
                'connections_without_tenant': connections_without_tenant.count(),
                'orphaned_percentage': round((connections_without_tenant.count() / max(connections.count(), 1)) * 100, 2),
                'active_connections': connections.filter(status='active').count()
            }
        except Exception as e:
            return {'error': str(e)}

    def check_plan_health(self):
        """Check plan availability health"""
        plan_health = {
            'service_plans': 0,
            'electricity_plans': 0,
            'broadband_plans': 0,
            'mobile_plans': 0,
            'total_plans': 0
        }
        
        try:
            from finance.pricing.models import ServicePlan
            plan_health['service_plans'] = ServicePlan.objects.filter(status='active').count()
        except Exception:
            pass
        
        try:
            from web_support.public_pricing.models import ElectricityPlan
            plan_health['electricity_plans'] = ElectricityPlan.objects.filter(valid_to__isnull=True).count()
        except Exception:
            pass
        
        try:
            from web_support.public_pricing.models import BroadbandPlan
            plan_health['broadband_plans'] = BroadbandPlan.objects.filter(valid_to__isnull=True).count()
        except Exception:
            pass
        
        try:
            from web_support.public_pricing.models import MobilePlan
            plan_health['mobile_plans'] = MobilePlan.objects.filter(valid_to__isnull=True).count()
        except Exception:
            pass
        
        plan_health['total_plans'] = sum([
            plan_health['service_plans'],
            plan_health['electricity_plans'],
            plan_health['broadband_plans'],
            plan_health['mobile_plans']
        ])
        
        return plan_health

    def analyze_health(self, health_report, options):
        """Analyze health metrics and identify issues"""
        threshold = options['threshold_orphaned']
        
        # Check for critical issues
        if health_report['metrics']['plans']['total_plans'] == 0:
            health_report['issues'].append('CRITICAL: No plans available - staff portal will show 0 plans')
            health_report['status'] = 'critical'
        
        if not health_report['metrics']['tenants'].get('has_default', False):
            health_report['issues'].append('CRITICAL: No default tenant found')
            health_report['status'] = 'critical'
        
        # Check for warnings
        users_orphaned = health_report['metrics']['users'].get('users_without_tenant', 0)
        if users_orphaned > threshold:
            health_report['warnings'].append(f'WARNING: {users_orphaned} users without tenant association')
        
        accounts_orphaned = health_report['metrics']['accounts'].get('accounts_without_tenant', 0)
        if accounts_orphaned > threshold:
            health_report['warnings'].append(f'WARNING: {accounts_orphaned} accounts without tenant association')
        
        connections_orphaned = health_report['metrics']['connections'].get('connections_without_tenant', 0)
        if connections_orphaned > threshold:
            health_report['warnings'].append(f'WARNING: {connections_orphaned} connections without tenant association')
        
        # Generate recommendations
        if health_report['issues'] or health_report['warnings']:
            health_report['recommendations'].append('Run: python manage.py setup_uat_environment')
        
        if users_orphaned > 0:
            health_report['recommendations'].append('Run: python manage.py fix_tenant_associations --model=users')
        
        if health_report['metrics']['plans']['total_plans'] < 5:
            health_report['recommendations'].append('Run: python manage.py create_sample_plans')

    def output_health_report(self, health_report):
        """Output health report to console"""
        status_color = self.style.SUCCESS
        if health_report['status'] == 'critical':
            status_color = self.style.ERROR
        elif health_report['warnings']:
            status_color = self.style.WARNING
        
        self.stdout.write(status_color(f'\n📊 TENANT HEALTH REPORT - Status: {health_report["status"].upper()}'))
        self.stdout.write('=' * 60)
        
        # Metrics
        self.stdout.write('\n📈 Metrics:')
        metrics = health_report['metrics']
        
        if 'tenants' in metrics and 'error' not in metrics['tenants']:
            self.stdout.write(f"  🏢 Tenants: {metrics['tenants']['active_tenants']}/{metrics['tenants']['total_tenants']} active")
        
        if 'plans' in metrics:
            plans = metrics['plans']
            self.stdout.write(f"  📋 Plans: {plans['total_plans']} total ({plans['service_plans']} service, {plans['electricity_plans']} electricity, {plans['broadband_plans']} broadband, {plans['mobile_plans']} mobile)")
        
        if 'users' in metrics and 'error' not in metrics['users']:
            users = metrics['users']
            self.stdout.write(f"  👥 Users: {users['users_with_tenant']}/{users['total_users']} with tenant ({users['orphaned_percentage']}% orphaned)")
        
        if 'accounts' in metrics and 'error' not in metrics['accounts']:
            accounts = metrics['accounts']
            self.stdout.write(f"  💳 Accounts: {accounts['accounts_with_tenant']}/{accounts['total_accounts']} with tenant ({accounts['orphaned_percentage']}% orphaned)")
        
        if 'connections' in metrics and 'error' not in metrics['connections']:
            connections = metrics['connections']
            self.stdout.write(f"  🔌 Connections: {connections['connections_with_tenant']}/{connections['total_connections']} with tenant ({connections['orphaned_percentage']}% orphaned)")
        
        # Issues
        if health_report['issues']:
            self.stdout.write(self.style.ERROR('\n🚨 Critical Issues:'))
            for issue in health_report['issues']:
                self.stdout.write(self.style.ERROR(f"  • {issue}"))
        
        # Warnings
        if health_report['warnings']:
            self.stdout.write(self.style.WARNING('\n⚠️ Warnings:'))
            for warning in health_report['warnings']:
                self.stdout.write(self.style.WARNING(f"  • {warning}"))
        
        # Recommendations
        if health_report['recommendations']:
            self.stdout.write(self.style.SUCCESS('\n💡 Recommendations:'))
            for rec in health_report['recommendations']:
                self.stdout.write(f"  • {rec}")
        
        if not health_report['issues'] and not health_report['warnings']:
            self.stdout.write(self.style.SUCCESS('\n✅ All tenant health checks passed!'))

    def send_health_alert(self, health_report, alert_email):
        """Send health alert email"""
        try:
            subject = f"SpotOn Tenant Health Alert - {health_report['status'].upper()}"
            
            message = f"""
SpotOn Tenant Health Monitoring Alert

Status: {health_report['status'].upper()}
Timestamp: {health_report['timestamp']}

Critical Issues:
{chr(10).join(['• ' + issue for issue in health_report['issues']]) if health_report['issues'] else 'None'}

Warnings:
{chr(10).join(['• ' + warning for warning in health_report['warnings']]) if health_report['warnings'] else 'None'}

Recommendations:
{chr(10).join(['• ' + rec for rec in health_report['recommendations']]) if health_report['recommendations'] else 'None'}

Metrics Summary:
• Total Plans: {health_report['metrics']['plans']['total_plans']}
• Users without Tenant: {health_report['metrics']['users'].get('users_without_tenant', 'N/A')}
• Accounts without Tenant: {health_report['metrics']['accounts'].get('accounts_without_tenant', 'N/A')}
• Connections without Tenant: {health_report['metrics']['connections'].get('connections_without_tenant', 'N/A')}

Please run the recommended commands to resolve these issues.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [alert_email],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(f'📧 Health alert sent to {alert_email}'))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Failed to send alert email: {str(e)}'))
