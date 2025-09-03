#!/usr/bin/env python3
"""
Test script for enhanced validation pipeline with trading periods and validation tracking
"""

import os
import sys
import django
from datetime import datetime, timezone

# Add project root to path
sys.path.append('/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from energy.validation.models import ValidationSession, ValidationRule

def test_enhanced_validation():
    """Test the enhanced validation logic"""
    
    print("🧪 Testing Enhanced Validation Pipeline")
    print("=" * 50)
    
    # Test trading period calculation
    test_timestamps = [
        datetime(2024, 3, 1, 0, 0, tzinfo=timezone.utc),   # TP 1 (00:00)
        datetime(2024, 3, 1, 0, 30, tzinfo=timezone.utc),  # TP 2 (00:30)
        datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc),  # TP 25 (12:00)
        datetime(2024, 3, 1, 23, 30, tzinfo=timezone.utc), # TP 48 (23:30)
    ]
    
    for ts in test_timestamps:
        hour = ts.hour
        minute = ts.minute
        interval_of_day = (hour * 2) + (1 if minute >= 30 else 0)
        trading_period = interval_of_day + 1
        print(f"⏰ {ts.strftime('%H:%M')} → Trading Period {trading_period}")
    
    print("\n📊 Database Status:")
    
    # Check validation sessions
    sessions = ValidationSession.objects.all().order_by('-created_at')[:3]
    print(f"📋 Recent Validation Sessions: {len(sessions)}")
    for session in sessions:
        print(f"   - {session.session_id}: {session.status} ({session.processed_readings} readings)")
    
    # Check validation rules
    rules = ValidationRule.objects.all()
    print(f"📏 Validation Rules: {len(rules)}")
    for rule in rules:
        print(f"   - {rule.rule_code}: {rule.rule_type}")
    
    # Test sample reading with enhanced tracking
    print("\n🔍 Testing Enhanced Reading Structure:")
    sample_reading = {
        'id': 1,
        'tenant_id': 'test-tenant',
        'icp_id': 'TEST123456',
        'meter_register_id': '001',
        'timestamp': datetime(2024, 3, 1, 14, 30, tzinfo=timezone.utc),
        'value': 1.234,
        'source': 'TEST',
        'validation_rules_applied': ['MISSING_VALUE_CHECK', 'HIGH_VALUE_CHECK'],
        'validation_results': {
            'MISSING_VALUE_CHECK': {
                'passed': True,
                'rule_type': 'missing_data',
                'execution_time': '2025-07-05T01:45:00+00:00',
                'notes': ''
            },
            'HIGH_VALUE_CHECK': {
                'passed': True,
                'rule_type': 'range_check',
                'execution_time': '2025-07-05T01:45:00+00:00',
                'notes': ''
            }
        },
        'trading_period': 30,  # 14:30 = TP 30
        'interval_number': 30,
        'is_final_reading': True
    }
    
    print(f"📄 Sample Reading Structure:")
    print(f"   - ICP: {sample_reading['icp_id']}")
    print(f"   - Timestamp: {sample_reading['timestamp']}")
    print(f"   - Trading Period: {sample_reading['trading_period']}")
    print(f"   - Validation Rules Applied: {sample_reading['validation_rules_applied']}")
    print(f"   - Is Final Reading: {sample_reading['is_final_reading']}")
    
    print("\n✅ Enhanced validation structure test completed!")

if __name__ == '__main__':
    test_enhanced_validation() 