"""
Validation Failure Logger - Detailed logging system for validation failures

This module provides comprehensive logging for validation failures with:
- Detailed failure analysis
- Root cause identification
- Data quality metrics
- Remediation suggestions
- Trend analysis
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from django.db import connection
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

# Configure detailed failure logger
failure_logger = logging.getLogger('validation_failures')
failure_logger.setLevel(logging.INFO)

# Create file handler for failure logs
failure_handler = logging.FileHandler('/app/logs/validation_failures.log')
failure_handler.setLevel(logging.INFO)

# Create detailed formatter
failure_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
failure_handler.setFormatter(failure_formatter)
failure_logger.addHandler(failure_handler)


class FailureCategory(Enum):
    """Categories of validation failures"""
    DATA_QUALITY = "data_quality"
    BUSINESS_RULE = "business_rule"
    TECHNICAL = "technical"
    DST_RELATED = "dst_related"
    DUPLICATE = "duplicate"
    MISSING_DATA = "missing_data"
    OUTLIER = "outlier"
    CONTINUITY = "continuity"


class FailureSeverity(Enum):
    """Severity levels for validation failures"""
    CRITICAL = "critical"    # Affects settlement/billing
    HIGH = "high"           # Significant data quality impact
    MEDIUM = "medium"       # Moderate impact
    LOW = "low"            # Minor issues
    INFO = "info"          # Informational only


@dataclass
class ValidationFailureDetail:
    """Detailed information about a validation failure"""
    failure_id: str
    timestamp: datetime
    session_id: str
    rule_code: str
    rule_name: str
    category: FailureCategory
    severity: FailureSeverity
    
    # Reading details
    icp_id: str
    meter_serial_number: str
    meter_register_id: str
    reading_timestamp: datetime
    trading_period: int
    source: str
    
    # Failure details
    expected_value: Optional[float]
    actual_value: Optional[float]
    failure_reason: str
    error_message: str
    validation_context: Dict[str, Any]
    
    # Data quality metrics
    data_completeness: float
    data_accuracy: float
    data_consistency: float
    
    # Remediation
    suggested_action: str
    auto_fixable: bool
    estimated_fix_confidence: float
    
    # Metadata
    processing_duration_ms: int
    related_failures: List[str]
    impact_assessment: Dict[str, Any]


class ValidationFailureLogger:
    """Comprehensive validation failure logging system"""
    
    def __init__(self):
        self.logger = failure_logger
        
    def log_validation_failure(
        self,
        session_id: str,
        rule_code: str,
        reading_data: Dict[str, Any],
        failure_reason: str,
        validation_context: Dict[str, Any] = None,
        severity: FailureSeverity = FailureSeverity.MEDIUM
    ) -> str:
        """Log a detailed validation failure"""
        
        failure_id = str(uuid.uuid4())
        
        # Analyze failure category
        category = self._categorize_failure(rule_code, failure_reason, reading_data)
        
        # Calculate data quality metrics
        quality_metrics = self._calculate_quality_metrics(reading_data, validation_context)
        
        # Generate remediation suggestions
        remediation = self._generate_remediation_suggestions(category, rule_code, reading_data)
        
        # Assess impact
        impact = self._assess_failure_impact(reading_data, category, severity)
        
        # Create failure detail
        failure_detail = ValidationFailureDetail(
            failure_id=failure_id,
            timestamp=timezone.now(),
            session_id=session_id,
            rule_code=rule_code,
            rule_name=self._get_rule_name(rule_code),
            category=category,
            severity=severity,
            
            # Reading details
            icp_id=reading_data.get('icp_id', ''),
            meter_serial_number=reading_data.get('meter_serial_number', ''),
            meter_register_id=reading_data.get('meter_register_id', ''),
            reading_timestamp=reading_data.get('timestamp'),
            trading_period=reading_data.get('trading_period', 0),
            source=reading_data.get('source', ''),
            
            # Failure details
            expected_value=validation_context.get('expected_value') if validation_context else None,
            actual_value=reading_data.get('value'),
            failure_reason=failure_reason,
            error_message=validation_context.get('error_message', '') if validation_context else '',
            validation_context=validation_context or {},
            
            # Data quality metrics
            data_completeness=quality_metrics['completeness'],
            data_accuracy=quality_metrics['accuracy'],
            data_consistency=quality_metrics['consistency'],
            
            # Remediation
            suggested_action=remediation['action'],
            auto_fixable=remediation['auto_fixable'],
            estimated_fix_confidence=remediation['confidence'],
            
            # Metadata
            processing_duration_ms=validation_context.get('processing_time_ms', 0) if validation_context else 0,
            related_failures=[],
            impact_assessment=impact
        )
        
        # Log to file
        self._log_to_file(failure_detail)
        
        # Store in database
        self._store_in_database(failure_detail)
        
        return failure_id
    
    def log_batch_failure_summary(
        self,
        session_id: str,
        total_readings: int,
        failed_readings: int,
        failure_breakdown: Dict[str, int],
        processing_time: timedelta
    ):
        """Log a summary of batch validation failures"""
        
        summary = {
            'session_id': session_id,
            'timestamp': timezone.now().isoformat(),
            'total_readings': total_readings,
            'failed_readings': failed_readings,
            'success_rate': ((total_readings - failed_readings) / total_readings * 100) if total_readings > 0 else 0,
            'failure_breakdown': failure_breakdown,
            'processing_time_seconds': processing_time.total_seconds(),
            'failures_per_second': failed_readings / processing_time.total_seconds() if processing_time.total_seconds() > 0 else 0
        }
        
        self.logger.info(f"BATCH_SUMMARY | {json.dumps(summary, cls=DjangoJSONEncoder)}")
    
    def log_dst_transition_issues(
        self,
        session_id: str,
        transition_date: datetime,
        expected_trading_periods: int,
        actual_trading_periods: int,
        affected_readings: List[Dict[str, Any]]
    ):
        """Log DST transition-related issues"""
        
        dst_issue = {
            'session_id': session_id,
            'timestamp': timezone.now().isoformat(),
            'transition_date': transition_date.isoformat(),
            'expected_trading_periods': expected_trading_periods,
            'actual_trading_periods': actual_trading_periods,
            'trading_period_variance': actual_trading_periods - expected_trading_periods,
            'affected_readings_count': len(affected_readings),
            'affected_icps': list(set(r.get('icp_id') for r in affected_readings)),
            'severity': 'CRITICAL' if abs(actual_trading_periods - expected_trading_periods) > 10 else 'HIGH'
        }
        
        self.logger.warning(f"DST_TRANSITION_ISSUE | {json.dumps(dst_issue, cls=DjangoJSONEncoder)}")
    
    def log_data_quality_trend(
        self,
        source: str,
        time_period: str,
        quality_metrics: Dict[str, float],
        trend_direction: str,
        recommendations: List[str]
    ):
        """Log data quality trends"""
        
        trend = {
            'timestamp': timezone.now().isoformat(),
            'source': source,
            'time_period': time_period,
            'quality_metrics': quality_metrics,
            'trend_direction': trend_direction,
            'recommendations': recommendations
        }
        
        self.logger.info(f"QUALITY_TREND | {json.dumps(trend, cls=DjangoJSONEncoder)}")
    
    def _categorize_failure(self, rule_code: str, failure_reason: str, reading_data: Dict[str, Any]) -> FailureCategory:
        """Categorize the validation failure"""
        
        rule_categories = {
            'MISSING_VALUE_CHECK': FailureCategory.MISSING_DATA,
            'MISSING_DATA_CHECK': FailureCategory.MISSING_DATA,
            'HIGH_VALUE_CHECK': FailureCategory.OUTLIER,
            'NEGATIVE_VALUE_CHECK': FailureCategory.DATA_QUALITY,
            'PLAUSIBILITY_CHECK': FailureCategory.BUSINESS_RULE,
            'CONTINUITY_CHECK': FailureCategory.CONTINUITY,
            'HIGH_USAGE_CHECK': FailureCategory.OUTLIER
        }
        
        # Check for DST-related issues
        if reading_data.get('trading_period', 0) > 48:
            return FailureCategory.DST_RELATED
        
        # Check for duplicate indicators
        if 'duplicate' in failure_reason.lower():
            return FailureCategory.DUPLICATE
        
        return rule_categories.get(rule_code, FailureCategory.TECHNICAL)
    
    def _calculate_quality_metrics(self, reading_data: Dict[str, Any], validation_context: Dict[str, Any] = None) -> Dict[str, float]:
        """Calculate data quality metrics for the reading"""
        
        # Completeness: Are all required fields present?
        required_fields = ['icp_id', 'meter_register_id', 'timestamp', 'value', 'source']
        present_fields = sum(1 for field in required_fields if reading_data.get(field) is not None)
        completeness = present_fields / len(required_fields)
        
        # Accuracy: Is the value within reasonable bounds?
        value = reading_data.get('value', 0)
        accuracy = 1.0  # Default to perfect accuracy
        if value is not None:
            if value < 0:
                accuracy = 0.0  # Negative values are always inaccurate for consumption
            elif value > 1000:  # Extremely high value
                accuracy = 0.3
            elif value > 100:   # High value
                accuracy = 0.7
        
        # Consistency: Does this value fit with historical patterns?
        consistency = validation_context.get('consistency_score', 0.8) if validation_context else 0.8
        
        return {
            'completeness': completeness,
            'accuracy': accuracy,
            'consistency': consistency
        }
    
    def _generate_remediation_suggestions(self, category: FailureCategory, rule_code: str, reading_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate remediation suggestions based on failure category"""
        
        remediation_map = {
            FailureCategory.MISSING_DATA: {
                'action': 'Apply interpolation estimation or use historical average',
                'auto_fixable': True,
                'confidence': 0.8
            },
            FailureCategory.OUTLIER: {
                'action': 'Review meter configuration and validate with customer usage patterns',
                'auto_fixable': False,
                'confidence': 0.6
            },
            FailureCategory.DATA_QUALITY: {
                'action': 'Flag for manual review and potential re-reading',
                'auto_fixable': False,
                'confidence': 0.4
            },
            FailureCategory.BUSINESS_RULE: {
                'action': 'Apply business rule override or escalate to energy team',
                'auto_fixable': True,
                'confidence': 0.7
            },
            FailureCategory.CONTINUITY: {
                'action': 'Check for meter communication issues and fill gaps via estimation',
                'auto_fixable': True,
                'confidence': 0.9
            },
            FailureCategory.DST_RELATED: {
                'action': 'Apply DST-aware trading period calculation and reprocess',
                'auto_fixable': True,
                'confidence': 0.95
            },
            FailureCategory.DUPLICATE: {
                'action': 'Remove duplicate entries keeping the most recent or highest quality reading',
                'auto_fixable': True,
                'confidence': 0.99
            }
        }
        
        return remediation_map.get(category, {
            'action': 'Manual investigation required',
            'auto_fixable': False,
            'confidence': 0.3
        })
    
    def _assess_failure_impact(self, reading_data: Dict[str, Any], category: FailureCategory, severity: FailureSeverity) -> Dict[str, Any]:
        """Assess the impact of the validation failure"""
        
        reading_value = reading_data.get('value') or 0
        
        impact = {
            'settlement_impact': category in [FailureCategory.BUSINESS_RULE, FailureCategory.DST_RELATED],
            'billing_impact': severity in [FailureSeverity.CRITICAL, FailureSeverity.HIGH],
            'customer_impact': reading_value > 50,  # High consumption readings
            'regulatory_impact': category == FailureCategory.DST_RELATED,
            'data_integrity_impact': True,
            'estimated_financial_impact_nzd': self._estimate_financial_impact(reading_data, severity)
        }
        
        return impact
    
    def _estimate_financial_impact(self, reading_data: Dict[str, Any], severity: FailureSeverity) -> float:
        """Estimate financial impact of the failure"""
        
        # Rough estimation based on reading value and severity
        value = reading_data.get('value') or 0
        if not value:
            return 0.0
        
        # Assume average NZ electricity price of $0.30/kWh
        base_impact = abs(float(value)) * 0.30
        
        severity_multipliers = {
            FailureSeverity.CRITICAL: 1.0,
            FailureSeverity.HIGH: 0.7,
            FailureSeverity.MEDIUM: 0.4,
            FailureSeverity.LOW: 0.1,
            FailureSeverity.INFO: 0.0
        }
        
        return base_impact * severity_multipliers.get(severity, 0.5)
    
    def _get_rule_name(self, rule_code: str) -> str:
        """Get human-readable rule name"""
        
        rule_names = {
            'MISSING_VALUE_CHECK': 'Missing Value Check',
            'MISSING_DATA_CHECK': 'Missing Data Check',
            'HIGH_VALUE_CHECK': 'High Value Check',
            'NEGATIVE_VALUE_CHECK': 'Negative Value Check',
            'PLAUSIBILITY_CHECK': 'Plausibility Check',
            'CONTINUITY_CHECK': 'Continuity Check',
            'HIGH_USAGE_CHECK': 'High Usage Check'
        }
        
        return rule_names.get(rule_code, rule_code)
    
    def _log_to_file(self, failure_detail: ValidationFailureDetail):
        """Log failure detail to file"""
        
        log_entry = {
            'type': 'VALIDATION_FAILURE',
            'failure_id': failure_detail.failure_id,
            'timestamp': failure_detail.timestamp.isoformat(),
            'session_id': failure_detail.session_id,
            'rule_code': failure_detail.rule_code,
            'category': failure_detail.category.value,
            'severity': failure_detail.severity.value,
            'icp_id': failure_detail.icp_id,
            'meter_serial': failure_detail.meter_serial_number,
            'register': failure_detail.meter_register_id,
            'reading_time': failure_detail.reading_timestamp.isoformat() if failure_detail.reading_timestamp else None,
            'trading_period': failure_detail.trading_period,
            'source': failure_detail.source,
            'actual_value': failure_detail.actual_value,
            'expected_value': failure_detail.expected_value,
            'failure_reason': failure_detail.failure_reason,
            'suggested_action': failure_detail.suggested_action,
            'auto_fixable': failure_detail.auto_fixable,
            'quality_metrics': {
                'completeness': failure_detail.data_completeness,
                'accuracy': failure_detail.data_accuracy,
                'consistency': failure_detail.data_consistency
            },
            'impact': failure_detail.impact_assessment
        }
        
        self.logger.error(f"FAILURE_DETAIL | {json.dumps(log_entry, cls=DjangoJSONEncoder)}")
    
    def _store_in_database(self, failure_detail: ValidationFailureDetail):
        """Store failure detail in database for analysis"""
        
        # Store in validation_failure_log table (create if needed)
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO energy_validation_failure_log (
                    failure_id, session_id, rule_code, category, severity,
                    icp_id, meter_serial_number, meter_register_id, reading_timestamp,
                    trading_period, source, actual_value, expected_value,
                    failure_reason, suggested_action, auto_fixable,
                    data_completeness, data_accuracy, data_consistency,
                    estimated_financial_impact, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (failure_id) DO NOTHING
            """, [
                failure_detail.failure_id,
                failure_detail.session_id,
                failure_detail.rule_code,
                failure_detail.category.value,
                failure_detail.severity.value,
                failure_detail.icp_id,
                failure_detail.meter_serial_number,
                failure_detail.meter_register_id,
                failure_detail.reading_timestamp,
                failure_detail.trading_period,
                failure_detail.source,
                failure_detail.actual_value,
                failure_detail.expected_value,
                failure_detail.failure_reason,
                failure_detail.suggested_action,
                failure_detail.auto_fixable,
                failure_detail.data_completeness,
                failure_detail.data_accuracy,
                failure_detail.data_consistency,
                failure_detail.impact_assessment.get('estimated_financial_impact_nzd', 0),
                failure_detail.timestamp
            ])


# Global instance
validation_failure_logger = ValidationFailureLogger() 