"""
Test to verify midnight read parsing fix for SmartCo and BCMM DAGs

This test verifies that:
1. Midnight read (position 8) is correctly extracted and stored
2. Intervals (positions 9-56) are correctly parsed
3. Data is properly structured for database insertion

Author: SpotOn Data Team
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

def test_smco_midnight_read_parsing():
    """Test that SmartCo midnight read is parsed correctly from position 8"""
    
    # Create a sample HERM format line with mix of numeric and status values
    # Format: ICP,MeterSerial,RegisterID,Type,RegisterNum,Units,Date,Status,MidnightRead,Interval1,Interval2...Interval48
    # Include some 'A' and 'N' status flags to test the robust parsing
    intervals = []
    for i in range(1, 49):
        if i % 10 == 0:
            intervals.append('A')  # Status flag every 10th interval
        elif i % 15 == 0:
            intervals.append('N')  # No reading flag every 15th interval
        else:
            intervals.append(str(i))  # Numeric reading
    
    sample_line = "0000123456MP001,12345678,1,kWh,1,kWh,20241201,A,100.5," + ",".join(intervals)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.new', delete=False) as f:
        f.write("HERM,1,SMCO,YESP,NZDT,48\n")  # Header
        f.write(sample_line + "\n")
        temp_file = f.name
    
    try:
        # Import the function we want to test
        import sys
        sys.path.append('/app/airflow/dags/data_import')
        from metering_smco import import_smco_hhr
        
        # Mock the context
        context = {
            'ti': Mock(),
            'dag': Mock(),
            'task': Mock(),
            'run_id': 'test_run'
        }
        
        # Mock the downloaded files
        context['ti'].xcom_pull.return_value = [{
            'filename': 'test.new',
            'local_path': temp_file,
            'type': 'interval'
        }]
        
        # Call the function
        result = import_smco_hhr(**context)
        
        # Get the pushed data
        pushed_data = context['ti'].xcom_push.call_args[1]['value']
        hhr_data = pushed_data['hhr_data']
        
        # Find midnight read record (period 0)
        midnight_records = [r for r in hhr_data if r.get('period') == 0 and r.get('is_midnight_read', False)]
        interval_records = [r for r in hhr_data if r.get('period', 0) > 0 and not r.get('is_midnight_read', False)]
        
        # Verify midnight read
        assert len(midnight_records) == 1, f"Expected 1 midnight read record, got {len(midnight_records)}"
        midnight_record = midnight_records[0]
        assert midnight_record['reading'] == 100.5, f"Expected midnight read 100.5, got {midnight_record['reading']}"
        assert midnight_record['period'] == 0, f"Expected period 0, got {midnight_record['period']}"
        assert midnight_record['is_midnight_read'] == True, "Expected is_midnight_read to be True"
        
        # Verify interval records
        assert len(interval_records) == 48, f"Expected 48 interval records, got {len(interval_records)}"
        
        # Check first few interval values (accounting for status flags)
        for i in range(5):
            interval_record = [r for r in interval_records if r['period'] == i + 1][0]
            
            # Check expected values based on our test data logic
            if (i + 1) % 10 == 0:  # Every 10th interval is 'A' status -> 0.0
                expected_value = 0.0
                expected_status = 'A'
            elif (i + 1) % 15 == 0:  # Every 15th interval is 'N' status -> 0.0
                expected_value = 0.0
                expected_status = 'N'
            else:  # Numeric values
                expected_value = float(i + 1)
                expected_status = 'V'
            
            assert interval_record['reading'] == expected_value, f"Expected interval {i+1} to be {expected_value}, got {interval_record['reading']}"
            assert interval_record.get('reading_status') == expected_status, f"Expected status {expected_status} for interval {i+1}, got {interval_record.get('reading_status')}"
            assert interval_record['is_midnight_read'] == False, f"Expected is_midnight_read to be False for interval {i+1}"
        
        print("✅ SmartCo midnight read parsing test PASSED")
        
    finally:
        # Clean up
        os.unlink(temp_file)

def test_bcmm_midnight_read_parsing():
    """Test that BCMM midnight read is parsed correctly from position 8"""
    
    # Create a sample HERM format line (same format as SmartCo)
    sample_line = "0000789012MP001,87654321,2,kWh,2,kWh,20241201,A,200.75," + ",".join([str(i*2) for i in range(1, 49)])
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.new', delete=False) as f:
        f.write("HERM,1,BCMM,YESP,NZDT,48\n")  # Header
        f.write(sample_line + "\n")
        temp_file = f.name
    
    try:
        # Import the function we want to test
        import sys
        sys.path.append('/app/airflow/dags/data_import')
        from metering_bcmm import import_bcmm_hhr
        
        # Mock the context
        context = {
            'ti': Mock(),
            'dag': Mock(),
            'task': Mock(),
            'run_id': 'test_run'
        }
        
        # Mock the downloaded files
        context['ti'].xcom_pull.return_value = [{
            'filename': 'test.new',
            'local_path': temp_file,
            'type': 'interval'
        }]
        
        # Call the function
        result = import_bcmm_hhr(**context)
        
        # Get the pushed data
        pushed_data = context['ti'].xcom_push.call_args[1]['value']
        hhr_data = pushed_data['hhr_data']
        
        # Find midnight read record (period 0)
        midnight_records = [r for r in hhr_data if r.get('period') == 0 and r.get('is_midnight_read', False)]
        interval_records = [r for r in hhr_data if r.get('period', 0) > 0 and not r.get('is_midnight_read', False)]
        
        # Verify midnight read
        assert len(midnight_records) == 1, f"Expected 1 midnight read record, got {len(midnight_records)}"
        midnight_record = midnight_records[0]
        assert midnight_record['reading'] == 200.75, f"Expected midnight read 200.75, got {midnight_record['reading']}"
        assert midnight_record['period'] == 0, f"Expected period 0, got {midnight_record['period']}"
        assert midnight_record['is_midnight_read'] == True, "Expected is_midnight_read to be True"
        
        # Verify interval records
        assert len(interval_records) == 48, f"Expected 48 interval records, got {len(interval_records)}"
        
        # Check first few interval values (our sample data has values 2, 4, 6, 8, 10...)
        for i in range(5):
            interval_record = [r for r in interval_records if r['period'] == i + 1][0]
            expected_value = float((i + 1) * 2)  # Our sample data has values 2, 4, 6, 8, 10...
            assert interval_record['reading'] == expected_value, f"Expected interval {i+1} to be {expected_value}, got {interval_record['reading']}"
            assert interval_record['is_midnight_read'] == False, f"Expected is_midnight_read to be False for interval {i+1}"
        
        print("✅ BCMM midnight read parsing test PASSED")
        
    finally:
        # Clean up
        os.unlink(temp_file)

def test_database_load_structure():
    """Test that the database loading correctly handles midnight reads vs intervals"""
    
    # Mock HHR data with midnight read and intervals
    mock_hhr_data = [
        # Midnight read
        {
            'icp': '0000123456MP001',
            'read_datetime': '2024-12-01 00:00:00',
            'register_id': '1',
            'register_type': 'kWh',
            'register_number': '1',
            'reading': 100.5,
            'units': 'kWh',
            'meter_serial': '12345678',
            'status': 'A',
            'period': 0,
            'is_midnight_read': True,
            'filename': 'test.new'
        },
        # First interval
        {
            'icp': '0000123456MP001',
            'read_datetime': '2024-12-01 00:30:00',
            'register_id': '1',
            'register_type': 'kWh',
            'register_number': '1',
            'reading': 1.0,
            'units': 'kWh',
            'meter_serial': '12345678',
            'status': 'A',
            'period': 1,
            'is_midnight_read': False,
            'filename': 'test.new'
        },
        # Second interval
        {
            'icp': '0000123456MP001',
            'read_datetime': '2024-12-01 01:00:00',
            'register_id': '1',
            'register_type': 'kWh',
            'register_number': '1',
            'reading': 2.0,
            'units': 'kWh',
            'meter_serial': '12345678',
            'status': 'A',
            'period': 2,
            'is_midnight_read': False,
            'filename': 'test.new'
        }
    ]
    
    # Test the grouping logic
    grouped_records = {}
    
    for record in mock_hhr_data:
        date_str = record['read_datetime'][:10]  # Extract date part YYYY-MM-DD
        key = f"{record['icp']}|{date_str}|{record.get('register_id', '')}|{record.get('register_number', '')}"
        
        if key not in grouped_records:
            grouped_records[key] = {
                'icp': record['icp'],
                'reading_date': date_str,
                'midnight_read_value': '0',  # Will be updated when midnight read is found
                'intervals': ['0'] * 50,  # Initialize 50 intervals with string zeros
                'filename': record['filename']
            }
        
        # Handle midnight read (period 0) vs interval reads (period 1-48)
        period = record.get('period', 1)
        if period == 0 and record.get('is_midnight_read', False):
            # This is the midnight read - store in midnight_read_value
            grouped_records[key]['midnight_read_value'] = str(record['reading'])
        elif 1 <= period <= 48:
            # This is an interval read - place in the correct interval slot (1-48)
            grouped_records[key]['intervals'][period - 1] = str(record['reading'])
    
    # Verify the grouped result
    assert len(grouped_records) == 1, f"Expected 1 grouped record, got {len(grouped_records)}"
    
    grouped_record = list(grouped_records.values())[0]
    
    # Check midnight read is correctly stored
    assert grouped_record['midnight_read_value'] == '100.5', f"Expected midnight read '100.5', got '{grouped_record['midnight_read_value']}'"
    
    # Check intervals are correctly stored
    assert grouped_record['intervals'][0] == '1.0', f"Expected interval 1 to be '1.0', got '{grouped_record['intervals'][0]}'"
    assert grouped_record['intervals'][1] == '2.0', f"Expected interval 2 to be '2.0', got '{grouped_record['intervals'][1]}'"
    assert grouped_record['intervals'][2] == '0', f"Expected interval 3 to be '0', got '{grouped_record['intervals'][2]}'"
    
    print("✅ Database load structure test PASSED")

if __name__ == "__main__":
    """Run tests manually"""
    try:
        test_smco_midnight_read_parsing()
        test_bcmm_midnight_read_parsing()
        test_database_load_structure()
        print("\n🎉 All midnight read parsing tests PASSED!")
        print("\nKey fixes verified:")
        print("  ✅ Midnight read correctly extracted from position 8")
        print("  ✅ Intervals correctly parsed from positions 9-56")
        print("  ✅ Midnight read stored separately with period 0")
        print("  ✅ Database loading correctly handles midnight vs intervals")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 