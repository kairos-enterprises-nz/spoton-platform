"""
BCMM Metering Data Quality Checks

This module implements comprehensive data quality checks for BCMM metering data
including validation rules, anomaly detection, and quality scoring.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from dataclasses import dataclass
from enum import Enum

from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)


class QualityIssueType(Enum):
    """Types of data quality issues"""
    MISSING_DATA = "missing_data"
    NEGATIVE_VALUES = "negative_values"
    HIGH_VALUES = "high_values"
    ZERO_VALUES = "zero_values"
    INCOMPLETE_INTERVALS = "incomplete_intervals"
    DUPLICATE_READINGS = "duplicate_readings"
    TIME_GAPS = "time_gaps"
    SUSPICIOUS_PATTERNS = "suspicious_patterns"
    INCONSISTENT_UNITS = "inconsistent_units"
    FUTURE_DATES = "future_dates"


class QualitySeverity(Enum):
    """Severity levels for quality issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """Represents a data quality issue"""
    issue_type: QualityIssueType
    severity: QualitySeverity
    description: str
    affected_records: int
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class QualityReport:
    """Data quality assessment report"""
    tenant_id: int
    source_system: str
    assessment_date: datetime
    total_records: int
    quality_score: float  # 0-100
    issues: List[QualityIssue]
    recommendations: List[str]
    metadata: Dict[str, Any]


class BCMMDataQualityChecker:
    """
    Comprehensive data quality checker for BCMM metering data
    """
    
    # Quality thresholds
    MAX_INTERVAL_KWH = 100.0
    MAX_DAILY_KWH = 10000.0
    MIN_INTERVALS_PER_DAY = 46  # Allow for some missing intervals
    MAX_ZERO_CONSECUTIVE_INTERVALS = 12  # 6 hours
    
    def __init__(self, tenant_id: int = 1):
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def assess_interval_data_quality(self, 
                                   start_date: Optional[date] = None,
                                   end_date: Optional[date] = None,
                                   icp_filter: Optional[str] = None) -> QualityReport:
        """
        Assess data quality for interval data
        """
        self.logger.info(f"Starting interval data quality assessment for tenant {self.tenant_id}")
        
        if not start_date:
            start_date = date.today() - timedelta(days=7)
        if not end_date:
            end_date = date.today()
        
        issues = []
        recommendations = []
        metadata = {}
        
        with connection.cursor() as cursor:
            # Base query conditions
            base_conditions = [
                "raw_data->>'source_system' = 'BCMM'",
                "tenant_id = %s",
                "read_at::date BETWEEN %s AND %s"
            ]
            params = [self.tenant_id, start_date, end_date]
            
            if icp_filter:
                base_conditions.append("icp_id = %s")
                params.append(icp_filter)
            
            base_where = " AND ".join(base_conditions)
            
            # Get total records
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM metering_raw_interval 
                WHERE {base_where}
            """, params)
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                return QualityReport(
                    tenant_id=self.tenant_id,
                    source_system='BCMM',
                    assessment_date=timezone.now(),
                    total_records=0,
                    quality_score=0.0,
                    issues=[],
                    recommendations=["No data found for assessment period"],
                    metadata={"start_date": str(start_date), "end_date": str(end_date)}
                )
            
            # Check 1: Missing intervals (incomplete days)
            issues.extend(self._check_missing_intervals(cursor, base_where, params))
            
            # Check 2: Negative values
            issues.extend(self._check_negative_values(cursor, base_where, params))
            
            # Check 3: High values
            issues.extend(self._check_high_interval_values(cursor, base_where, params))
            
            # Check 4: Zero value patterns
            issues.extend(self._check_zero_patterns(cursor, base_where, params))
            
            # Check 5: Duplicate readings
            issues.extend(self._check_duplicate_intervals(cursor, base_where, params))
            
            # Check 6: Future dates
            issues.extend(self._check_future_dates(cursor, base_where, params))
            
            # Check 7: Time gaps
            issues.extend(self._check_time_gaps(cursor, base_where, params))
            
            # Generate metadata
            metadata = self._generate_interval_metadata(cursor, base_where, params)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(total_records, issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues)
        
        return QualityReport(
            tenant_id=self.tenant_id,
            source_system='BCMM',
            assessment_date=timezone.now(),
            total_records=total_records,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations,
            metadata=metadata
        )
    
    def assess_daily_data_quality(self,
                                start_date: Optional[date] = None,
                                end_date: Optional[date] = None,
                                icp_filter: Optional[str] = None) -> QualityReport:
        """
        Assess data quality for daily data
        """
        self.logger.info(f"Starting daily data quality assessment for tenant {self.tenant_id}")
        
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        issues = []
        recommendations = []
        metadata = {}
        
        with connection.cursor() as cursor:
            # Base query conditions
            base_conditions = [
                "raw_data->>'source_system' = 'BCMM'",
                "tenant_id = %s",
                "read_date BETWEEN %s AND %s"
            ]
            params = [self.tenant_id, start_date, end_date]
            
            if icp_filter:
                base_conditions.append("icp_id = %s")
                params.append(icp_filter)
            
            base_where = " AND ".join(base_conditions)
            
            # Get total records
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM metering_raw_daily 
                WHERE {base_where}
            """, params)
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                return QualityReport(
                    tenant_id=self.tenant_id,
                    source_system='BCMM',
                    assessment_date=timezone.now(),
                    total_records=0,
                    quality_score=0.0,
                    issues=[],
                    recommendations=["No daily data found for assessment period"],
                    metadata={"start_date": str(start_date), "end_date": str(end_date)}
                )
            
            # Check 1: Negative values
            issues.extend(self._check_negative_daily_values(cursor, base_where, params))
            
            # Check 2: High values
            issues.extend(self._check_high_daily_values(cursor, base_where, params))
            
            # Check 3: Duplicate readings
            issues.extend(self._check_duplicate_daily_readings(cursor, base_where, params))
            
            # Check 4: Missing days
            issues.extend(self._check_missing_daily_readings(cursor, base_where, params, start_date, end_date))
            
            # Check 5: Inconsistent register readings
            issues.extend(self._check_register_consistency(cursor, base_where, params))
            
            # Generate metadata
            metadata = self._generate_daily_metadata(cursor, base_where, params)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(total_records, issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues)
        
        return QualityReport(
            tenant_id=self.tenant_id,
            source_system='BCMM',
            assessment_date=timezone.now(),
            total_records=total_records,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations,
            metadata=metadata
        )
    
    def _check_missing_intervals(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for missing intervals (incomplete days)"""
        issues = []
        
        cursor.execute(f"""
            SELECT 
                icp_id, 
                register_code, 
                read_at::date as read_date, 
                COUNT(*) as interval_count
            FROM metering_raw_interval 
            WHERE {base_where}
            GROUP BY icp_id, register_code, read_at::date
            HAVING COUNT(*) < %s
            ORDER BY interval_count ASC
            LIMIT 100
        """, params + [self.MIN_INTERVALS_PER_DAY])
        
        incomplete_days = cursor.fetchall()
        
        if incomplete_days:
            affected_records = len(incomplete_days)
            severity = QualitySeverity.HIGH if affected_records > 10 else QualitySeverity.MEDIUM
            
            details = {
                "incomplete_days": [
                    {"icp": row[0], "register": row[1], "date": str(row[2]), "intervals": row[3]}
                    for row in incomplete_days[:10]  # Limit details
                ],
                "total_incomplete_days": affected_records,
                "minimum_expected_intervals": self.MIN_INTERVALS_PER_DAY
            }
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.INCOMPLETE_INTERVALS,
                severity=severity,
                description=f"Found {affected_records} days with incomplete interval data",
                affected_records=affected_records,
                details=details,
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_negative_values(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for negative interval values"""
        issues = []
        
        cursor.execute(f"""
            SELECT COUNT(*), MIN(kwh), AVG(kwh)
            FROM metering_raw_interval 
            WHERE {base_where} AND kwh < 0
        """, params)
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            count, min_kwh, avg_kwh = result
            severity = QualitySeverity.CRITICAL if count > 100 else QualitySeverity.HIGH
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.NEGATIVE_VALUES,
                severity=severity,
                description=f"Found {count} negative interval values",
                affected_records=count,
                details={
                    "min_value": float(min_kwh),
                    "avg_negative_value": float(avg_kwh),
                    "total_negative_intervals": count
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_high_interval_values(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for unusually high interval values"""
        issues = []
        
        cursor.execute(f"""
            SELECT COUNT(*), MAX(kwh), AVG(kwh)
            FROM metering_raw_interval 
            WHERE {base_where} AND kwh > %s
        """, params + [self.MAX_INTERVAL_KWH])
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            count, max_kwh, avg_kwh = result
            severity = QualitySeverity.MEDIUM if count < 10 else QualitySeverity.HIGH
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.HIGH_VALUES,
                severity=severity,
                description=f"Found {count} unusually high interval values (>{self.MAX_INTERVAL_KWH} kWh)",
                affected_records=count,
                details={
                    "max_value": float(max_kwh),
                    "avg_high_value": float(avg_kwh),
                    "threshold": self.MAX_INTERVAL_KWH,
                    "total_high_intervals": count
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_zero_patterns(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for suspicious zero value patterns"""
        issues = []
        
        # Check for excessive consecutive zeros
        cursor.execute(f"""
            WITH zero_intervals AS (
                SELECT 
                    icp_id, 
                    register_code, 
                    read_at,
                    kwh,
                    LAG(kwh) OVER (PARTITION BY icp_id, register_code ORDER BY read_at) as prev_kwh,
                    LEAD(kwh) OVER (PARTITION BY icp_id, register_code ORDER BY read_at) as next_kwh
                FROM metering_raw_interval 
                WHERE {base_where}
                ORDER BY icp_id, register_code, read_at
            ),
            zero_sequences AS (
                SELECT 
                    icp_id,
                    register_code,
                    COUNT(*) as consecutive_zeros
                FROM zero_intervals
                WHERE kwh = 0 AND prev_kwh = 0 AND next_kwh = 0
                GROUP BY icp_id, register_code
                HAVING COUNT(*) > %s
            )
            SELECT COUNT(*), MAX(consecutive_zeros), AVG(consecutive_zeros)
            FROM zero_sequences
        """, params + [self.MAX_ZERO_CONSECUTIVE_INTERVALS])
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            count, max_zeros, avg_zeros = result
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.ZERO_VALUES,
                severity=QualitySeverity.MEDIUM,
                description=f"Found {count} meter/register combinations with excessive consecutive zero values",
                affected_records=count,
                details={
                    "max_consecutive_zeros": max_zeros,
                    "avg_consecutive_zeros": float(avg_zeros),
                    "threshold": self.MAX_ZERO_CONSECUTIVE_INTERVALS,
                    "affected_meters": count
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_duplicate_intervals(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for duplicate interval readings"""
        issues = []
        
        cursor.execute(f"""
            SELECT 
                icp_id, 
                register_code, 
                read_at, 
                COUNT(*) as duplicate_count
            FROM metering_raw_interval 
            WHERE {base_where}
            GROUP BY icp_id, register_code, read_at
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 100
        """, params)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            total_duplicates = sum(row[3] - 1 for row in duplicates)  # Extra records beyond the first
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.DUPLICATE_READINGS,
                severity=QualitySeverity.MEDIUM,
                description=f"Found {total_duplicates} duplicate interval readings across {len(duplicates)} timestamps",
                affected_records=total_duplicates,
                details={
                    "duplicate_timestamps": len(duplicates),
                    "total_extra_records": total_duplicates,
                    "examples": [
                        {"icp": row[0], "register": row[1], "timestamp": str(row[2]), "count": row[3]}
                        for row in duplicates[:5]
                    ]
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_future_dates(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for readings with future dates"""
        issues = []
        
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM metering_raw_interval 
            WHERE {base_where} AND read_at > NOW()
        """, params)
        
        future_count = cursor.fetchone()[0]
        
        if future_count > 0:
            issues.append(QualityIssue(
                issue_type=QualityIssueType.FUTURE_DATES,
                severity=QualitySeverity.HIGH,
                description=f"Found {future_count} readings with future timestamps",
                affected_records=future_count,
                details={"future_readings": future_count},
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_time_gaps(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for unexpected time gaps in readings"""
        issues = []
        
        cursor.execute(f"""
            WITH time_gaps AS (
                SELECT 
                    icp_id,
                    register_code,
                    read_at,
                    LAG(read_at) OVER (PARTITION BY icp_id, register_code ORDER BY read_at) as prev_read_at,
                    EXTRACT(EPOCH FROM (read_at - LAG(read_at) OVER (PARTITION BY icp_id, register_code ORDER BY read_at))) / 60 as gap_minutes
                FROM metering_raw_interval 
                WHERE {base_where}
            )
            SELECT COUNT(*)
            FROM time_gaps
            WHERE gap_minutes > 60  -- More than 1 hour gap
        """, params)
        
        gap_count = cursor.fetchone()[0]
        
        if gap_count > 0:
            issues.append(QualityIssue(
                issue_type=QualityIssueType.TIME_GAPS,
                severity=QualitySeverity.MEDIUM,
                description=f"Found {gap_count} unexpected time gaps (>1 hour) between readings",
                affected_records=gap_count,
                details={"time_gaps": gap_count},
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_negative_daily_values(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for negative daily values"""
        issues = []
        
        cursor.execute(f"""
            SELECT COUNT(*), MIN(kwh)
            FROM metering_raw_daily 
            WHERE {base_where} AND kwh < 0
        """, params)
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            count, min_kwh = result
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.NEGATIVE_VALUES,
                severity=QualitySeverity.CRITICAL,
                description=f"Found {count} negative daily values",
                affected_records=count,
                details={
                    "min_value": float(min_kwh),
                    "total_negative_dailies": count
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_high_daily_values(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for unusually high daily values"""
        issues = []
        
        cursor.execute(f"""
            SELECT COUNT(*), MAX(kwh), AVG(kwh)
            FROM metering_raw_daily 
            WHERE {base_where} AND kwh > %s
        """, params + [self.MAX_DAILY_KWH])
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            count, max_kwh, avg_kwh = result
            severity = QualitySeverity.MEDIUM if count < 5 else QualitySeverity.HIGH
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.HIGH_VALUES,
                severity=severity,
                description=f"Found {count} unusually high daily values (>{self.MAX_DAILY_KWH} kWh)",
                affected_records=count,
                details={
                    "max_value": float(max_kwh),
                    "avg_high_value": float(avg_kwh),
                    "threshold": self.MAX_DAILY_KWH,
                    "total_high_dailies": count
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_duplicate_daily_readings(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for duplicate daily readings"""
        issues = []
        
        cursor.execute(f"""
            SELECT 
                icp_id, 
                register_code, 
                read_date, 
                COUNT(*) as duplicate_count
            FROM metering_raw_daily 
            WHERE {base_where}
            GROUP BY icp_id, register_code, read_date
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 100
        """, params)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            total_duplicates = sum(row[3] - 1 for row in duplicates)
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.DUPLICATE_READINGS,
                severity=QualitySeverity.HIGH,
                description=f"Found {total_duplicates} duplicate daily readings across {len(duplicates)} dates",
                affected_records=total_duplicates,
                details={
                    "duplicate_dates": len(duplicates),
                    "total_extra_records": total_duplicates,
                    "examples": [
                        {"icp": row[0], "register": row[1], "date": str(row[2]), "count": row[3]}
                        for row in duplicates[:5]
                    ]
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_missing_daily_readings(self, cursor, base_where: str, params: List, 
                                    start_date: date, end_date: date) -> List[QualityIssue]:
        """Check for missing daily readings"""
        issues = []
        
        # This is a simplified check - in production you'd want to check against expected reading schedules
        # Calculate expected days
        expected_days = (end_date - start_date).days + 1
        
        cursor.execute(f"""
            SELECT 
                icp_id,
                register_code,
                COUNT(DISTINCT read_date) as reading_days,
                %s as expected_days
            FROM metering_raw_daily 
            WHERE {base_where}
            GROUP BY icp_id, register_code
            HAVING COUNT(DISTINCT read_date) < %s * 0.9  -- Allow 10% missing
        """, params + [expected_days, expected_days])
        
        missing_readings = cursor.fetchall()
        
        if missing_readings:
            total_missing = sum(row[3] - row[2] for row in missing_readings)
            
            issues.append(QualityIssue(
                issue_type=QualityIssueType.MISSING_DATA,
                severity=QualitySeverity.MEDIUM,
                description=f"Found {len(missing_readings)} meter/register combinations with missing daily readings",
                affected_records=len(missing_readings),
                details={
                    "affected_meters": len(missing_readings),
                    "estimated_missing_days": total_missing,
                    "assessment_period_days": (end_date - start_date).days + 1
                },
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _check_register_consistency(self, cursor, base_where: str, params: List) -> List[QualityIssue]:
        """Check for register reading consistency (cumulative registers should be non-decreasing)"""
        issues = []
        
        cursor.execute(f"""
            WITH ordered_readings AS (
                SELECT 
                    icp_id,
                    register_code,
                    read_date,
                    kwh,
                    LAG(kwh) OVER (PARTITION BY icp_id, register_code ORDER BY read_date) as prev_kwh
                FROM metering_raw_daily 
                WHERE {base_where}
            )
            SELECT COUNT(*)
            FROM ordered_readings
            WHERE prev_kwh IS NOT NULL AND kwh < prev_kwh * 0.9  -- Allow for some meter resets
        """, params)
        
        inconsistent_count = cursor.fetchone()[0]
        
        if inconsistent_count > 0:
            issues.append(QualityIssue(
                issue_type=QualityIssueType.SUSPICIOUS_PATTERNS,
                severity=QualitySeverity.MEDIUM,
                description=f"Found {inconsistent_count} potentially inconsistent register readings (backward movement)",
                affected_records=inconsistent_count,
                details={"inconsistent_readings": inconsistent_count},
                timestamp=timezone.now()
            ))
        
        return issues
    
    def _generate_interval_metadata(self, cursor, base_where: str, params: List) -> Dict[str, Any]:
        """Generate metadata for interval data assessment"""
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_intervals,
                COUNT(DISTINCT icp_id) as unique_icps,
                COUNT(DISTINCT register_code) as unique_registers,
                COUNT(DISTINCT DATE(read_at)) as unique_days,
                MIN(read_at) as earliest_reading,
                MAX(read_at) as latest_reading,
                AVG(kwh) as avg_kwh,
                MIN(kwh) as min_kwh,
                MAX(kwh) as max_kwh,
                SUM(kwh) as total_kwh
            FROM metering_raw_interval 
            WHERE {base_where}
        """, params)
        
        result = cursor.fetchone()
        if result:
            return {
                "total_intervals": result[0],
                "unique_icps": result[1],
                "unique_registers": result[2],
                "unique_days": result[3],
                "earliest_reading": str(result[4]) if result[4] else None,
                "latest_reading": str(result[5]) if result[5] else None,
                "avg_kwh": float(result[6]) if result[6] else 0,
                "min_kwh": float(result[7]) if result[7] else 0,
                "max_kwh": float(result[8]) if result[8] else 0,
                "total_kwh": float(result[9]) if result[9] else 0
            }
        return {}
    
    def _generate_daily_metadata(self, cursor, base_where: str, params: List) -> Dict[str, Any]:
        """Generate metadata for daily data assessment"""
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_dailies,
                COUNT(DISTINCT icp_id) as unique_icps,
                COUNT(DISTINCT register_code) as unique_registers,
                COUNT(DISTINCT read_date) as unique_days,
                MIN(read_date) as earliest_date,
                MAX(read_date) as latest_date,
                AVG(kwh) as avg_kwh,
                MIN(kwh) as min_kwh,
                MAX(kwh) as max_kwh,
                SUM(kwh) as total_kwh
            FROM metering_raw_daily 
            WHERE {base_where}
        """, params)
        
        result = cursor.fetchone()
        if result:
            return {
                "total_dailies": result[0],
                "unique_icps": result[1],
                "unique_registers": result[2],
                "unique_days": result[3],
                "earliest_date": str(result[4]) if result[4] else None,
                "latest_date": str(result[5]) if result[5] else None,
                "avg_kwh": float(result[6]) if result[6] else 0,
                "min_kwh": float(result[7]) if result[7] else 0,
                "max_kwh": float(result[8]) if result[8] else 0,
                "total_kwh": float(result[9]) if result[9] else 0
            }
        return {}
    
    def _calculate_quality_score(self, total_records: int, issues: List[QualityIssue]) -> float:
        """Calculate overall data quality score (0-100)"""
        if total_records == 0:
            return 0.0
        
        # Start with perfect score
        score = 100.0
        
        # Deduct points based on issues
        for issue in issues:
            severity_multiplier = {
                QualitySeverity.LOW: 0.5,
                QualitySeverity.MEDIUM: 1.0,
                QualitySeverity.HIGH: 2.0,
                QualitySeverity.CRITICAL: 5.0
            }
            
            # Calculate impact as percentage of affected records
            impact_percentage = min(100.0, (issue.affected_records / total_records) * 100)
            
            # Deduct points based on severity and impact
            deduction = impact_percentage * severity_multiplier[issue.severity] * 0.1
            score -= deduction
        
        return max(0.0, score)
    
    def _generate_recommendations(self, issues: List[QualityIssue]) -> List[str]:
        """Generate recommendations based on identified issues"""
        recommendations = []
        
        issue_types = {issue.issue_type for issue in issues}
        
        if QualityIssueType.MISSING_DATA in issue_types or QualityIssueType.INCOMPLETE_INTERVALS in issue_types:
            recommendations.append("Review data collection processes to ensure complete data capture")
            recommendations.append("Implement data validation at the point of collection")
        
        if QualityIssueType.NEGATIVE_VALUES in issue_types:
            recommendations.append("Investigate negative values - check meter configuration and data processing logic")
            recommendations.append("Implement validation rules to flag negative consumption values")
        
        if QualityIssueType.HIGH_VALUES in issue_types:
            recommendations.append("Review high consumption values for accuracy - may indicate meter faults or data errors")
            recommendations.append("Set up automated alerts for values exceeding normal thresholds")
        
        if QualityIssueType.DUPLICATE_READINGS in issue_types:
            recommendations.append("Review data import processes to prevent duplicate records")
            recommendations.append("Implement deduplication logic in ETL pipeline")
        
        if QualityIssueType.ZERO_VALUES in issue_types:
            recommendations.append("Investigate patterns of zero consumption - may indicate meter or communication issues")
        
        if QualityIssueType.TIME_GAPS in issue_types:
            recommendations.append("Review data collection schedules and communication reliability")
        
        if QualityIssueType.FUTURE_DATES in issue_types:
            recommendations.append("Check system clocks and time zone configurations")
        
        if not recommendations:
            recommendations.append("Data quality appears good - continue monitoring")
        
        return recommendations
    
    def export_quality_report(self, report: QualityReport, format: str = 'json') -> str:
        """Export quality report in specified format"""
        if format.lower() == 'json':
            import json
            
            report_dict = {
                "tenant_id": report.tenant_id,
                "source_system": report.source_system,
                "assessment_date": report.assessment_date.isoformat(),
                "total_records": report.total_records,
                "quality_score": report.quality_score,
                "issues": [
                    {
                        "type": issue.issue_type.value,
                        "severity": issue.severity.value,
                        "description": issue.description,
                        "affected_records": issue.affected_records,
                        "details": issue.details,
                        "timestamp": issue.timestamp.isoformat()
                    }
                    for issue in report.issues
                ],
                "recommendations": report.recommendations,
                "metadata": report.metadata
            }
            
            return json.dumps(report_dict, indent=2)
        
        elif format.lower() == 'text':
            lines = [
                f"BCMM Data Quality Report",
                f"========================",
                f"Tenant: {report.tenant_id}",
                f"Source System: {report.source_system}",
                f"Assessment Date: {report.assessment_date}",
                f"Total Records: {report.total_records:,}",
                f"Quality Score: {report.quality_score:.1f}/100",
                f"",
                f"Issues Found: {len(report.issues)}",
                f"============="
            ]
            
            for issue in report.issues:
                lines.extend([
                    f"",
                    f"Issue: {issue.issue_type.value}",
                    f"Severity: {issue.severity.value}",
                    f"Description: {issue.description}",
                    f"Affected Records: {issue.affected_records:,}",
                ])
            
            lines.extend([
                f"",
                f"Recommendations:",
                f"==============="
            ])
            
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


def run_bcmm_quality_assessment(tenant_id: int = 1, 
                               days_back: int = 7,
                               export_format: str = 'json') -> Tuple[QualityReport, QualityReport]:
    """
    Run comprehensive BCMM data quality assessment
    
    Returns:
        Tuple of (interval_report, daily_report)
    """
    checker = BCMMDataQualityChecker(tenant_id)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)
    
    # Assess interval data
    interval_report = checker.assess_interval_data_quality(start_date, end_date)
    
    # Assess daily data
    daily_report = checker.assess_daily_data_quality(start_date, end_date)
    
    return interval_report, daily_report 