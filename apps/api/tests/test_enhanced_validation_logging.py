#!/usr/bin/env python3
"""
Test script for enhanced validation failure logging system
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from energy.validation.failure_logger import validation_failure_logger, FailureSeverity
from django.db import connection

def test_validation_failure_logging():
    """Test the enhanced validation failure logging system"""
    
    print("🧪 TESTING ENHANCED VALIDATION FAILURE LOGGING")
    print("=" * 60)
    
    # Test data for different failure scenarios
    test_scenarios = [
        {
            'name': 'High Value Outlier',
            'session_id': 'test_session_001',
            'rule_code': 'HIGH_VALUE_CHECK',
            'reading_data': {
                'icp_id': '0000123456TB123',
                'meter_serial_number': 'MTR001',
                'meter_register_id': '001',
                'timestamp': datetime.now(),
                'value': 1500.0,  # Very high value
                'trading_period': 25,
                'source': 'BCMM'
            },
            'failure_reason': 'Reading value 1500.0 kWh exceeds maximum threshold of 1000.0 kWh',
            'severity': FailureSeverity.CRITICAL
        },
        {
            'name': 'Negative Value',
            'session_id': 'test_session_001',
            'rule_code': 'NEGATIVE_VALUE_CHECK',
            'reading_data': {
                'icp_id': '0000987654TB456',
                'meter_serial_number': 'MTR002',
                'meter_register_id': '001',
                'timestamp': datetime.now() - timedelta(hours=1),
                'value': -25.5,  # Negative value
                'trading_period': 24,
                'source': 'SmartCo'
            },
            'failure_reason': 'Negative consumption value detected for import meter',
            'severity': FailureSeverity.HIGH
        },
        {
            'name': 'Missing Data',
            'session_id': 'test_session_001',
            'rule_code': 'MISSING_VALUE_CHECK',
            'reading_data': {
                'icp_id': '0000555666TB789',
                'meter_serial_number': 'MTR003',
                'meter_register_id': '001',
                'timestamp': datetime.now() - timedelta(hours=2),
                'value': None,  # Missing value
                'trading_period': 23,
                'source': 'FCLM'
            },
            'failure_reason': 'Reading value is null or missing',
            'severity': FailureSeverity.MEDIUM
        },
        {
            'name': 'DST Trading Period Issue',
            'session_id': 'test_session_001',
            'rule_code': 'CONTINUITY_CHECK',
            'reading_data': {
                'icp_id': '0000111222TB999',
                'meter_serial_number': 'MTR004',
                'meter_register_id': '001',
                'timestamp': datetime.now() - timedelta(hours=3),
                'value': 45.2,
                'trading_period': 51,  # Invalid trading period
                'source': 'IntelliHub'
            },
            'failure_reason': 'Trading period 51 exceeds maximum of 50 for DST autumn day',
            'severity': FailureSeverity.CRITICAL
        },
        {
            'name': 'Plausibility Failure',
            'session_id': 'test_session_001',
            'rule_code': 'PLAUSIBILITY_CHECK',
            'reading_data': {
                'icp_id': '0000333444TB111',
                'meter_serial_number': 'MTR005',
                'meter_register_id': '001',
                'timestamp': datetime.now() - timedelta(hours=4),
                'value': 750.0,
                'trading_period': 22,
                'source': 'MTRX'
            },
            'failure_reason': 'Reading inconsistent with historical consumption patterns',
            'severity': FailureSeverity.MEDIUM
        }
    ]
    
    # Log each test scenario
    failure_ids = []
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{i}️⃣ Testing: {scenario['name']}")
        
        validation_context = {
            'test_scenario': True,
            'scenario_name': scenario['name'],
            'processing_time_ms': 150 + (i * 25),  # Simulate varying processing times
            'consistency_score': 0.3 if 'plausibility' in scenario['name'].lower() else 0.8
        }
        
        failure_id = validation_failure_logger.log_validation_failure(
            session_id=scenario['session_id'],
            rule_code=scenario['rule_code'],
            reading_data=scenario['reading_data'],
            failure_reason=scenario['failure_reason'],
            validation_context=validation_context,
            severity=scenario['severity']
        )
        
        failure_ids.append(failure_id)
        print(f"   ✅ Logged failure: {failure_id[:8]}...")
    
    print()
    
    # Test batch failure summary
    print("📊 Testing Batch Failure Summary")
    validation_failure_logger.log_batch_failure_summary(
        session_id='test_session_001',
        total_readings=10000,
        failed_readings=len(test_scenarios),
        failure_breakdown={
            'HIGH_VALUE_CHECK': 1,
            'NEGATIVE_VALUE_CHECK': 1,
            'MISSING_VALUE_CHECK': 1,
            'CONTINUITY_CHECK': 1,
            'PLAUSIBILITY_CHECK': 1
        },
        processing_time=timedelta(minutes=5, seconds=30)
    )
    print("   ✅ Batch summary logged")
    print()
    
    # Test DST transition logging
    print("🕐 Testing DST Transition Logging")
    validation_failure_logger.log_dst_transition_issues(
        session_id='test_session_001',
        transition_date=datetime(2024, 4, 7),  # First Sunday in April 2024
        expected_trading_periods=50,
        actual_trading_periods=48,
        affected_readings=[
            {'icp_id': '0000111222TB999', 'trading_period': 49},
            {'icp_id': '0000111222TB999', 'trading_period': 50}
        ]
    )
    print("   ✅ DST transition issue logged")
    print()
    
    # Test data quality trend logging
    print("📈 Testing Data Quality Trend Logging")
    validation_failure_logger.log_data_quality_trend(
        source='BCMM',
        time_period='last_24_hours',
        quality_metrics={
            'completeness': 0.987,
            'accuracy': 0.923,
            'consistency': 0.856,
            'timeliness': 0.945
        },
        trend_direction='improving',
        recommendations=[
            'Monitor high value readings more closely',
            'Implement automated outlier detection',
            'Review meter calibration for MTR001'
        ]
    )
    print("   ✅ Quality trend logged")
    print()
    
    # Query and display logged failures
    print("🔍 QUERYING LOGGED FAILURES")
    print("-" * 40)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                failure_id,
                rule_code,
                category,
                severity,
                icp_id,
                source,
                actual_value,
                failure_reason,
                auto_fixable,
                estimated_financial_impact,
                created_at
            FROM energy_validation_failure_log
            WHERE session_id = 'test_session_001'
            ORDER BY created_at DESC
        """)
        
        failures = cursor.fetchall()
        
        if failures:
            print(f"Found {len(failures)} logged failures:")
            print()
            
            for failure in failures:
                (failure_id, rule_code, category, severity, icp_id, source, 
                 actual_value, failure_reason, auto_fixable, financial_impact, created_at) = failure
                
                print(f"🔸 Failure ID: {failure_id}")
                print(f"   Rule: {rule_code}")
                print(f"   Category: {category}")
                print(f"   Severity: {severity}")
                print(f"   ICP: {icp_id}")
                print(f"   Source: {source}")
                print(f"   Value: {actual_value}")
                print(f"   Reason: {failure_reason}")
                print(f"   Auto-fixable: {'Yes' if auto_fixable else 'No'}")
                print(f"   Financial Impact: ${financial_impact:.2f} NZD")
                print(f"   Logged: {created_at}")
                print()
        else:
            print("❌ No failures found in database")
    
    # Test failure analytics
    print("📊 FAILURE ANALYTICS")
    print("-" * 40)
    
    with connection.cursor() as cursor:
        # Get failure summary by category
        cursor.execute("""
            SELECT 
                category,
                severity,
                COUNT(*) as count,
                AVG(data_accuracy) as avg_accuracy,
                SUM(estimated_financial_impact) as total_impact
            FROM energy_validation_failure_log
            WHERE session_id = 'test_session_001'
            GROUP BY category, severity
            ORDER BY count DESC
        """)
        
        summary = cursor.fetchall()
        
        if summary:
            print("Failure Summary by Category & Severity:")
            for row in summary:
                category, severity, count, avg_accuracy, total_impact = row
                print(f"  {category:15} | {severity:8} | Count: {count:2} | Accuracy: {avg_accuracy:.2f} | Impact: ${total_impact:.2f}")
        
        print()
        
        # Get auto-fixable analysis
        cursor.execute("""
            SELECT 
                auto_fixable,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM energy_validation_failure_log WHERE session_id = 'test_session_001'), 1) as percentage
            FROM energy_validation_failure_log
            WHERE session_id = 'test_session_001'
            GROUP BY auto_fixable
        """)
        
        auto_fix_stats = cursor.fetchall()
        
        if auto_fix_stats:
            print("Auto-fixable Analysis:")
            for auto_fixable, count, percentage in auto_fix_stats:
                status = "Auto-fixable" if auto_fixable else "Manual review required"
                print(f"  {status:20} | {count:2} failures ({percentage:4.1f}%)")
    
    print()
    print("✅ Enhanced validation failure logging test completed!")
    print("📁 Check /app/logs/validation_failures.log for detailed file logs")

if __name__ == "__main__":
    test_validation_failure_logging() 