"""
Comprehensive UAT environment setup
Fixes all critical multi-tenancy and data issues in sequence
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import io
import sys


class Command(BaseCommand):
    help = 'Complete UAT environment setup - fixes all critical multi-tenancy and data issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--skip-audit',
            action='store_true',
            help='Skip the final audit step'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('🚀 SpotOn UAT Environment Setup'))
        self.stdout.write('=' * 60)
        self.stdout.write('This will fix all critical multi-tenancy and data issues:')
        self.stdout.write('• Create default tenant')
        self.stdout.write('• Associate existing data with tenant')
        self.stdout.write('• Create sample plans (fixes 0 plans issue)')
        self.stdout.write('• Fix connection relationships')
        self.stdout.write('• Run comprehensive audit')
        self.stdout.write('=' * 60)
        
        try:
            with transaction.atomic():
                # Step 1: Create default tenant and associate existing data
                self.run_step(
                    "1. Creating Default Tenant & Associating Data",
                    'create_default_tenant',
                    {'dry_run': dry_run}
                )
                
                # Step 2: Create sample plans to fix 0 plans issue
                self.run_step(
                    "2. Creating Sample Plans (Fixes 0 Plans Issue)",
                    'create_sample_plans',
                    {'dry_run': dry_run}
                )
                
                # Step 3: Fix tenant associations for any remaining orphaned data
                self.run_step(
                    "3. Fixing Remaining Tenant Associations",
                    'fix_tenant_associations',
                    {'model': 'all', 'dry_run': dry_run}
                )
                
                # Step 4: Fix user-tenant associations
                self.run_step(
                    "4. Fixing User-Tenant Associations",
                    'fix_user_tenant_associations',
                    {'dry_run': dry_run}
                )
                
                # Step 5: Fix connection relationships (from previous work)
                if not dry_run:
                    self.run_step(
                        "5. Fixing Connection Relationships",
                        'fix_connection_relationships',
                        {'dry_run': dry_run}
                    )
                else:
                    self.stdout.write(self.style.SUCCESS('\n🔧 Step 5: Fixing Connection Relationships'))
                    self.stdout.write('   Would run: python manage.py fix_connection_relationships')
                
                # Step 6: Run comprehensive audit to verify fixes
                if not options['skip_audit']:
                    self.run_step(
                        "6. Final Audit - Verifying All Fixes",
                        'audit_tenant_data',
                        {'format': 'summary'}
                    )
                
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS('\n✅ UAT Environment Setup Complete!'))
                    self.stdout.write('\n📋 Next Steps:')
                    self.stdout.write('1. Restart your staff portal application')
                    self.stdout.write('2. Check that plans are now showing (should see > 0 plans)')
                    self.stdout.write('3. Verify tenant selection is working')
                    self.stdout.write('4. Test connection management features')
                else:
                    self.stdout.write(self.style.WARNING('\n✅ Dry run completed successfully!'))
                    self.stdout.write('Run without --dry-run to apply all fixes.')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Setup failed: {str(e)}'))
            if not dry_run:
                self.stdout.write('Rolling back all changes...')
            raise

    def run_step(self, step_name, command_name, command_options=None):
        """Run a management command step with proper output capture"""
        self.stdout.write(self.style.SUCCESS(f'\n🔧 {step_name}'))
        
        if command_options is None:
            command_options = {}
        
        try:
            # Capture command output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            # Create string buffers to capture output
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            # Temporarily redirect output
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer
            
            # Run the command
            call_command(command_name, **command_options)
            
            # Restore output
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Get captured output
            stdout_content = stdout_buffer.getvalue()
            stderr_content = stderr_buffer.getvalue()
            
            # Display relevant output with indentation
            if stdout_content:
                for line in stdout_content.strip().split('\n'):
                    if line.strip():
                        self.stdout.write(f'   {line}')
            
            if stderr_content:
                for line in stderr_content.strip().split('\n'):
                    if line.strip():
                        self.stdout.write(self.style.WARNING(f'   Warning: {line}'))
            
        except Exception as e:
            # Restore output in case of error
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            self.stdout.write(self.style.ERROR(f'   ❌ Step failed: {str(e)}'))
            raise
        
        self.stdout.write(f'   ✅ {step_name} completed')

    def show_summary(self):
        """Show setup summary"""
        self.stdout.write(self.style.SUCCESS('\n📊 SETUP SUMMARY'))
        self.stdout.write('=' * 40)
        self.stdout.write('The following issues have been fixed:')
        self.stdout.write('')
        self.stdout.write('✅ Multi-tenancy Setup:')
        self.stdout.write('   • Default tenant created')
        self.stdout.write('   • All users associated with tenant')
        self.stdout.write('   • All data linked to proper tenant')
        self.stdout.write('')
        self.stdout.write('✅ Plans Issue Fixed:')
        self.stdout.write('   • Sample plans created for all service types')
        self.stdout.write('   • Staff portal will now show available plans')
        self.stdout.write('')
        self.stdout.write('✅ Data Relationships:')
        self.stdout.write('   • Connection-account-contract linkages fixed')
        self.stdout.write('   • No more "N/A" values in staff portal')
        self.stdout.write('')
        self.stdout.write('✅ API Consistency:')
        self.stdout.write('   • Tenant filtering working correctly')
        self.stdout.write('   • Connection management endpoints active')
        self.stdout.write('')
        self.stdout.write('🎯 Expected Results in Staff Portal:')
        self.stdout.write('   • Plans count > 0 (instead of 0)')
        self.stdout.write('   • Proper tenant context throughout')
        self.stdout.write('   • Connection state management working')
        self.stdout.write('   • All relationships showing proper data')
