#!/usr/bin/env python3
"""
Comprehensive test of the validation pipeline to ensure all steps are working correctly
"""

import os
import sys
import django
from django.db import connection
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

def test_validation_pipeline():
    """Test the complete validation pipeline"""
    
    print("🧪 COMPREHENSIVE VALIDATION PIPELINE TEST")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        
        # 1. Data Flow Verification
        print("1️⃣ DATA FLOW VERIFICATION")
        print("-" * 30)
        
        # Check MEP to Raw conversion
        cursor.execute("""
            SELECT 
                'MEP_TABLES' as stage,
                SUM(count) as total_rows
            FROM (
                SELECT COUNT(*) as count FROM metering_raw.bcmm_hhr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.bcmm_drr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.smartco_hhr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.smartco_drr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.fclm_hhr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.fclm_drr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.intellihub_hhr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.intellihub_drr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.mtrx_hhr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.mtrx_drr
                UNION ALL
                SELECT COUNT(*) as count FROM metering_raw.bluecurrent_eiep3
            ) counts
        """)
        mep_total = cursor.fetchone()[1]
        
        cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_raw")
        raw_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_calculated")
        calc_total = cursor.fetchone()[0]
        
        print(f"  MEP Tables:           {mep_total:6,} rows")
        print(f"  Raw Readings:         {raw_total:6,} rows")
        print(f"  Calculated Readings:  {calc_total:6,} rows")
        print(f"  MEP→Raw Expansion:    {raw_total/mep_total:.1f}x" if mep_total > 0 else "  MEP→Raw Expansion:    N/A")
        print(f"  Raw→Calc Success:     {calc_total/raw_total*100:.1f}%" if raw_total > 0 else "  Raw→Calc Success:     N/A")
        print()
        
        # 2. Quality Flag Processing
        print("2️⃣ QUALITY FLAG PROCESSING")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                r.quality_flag,
                COUNT(r.*) as raw_count,
                COUNT(c.*) as calc_count,
                ROUND(100.0 * COUNT(c.*) / COUNT(r.*), 1) as success_rate
            FROM metering_processed.interval_reads_raw r
            LEFT JOIN metering_processed.interval_reads_calculated c 
                ON r.icp_id = c.icp_id 
                AND r.meter_register_id = c.meter_register_id 
                AND r.timestamp = c.timestamp
            GROUP BY r.quality_flag
            ORDER BY raw_count DESC
        """)
        
        for row in cursor.fetchall():
            quality_flag, raw_count, calc_count, success_rate = row
            flag_name = quality_flag or 'NULL'
            status = "✅" if success_rate >= 99.9 else "⚠️" if success_rate >= 95.0 else "❌"
            print(f"  {flag_name:12} | {raw_count:6,} → {calc_count:6,} | {success_rate:5.1f}% {status}")
        print()
        
        # 3. Trading Period Analysis
        print("3️⃣ TRADING PERIOD ANALYSIS")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                DATE(timestamp) as reading_date,
                COUNT(DISTINCT trading_period) as unique_tps,
                MIN(trading_period) as min_tp,
                MAX(trading_period) as max_tp,
                COUNT(*) as total_readings
            FROM metering_processed.interval_reads_calculated
            WHERE trading_period IS NOT NULL
            GROUP BY DATE(timestamp)
            ORDER BY reading_date
        """)
        
        normal_days = 0
        dst_days = 0
        
        for row in cursor.fetchall():
            date, unique_tps, min_tp, max_tp, total_readings = row
            
            if unique_tps == 48:
                normal_days += 1
            elif unique_tps in [46, 50]:
                dst_days += 1
                print(f"  {date} | TPs: {unique_tps:2} ({min_tp:2}-{max_tp:2}) | Readings: {total_readings:5,} | DST Day")
            else:
                print(f"  {date} | TPs: {unique_tps:2} ({min_tp:2}-{max_tp:2}) | Readings: {total_readings:5,} | ⚠️ Irregular")
        
        print(f"  Normal days (48 TPs): {normal_days}")
        print(f"  DST days (46/50 TPs): {dst_days}")
        print()
        
        # 4. Validation Rule Effectiveness
        print("4️⃣ VALIDATION RULE EFFECTIVENESS")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                validation_flag,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM metering_processed.interval_reads_calculated), 1) as percentage
            FROM metering_processed.interval_reads_calculated
            GROUP BY validation_flag
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            flag, count, percentage = row
            flag_name = {'V': 'Valid', 'S': 'Suspicious', 'E': 'Estimated', 'P': 'Provisional'}.get(flag, flag)
            print(f"  {flag_name:12} | {count:6,} readings | {percentage:5.1f}%")
        print()
        
        # 5. Estimation Analysis
        print("5️⃣ ESTIMATION ANALYSIS")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                is_estimated,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM metering_processed.interval_reads_calculated), 1) as percentage
            FROM metering_processed.interval_reads_calculated
            GROUP BY is_estimated
            ORDER BY is_estimated DESC
        """)
        
        for row in cursor.fetchall():
            is_estimated, count, percentage = row
            status = "Estimated" if is_estimated else "Original"
            print(f"  {status:12} | {count:6,} readings | {percentage:5.1f}%")
        print()
        
        # 6. Data Source Performance
        print("6️⃣ DATA SOURCE PERFORMANCE")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                source,
                COUNT(*) as total_readings,
                COUNT(CASE WHEN validation_flag = 'V' THEN 1 END) as valid_readings,
                COUNT(CASE WHEN is_estimated = true THEN 1 END) as estimated_readings,
                ROUND(100.0 * COUNT(CASE WHEN validation_flag = 'V' THEN 1 END) / COUNT(*), 1) as valid_rate,
                ROUND(100.0 * COUNT(CASE WHEN is_estimated = true THEN 1 END) / COUNT(*), 1) as estimation_rate
            FROM metering_processed.interval_reads_calculated
            GROUP BY source
            ORDER BY total_readings DESC
        """)
        
        for row in cursor.fetchall():
            source, total, valid, estimated, valid_rate, est_rate = row
            print(f"  {source:12} | {total:6,} | Valid: {valid_rate:5.1f}% | Estimated: {est_rate:4.1f}%")
        print()
        
        # 7. Final Reading Identification
        print("7️⃣ FINAL READING IDENTIFICATION")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_readings,
                COUNT(CASE WHEN is_final_reading = true THEN 1 END) as final_readings,
                ROUND(100.0 * COUNT(CASE WHEN is_final_reading = true THEN 1 END) / COUNT(*), 1) as final_rate
            FROM metering_processed.interval_reads_calculated
        """)
        
        total_readings, final_readings, final_rate = cursor.fetchone()
        print(f"  Total Readings:       {total_readings:6,}")
        print(f"  Final Readings:       {final_readings:6,}")
        print(f"  Final Reading Rate:   {final_rate:5.1f}%")
        print()
        
        # 8. Duplicate Detection
        print("8️⃣ DUPLICATE DETECTION")
        print("-" * 30)
        
        cursor.execute("""
            SELECT COUNT(*) as duplicate_groups
            FROM (
                SELECT icp_id, meter_register_id, timestamp, source, COUNT(*) as count
                FROM metering_processed.interval_reads_calculated
                GROUP BY icp_id, meter_register_id, timestamp, source
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        
        duplicate_groups = cursor.fetchone()[0]
        print(f"  Duplicate Groups:     {duplicate_groups:6,}")
        
        if duplicate_groups > 0:
            print("  ❌ CRITICAL: Duplicates found in calculated table!")
        else:
            print("  ✅ No duplicates in calculated table")
        print()
        
        # 9. Overall Pipeline Health
        print("9️⃣ OVERALL PIPELINE HEALTH")
        print("-" * 30)
        
        success_rate = (calc_total / raw_total * 100) if raw_total > 0 else 0
        
        if success_rate >= 99.5:
            health_status = "🟢 EXCELLENT"
        elif success_rate >= 95.0:
            health_status = "🟡 GOOD"
        elif success_rate >= 90.0:
            health_status = "🟠 NEEDS ATTENTION"
        else:
            health_status = "🔴 CRITICAL"
        
        print(f"  Pipeline Success Rate: {success_rate:.2f}%")
        print(f"  Health Status:         {health_status}")
        print(f"  Data Loss:             {raw_total - calc_total:,} readings")
        
        # Recommendations
        print("\n🔧 RECOMMENDATIONS")
        print("-" * 30)
        
        if success_rate < 99.5:
            print("  • Investigate validation rules causing data loss")
        if dst_days == 0:
            print("  • Verify DST handling for spring/autumn transitions")
        if duplicate_groups > 0:
            print("  • Fix duplicate detection and handling logic")
        
        print("  • Monitor validation rule effectiveness")
        print("  • Implement alerting for data loss > 1%")
        print("  • Add automated testing for DST transitions")
        
        if success_rate >= 99.5 and duplicate_groups == 0:
            print("  ✅ Pipeline is operating within acceptable parameters")

if __name__ == "__main__":
    test_validation_pipeline() 