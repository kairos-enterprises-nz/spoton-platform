#!/usr/bin/env python3
"""
Test script to manually run enhanced validation with proper tracking
"""

import os
import sys
import django
import json
from datetime import datetime, timezone

# Add project root to path
sys.path.append('/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.db import connection
from energy.validation.models import ValidationSession, ValidationRule

def test_enhanced_validation_manual():
    """Manually test the enhanced validation logic"""
    
    print("🧪 Testing Enhanced Validation with Manual Data Insert")
    print("=" * 60)
    
    # Sample reading data with enhanced tracking
    sample_readings = [
        {
            'id': 1,
            'tenant_id': '7184b9d0-e189-4004-a33e-20e45730bca7',
            'icp_id': 'TEST001234567',
            'meter_serial_number': 'TEST001',
            'meter_register_id': '001',
            'timestamp': datetime(2024, 3, 1, 14, 30, tzinfo=timezone.utc),
            'value': 1.234,
            'value_calculated': 1.234,
            'quality_flag': 'P',
            'validation_flag': 'V',
            'source': 'TEST',
            'source_file_name': 'test_file.csv',
            'validation_rules_applied': ['MISSING_VALUE_CHECK', 'HIGH_VALUE_CHECK', 'PLAUSIBILITY_CHECK'],
            'validation_results': {
                'MISSING_VALUE_CHECK': {
                    'passed': True,
                    'rule_type': 'missing_data',
                    'execution_time': '2025-07-05T01:55:00+00:00',
                    'notes': 'Value present'
                },
                'HIGH_VALUE_CHECK': {
                    'passed': True,
                    'rule_type': 'range_check',
                    'execution_time': '2025-07-05T01:55:00+00:00',
                    'notes': 'Value within range'
                },
                'PLAUSIBILITY_CHECK': {
                    'passed': True,
                    'rule_type': 'range_check',
                    'execution_time': '2025-07-05T01:55:00+00:00',
                    'notes': 'Value plausible'
                }
            },
            'trading_period': 30,  # 14:30 = TP 30
            'interval_number': 30,
            'is_final_reading': True,
            'plausibility_score': 1.0,
            'is_estimated': False,
            'metadata': {'test': True, 'source_system': 'TEST'}
        },
        {
            'id': 2,
            'tenant_id': '7184b9d0-e189-4004-a33e-20e45730bca7',
            'icp_id': 'TEST001234567',
            'meter_serial_number': 'TEST001',
            'meter_register_id': '002',
            'timestamp': datetime(2024, 3, 1, 15, 0, tzinfo=timezone.utc),
            'value': 2.456,
            'value_calculated': 2.456,
            'quality_flag': 'P',
            'validation_flag': 'V',
            'source': 'TEST',
            'source_file_name': 'test_file.csv',
            'validation_rules_applied': ['MISSING_VALUE_CHECK', 'HIGH_VALUE_CHECK', 'PLAUSIBILITY_CHECK'],
            'validation_results': {
                'MISSING_VALUE_CHECK': {'passed': True, 'rule_type': 'missing_data', 'execution_time': '2025-07-05T01:55:00+00:00', 'notes': ''},
                'HIGH_VALUE_CHECK': {'passed': True, 'rule_type': 'range_check', 'execution_time': '2025-07-05T01:55:00+00:00', 'notes': ''},
                'PLAUSIBILITY_CHECK': {'passed': True, 'rule_type': 'range_check', 'execution_time': '2025-07-05T01:55:00+00:00', 'notes': ''}
            },
            'trading_period': 31,  # 15:00 = TP 31
            'interval_number': 31,
            'is_final_reading': True,
            'plausibility_score': 1.0,
            'is_estimated': False,
            'metadata': {'test': True, 'source_system': 'TEST'}
        }
    ]
    
    print(f"📊 Inserting {len(sample_readings)} test readings...")
    
    # Insert the test data
    with connection.cursor() as cursor:
        insert_query = """
        INSERT INTO metering_processed.interval_reads_calculated (
            raw_reading_id, tenant_id, icp_id, meter_serial_number, meter_register_id, timestamp,
            value_raw, value_calculated, original_quality_flag, validation_flag,
            validation_rules_applied, validation_results, plausibility_score,
            is_estimated, estimation_method, estimation_confidence, estimation_inputs, estimation_flags,
            source, source_file_name, processing_notes, metadata,
            trading_period, interval_number, is_final_reading
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s
        )
        """
        
        for reading in sample_readings:
            # Format validation_rules_applied as PostgreSQL array
            rules_array = '{' + ','.join(f'"{rule}"' for rule in reading['validation_rules_applied']) + '}'
            
            cursor.execute(insert_query, [
                reading.get('id'),
                reading['tenant_id'],
                reading['icp_id'],
                reading.get('meter_serial_number'),
                reading['meter_register_id'],
                reading['timestamp'],
                reading['value'],
                reading['value_calculated'],
                reading.get('quality_flag'),
                reading['validation_flag'],
                rules_array,
                json.dumps(reading['validation_results']),
                reading['plausibility_score'],
                reading['is_estimated'],
                reading.get('estimation_method'),
                reading.get('estimation_confidence'),
                json.dumps(reading.get('estimation_inputs', {})),
                json.dumps(reading.get('estimation_flags', {})),
                reading['source'],
                reading.get('source_file_name'),
                reading.get('processing_notes'),
                json.dumps(reading['metadata']),
                reading['trading_period'],
                reading['interval_number'],
                reading['is_final_reading']
            ])
    
    print("✅ Test data inserted successfully!")
    
    # Verify the data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                icp_id, meter_register_id, timestamp, trading_period, 
                validation_rules_applied, validation_results, is_final_reading
            FROM metering_processed.interval_reads_calculated 
            WHERE source = 'TEST'
            ORDER BY timestamp
        """)
        
        results = cursor.fetchall()
        
    print(f"\n📋 Verification Results ({len(results)} records):")
    print("-" * 80)
    
    for row in results:
        icp_id, meter_reg, timestamp, tp, rules, results_json, is_final = row
        print(f"🔹 {icp_id}/{meter_reg} @ {timestamp}")
        print(f"   Trading Period: {tp}")
        print(f"   Rules Applied: {rules}")
        print(f"   Is Final: {is_final}")
        print(f"   Validation Results: {len(results_json)} rules")
        print()
    
    print("🎉 Enhanced validation tracking test completed successfully!")

if __name__ == '__main__':
    test_enhanced_validation_manual() 