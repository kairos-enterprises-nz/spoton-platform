#!/usr/bin/env python3
"""
Complete BCMM Workflow Validation Script
Tests all components: discovery, download, import, database loading, and logging
"""

import sys
import os
sys.path.append('/app/airflow/dags/metering')

# Import the DAG functions
from metering_bcmm import *

def test_complete_bcmm_workflow():
    """Test the complete BCMM workflow including database operations"""
    
    # Create a mock context
    class MockTaskInstance:
        def __init__(self):
            self.xcom_data = {}
        
        def xcom_pull(self, key):
            return self.xcom_data.get(key)
        
        def xcom_push(self, key, value):
            self.xcom_data[key] = value

    class MockContext:
        def __init__(self):
            self.ti = MockTaskInstance()
            self.dag = type('DAG', (), {'dag_id': 'metering_bcmm'})()
            self.task = type('Task', (), {'task_id': 'test_task'})()
            self.run_id = 'manual_test_run_complete'

    print('🚀 Testing Complete BCMM Workflow (Including Database Operations)')
    context = MockContext()

    try:
        # Step 1: Test connection
        print('\n🔍 Step 1: Testing Connection')
        result1 = test_bcmm_connection(**context.__dict__)
        print(f'✅ Connection test: {result1}')
        
        # Step 2: Discover files
        print('\n📁 Step 2: Discovering Files')
        result2 = discover_bcmm_files(**context.__dict__)
        print(f'✅ Files discovered: {len(result2)}')
        
        # Step 3: Download files
        print('\n⬇️ Step 3: Downloading Files')
        result3 = download_bcmm_files(**context.__dict__)
        print(f'✅ Files downloaded: {len(result3)}')
        
        # Step 4: Import DRR
        print('\n📊 Step 4: Importing DRR')
        result4 = import_bcmm_drr(**context.__dict__)
        print(f'✅ DRR import: {result4}')
        
        # Step 5: Import HHR
        print('\n📈 Step 5: Importing HHR')
        result5 = import_bcmm_hhr(**context.__dict__)
        print(f'✅ HHR import: {result5}')
        
        # Step 6a: Load DRR to Database
        print('\n💾 Step 6a: Loading DRR to Database')
        result6a = load_bcmm_drr_to_db(**context.__dict__)
        print(f'✅ DRR database load: {result6a}')
        
        # Step 6b: Load HHR to Database
        print('\n💾 Step 6b: Loading HHR to Database')
        result6b = load_bcmm_hhr_to_db(**context.__dict__)
        print(f'✅ HHR database load: {result6b}')
        
        # Step 7: Verify database load
        print('\n🔍 Step 7: Verifying Database Load')
        result7 = verify_bcmm_database_load(**context.__dict__)
        print(f'✅ Database verification: {result7}')
        
        # Step 8: Cleanup files
        print('\n🧹 Step 8: Cleaning Up Files')
        result8 = cleanup_bcmm_files(**context.__dict__)
        print(f'✅ File cleanup: {result8}')
        
        print('\n🎯 Complete Workflow Test Completed Successfully!')
        
        # Final validation
        print('\n📊 Final Database Validation:')
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Check DRR records
                cur.execute("""
                    SELECT COUNT(*) as drr_count, 
                           COUNT(DISTINCT icp) as unique_icps,
                           MIN(read_date) as earliest_date,
                           MAX(read_date) as latest_date
                    FROM metering.bluecurrent_drr 
                    WHERE file_name LIKE '%RMNG%' OR file_name LIKE '%AMS%'
                """)
                drr_stats = cur.fetchone()
                print(f"  📊 DRR: {drr_stats[0]} records, {drr_stats[1]} unique ICPs, dates: {drr_stats[2]} to {drr_stats[3]}")
                
                # Check HHR records
                cur.execute("""
                    SELECT COUNT(*) as hhr_count,
                           COUNT(DISTINCT icp) as unique_icps,
                           MIN(reading_date) as earliest_date,
                           MAX(reading_date) as latest_date
                    FROM metering.bluecurrent_hhr 
                    WHERE file_name LIKE '%HERM%' OR file_name LIKE '%AMS%'
                """)
                hhr_stats = cur.fetchone()
                print(f"  📈 HHR: {hhr_stats[0]} records, {hhr_stats[1]} unique ICPs, dates: {hhr_stats[2]} to {hhr_stats[3]}")
                
                # Check import log
                cur.execute("""
                    SELECT COUNT(*) as log_entries,
                           SUM(records_loaded) as total_records_loaded,
                           COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_imports
                    FROM metering.import_log 
                    WHERE mep_provider = 'BCMM' 
                      AND started_at > NOW() - INTERVAL '1 hour'
                """)
                log_stats = cur.fetchone()
                print(f"  📝 Import Log: {log_stats[0]} entries, {log_stats[1]} total records loaded, {log_stats[2]} successful imports")
        
        print('\n🎉 All Systems Operational - BCMM Import Pipeline Fully Functional!')
        return True
        
    except Exception as e:
        print(f'❌ Workflow test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_bcmm_workflow()
    sys.exit(0 if success else 1) 