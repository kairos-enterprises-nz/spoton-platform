from django.core.management.base import BaseCommand
from django.db import transaction
from energy.validation.models import ValidationRule


class Command(BaseCommand):
    help = 'Update PLAUSIBILITY_CHECK rule to use new plausibility_check rule type'

    def handle(self, *args, **options):
        self.stdout.write('Updating PLAUSIBILITY_CHECK rule...')
        
        try:
            with transaction.atomic():
                # Get or create the PLAUSIBILITY_CHECK rule
                rule, created = ValidationRule.objects.get_or_create(
                    rule_code='PLAUSIBILITY_CHECK',
                    defaults={
                        'name': 'Comprehensive Plausibility Check',
                        'description': 'Comprehensive plausibility validation for meter readings including estimated zero detection, pattern analysis, and quality flag validation',
                        'rule_type': 'plausibility_check',
                        'category': 'warning',
                        'parameters': {
                            'check_estimated_zeros': True,
                            'max_consecutive_zeros': 24,  # 12 hours
                            'max_consecutive_estimated': 12,  # 6 hours
                            'check_quality_transitions': True,
                            'zero_tolerance_hours': 12
                        },
                        'applies_to_meter_types': ['hhr'],
                        'is_active': True,
                        'is_blocking': False,
                        'triggers_estimation': False,
                        'priority': 50
                    }
                )
                
                if not created:
                    # Update existing rule to use new rule type
                    rule.rule_type = 'plausibility_check'
                    rule.name = 'Comprehensive Plausibility Check'
                    rule.description = 'Comprehensive plausibility validation for meter readings including estimated zero detection, pattern analysis, and quality flag validation'
                    rule.parameters = {
                        'check_estimated_zeros': True,
                        'max_consecutive_zeros': 24,  # 12 hours
                        'max_consecutive_estimated': 12,  # 6 hours
                        'check_quality_transitions': True,
                        'zero_tolerance_hours': 12
                    }
                    rule.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Updated existing PLAUSIBILITY_CHECK rule')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created new PLAUSIBILITY_CHECK rule')
                    )
                
                # Display rule details
                self.stdout.write(f'Rule Code: {rule.rule_code}')
                self.stdout.write(f'Rule Type: {rule.rule_type}')
                self.stdout.write(f'Category: {rule.category}')
                self.stdout.write(f'Priority: {rule.priority}')
                self.stdout.write(f'Active: {rule.is_active}')
                self.stdout.write(f'Parameters: {rule.parameters}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error updating PLAUSIBILITY_CHECK rule: {e}')
            )
            raise e
        
        self.stdout.write(
            self.style.SUCCESS('✅ PLAUSIBILITY_CHECK rule update completed successfully')
        ) 