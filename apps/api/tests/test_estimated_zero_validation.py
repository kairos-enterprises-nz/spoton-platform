#!/usr/bin/env python3
"""
Test script to verify that estimated readings with zero values are properly flagged as validation failures.
This addresses the issue where "E" (estimated) readings with 0.0 values were incorrectly passing all plausibility checks.
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

from airflow.hooks.postgres_hook import PostgresHook
from energy.validation.models import ValidationRule, ValidationWorkflow, ValidationSession
from users.models import Tenant


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
    
    # Import the validation orchestrator
    from airflow.dags.validation.hhr_validation_dag import HHRValidationOrchestrator
    
    orchestrator = HHRValidationOrchestrator()
    
    # Get the PLAUSIBILITY_CHECK rule
    try:
        plausibility_rule = ValidationRule.objects.get(rule_code='PLAUSIBILITY_CHECK')
        print(f"✅ Found PLAUSIBILITY_CHECK rule: {plausibility_rule.rule_type}")
        print(f"   Parameters: {plausibility_rule.parameters}")
    except ValidationRule.DoesNotExist:
        print("❌ PLAUSIBILITY_CHECK rule not found!")
        return False
    
    # Create a test session
    tenant = Tenant.objects.first()
    workflow = ValidationWorkflow.objects.first()
    
    session = ValidationSession.objects.create(
        tenant=tenant,
        session_id='test_estimated_zero_validation',
        workflow=workflow,
        start_date=datetime(2024, 2, 29).date(),
        end_date=datetime(2024, 2, 29).date(),
        status='pending'
    )
    
    print(f"\n📊 Test Data Summary:")
    print(f"   Total readings: {len(test_readings)}")
    print(f"   Actual readings: {len([r for r in test_readings if r['quality_flag'] == 'A'])}")
    print(f"   Estimated readings: {len([r for r in test_readings if r['quality_flag'] == 'E'])}")
    print(f"   Estimated zeros: {len([r for r in test_readings if r['quality_flag'] == 'E' and r['value'] == 0.0])}")
    
    # Test the range check (which includes estimated zero detection)
    print(f"\n🔍 Testing Range Check (includes estimated zero detection):")
    range_rule = ValidationRule.objects.get(rule_code='HIGH_VALUE_CHECK')  # This uses range_check
    
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
    
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Query for estimated readings with zero values
    query = """
    SELECT 
        icp_id,
        meter_register_id,
        timestamp,
        value_calculated,
        quality_flag,
        validation_flag,
        validation_notes,
        validation_results
    FROM metering_processed.interval_reads_calculated
    WHERE quality_flag = 'E' 
    AND value_calculated = 0.0
    AND validation_flag = 'V'  -- Currently passing validation
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    results = pg_hook.get_records(query)
    
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