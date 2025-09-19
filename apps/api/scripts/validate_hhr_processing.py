#!/usr/bin/env python3
"""
HHR Processing Validation Script

This script systematically validates HHR processing by comparing:
1. Raw import data from MEP providers
2. Processed interval data in interval_reads_raw table

Identifies discrepancies and provides detailed analysis.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import json

class HHRValidationAnalyzer:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'utilitybyte'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        self.conn.autocommit = True
        
    def get_raw_data_counts(self):
        """Get counts from raw MEP provider tables"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            results = {}
            
            # Wide format MEPs (BCMM, SmartCo, FCLM)
            wide_format_meps = [
                ('BCMM', 'metering_raw.bcmm_hhr'),
                ('SmartCo', 'metering_raw.smartco_hhr'),
                ('FCLM', 'metering_raw.fclm_hhr')
            ]
            
            for mep_name, table_name in wide_format_meps:
                try:
                    # Handle FCLM differently due to different column name
                    date_column = 'read_date' if 'fclm' in table_name else 'reading_date'
                    cur.execute(f"""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(*) * 48 as expected_intervals,
                            MIN(imported_at) as earliest_import,
                            MAX(imported_at) as latest_import,
                            COUNT(DISTINCT icp) as unique_icps,
                            COUNT(DISTINCT {date_column}) as unique_dates
                        FROM {table_name}
                        WHERE imported_at >= NOW() - INTERVAL '30 days'
                    """)
                    results[mep_name] = dict(cur.fetchone())
                    results[mep_name]['format'] = 'wide'
                except Exception as e:
                    results[mep_name] = {'error': str(e)}
            
            # Long format MEPs (IntelliHub, MTRX)
            long_format_meps = [
                ('IntelliHub', 'metering_raw.intellihub_hhr'),
                ('MTRX', 'metering_raw.mtrx_hhr')
            ]
            
            for mep_name, table_name in long_format_meps:
                try:
                    cur.execute(f"""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(*) as expected_intervals,
                            MIN(imported_at) as earliest_import,
                            MAX(imported_at) as latest_import,
                            COUNT(DISTINCT icp) as unique_icps,
                            COUNT(DISTINCT DATE(start_datetime)) as unique_dates
                        FROM {table_name}
                        WHERE imported_at >= NOW() - INTERVAL '30 days'
                    """)
                    results[mep_name] = dict(cur.fetchone())
                    results[mep_name]['format'] = 'long'
                except Exception as e:
                    results[mep_name] = {'error': str(e)}
            
            return results
    
    def get_processed_data_counts(self):
        """Get counts from processed interval_reads_raw table"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Overall counts
            cur.execute("""
                SELECT 
                    COUNT(*) as total_intervals,
                    COUNT(DISTINCT connection_id) as unique_icps,
                    COUNT(DISTINCT day) as unique_days,
                    COUNT(DISTINCT source) as unique_sources,
                    MIN(created_at) as earliest_created,
                    MAX(created_at) as latest_created
                FROM metering_processed.interval_reads_raw
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
            overall = dict(cur.fetchone())
            
            # Counts by MEP provider
            cur.execute("""
                SELECT 
                    source,
                    COUNT(*) as total_intervals,
                    COUNT(DISTINCT connection_id) as unique_icps,
                    COUNT(DISTINCT day) as unique_days,
                    MIN(created_at) as earliest_created,
                    MAX(created_at) as latest_created
                FROM metering_processed.interval_reads_raw
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY source
                ORDER BY source
            """)
            by_source = {row['source']: dict(row) for row in cur.fetchall()}
            
            return {'overall': overall, 'by_source': by_source}
    
    def analyze_duplicates(self):
        """Check for duplicate processing"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    connection_id,
                    register_code,
                    timestamp,
                    COUNT(*) as duplicate_count
                FROM metering_processed.interval_reads_raw
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY connection_id, register_code, timestamp
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT 10
            """)
            duplicates = [dict(row) for row in cur.fetchall()]
            
            cur.execute("""
                SELECT COUNT(*) as total_duplicates
                FROM (
                    SELECT 
                        connection_id,
                        register_code,
                        timestamp,
                        COUNT(*) as duplicate_count
                    FROM metering_processed.interval_reads_raw
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY connection_id, register_code, timestamp
                    HAVING COUNT(*) > 1
                ) dup
            """)
            total_duplicates = cur.fetchone()['total_duplicates']
            
            return {'total_duplicates': total_duplicates, 'examples': duplicates}
    
    def analyze_missing_data(self):
        """Analyze what raw data hasn't been processed"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            missing_analysis = {}
            
            # Wide format MEPs
            wide_format_meps = [
                ('BCMM', 'metering_raw.bcmm_hhr', 'reading_date', 'register_number'),
                ('SmartCo', 'metering_raw.smartco_hhr', 'reading_date', 'register_number'),
                ('FCLM', 'metering_raw.fclm_hhr', 'read_date', 'register_code')
            ]
            
            for mep_name, table_name, date_field, register_field in wide_format_meps:
                try:
                    cur.execute(f"""
                                                 SELECT COUNT(*) as unprocessed_records
                         FROM {table_name} h
                         WHERE NOT EXISTS (
                             SELECT 1 FROM metering_processed.interval_reads_raw p
                             WHERE p.connection_id = h.icp 
                             AND p.day = h.{date_field}::date
                             AND p.source = '{mep_name}'
                             AND p.register_code = h.{register_field}
                         )
                         AND h.imported_at >= NOW() - INTERVAL '30 days'
                    """)
                    missing_analysis[mep_name] = {'unprocessed_records': cur.fetchone()['unprocessed_records']}
                except Exception as e:
                    missing_analysis[mep_name] = {'error': str(e)}
            
            # Long format MEPs
            long_format_meps = [
                ('IntelliHub', 'metering_raw.intellihub_hhr'),
                ('MTRX', 'metering_raw.mtrx_hhr')
            ]
            
            for mep_name, table_name in long_format_meps:
                try:
                    cur.execute(f"""
                        SELECT COUNT(*) as unprocessed_records
                        FROM {table_name} h
                        WHERE NOT EXISTS (
                            SELECT 1 FROM metering_processed.interval_reads_raw p
                            WHERE p.connection_id = h.icp 
                            AND p.timestamp = h.start_datetime
                            AND p.source = '{mep_name}'
                            AND p.register_code = h.register
                        )
                        AND h.imported_at >= NOW() - INTERVAL '30 days'
                    """)
                    missing_analysis[mep_name] = {'unprocessed_records': cur.fetchone()['unprocessed_records']}
                except Exception as e:
                    missing_analysis[mep_name] = {'error': str(e)}
            
            return missing_analysis
    
    def validate_interval_counts(self):
        """Validate that wide format records generate correct number of intervals"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            validation_results = {}
            
            # For each wide format MEP, check if records generate expected intervals
            wide_format_meps = [
                ('BCMM', 'metering_raw.bcmm_hhr', 'reading_date', 'register_number'),
                ('SmartCo', 'metering_raw.smartco_hhr', 'reading_date', 'register_number'),
                ('FCLM', 'metering_raw.fclm_hhr', 'read_date', 'register_code')
            ]
            
            for mep_name, table_name, date_field, register_field in wide_format_meps:
                try:
                    cur.execute(f"""
                        SELECT 
                            h.icp,
                            h.{date_field} as reading_date,
                            h.{register_field} as register_code,
                            COUNT(p.id) as processed_intervals
                        FROM {table_name} h
                                                 LEFT JOIN metering_processed.interval_reads_raw p ON (
                             p.connection_id = h.icp 
                             AND p.day = h.{date_field}::date
                             AND p.source = '{mep_name}'
                             AND p.register_code = h.{register_field}
                         )
                        WHERE h.imported_at >= NOW() - INTERVAL '30 days'
                        GROUP BY h.icp, h.{date_field}, h.{register_field}
                        HAVING COUNT(p.id) != 48 AND COUNT(p.id) != 46 AND COUNT(p.id) != 50
                        ORDER BY processed_intervals DESC
                        LIMIT 10
                    """)
                    
                    incorrect_counts = [dict(row) for row in cur.fetchall()]
                    validation_results[mep_name] = {
                        'incorrect_interval_counts': len(incorrect_counts),
                        'examples': incorrect_counts
                    }
                except Exception as e:
                    validation_results[mep_name] = {'error': str(e)}
            
            return validation_results
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        print("=" * 80)
        print("HHR PROCESSING VALIDATION REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Raw data analysis
        print("1. RAW DATA ANALYSIS")
        print("-" * 40)
        raw_counts = self.get_raw_data_counts()
        total_expected_intervals = 0
        
        for mep_name, data in raw_counts.items():
            if 'error' in data:
                print(f"{mep_name}: ERROR - {data['error']}")
            else:
                print(f"{mep_name} ({data['format']} format):")
                print(f"  - Total records: {data['total_records']:,}")
                print(f"  - Expected intervals: {data['expected_intervals']:,}")
                print(f"  - Unique ICPs: {data['unique_icps']:,}")
                print(f"  - Unique dates: {data['unique_dates']:,}")
                print(f"  - Import period: {data['earliest_import']} to {data['latest_import']}")
                total_expected_intervals += data['expected_intervals']
                print()
        
        print(f"TOTAL EXPECTED INTERVALS: {total_expected_intervals:,}")
        print()
        
        # Processed data analysis
        print("2. PROCESSED DATA ANALYSIS")
        print("-" * 40)
        processed_counts = self.get_processed_data_counts()
        
        overall = processed_counts['overall']
        print(f"Overall processed intervals: {overall['total_intervals']:,}")
        print(f"Unique ICPs: {overall['unique_icps']:,}")
        print(f"Unique days: {overall['unique_days']:,}")
        print(f"Processing period: {overall['earliest_created']} to {overall['latest_created']}")
        print()
        
        print("By MEP Provider:")
        for source, data in processed_counts['by_source'].items():
            print(f"  {source}: {data['total_intervals']:,} intervals")
        print()
        
        # Discrepancy analysis
        print("3. DISCREPANCY ANALYSIS")
        print("-" * 40)
        actual_intervals = overall['total_intervals']
        discrepancy = actual_intervals - total_expected_intervals
        discrepancy_pct = (discrepancy / total_expected_intervals * 100) if total_expected_intervals > 0 else 0
        
        print(f"Expected intervals: {total_expected_intervals:,}")
        print(f"Actual intervals: {actual_intervals:,}")
        print(f"Discrepancy: {discrepancy:,} ({discrepancy_pct:+.2f}%)")
        print()
        
        # Duplicate analysis
        print("4. DUPLICATE ANALYSIS")
        print("-" * 40)
        duplicate_analysis = self.analyze_duplicates()
        print(f"Total duplicate groups: {duplicate_analysis['total_duplicates']:,}")
        
        if duplicate_analysis['examples']:
            print("Top duplicate examples:")
            for dup in duplicate_analysis['examples']:
                print(f"  {dup['connection_id']} | {dup['register_code']} | {dup['timestamp']} | Count: {dup['duplicate_count']}")
        print()
        
        # Missing data analysis
        print("5. MISSING DATA ANALYSIS")
        print("-" * 40)
        missing_analysis = self.analyze_missing_data()
        
        for mep_name, data in missing_analysis.items():
            if 'error' in data:
                print(f"{mep_name}: ERROR - {data['error']}")
            else:
                print(f"{mep_name}: {data['unprocessed_records']:,} unprocessed records")
        print()
        
        # Interval count validation
        print("6. INTERVAL COUNT VALIDATION")
        print("-" * 40)
        interval_validation = self.validate_interval_counts()
        
        for mep_name, data in interval_validation.items():
            if 'error' in data:
                print(f"{mep_name}: ERROR - {data['error']}")
            else:
                print(f"{mep_name}: {data['incorrect_interval_counts']} records with incorrect interval counts")
                if data['examples']:
                    print("  Examples:")
                    for example in data['examples']:
                        print(f"    {example['icp']} | {example['reading_date']} | {example['register_code']} | {example['processed_intervals']} intervals")
        print()
        
        # Summary and recommendations
        print("7. SUMMARY AND RECOMMENDATIONS")
        print("-" * 40)
        
        if abs(discrepancy) < 100:
            print("✅ Record counts are within acceptable range")
        else:
            print("❌ Significant discrepancy detected")
            
        if duplicate_analysis['total_duplicates'] > 0:
            print(f"⚠️  {duplicate_analysis['total_duplicates']} duplicate groups found - investigate processing logic")
        else:
            print("✅ No duplicates found")
            
        unprocessed_total = sum(data.get('unprocessed_records', 0) for data in missing_analysis.values() if 'unprocessed_records' in data)
        if unprocessed_total > 0:
            print(f"⚠️  {unprocessed_total} unprocessed records found - check DAG execution")
        else:
            print("✅ All raw data has been processed")
        
        print()
        print("=" * 80)
    
    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    analyzer = HHRValidationAnalyzer()
    try:
        analyzer.generate_report()
    finally:
        analyzer.close() 