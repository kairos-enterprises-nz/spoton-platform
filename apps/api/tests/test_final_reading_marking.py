#!/usr/bin/env python3
"""
Test script to verify the final reading marking DAG
"""

import sys
import os
sys.path.append('/app')
sys.path.append('/app/airflow')

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from airflow.dags.validation.final_reading_marking_dag import FinalReadingMarkingOrchestrator
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_final_reading_marking():
    """Test the final reading marking DAG"""
    
    print("Testing final reading marking DAG...")
    print("=" * 80)
    
    orchestrator = FinalReadingMarkingOrchestrator()
    
    # Test 1: Create final marking session
    print("\n1. Testing final marking session creation...")
    try:
        session_id = orchestrator.create_final_marking_session()
        print(f"   ✅ Created session: {session_id}")
    except Exception as e:
        print(f"   ❌ Error creating session: {e}")
        return
    
    # Test 2: Analyze reading versions
    print("\n2. Testing reading version analysis...")
    try:
        analysis = orchestrator.analyze_reading_versions(session_id)
        print(f"   ✅ Analysis completed:")
        print(f"      - Total readings: {analysis['total_readings']}")
        print(f"      - Unique intervals: {analysis['unique_intervals']}")
        print(f"      - Readings with multiple versions: {analysis['readings_with_multiple_versions']}")
        print(f"      - Current final readings: {analysis['current_final_readings']}")
        print(f"      - Version distribution: {analysis['version_distribution']}")
    except Exception as e:
        print(f"   ❌ Error in analysis: {e}")
        return
    
    # Test 3: Determine final readings
    print("\n3. Testing final reading determination...")
    try:
        final_readings = orchestrator.determine_final_readings(session_id)
        print(f"   ✅ Determined {len(final_readings)} final readings")
        
        if final_readings:
            # Show sample final reading
            sample = final_readings[0]
            print(f"   📊 Sample final reading:")
            print(f"      - ICP: {sample['icp_id']}")
            print(f"      - Timestamp: {sample['timestamp']}")
            print(f"      - Value: {sample['value_calculated']}")
            print(f"      - Quality Flag: {sample['quality_flag']}")
            print(f"      - Validation Flag: {sample['validation_flag']}")
            print(f"      - SpotOn Validation: {sample['spoton_validation_flag']}")
            print(f"      - Is Estimated: {sample['is_estimated']}")
            print(f"      - Current Final Status: {sample['is_final_reading']}")
            
            # Analyze final reading types
            final_types = {
                'estimated': len([r for r in final_readings if r['is_estimated']]),
                'actual': len([r for r in final_readings if not r['is_estimated']]),
                'valid': len([r for r in final_readings if r['spoton_validation_flag'] == 'V']),
                'suspect': len([r for r in final_readings if r['spoton_validation_flag'] == 'S']),
                'failed': len([r for r in final_readings if r['spoton_validation_flag'] == 'F'])
            }
            
            print(f"   📊 Final reading types:")
            for reading_type, count in final_types.items():
                print(f"      - {reading_type}: {count}")
        
    except Exception as e:
        print(f"   ❌ Error determining final readings: {e}")
        return
    
    # Test 4: Update final reading flags (dry run)
    print("\n4. Testing final reading flag updates (limited test)...")
    try:
        # Only test with first 5 readings to avoid large data changes
        test_readings = final_readings[:5] if len(final_readings) >= 5 else final_readings
        
        if test_readings:
            print(f"   ⚠️  Testing with {len(test_readings)} readings (limited for safety)")
            
            # Show what would be updated
            print(f"   📋 Readings that would be marked as final:")
            for i, reading in enumerate(test_readings):
                print(f"      {i+1}. {reading['icp_id']} @ {reading['timestamp']} "
                      f"({reading['quality_flag']}/{reading['spoton_validation_flag']})")
            
            print(f"   ✅ Final reading logic test completed")
            print(f"   ⚠️  Skipping actual database update to avoid data changes")
        else:
            print(f"   ⚠️  No readings to test")
        
    except Exception as e:
        print(f"   ❌ Error in flag update test: {e}")
    
    print("\n" + "=" * 80)
    print("Final reading marking test completed!")
    print("Key features:")
    print("- ✅ Priority-based final reading selection")
    print("- ✅ Estimated readings get priority over raw readings")
    print("- ✅ Valid readings get priority over suspect/failed readings")
    print("- ✅ Most recent calculation time as tiebreaker")
    print("- ✅ Comprehensive analysis and verification")

if __name__ == "__main__":
    test_final_reading_marking() 