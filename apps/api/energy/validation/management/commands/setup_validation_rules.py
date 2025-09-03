"""
Django management command to set up comprehensive validation rules
for meter data validation and estimation.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from energy.validation.models import (
    ValidationRule, TariffRegisterMap, MeterType, EstimationProfile
)


class Command(BaseCommand):
    help = 'Set up comprehensive validation rules for meter data validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all validation rules before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting existing validation rules...')
            ValidationRule.objects.all().delete()
            TariffRegisterMap.objects.all().delete()
            MeterType.objects.all().delete()
            EstimationProfile.objects.all().delete()

        with transaction.atomic():
            self.setup_meter_types()
            self.setup_tariff_register_maps()
            self.setup_validation_rules()
            self.setup_estimation_profiles()

        self.stdout.write(
            self.style.SUCCESS('Successfully set up validation rules')
        )

    def setup_meter_types(self):
        """Set up meter type configurations"""
        self.stdout.write('Setting up meter types...')
        
        meter_types = [
            {
                'code': 'smart_hhr',
                'name': 'Smart Meter (Half-Hourly)',
                'is_smart': True,
                'supports_hhr': True,
                'supports_interval': True,
                'typical_read_frequency': 'half_hourly',
                'supported_registers': ['A+', 'A-', 'B+', 'B-', 'C+', 'C-']
            },
            {
                'code': 'smart_daily',
                'name': 'Smart Meter (Daily)',
                'is_smart': True,
                'supports_hhr': False,
                'supports_interval': False,
                'typical_read_frequency': 'daily',
                'supported_registers': ['A+', 'A-']
            },
            {
                'code': 'legacy_monthly',
                'name': 'Legacy Meter (Monthly)',
                'is_smart': False,
                'supports_hhr': False,
                'supports_interval': False,
                'typical_read_frequency': 'monthly',
                'supported_registers': ['A+']
            },
            {
                'code': 'amr_daily',
                'name': 'AMR Meter (Daily)',
                'is_smart': False,
                'supports_hhr': False,
                'supports_interval': True,
                'typical_read_frequency': 'daily',
                'supported_registers': ['A+', 'A-']
            }
        ]
        
        for meter_data in meter_types:
            meter_type, created = MeterType.objects.get_or_create(
                code=meter_data['code'],
                defaults=meter_data
            )
            if created:
                self.stdout.write(f'  Created meter type: {meter_type.name}')

    def setup_tariff_register_maps(self):
        """Set up tariff register mappings"""
        self.stdout.write('Setting up tariff register maps...')
        
        register_maps = [
            {
                'register_code': 'A+',
                'tariff_group': 'inclusive',
                'is_import': True,
                'is_export': False,
                'typical_daily_min': Decimal('0.5'),
                'typical_daily_max': Decimal('150.0'),
                'description': 'Import Active Energy (Single Rate)'
            },
            {
                'register_code': 'A-',
                'tariff_group': 'generation',
                'is_import': False,
                'is_export': True,
                'typical_daily_min': Decimal('0.0'),
                'typical_daily_max': Decimal('100.0'),
                'description': 'Export Active Energy (Generation)'
            },
            {
                'register_code': 'B+',
                'tariff_group': 'day',
                'is_import': True,
                'is_export': False,
                'typical_daily_min': Decimal('0.2'),
                'typical_daily_max': Decimal('80.0'),
                'description': 'Import Active Energy (Day Rate)'
            },
            {
                'register_code': 'B-',
                'tariff_group': 'generation',
                'is_import': False,
                'is_export': True,
                'typical_daily_min': Decimal('0.0'),
                'typical_daily_max': Decimal('50.0'),
                'description': 'Export Active Energy (Day Rate)'
            },
            {
                'register_code': 'C+',
                'tariff_group': 'night',
                'is_import': True,
                'is_export': False,
                'typical_daily_min': Decimal('0.1'),
                'typical_daily_max': Decimal('60.0'),
                'description': 'Import Active Energy (Night Rate)'
            },
            {
                'register_code': 'C-',
                'tariff_group': 'generation',
                'is_import': False,
                'is_export': True,
                'typical_daily_min': Decimal('0.0'),
                'typical_daily_max': Decimal('30.0'),
                'description': 'Export Active Energy (Night Rate)'
            },
            {
                'register_code': 'D+',
                'tariff_group': 'controlled',
                'is_controlled': True,
                'is_import': True,
                'is_export': False,
                'typical_daily_min': Decimal('0.0'),
                'typical_daily_max': Decimal('40.0'),
                'description': 'Import Active Energy (Controlled Load)'
            }
        ]
        
        for register_data in register_maps:
            register_map, created = TariffRegisterMap.objects.get_or_create(
                register_code=register_data['register_code'],
                defaults=register_data
            )
            if created:
                self.stdout.write(f'  Created register map: {register_map.register_code}')

    def setup_validation_rules(self):
        """Set up comprehensive validation rules"""
        self.stdout.write('Setting up validation rules...')
        
        validation_rules = [
            # Missing Values Rule
            {
                'rule_code': 'MISSING_INTERVAL_CHECK',
                'name': 'Missing Interval Check',
                'description': 'Check for missing kWh values in interval data',
                'category': 'critical',
                'meter_type': 'interval',
                'priority': 1,
                'is_active': True,
                'is_blocking': True,
                'triggers_estimation': True,
                'estimation_method': 'linear_interpolation',
                'parameters': {
                    'check_null_values': True,
                    'check_empty_strings': True
                }
            },
            # Zero Values Rule
            {
                'rule_code': 'UNEXPECTED_ZERO_CHECK',
                'name': 'Unexpected Zero Check',
                'description': 'Check for unexpected zero consumption values',
                'category': 'warning',
                'meter_type': 'interval',
                'priority': 2,
                'is_active': True,
                'is_blocking': False,
                'triggers_estimation': False,
                'parameters': {
                    'consecutive_zero_threshold': 48,  # 24 hours
                    'exclude_controlled_load': True
                }
            },
            # High Values Rule
            {
                'rule_code': 'HIGH_VALUE_CHECK',
                'name': 'High Value Check',
                'description': 'Check for abnormally high consumption values',
                'category': 'warning',
                'meter_type': 'interval',
                'priority': 3,
                'is_active': True,
                'is_blocking': False,
                'triggers_estimation': False,
                'parameters': {
                    'interval_threshold_kwh': 100.0,
                    'daily_threshold_kwh': 1500.0,
                    'apply_to_registers': ['A+', 'B+', 'C+', 'D+']
                }
            },
            # Negative Values Rule
            {
                'rule_code': 'NEGATIVE_VALUE_CHECK',
                'name': 'Negative Value Check',
                'description': 'Check for negative consumption values',
                'category': 'critical',
                'meter_type': 'interval',
                'priority': 4,
                'is_active': True,
                'is_blocking': True,
                'triggers_estimation': True,
                'estimation_method': 'zero_fill',
                'parameters': {
                    'allow_export_registers': True,
                    'export_registers': ['A-', 'B-', 'C-']
                }
            },
            # Abnormal Trends Rule
            {
                'rule_code': 'DAILY_TREND_CHECK',
                'name': 'Daily Trend Check',
                'description': 'Check for abnormal daily consumption trends',
                'category': 'warning',
                'meter_type': 'daily',
                'priority': 5,
                'is_active': True,
                'is_blocking': False,
                'triggers_estimation': False,
                'parameters': {
                    'max_daily_deviation_percent': 400.0,
                    'min_comparison_days': 7,
                    'exclude_weekends': False
                }
            },
            # Date/Time Validation Rule
            {
                'rule_code': 'DATETIME_VALIDATION',
                'name': 'Date/Time Validation',
                'description': 'Check for invalid dates and timestamps',
                'category': 'critical',
                'meter_type': 'interval',
                'priority': 6,
                'is_active': True,
                'is_blocking': True,
                'triggers_estimation': False,
                'parameters': {
                    'future_tolerance_minutes': 60,
                    'past_tolerance_days': 365,
                    'check_timestamp_alignment': True,
                    'required_interval_minutes': 30
                }
            },
            # Load Curve Validation Rule
            {
                'rule_code': 'LOAD_CURVE_CHECK',
                'name': 'Load Curve Validation',
                'description': 'Validate load curve consistency',
                'category': 'warning',
                'meter_type': 'interval',
                'priority': 7,
                'is_active': True,
                'is_blocking': False,
                'triggers_estimation': False,
                'parameters': {
                    'min_curve_points': 24,  # Minimum intervals per day
                    'max_spike_ratio': 5.0,
                    'smoothness_threshold': 2.0
                }
            },
            # Daily Sum Thresholds Rule
            {
                'rule_code': 'DAILY_SUM_CHECK',
                'name': 'Daily Sum Check',
                'description': 'Check daily consumption sum thresholds',
                'category': 'warning',
                'meter_type': 'daily',
                'priority': 8,
                'is_active': True,
                'is_blocking': False,
                'triggers_estimation': False,
                'parameters': {
                    'min_daily_kwh': 0.0,
                    'max_daily_kwh': 10000.0,
                    'apply_to_registers': ['A+', 'B+', 'C+']
                }
            },
            # Monthly Variance Rule
            {
                'rule_code': 'MONTHLY_VARIANCE_CHECK',
                'name': 'Monthly Variance Check',
                'description': 'Check monthly consumption variance',
                'category': 'warning',
                'meter_type': 'monthly',
                'priority': 9,
                'is_active': True,
                'is_blocking': False,
                'triggers_estimation': False,
                'parameters': {
                    'max_variance_percent': 500.0,
                    'min_comparison_months': 3,
                    'seasonal_adjustment': True
                }
            },
            # Duplicate Reading Rule
            {
                'rule_code': 'DUPLICATE_READING_CHECK',
                'name': 'Duplicate Reading Check',
                'description': 'Check for duplicate readings',
                'category': 'critical',
                'meter_type': 'interval',
                'priority': 10,
                'is_active': True,
                'is_blocking': True,
                'triggers_estimation': False,
                'parameters': {
                    'check_same_timestamp': True,
                    'check_same_value': False,
                    'resolution_method': 'keep_latest'
                }
            }
        ]
        
        for rule_data in validation_rules:
            rule, created = ValidationRule.objects.get_or_create(
                rule_code=rule_data['rule_code'],
                defaults=rule_data
            )
            if created:
                self.stdout.write(f'  Created validation rule: {rule.name}')

    def setup_estimation_profiles(self):
        """Set up estimation profiles"""
        self.stdout.write('Setting up estimation profiles...')
        
        estimation_profiles = [
            {
                'profile_code': 'RESIDENTIAL_STANDARD',
                'name': 'Residential Standard Profile',
                'description': 'Standard residential consumption profile',
                'meter_types': ['smart_hhr', 'smart_daily'],
                'parameters': {
                    'peak_hours': [7, 8, 9, 17, 18, 19, 20],
                    'off_peak_hours': [22, 23, 0, 1, 2, 3, 4, 5, 6],
                    'weekend_adjustment': 0.9,
                    'seasonal_factors': {
                        'summer': 1.2,
                        'winter': 1.1,
                        'spring': 1.0,
                        'autumn': 1.0
                    }
                },
                'is_active': True
            },
            {
                'profile_code': 'COMMERCIAL_STANDARD',
                'name': 'Commercial Standard Profile',
                'description': 'Standard commercial consumption profile',
                'meter_types': ['smart_hhr', 'smart_daily'],
                'parameters': {
                    'peak_hours': [8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                    'off_peak_hours': [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7],
                    'weekend_adjustment': 0.3,
                    'seasonal_factors': {
                        'summer': 1.3,
                        'winter': 1.0,
                        'spring': 1.0,
                        'autumn': 1.0
                    }
                },
                'is_active': True
            },
            {
                'profile_code': 'INDUSTRIAL_STANDARD',
                'name': 'Industrial Standard Profile',
                'description': 'Standard industrial consumption profile',
                'meter_types': ['smart_hhr'],
                'parameters': {
                    'peak_hours': [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
                    'off_peak_hours': [22, 23, 0, 1, 2, 3, 4, 5],
                    'weekend_adjustment': 0.8,
                    'seasonal_factors': {
                        'summer': 1.1,
                        'winter': 1.0,
                        'spring': 1.0,
                        'autumn': 1.0
                    }
                },
                'is_active': True
            }
        ]
        
        for profile_data in estimation_profiles:
            profile, created = EstimationProfile.objects.get_or_create(
                profile_code=profile_data['profile_code'],
                defaults=profile_data
            )
            if created:
                self.stdout.write(f'  Created estimation profile: {profile.name}') 