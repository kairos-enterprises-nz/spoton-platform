#!/usr/bin/env python3
"""
Query script to analyze validation failures from the database
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

def analyze_validation_failures():
    """Analyze validation failures from the database"""
    
    print("📊 VALIDATION FAILURE ANALYSIS")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        
        # 1. Overall failure statistics
        print("1️⃣ Overall Failure Statistics")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_failures,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT icp_id) as affected_icps,
                COUNT(DISTINCT source) as data_sources,
                ROUND(AVG(data_completeness), 3) as avg_completeness,
                ROUND(AVG(data_accuracy), 3) as avg_accuracy,
                ROUND(AVG(data_consistency), 3) as avg_consistency,
                ROUND(SUM(estimated_financial_impact), 2) as total_financial_impact
            FROM energy_validation_failure_log
        """)
        
        stats = cursor.fetchone()
        if stats:
            print(f"Total Failures: {stats[0]:,}")
            print(f"Unique Sessions: {stats[1]:,}")
            print(f"Affected ICPs: {stats[2]:,}")
            print(f"Data Sources: {stats[3]:,}")
            print(f"Avg Completeness: {stats[4]:.3f}")
            print(f"Avg Accuracy: {stats[5]:.3f}")
            print(f"Avg Consistency: {stats[6]:.3f}")
            print(f"Total Financial Impact: ${stats[7]:,.2f} NZD")
        
        print()
        
        # 2. Failure breakdown by category and severity
        print("2️⃣ Failure Breakdown by Category & Severity")
        print("-" * 45)
        
        cursor.execute("""
            SELECT 
                category,
                severity,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM energy_validation_failure_log), 1) as percentage,
                ROUND(AVG(data_accuracy), 3) as avg_accuracy,
                ROUND(SUM(estimated_financial_impact), 2) as total_impact
            FROM energy_validation_failure_log
            GROUP BY category, severity
            ORDER BY count DESC
        """)
        
        breakdown = cursor.fetchall()
        if breakdown:
            print(f"{'Category':<15} {'Severity':<10} {'Count':<6} {'%':<6} {'Accuracy':<9} {'Impact ($)':<12}")
            print("-" * 70)
            for row in breakdown:
                category, severity, count, percentage, avg_accuracy, total_impact = row
                print(f"{category:<15} {severity:<10} {count:<6} {percentage:<6.1f} {avg_accuracy:<9.3f} ${total_impact:<11.2f}")
        
        print()
        
        # 3. Failure breakdown by data source
        print("3️⃣ Failure Breakdown by Data Source")
        print("-" * 35)
        
        cursor.execute("""
            SELECT 
                source,
                COUNT(*) as failures,
                COUNT(DISTINCT icp_id) as affected_icps,
                ROUND(AVG(data_completeness), 3) as avg_completeness,
                ROUND(AVG(data_accuracy), 3) as avg_accuracy,
                COUNT(CASE WHEN auto_fixable THEN 1 END) as auto_fixable_count,
                ROUND(SUM(estimated_financial_impact), 2) as total_impact
            FROM energy_validation_failure_log
            GROUP BY source
            ORDER BY failures DESC
        """)
        
        source_breakdown = cursor.fetchall()
        if source_breakdown:
            print(f"{'Source':<10} {'Failures':<8} {'ICPs':<5} {'Complete':<8} {'Accurate':<8} {'Auto-fix':<8} {'Impact ($)':<12}")
            print("-" * 75)
            for row in source_breakdown:
                source, failures, icps, completeness, accuracy, auto_fix, impact = row
                print(f"{source:<10} {failures:<8} {icps:<5} {completeness:<8.3f} {accuracy:<8.3f} {auto_fix:<8} ${impact:<11.2f}")
        
        print()
        
        # 4. Rule performance analysis
        print("4️⃣ Rule Performance Analysis")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                rule_code,
                COUNT(*) as failures,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM energy_validation_failure_log), 1) as percentage,
                COUNT(CASE WHEN auto_fixable THEN 1 END) as auto_fixable,
                COUNT(CASE WHEN severity IN ('critical', 'high') THEN 1 END) as high_severity,
                ROUND(AVG(estimated_financial_impact), 2) as avg_impact
            FROM energy_validation_failure_log
            GROUP BY rule_code
            ORDER BY failures DESC
        """)
        
        rule_performance = cursor.fetchall()
        if rule_performance:
            print(f"{'Rule Code':<20} {'Failures':<8} {'%':<6} {'Auto-fix':<8} {'High Sev':<8} {'Avg Impact':<12}")
            print("-" * 75)
            for row in rule_performance:
                rule_code, failures, percentage, auto_fixable, high_severity, avg_impact = row
                print(f"{rule_code:<20} {failures:<8} {percentage:<6.1f} {auto_fixable:<8} {high_severity:<8} ${avg_impact:<11.2f}")
        
        print()
        
        # 5. Trading period analysis
        print("5️⃣ Trading Period Analysis")
        print("-" * 25)
        
        cursor.execute("""
            SELECT 
                trading_period,
                COUNT(*) as failures,
                COUNT(DISTINCT icp_id) as affected_icps,
                ROUND(AVG(actual_value), 2) as avg_value,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_failures
            FROM energy_validation_failure_log
            WHERE trading_period IS NOT NULL
            GROUP BY trading_period
            ORDER BY failures DESC
            LIMIT 10
        """)
        
        tp_analysis = cursor.fetchall()
        if tp_analysis:
            print(f"{'TP':<3} {'Failures':<8} {'ICPs':<5} {'Avg Value':<10} {'Critical':<8}")
            print("-" * 40)
            for row in tp_analysis:
                tp, failures, icps, avg_value, critical = row
                avg_val_str = f"{avg_value:.2f}" if avg_value is not None else "N/A"
                print(f"{tp:<3} {failures:<8} {icps:<5} {avg_val_str:<10} {critical:<8}")
        
        print()
        
        # 6. Recent failures (last 24 hours)
        print("6️⃣ Recent Failures (Last 24 Hours)")
        print("-" * 35)
        
        cursor.execute("""
            SELECT 
                failure_id,
                rule_code,
                severity,
                icp_id,
                source,
                actual_value,
                failure_reason,
                created_at
            FROM energy_validation_failure_log
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        recent_failures = cursor.fetchall()
        if recent_failures:
            for i, row in enumerate(recent_failures, 1):
                failure_id, rule_code, severity, icp_id, source, actual_value, failure_reason, created_at = row
                failure_id_str = str(failure_id)[:8] if failure_id else "unknown"
                print(f"{i}. {failure_id_str}... | {rule_code} | {severity.upper()} | {icp_id} | {source}")
                print(f"   Value: {actual_value} | {failure_reason[:80]}...")
                print(f"   Time: {created_at}")
                print()
        else:
            print("No recent failures found.")
        
        print()
        
        # 7. Auto-fixable vs Manual review breakdown
        print("7️⃣ Auto-fixable vs Manual Review")
        print("-" * 32)
        
        cursor.execute("""
            SELECT 
                auto_fixable,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM energy_validation_failure_log), 1) as percentage,
                ROUND(AVG(estimated_financial_impact), 2) as avg_impact,
                COUNT(CASE WHEN severity IN ('critical', 'high') THEN 1 END) as high_severity_count
            FROM energy_validation_failure_log
            GROUP BY auto_fixable
            ORDER BY count DESC
        """)
        
        auto_fix_analysis = cursor.fetchall()
        if auto_fix_analysis:
            for row in auto_fix_analysis:
                auto_fixable, count, percentage, avg_impact, high_severity = row
                status = "✅ Auto-fixable" if auto_fixable else "🔧 Manual review required"
                print(f"{status}")
                print(f"   Count: {count} ({percentage:.1f}%)")
                print(f"   Avg Impact: ${avg_impact:.2f}")
                print(f"   High Severity: {high_severity}")
                print()

if __name__ == "__main__":
    analyze_validation_failures() 