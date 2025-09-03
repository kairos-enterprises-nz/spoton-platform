#!/usr/bin/env python3
"""
Debug script to identify where the 4,727 readings are being lost in validation pipeline
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

def debug_data_loss():
    """Debug where readings are being lost in the validation pipeline"""
    
    with connection.cursor() as cursor:
        print("🔍 DEBUGGING VALIDATION DATA LOSS")
        print("=" * 50)
        
        # 1. Check total raw readings
        cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_raw")
        raw_count = cursor.fetchone()[0]
        print(f"📊 Total raw readings: {raw_count:,}")
        
        # 2. Check total calculated readings
        cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_calculated")
        calc_count = cursor.fetchone()[0]
        print(f"📊 Total calculated readings: {calc_count:,}")
        
        # 3. Data loss summary
        lost_count = raw_count - calc_count
        loss_percentage = (lost_count / raw_count) * 100 if raw_count > 0 else 0
        print(f"❌ Lost readings: {lost_count:,} ({loss_percentage:.1f}%)")
        print()
        
        # 4. Check data loss by source
        print("🔍 DATA LOSS BY SOURCE:")
        cursor.execute("""
            SELECT 
                r.source,
                COUNT(r.*) as raw_count,
                COUNT(c.*) as calculated_count,
                COUNT(r.*) - COUNT(c.*) as missing_count,
                ROUND(100.0 * COUNT(c.*) / COUNT(r.*), 2) as success_rate
            FROM metering_processed.interval_reads_raw r
            LEFT JOIN metering_processed.interval_reads_calculated c 
                ON r.icp_id = c.icp_id 
                AND r.meter_register_id = c.meter_register_id 
                AND r.timestamp = c.timestamp
            GROUP BY r.source
            ORDER BY missing_count DESC
        """)
        
        for row in cursor.fetchall():
            source, raw_count, calc_count, missing_count, success_rate = row
            print(f"  {source:12} | Raw: {raw_count:5,} | Calc: {calc_count:5,} | Lost: {missing_count:4,} | Success: {success_rate:5.1f}%")
        print()
        
        # 5. Check data loss by quality flag
        print("🔍 DATA LOSS BY QUALITY FLAG:")
        cursor.execute("""
            SELECT 
                r.quality_flag,
                COUNT(r.*) as raw_count,
                COUNT(c.*) as calculated_count,
                COUNT(r.*) - COUNT(c.*) as missing_count,
                ROUND(100.0 * COUNT(c.*) / COUNT(r.*), 2) as success_rate
            FROM metering_processed.interval_reads_raw r
            LEFT JOIN metering_processed.interval_reads_calculated c 
                ON r.icp_id = c.icp_id 
                AND r.meter_register_id = c.meter_register_id 
                AND r.timestamp = c.timestamp
            GROUP BY r.quality_flag
            ORDER BY missing_count DESC
        """)
        
        for row in cursor.fetchall():
            quality_flag, raw_count, calc_count, missing_count, success_rate = row
            print(f"  {quality_flag or 'NULL':12} | Raw: {raw_count:5,} | Calc: {calc_count:5,} | Lost: {missing_count:4,} | Success: {success_rate:5.1f}%")
        print()
        
        # 6. Check for specific problematic readings
        print("🔍 SAMPLE FAILED READINGS:")
        cursor.execute("""
            SELECT 
                r.source,
                r.icp_id,
                r.meter_register_id,
                r.timestamp,
                r.value,
                r.quality_flag,
                r.validation_flag
            FROM metering_processed.interval_reads_raw r
            LEFT JOIN metering_processed.interval_reads_calculated c 
                ON r.icp_id = c.icp_id 
                AND r.meter_register_id = c.meter_register_id 
                AND r.timestamp = c.timestamp
            WHERE c.id IS NULL
            ORDER BY r.source, r.timestamp
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            source, icp_id, register_id, timestamp, value, quality_flag, validation_flag = row
            print(f"  {source:8} | {icp_id:15} | {register_id:3} | {timestamp} | {value:8} | {quality_flag:1} | {validation_flag:1}")
        print()
        
        # 7. Check for duplicate issues
        print("🔍 CHECKING FOR DUPLICATE ISSUES:")
        cursor.execute("""
            SELECT 
                icp_id,
                meter_register_id,
                timestamp,
                COUNT(*) as count
            FROM metering_processed.interval_reads_raw
            GROUP BY icp_id, meter_register_id, timestamp
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"  Found {len(duplicates)} duplicate groups in raw data:")
            for row in duplicates:
                icp_id, register_id, timestamp, count = row
                print(f"    {icp_id:15} | {register_id:3} | {timestamp} | {count} duplicates")
        else:
            print("  ✅ No duplicates found in raw data")
        print()
        
        # 8. Check for timestamp/trading period issues
        print("🔍 CHECKING FOR TIMESTAMP ISSUES:")
        cursor.execute("""
            SELECT 
                DATE(r.timestamp) as reading_date,
                COUNT(DISTINCT r.trading_period) as unique_trading_periods,
                MIN(r.trading_period) as min_tp,
                MAX(r.trading_period) as max_tp,
                COUNT(*) as total_readings,
                COUNT(c.*) as processed_readings
            FROM metering_processed.interval_reads_raw r
            LEFT JOIN metering_processed.interval_reads_calculated c 
                ON r.icp_id = c.icp_id 
                AND r.meter_register_id = c.meter_register_id 
                AND r.timestamp = c.timestamp
            WHERE r.trading_period IS NOT NULL
            GROUP BY DATE(r.timestamp)
            HAVING COUNT(DISTINCT r.trading_period) != 48
            ORDER BY reading_date
            LIMIT 10
        """)
        
        dst_issues = cursor.fetchall()
        if dst_issues:
            print(f"  Found {len(dst_issues)} days with non-48 trading periods:")
            for row in dst_issues:
                date, unique_tps, min_tp, max_tp, total, processed = row
                print(f"    {date} | TPs: {unique_tps:2} ({min_tp:2}-{max_tp:2}) | Total: {total:5,} | Processed: {processed:5,}")
        else:
            print("  ✅ All days have normal 48 trading periods")
        print()
        
        # 9. Check validation session status
        print("🔍 CHECKING VALIDATION SESSIONS:")
        cursor.execute("""
            SELECT 
                session_id,
                status,
                total_readings,
                processed_readings,
                valid_readings,
                estimated_readings,
                started_at,
                completed_at
            FROM energy_validation_session
            ORDER BY started_at DESC
            LIMIT 5
        """)
        
        sessions = cursor.fetchall()
        if sessions:
            print("  Recent validation sessions:")
            for row in sessions:
                session_id, status, total, processed, valid, estimated, started, completed = row
                print(f"    {session_id[:8]}... | {status:10} | Total: {total:5,} | Processed: {processed:5,} | Valid: {valid:5,} | Est: {estimated:4,}")
        else:
            print("  ❌ No validation sessions found")

if __name__ == "__main__":
    debug_data_loss() 