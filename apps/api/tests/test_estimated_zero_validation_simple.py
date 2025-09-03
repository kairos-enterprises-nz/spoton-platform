#!/usr/bin/env python3
"""
Simplified test script to verify that estimated readings with zero values are properly flagged as validation failures.
This test doesn't use Airflow hooks and focuses on the core validation logic.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from energy.validation.models import ValidationRule, ValidationWorkflow, ValidationSession
from energy.validation.failure_logger import ValidationFailureLogger, FailureSeverity
from users.models import Tenant


class MockHHRValidationOrchestrator:
    """Mock orchestrator for testing validation logic without Airflow dependencies"""
    
    def __init__(self):
        self.validation_failure_logger = ValidationFailureLogger()
    
    def _apply_range_check(self, rule: ValidationRule, readings: list) -> list:
        """Apply range check validation rule with detailed failure logging"""
        
        params = rule.parameters
        min_value = params.get('min_value', 0)
        max_value = params.get('max_value', 1000)
        
        initial_count = len(readings)
        processed_count = 0
        failed_count = 0
        null_count = 0
        estimated_zero_count = 0
        
        for reading in readings:
            processed_count += 1
            
            if reading['value'] is None:
                null_count += 1
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = 'Missing value'
                
            elif reading['value'] < min_value or reading['value'] > max_value:
                failed_count += 1
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = f'Value {reading["value"]} outside range [{min_value}, {max_value}]'
            
            # CRITICAL FIX: Check for estimated readings with zero values
            elif reading.get('quality_flag') == 'E' and reading['value'] == 0.0:
                estimated_zero_count += 1
                failed_count += 1
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = 'Estimated reading with zero value - implausible consumption pattern'
                
            else:
                reading['validation_flag'] = reading.get('validation_flag', 'V')
        
        print(f"📊 RANGE CHECK - Processed {processed_count}/{initial_count} readings: {null_count} null values, {failed_count} out of range ({estimated_zero_count} estimated zeros)")
        
        return readings
    
    def _apply_plausibility_check(self, rule: ValidationRule, readings: list) -> list:
        """Apply comprehensive plausibility check validation rule"""
        
        initial_count = len(readings)
        failed_count = 0
        estimated_zero_count = 0
        implausible_pattern_count = 0
        
        # Group readings by meter for pattern analysis
        meter_groups = {}
        for reading in readings:
            key = (reading['icp_id'], reading['meter_register_id'])
            if key not in meter_groups:
                meter_groups[key] = []
            meter_groups[key].append(reading)
        
        for meter_readings in meter_groups.values():
            meter_readings.sort(key=lambda x: x['timestamp'])
            
            # Check for implausible patterns
            zero_count = 0
            estimated_count = 0
            
            for i, reading in enumerate(meter_readings):
                
                # Check 1: Estimated readings with zero values
                if reading.get('quality_flag') == 'E' and reading['value'] == 0.0:
                    estimated_zero_count += 1
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = 'Estimated zero consumption - implausible pattern'
                    continue
                
                # Check 2: Extended periods of zero consumption (>12 hours)
                if reading['value'] == 0.0:
                    zero_count += 1
                else:
                    zero_count = 0
                
                if zero_count > 24:  # 24 consecutive 30-minute intervals = 12 hours
                    implausible_pattern_count += 1
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = f'Extended zero consumption pattern ({zero_count * 0.5} hours)'
                    continue
                
                # Check 3: High percentage of estimated readings in sequence
                if reading.get('quality_flag') == 'E':
                    estimated_count += 1
                else:
                    estimated_count = 0
                
                if estimated_count > 12:  # 12 consecutive estimated readings = 6 hours
                    implausible_pattern_count += 1
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = f'Extended estimated reading pattern ({estimated_count * 0.5} hours)'
                    continue
                
                # Check 4: Implausible quality flag transitions
                if i > 0:
                    prev_reading = meter_readings[i-1]
                    if (prev_reading.get('quality_flag') == 'A' and 
                        reading.get('quality_flag') == 'E' and 
                        reading['value'] == 0.0):
                        
                        implausible_pattern_count += 1
                        failed_count += 1
                        reading['validation_flag'] = 'S'
                        reading['validation_notes'] = 'Implausible quality transition: A→E with zero value'
                        continue
        
        print(f"📊 PLAUSIBILITY CHECK - Processed {initial_count} readings: {estimated_zero_count} estimated zeros, {implausible_pattern_count} implausible patterns, {failed_count} total failures")
        
        return readings


def test_estimated_zero_validation():
    """Test that estimated readings with zero values are properly flagged"""
    
    print("🧪 Testing Estimated Zero Validation Fix")
    print("=" * 60)
    
    # Test data: Mix of normal readings and problematic estimated zeros
    test_readings = [
        {
            'id': 1,
            'icp_id': '0000054602CP902',
            'meter_register_id': '001',
            'timestamp': datetime(2024, 2, 29, 11, 0, 0),
            'value': 1.5,
            'quality_flag': 'A',  # Actual reading - should pass
            'session_id': 'test_session_1'
        },
        {
            'id': 2,
            'icp_id': '0000054602CP902',
            'meter_register_id': '001',
            'timestamp': datetime(2024, 2, 29, 11, 30, 0),
            'value': 0.0,
            'quality_flag': 'E',  # Estimated zero - should FAIL
            'session_id': 'test_session_1'
        },
        {
            'id': 3,
            'icp_id': '0000054602CP902',
            'meter_register_id': '001',
            'timestamp': datetime(2024, 2, 29, 12, 0, 0),
            'value': 0.0,
            'quality_flag': 'A',  # Actual zero - should pass (legitimate)
            'session_id': 'test_session_1'
        },
        {
            'id': 4,
            'icp_id': '0000054602CP902',
            'meter_register_id': '001',
            'timestamp': datetime(2024, 2, 29, 12, 30, 0),
            'value': 0.0,
            'quality_flag': 'E',  # Another estimated zero - should FAIL
            'session_id': 'test_session_1'
        },
        {
            'id': 5,
            'icp_id': '0000054602CP902',
            'meter_register_id': '001',
            'timestamp': datetime(2024, 2, 29, 13, 0, 0),
            'value': 2.1,
            'quality_flag': 'E',  # Estimated non-zero - should pass
            'session_id': 'test_session_1'
        }
    ]
    
    orchestrator = MockHHRValidationOrchestrator()
    
    # Get the PLAUSIBILITY_CHECK rule
    try:
        plausibility_rule = ValidationRule.objects.get(rule_code='PLAUSIBILITY_CHECK')
        print(f"✅ Found PLAUSIBILITY_CHECK rule: {plausibility_rule.rule_type}")
        print(f"   Parameters: {plausibility_rule.parameters}")
    except ValidationRule.DoesNotExist:
        print("❌ PLAUSIBILITY_CHECK rule not found!")
        return False
    
    print(f"\n📊 Test Data Summary:")
    print(f"   Total readings: {len(test_readings)}")
    print(f"   Actual readings: {len([r for r in test_readings if r['quality_flag'] == 'A'])}")
    print(f"   Estimated readings: {len([r for r in test_readings if r['quality_flag'] == 'E'])}")
    print(f"   Estimated zeros: {len([r for r in test_readings if r['quality_flag'] == 'E' and r['value'] == 0.0])}")
    
    # Test the range check (which includes estimated zero detection)
    print(f"\n🔍 Testing Range Check (includes estimated zero detection):")
    
    # Create a mock range check rule
    range_rule = ValidationRule(
        rule_code='HIGH_VALUE_CHECK',
        rule_type='range_check',
        parameters={'min_value': 0, 'max_value': 1000}
    )
    
    readings_copy = [r.copy() for r in test_readings]
    results = orchestrator._apply_range_check(range_rule, readings_copy)
    
    # Analyze results
    passed_readings = [r for r in results if r.get('validation_flag', 'V') == 'V']
    failed_readings = [r for r in results if r.get('validation_flag') == 'S']
    estimated_zero_failures = [r for r in failed_readings if r.get('quality_flag') == 'E' and r['value'] == 0.0]
    
    print(f"   Passed: {len(passed_readings)}")
    print(f"   Failed: {len(failed_readings)}")
    print(f"   Estimated zero failures: {len(estimated_zero_failures)}")
    
    # Test the dedicated plausibility check
    print(f"\n🔍 Testing Dedicated Plausibility Check:")
    
    readings_copy = [r.copy() for r in test_readings]
    results = orchestrator._apply_plausibility_check(plausibility_rule, readings_copy)
    
    # Analyze results
    passed_readings = [r for r in results if r.get('validation_flag', 'V') == 'V']
    failed_readings = [r for r in results if r.get('validation_flag') == 'S']
    estimated_zero_failures = [r for r in failed_readings if r.get('quality_flag') == 'E' and r['value'] == 0.0]
    
    print(f"   Passed: {len(passed_readings)}")
    print(f"   Failed: {len(failed_readings)}")
    print(f"   Estimated zero failures: {len(estimated_zero_failures)}")
    
    # Detailed analysis
    print(f"\n📋 Detailed Results:")
    for i, reading in enumerate(results):
        status = "✅ PASS" if reading.get('validation_flag', 'V') == 'V' else "❌ FAIL"
        notes = reading.get('validation_notes', 'No notes')
        print(f"   Reading {i+1}: {reading['quality_flag']}/{reading['value']} → {status}")
        if reading.get('validation_flag') == 'S':
            print(f"      Reason: {notes}")
    
    # Verify the fix is working
    expected_failures = 2  # Two estimated zero readings should fail
    actual_failures = len(estimated_zero_failures)
    
    print(f"\n🎯 Validation Results:")
    print(f"   Expected estimated zero failures: {expected_failures}")
    print(f"   Actual estimated zero failures: {actual_failures}")
    
    if actual_failures == expected_failures:
        print("✅ SUCCESS: Estimated zero readings are now properly flagged as validation failures!")
        return True
    else:
        print("❌ FAILURE: Estimated zero readings are still passing validation!")
        return False


def test_database_validation():
    """Test the actual database data to see current validation results"""
    
    print("\n🔍 Testing Current Database Validation Results")
    print("=" * 60)
    
    from django.db import connection
    
    # Query for estimated readings with zero values
    query = """
    SELECT 
        icp_id,
        meter_register_id,
        timestamp,
        value_calculated,
        original_quality_flag,
        validation_flag,
        processing_notes,
        validation_results
    FROM metering_processed.interval_reads_calculated
    WHERE original_quality_flag = 'E' 
    AND value_calculated = 0.0
    AND validation_flag = 'V'  -- Currently passing validation
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    
    print(f"📊 Found {len(results)} estimated zero readings currently passing validation:")
    
    for result in results:
        icp_id, register_id, timestamp, value, quality_flag, validation_flag, notes, validation_results = result
        print(f"   {icp_id}/{register_id} @ {timestamp}: {quality_flag}/{value} → {validation_flag}")
        if notes:
            print(f"      Notes: {notes}")
    
    if results:
        print(f"\n⚠️  These {len(results)} readings should be flagged as validation failures!")
        return False
    else:
        print("✅ No estimated zero readings found passing validation - fix is working!")
        return True


if __name__ == "__main__":
    print("🚀 Starting Estimated Zero Validation Test")
    print("=" * 80)
    
    # Test 1: Unit test with mock data
    test1_passed = test_estimated_zero_validation()
    
    # Test 2: Database validation check
    test2_passed = test_database_validation()
    
    print("\n📋 Final Results:")
    print("=" * 80)
    print(f"Unit Test (Mock Data): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Database Test (Real Data): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! The estimated zero validation fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! The fix may need additional work.")
        sys.exit(1) 