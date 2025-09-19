"""
Meter Reading Validation Engine

This module implements the core validation logic for meter readings:
- Rule-based validation with configurable business rules
- Estimation engine for missing or invalid readings
- Batch processing for performance
- Audit trail and quality metrics
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
import pandas as pd

from .models import (
    ValidationRule, ValidationRuleOverride, ValidationBatch, ValidationResult,
    EstimationProfile, EstimationHistory, TariffRegisterMap, MeterType
)
from energy.metering.timescale_models import (
    MeterRawInterval, MeterRawDaily, MeterCalcInterval, MeterCalcDaily
)
from users.models import Tenant, User

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status enumeration"""
    VALID = 'valid'
    ESTIMATED = 'estimated'
    INVALID = 'invalid'
    SUSPICIOUS = 'suspicious'
    MISSING = 'missing'


class EstimationMethod(Enum):
    """Estimation method enumeration"""
    HISTORICAL_AVERAGE = 'historical_average'
    LINEAR_INTERPOLATION = 'linear_interpolation'
    SEASONAL_PROFILE = 'seasonal_profile'
    PEER_AVERAGE = 'peer_average'
    ZERO_FILL = 'zero_fill'
    CARRY_FORWARD = 'carry_forward'


@dataclass
class ReadingData:
    """Data structure for meter reading validation"""
    icp_id: str
    register_code: str
    read_at: datetime
    kwh: Decimal
    source_file_id: str = ""
    raw_status: str = ""
    raw_quality: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Validation results (populated during validation)
    final_kwh: Optional[Decimal] = None
    final_status: ValidationStatus = ValidationStatus.VALID
    is_estimated: bool = False
    estimation_method: Optional[EstimationMethod] = None
    estimation_confidence: Optional[Decimal] = None
    rule_fail_mask: int = 0
    failed_rules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_notes: str = ""
    quality_score: Optional[Decimal] = None
    processing_time_ms: Optional[int] = None


@dataclass
class ValidationContext:
    """Context for validation processing"""
    tenant: Tenant
    batch_id: str
    validation_rules: List[ValidationRule]
    rule_overrides: Dict[str, ValidationRuleOverride]
    tariff_register_map: Dict[str, TariffRegisterMap]
    meter_types: Dict[str, MeterType]
    estimation_profiles: Dict[str, EstimationProfile]
    user: Optional[User] = None


class ValidationEngine:
    """
    Core validation engine for meter readings.
    Implements rule-based validation and estimation logic.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_batch(
        self, 
        readings: List[ReadingData], 
        tenant: Tenant,
        batch_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> ValidationBatch:
        """
        Validate a batch of meter readings.
        
        Args:
            readings: List of ReadingData objects to validate
            tenant: Tenant for multi-tenancy
            batch_id: Optional batch identifier
            user: User performing validation
            
        Returns:
            ValidationBatch with results
        """
        if not batch_id:
            batch_id = f"batch_{uuid.uuid4().hex[:8]}_{int(timezone.now().timestamp())}"
        
        # Create validation batch
        batch = ValidationBatch.objects.create(
            tenant=tenant,
            batch_id=batch_id,
            start_date=min(r.read_at.date() for r in readings),
            end_date=max(r.read_at.date() for r in readings),
            status='processing',
            total_readings=len(readings),
            created_by=user,
            started_at=timezone.now()
        )
        
        try:
            # Load validation context
            context = self._load_validation_context(tenant, batch_id)
            
            # Process readings
            results = []
            for reading in readings:
                start_time = timezone.now()
                
                # Validate individual reading
                validated_reading = self._validate_reading(reading, context)
                
                # Calculate processing time
                processing_time = (timezone.now() - start_time).total_seconds() * 1000
                validated_reading.processing_time_ms = int(processing_time)
                
                # Create validation result
                result = self._create_validation_result(validated_reading, batch)
                results.append(result)
            
            # Update batch statistics
            self._update_batch_statistics(batch, results)
            
            # Mark batch as completed
            batch.status = 'completed'
            batch.completed_at = timezone.now()
            batch.processing_duration = batch.completed_at - batch.started_at
            batch.save()
            
            self.logger.info(f"Validation batch {batch_id} completed: {len(results)} readings processed")
            
            return batch
            
        except Exception as e:
            # Mark batch as failed
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.error_details = {'exception_type': type(e).__name__}
            batch.save()
            
            self.logger.error(f"Validation batch {batch_id} failed: {e}")
            raise
    
    def _load_validation_context(self, tenant: Tenant, batch_id: str) -> ValidationContext:
        """Load validation context (rules, overrides, etc.)"""
        # Load active validation rules
        validation_rules = list(
            ValidationRule.objects.active(tenant=tenant)
            .filter(is_active=True)
            .order_by('priority', 'rule_code')
        )
        
        # Load rule overrides
        rule_overrides = {}
        for override in ValidationRuleOverride.objects.active(tenant=tenant):
            key = f"{override.rule.rule_code}_{override.icp_id}_{override.register_code}"
            rule_overrides[key] = override
        
        # Load tariff register mapping
        tariff_register_map = {
            trm.register_code: trm 
            for trm in TariffRegisterMap.objects.all()
        }
        
        # Load meter types
        meter_types = {
            mt.code: mt 
            for mt in MeterType.objects.all()
        }
        
        # Load estimation profiles
        estimation_profiles = {
            ep.profile_code: ep 
            for ep in EstimationProfile.objects.active(tenant=tenant)
        }
        
        return ValidationContext(
            tenant=tenant,
            batch_id=batch_id,
            validation_rules=validation_rules,
            rule_overrides=rule_overrides,
            tariff_register_map=tariff_register_map,
            meter_types=meter_types,
            estimation_profiles=estimation_profiles
        )
    
    def _validate_reading(self, reading: ReadingData, context: ValidationContext) -> ReadingData:
        """
        Validate a single meter reading against all applicable rules.
        
        Args:
            reading: ReadingData to validate
            context: ValidationContext with rules and settings
            
        Returns:
            ReadingData with validation results
        """
        # Initialize validation results
        reading.final_kwh = reading.kwh
        reading.final_status = ValidationStatus.VALID
        reading.failed_rules = []
        reading.warnings = []
        reading.rule_fail_mask = 0
        
        # Apply validation rules
        for rule in context.validation_rules:
            if self._rule_applies_to_reading(rule, reading, context):
                # Check for overrides
                override = self._get_rule_override(rule, reading, context)
                if override and override.is_disabled:
                    continue
                
                # Apply rule
                rule_result = self._apply_validation_rule(rule, reading, context, override)
                
                if not rule_result.passed:
                    # Rule failed
                    reading.failed_rules.append(rule.rule_code)
                    reading.rule_fail_mask |= (1 << rule.priority)
                    
                    if rule.category == 'critical':
                        reading.final_status = ValidationStatus.INVALID
                    elif rule.category == 'warning' and reading.final_status == ValidationStatus.VALID:
                        reading.final_status = ValidationStatus.SUSPICIOUS
                    
                    # Add warnings
                    reading.warnings.extend(rule_result.warnings)
                    
                    # Trigger estimation if configured
                    if rule.triggers_estimation and not reading.is_estimated:
                        estimated_value = self._estimate_reading(
                            reading, rule.estimation_method, context
                        )
                        if estimated_value is not None:
                            reading.final_kwh = estimated_value.value
                            reading.is_estimated = True
                            reading.estimation_method = estimated_value.method
                            reading.estimation_confidence = estimated_value.confidence
                            reading.final_status = ValidationStatus.ESTIMATED
                    
                    # Check if rule is blocking
                    if rule.is_blocking:
                        break
        
        # Calculate quality score
        reading.quality_score = self._calculate_quality_score(reading)
        
        return reading
    
    def _rule_applies_to_reading(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        context: ValidationContext
    ) -> bool:
        """Check if a validation rule applies to a specific reading"""
        # Check meter type scope
        if rule.applies_to_meter_types:
            # TODO: Determine meter type from ICP or reading context
            # For now, assume all rules apply
            pass
        
        # Check register scope
        if rule.applies_to_registers:
            if reading.register_code not in rule.applies_to_registers:
                return False
        
        # Check tariff group scope
        if rule.applies_to_tariff_groups:
            register_map = context.tariff_register_map.get(reading.register_code)
            if not register_map or register_map.tariff_group not in rule.applies_to_tariff_groups:
                return False
        
        return True
    
    def _get_rule_override(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        context: ValidationContext
    ) -> Optional[ValidationRuleOverride]:
        """Get rule override for specific reading"""
        # Check for ICP-specific override
        key = f"{rule.rule_code}_{reading.icp_id}_{reading.register_code}"
        override = context.rule_overrides.get(key)
        if override:
            return override
        
        # Check for register-specific override
        key = f"{rule.rule_code}__{reading.register_code}"
        override = context.rule_overrides.get(key)
        if override:
            return override
        
        # Check for global override
        key = f"{rule.rule_code}__"
        override = context.rule_overrides.get(key)
        if override:
            return override
        
        return None
    
    def _apply_validation_rule(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        context: ValidationContext,
        override: Optional[ValidationRuleOverride] = None
    ) -> 'RuleResult':
        """Apply a specific validation rule to a reading"""
        # Merge parameters with override
        parameters = rule.parameters.copy()
        if override and override.override_parameters:
            parameters.update(override.override_parameters)
        
        # Apply rule based on type
        if rule.rule_type == 'range_check':
            return self._apply_range_check(rule, reading, parameters)
        elif rule.rule_type == 'spike_detection':
            return self._apply_spike_detection(rule, reading, parameters, context)
        elif rule.rule_type == 'continuity_check':
            return self._apply_continuity_check(rule, reading, parameters, context)
        elif rule.rule_type == 'consistency_check':
            return self._apply_consistency_check(rule, reading, parameters, context)
        elif rule.rule_type == 'seasonal_check':
            return self._apply_seasonal_check(rule, reading, parameters, context)
        elif rule.rule_type == 'peer_comparison':
            return self._apply_peer_comparison(rule, reading, parameters, context)
        elif rule.rule_type == 'trend_analysis':
            return self._apply_trend_analysis(rule, reading, parameters, context)
        elif rule.rule_type == 'missing_data':
            return self._apply_missing_data_check(rule, reading, parameters, context)
        elif rule.rule_type == 'invalid_datetime':
            return self._apply_invalid_datetime_check(rule, reading, parameters, context)
        else:
            return RuleResult(passed=True, warnings=[f"Unknown rule type: {rule.rule_type}"])
    
    def _apply_range_check(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any]
    ) -> 'RuleResult':
        """Apply range check validation rule"""
        min_value = Decimal(str(parameters.get('min_value', 0)))
        max_value = Decimal(str(parameters.get('max_value', 999999)))
        
        if reading.kwh < min_value:
            return RuleResult(
                passed=False,
                warnings=[f"Reading {reading.kwh} below minimum {min_value}"]
            )
        
        if reading.kwh > max_value:
            return RuleResult(
                passed=False,
                warnings=[f"Reading {reading.kwh} above maximum {max_value}"]
            )
        
        return RuleResult(passed=True)
    
    def _apply_spike_detection(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply spike detection validation rule"""
        # Get historical readings for comparison
        historical_readings = self._get_historical_readings(
            reading.icp_id, 
            reading.register_code,
            reading.read_at,
            context.tenant,
            days_back=parameters.get('days_back', 30)
        )
        
        if not historical_readings:
            return RuleResult(passed=True, warnings=["No historical data for spike detection"])
        
        # Calculate average and standard deviation
        values = [r.kwh for r in historical_readings]
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** Decimal('0.5')
        
        # Check for spike
        spike_threshold = parameters.get('spike_threshold', 3)  # Standard deviations
        if abs(reading.kwh - avg) > std_dev * spike_threshold:
            return RuleResult(
                passed=False,
                warnings=[f"Reading {reading.kwh} is {abs(reading.kwh - avg)/std_dev:.1f} std devs from average {avg}"]
            )
        
        return RuleResult(passed=True)
    
    def _apply_continuity_check(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply continuity check validation rule"""
        # Check for gaps in time series
        expected_interval = parameters.get('expected_interval_minutes', 30)
        
        # Get previous reading
        previous_reading = self._get_previous_reading(
            reading.icp_id,
            reading.register_code,
            reading.read_at,
            context.tenant
        )
        
        if not previous_reading:
            return RuleResult(passed=True, warnings=["No previous reading for continuity check"])
        
        # Check time gap
        time_diff = reading.read_at - previous_reading.read_at
        expected_diff = timedelta(minutes=expected_interval)
        
        if time_diff > expected_diff * 2:  # Allow some tolerance
            return RuleResult(
                passed=False,
                warnings=[f"Gap of {time_diff} detected (expected {expected_diff})"]
            )
        
        return RuleResult(passed=True)
    
    def _apply_consistency_check(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply consistency check validation rule"""
        # Check consistency across registers for same ICP
        consistency_threshold = parameters.get('consistency_threshold', 0.1)  # 10%
        
        # Get concurrent readings for other registers
        concurrent_readings = self._get_concurrent_readings(
            reading.icp_id,
            reading.read_at,
            context.tenant,
            exclude_register=reading.register_code
        )
        
        if not concurrent_readings:
            return RuleResult(passed=True)
        
        # Simple consistency check: compare ratios
        total_other = sum(r.kwh for r in concurrent_readings)
        if total_other > 0:
            ratio = reading.kwh / total_other
            expected_ratio = parameters.get('expected_ratio', 1.0)
            
            if abs(ratio - expected_ratio) > consistency_threshold:
                return RuleResult(
                    passed=False,
                    warnings=[f"Inconsistent ratio {ratio:.2f} (expected ~{expected_ratio})"]
                )
        
        return RuleResult(passed=True)
    
    def _apply_seasonal_check(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply seasonal check validation rule"""
        # Get seasonal profile
        profile_code = parameters.get('profile_code', 'default_seasonal')
        profile = context.estimation_profiles.get(profile_code)
        
        if not profile:
            return RuleResult(passed=True, warnings=["No seasonal profile available"])
        
        # Extract seasonal data
        seasonal_data = profile.profile_data.get('seasonal_patterns', {})
        month_key = str(reading.read_at.month)
        
        if month_key not in seasonal_data:
            return RuleResult(passed=True)
        
        # Check against seasonal bounds
        seasonal_min = Decimal(str(seasonal_data[month_key].get('min', 0)))
        seasonal_max = Decimal(str(seasonal_data[month_key].get('max', 999999)))
        
        if not (seasonal_min <= reading.kwh <= seasonal_max):
            return RuleResult(
                passed=False,
                warnings=[f"Reading {reading.kwh} outside seasonal range [{seasonal_min}, {seasonal_max}]"]
            )
        
        return RuleResult(passed=True)
    
    def _apply_peer_comparison(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply peer comparison validation rule"""
        # Get peer readings (similar ICPs)
        peer_readings = self._get_peer_readings(
            reading.icp_id,
            reading.register_code,
            reading.read_at,
            context.tenant,
            parameters
        )
        
        if len(peer_readings) < parameters.get('min_peers', 5):
            return RuleResult(passed=True, warnings=["Insufficient peer data"])
        
        # Calculate peer statistics
        peer_values = [r.kwh for r in peer_readings]
        peer_avg = sum(peer_values) / len(peer_values)
        peer_std = (sum((x - peer_avg) ** 2 for x in peer_values) / len(peer_values)) ** Decimal('0.5')
        
        # Check deviation from peers
        deviation_threshold = parameters.get('deviation_threshold', 2.0)
        if abs(reading.kwh - peer_avg) > peer_std * deviation_threshold:
            return RuleResult(
                passed=False,
                warnings=[f"Reading {reading.kwh} deviates {abs(reading.kwh - peer_avg)/peer_std:.1f} std devs from peers"]
            )
        
        return RuleResult(passed=True)
    
    def _apply_trend_analysis(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply trend analysis validation rule"""
        # Get recent readings for trend analysis
        recent_readings = self._get_historical_readings(
            reading.icp_id,
            reading.register_code,
            reading.read_at,
            context.tenant,
            days_back=parameters.get('trend_days', 7)
        )
        
        if len(recent_readings) < 3:
            return RuleResult(passed=True, warnings=["Insufficient data for trend analysis"])
        
        # Simple trend analysis: check if reading fits the trend
        # TODO: Implement more sophisticated trend analysis
        values = [r.kwh for r in recent_readings]
        trend_tolerance = parameters.get('trend_tolerance', 0.5)
        
        # Calculate simple moving average
        if len(values) >= 3:
            recent_avg = sum(values[-3:]) / 3
            if abs(reading.kwh - recent_avg) > recent_avg * trend_tolerance:
                return RuleResult(
                    passed=False,
                    warnings=[f"Reading {reading.kwh} breaks trend (recent avg: {recent_avg})"]
                )
        
        return RuleResult(passed=True)
    
    def _apply_missing_data_check(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply missing data check validation rule"""
        # Check for missing intervals
        expected_interval = parameters.get('expected_interval_minutes', 30)
        
        # Get readings around this time
        time_window = timedelta(minutes=expected_interval * 2)
        start_time = reading.read_at - time_window
        end_time = reading.read_at + time_window
        
        nearby_readings = self._get_readings_in_range(
            reading.icp_id,
            reading.register_code,
            start_time,
            end_time,
            context.tenant
        )
        
        expected_count = int((end_time - start_time).total_seconds() / (expected_interval * 60))
        actual_count = len(nearby_readings)
        
        missing_threshold = parameters.get('missing_threshold', 0.8)  # 80% completeness
        if actual_count < expected_count * missing_threshold:
            return RuleResult(
                passed=False,
                warnings=[f"Missing data: {actual_count}/{expected_count} readings in time window"]
            )
        
        return RuleResult(passed=True)
    
    def _apply_invalid_datetime_check(
        self, 
        rule: ValidationRule, 
        reading: ReadingData, 
        parameters: Dict[str, Any],
        context: ValidationContext
    ) -> 'RuleResult':
        """Apply invalid datetime check validation rule"""
        logging.info(f"Running invalid datetime check for meter {reading.icp_id}")
        results = []

        # 1. Check for future dates
        now = datetime.now()
        if reading.read_at > now:
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Future Timestamp',
                    details=f"Timestamp {reading.read_at} is in the future."
                )
            )

        # 2. Check for duplicate timestamps
        duplicates = self._get_readings_in_range(
            reading.icp_id,
            reading.register_code,
            reading.read_at - timedelta(minutes=1),
            reading.read_at + timedelta(minutes=1),
            context.tenant
        )
        if len(duplicates) > 1:
            # Report one failure for the entire set of duplicates
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Duplicate Timestamp',
                    details=f"Found {len(duplicates) - 1} duplicate timestamps. First duplicate at {duplicates[1].read_at}"
                )
            )

        # 3. Check for out-of-range timestamps
        # This requires a defined valid range, which is not yet specified.
        # Placeholder for this logic.

        if not results:
            logging.info(f"Invalid datetime check passed for meter {reading.icp_id}")
            results.append(ValidationResult(status='pass', rule_name='Invalid Datetime Check'))

        return RuleResult(passed=True, warnings=results)
    
    def _estimate_reading(
        self, 
        reading: ReadingData, 
        method: Optional[str], 
        context: ValidationContext
    ) -> Optional['EstimationResult']:
        """Estimate a reading value using specified method"""
        if not method:
            return None
        
        estimation_method = EstimationMethod(method)
        
        if estimation_method == EstimationMethod.HISTORICAL_AVERAGE:
            return self._estimate_historical_average(reading, context)
        elif estimation_method == EstimationMethod.LINEAR_INTERPOLATION:
            return self._estimate_linear_interpolation(reading, context)
        elif estimation_method == EstimationMethod.SEASONAL_PROFILE:
            return self._estimate_seasonal_profile(reading, context)
        elif estimation_method == EstimationMethod.PEER_AVERAGE:
            return self._estimate_peer_average(reading, context)
        elif estimation_method == EstimationMethod.ZERO_FILL:
            return EstimationResult(Decimal('0'), estimation_method, Decimal('50'))
        elif estimation_method == EstimationMethod.CARRY_FORWARD:
            return self._estimate_carry_forward(reading, context)
        
        return None
    
    def _estimate_historical_average(
        self, 
        reading: ReadingData, 
        context: ValidationContext
    ) -> Optional['EstimationResult']:
        """Estimate using historical average"""
        historical_readings = self._get_historical_readings(
            reading.icp_id,
            reading.register_code,
            reading.read_at,
            context.tenant,
            days_back=30
        )
        
        if not historical_readings:
            return None
        
        # Calculate average
        avg_value = sum(r.kwh for r in historical_readings) / len(historical_readings)
        confidence = min(Decimal('95'), Decimal(str(len(historical_readings) * 2)))
        
        return EstimationResult(avg_value, EstimationMethod.HISTORICAL_AVERAGE, confidence)
    
    def _estimate_linear_interpolation(
        self, 
        reading: ReadingData, 
        context: ValidationContext
    ) -> Optional['EstimationResult']:
        """Estimate using linear interpolation"""
        # Get previous and next readings
        prev_reading = self._get_previous_reading(
            reading.icp_id, reading.register_code, reading.read_at, context.tenant
        )
        next_reading = self._get_next_reading(
            reading.icp_id, reading.register_code, reading.read_at, context.tenant
        )
        
        if not prev_reading or not next_reading:
            return None
        
        # Linear interpolation
        time_diff = (next_reading.read_at - prev_reading.read_at).total_seconds()
        target_diff = (reading.read_at - prev_reading.read_at).total_seconds()
        
        if time_diff == 0:
            return None
        
        ratio = Decimal(str(target_diff / time_diff))
        interpolated_value = prev_reading.kwh + (next_reading.kwh - prev_reading.kwh) * ratio
        
        return EstimationResult(interpolated_value, EstimationMethod.LINEAR_INTERPOLATION, Decimal('80'))
    
    def _estimate_seasonal_profile(
        self, 
        reading: ReadingData, 
        context: ValidationContext
    ) -> Optional['EstimationResult']:
        """Estimate using seasonal profile"""
        # Find appropriate profile
        profile = None
        for p in context.estimation_profiles.values():
            if p.tariff_group == context.tariff_register_map.get(reading.register_code, {}).tariff_group:
                profile = p
                break
        
        if not profile:
            return None
        
        # Get seasonal value
        seasonal_data = profile.profile_data.get('seasonal_patterns', {})
        month_key = str(reading.read_at.month)
        
        if month_key not in seasonal_data:
            return None
        
        seasonal_avg = Decimal(str(seasonal_data[month_key].get('average', 0)))
        confidence = Decimal(str(seasonal_data[month_key].get('confidence', 70)))
        
        return EstimationResult(seasonal_avg, EstimationMethod.SEASONAL_PROFILE, confidence)
    
    def _estimate_peer_average(
        self, 
        reading: ReadingData, 
        context: ValidationContext
    ) -> Optional['EstimationResult']:
        """Estimate using peer average"""
        peer_readings = self._get_peer_readings(
            reading.icp_id,
            reading.register_code,
            reading.read_at,
            context.tenant,
            {'min_peers': 3}
        )
        
        if len(peer_readings) < 3:
            return None
        
        peer_avg = sum(r.kwh for r in peer_readings) / len(peer_readings)
        confidence = min(Decimal('90'), Decimal(str(len(peer_readings) * 10)))
        
        return EstimationResult(peer_avg, EstimationMethod.PEER_AVERAGE, confidence)
    
    def _estimate_carry_forward(
        self, 
        reading: ReadingData, 
        context: ValidationContext
    ) -> Optional['EstimationResult']:
        """Estimate using carry forward"""
        prev_reading = self._get_previous_reading(
            reading.icp_id, reading.register_code, reading.read_at, context.tenant
        )
        
        if not prev_reading:
            return None
        
        return EstimationResult(prev_reading.kwh, EstimationMethod.CARRY_FORWARD, Decimal('60'))
    
    def _calculate_quality_score(self, reading: ReadingData) -> Decimal:
        """Calculate quality score for a reading"""
        base_score = Decimal('100')
        
        # Deduct points for failed rules
        critical_failures = len([r for r in reading.failed_rules if r.endswith('_critical')])
        warning_failures = len([r for r in reading.failed_rules if r.endswith('_warning')])
        
        base_score -= critical_failures * 30
        base_score -= warning_failures * 10
        
        # Deduct points for estimation
        if reading.is_estimated:
            base_score -= 20
            if reading.estimation_confidence:
                base_score += (reading.estimation_confidence - 50) / 10
        
        return max(Decimal('0'), base_score)
    
    # Helper methods for database queries
    def _get_historical_readings(
        self, 
        icp_id: str, 
        register_code: str, 
        read_at: datetime, 
        tenant: Tenant,
        days_back: int = 30
    ) -> List[Any]:
        """Get historical readings for validation"""
        start_date = read_at - timedelta(days=days_back)
        return list(
            MeterCalcInterval.objects.filter(
                tenant=tenant,
                icp_id=icp_id,
                register_code=register_code,
                read_at__gte=start_date,
                read_at__lt=read_at
            ).order_by('-read_at')
        )
    
    def _get_previous_reading(
        self, 
        icp_id: str, 
        register_code: str, 
        read_at: datetime, 
        tenant: Tenant
    ) -> Optional[Any]:
        """Get previous reading"""
        return MeterCalcInterval.objects.filter(
            tenant=tenant,
            icp_id=icp_id,
            register_code=register_code,
            read_at__lt=read_at
        ).order_by('-read_at').first()
    
    def _get_next_reading(
        self, 
        icp_id: str, 
        register_code: str, 
        read_at: datetime, 
        tenant: Tenant
    ) -> Optional[Any]:
        """Get next reading"""
        return MeterCalcInterval.objects.filter(
            tenant=tenant,
            icp_id=icp_id,
            register_code=register_code,
            read_at__gt=read_at
        ).order_by('read_at').first()
    
    def _get_concurrent_readings(
        self, 
        icp_id: str, 
        read_at: datetime, 
        tenant: Tenant,
        exclude_register: str = ""
    ) -> List[Any]:
        """Get concurrent readings for other registers"""
        return list(
            MeterCalcInterval.objects.filter(
                tenant=tenant,
                icp_id=icp_id,
                read_at=read_at
            ).exclude(register_code=exclude_register)
        )
    
    def _get_peer_readings(
        self, 
        icp_id: str, 
        register_code: str, 
        read_at: datetime, 
        tenant: Tenant,
        parameters: Dict[str, Any]
    ) -> List[Any]:
        """Get peer readings for comparison"""
        # This is a simplified example. A real implementation would need
        # to identify a peer group based on location, consumption patterns, etc.
        return list(
            MeterCalcInterval.objects.filter(
                tenant=tenant,
                register_code=register_code,
                read_at=read_at
            ).exclude(icp_id=icp_id)[:parameters.get('peer_group_size', 20)]
        )
    
    def _get_readings_in_range(
        self, 
        icp_id: str, 
        register_code: str, 
        start_time: datetime, 
        end_time: datetime, 
        tenant: Tenant
    ) -> List[Any]:
        """Get readings in time range"""
        return list(
            MeterCalcInterval.objects.filter(
                tenant=tenant,
                icp_id=icp_id,
                register_code=register_code,
                read_at__gte=start_time,
                read_at__lte=end_time
            )
        )
    
    def _create_validation_result(
        self, 
        reading: ReadingData, 
        batch: ValidationBatch
    ) -> ValidationResult:
        """Create ValidationResult from validated reading"""
        return ValidationResult.objects.create(
            batch=batch,
            icp_id=reading.icp_id,
            register_code=reading.register_code,
            read_at=reading.read_at,
            original_kwh=reading.kwh,
            original_status=reading.raw_status,
            final_kwh=reading.final_kwh,
            final_status=reading.final_status.value,
            is_estimated=reading.is_estimated,
            estimation_method=reading.estimation_method.value if reading.estimation_method else "",
            estimation_confidence=reading.estimation_confidence,
            rule_fail_mask=reading.rule_fail_mask,
            failed_rules=reading.failed_rules,
            warnings=reading.warnings,
            validation_notes=reading.validation_notes,
            processing_time_ms=reading.processing_time_ms
        )
    
    def _update_batch_statistics(
        self, 
        batch: ValidationBatch, 
        results: List[ValidationResult]
    ):
        """Update batch statistics"""
        batch.valid_readings = len([r for r in results if r.final_status == 'valid'])
        batch.invalid_readings = len([r for r in results if r.final_status == 'invalid'])
        batch.estimated_readings = len([r for r in results if r.is_estimated])
        batch.save()


@dataclass
class RuleResult:
    """Result of applying a validation rule"""
    passed: bool
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EstimationResult:
    """Result of estimation process"""
    value: Decimal
    method: EstimationMethod
    confidence: Decimal
    metadata: Dict[str, Any] = field(default_factory=dict)


    def validate_hhr(self, meter_id, data):
        """
        Run all HHR validation checks based on the provided policy.
        
        Args:
            meter_id (int): The ID of the meter to validate.
            data (pd.DataFrame): DataFrame with 'timestamp' and 'value' columns.
        
        Returns:
            list: A list of ValidationResult objects.
        """
        logging.info(f"Starting HHR validation for meter {meter_id}")
        results = []

        # Execute all validation checks
        results.extend(self.check_missing_values(meter_id, data))
        results.extend(self.check_unexpected_zero_values(meter_id, data))
        results.extend(self.check_high_values(meter_id, data))
        results.extend(self.check_negative_values(meter_id, data))
        results.extend(self.check_abnormal_trends(meter_id, data))
        results.extend(self.check_invalid_datetime(meter_id, data))
        results.extend(self.check_daily_sum_thresholds(meter_id, data))
        results.extend(self.check_monthly_sum_variance(meter_id, data))

        # Here, we would save the results to the database
        # For now, just logging them.
        for result in results:
            if result.status == 'fail':
                logging.warning(f"Validation failed for meter {meter_id}: {result.rule.name} - {result.details}")
        
        return results

    def check_missing_values(self, meter_id, data):
        """Clause 3.1: Check for missing intervals."""
        logging.info(f"Running missing values check for meter {meter_id}")
        results = []
        
        # Assume 30-minute intervals for now. This should be configurable.
        expected_interval = timedelta(minutes=30)
        
        # Sort by timestamp just in case
        data = data.sort_values(by='timestamp').reset_index(drop=True)
        
        time_diffs = data['timestamp'].diff()
        
        # The first diff is always NaT, so we skip it
        missing = time_diffs[time_diffs > expected_interval]
        
        for index, diff in missing.items():
            prev_timestamp = data['timestamp'][index - 1]
            num_missing = (diff / expected_interval) - 1
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Missing Interval',
                    details=f"Detected {int(num_missing)} missing intervals after {prev_timestamp}."
                )
            )

        if not results:
            logging.info(f"Missing values check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='Missing Interval Check'))
            
        return results

    def check_unexpected_zero_values(self, meter_id, data):
        """Clause 3.2: Check for unexpected zero consumption, which may indicate a bridged meter."""
        logging.info(f"Running unexpected zero values check for meter {meter_id}")
        results = []

        # A simple check is to see if a whole day has zero consumption.
        # A more advanced check could look for long consecutive strings of zero-value intervals.
        daily_sums = data.set_index('timestamp').resample('D')['value'].sum()

        zero_value_days = daily_sums[daily_sums == 0]

        for day, total in zero_value_days.items():
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Unexpected Zero Value',
                    details=f"Day {day.date()} has zero total consumption, which may indicate a bridged meter."
                )
            )

        if not results:
            logging.info(f"Unexpected zero values check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='Unexpected Zero Value Check'))

        return results

    def check_high_values(self, meter_id, data):
        """Clause 3.3: Check for values exceeding high value thresholds."""
        logging.info(f"Running high value check for meter {meter_id}")
        results = []
        
        # Thresholds (to be made configurable later)
        INTERVAL_HIGH_VALUE_THRESHOLD = 100  # kWh
        DAILY_HIGH_VALUE_THRESHOLD = 1500    # kWh

        # 1. Check interval high values
        high_value_intervals = data[data['value'] > INTERVAL_HIGH_VALUE_THRESHOLD]
        for index, row in high_value_intervals.iterrows():
            # This would create a ValidationResult object
            # from a ValidationRule model instance
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Interval High Value',
                    details=f"Interval at {row['timestamp']} has value {row['value']} kWh, which exceeds the threshold of {INTERVAL_HIGH_VALUE_THRESHOLD} kWh."
                )
            )

        # 2. Check daily high values
        daily_sum = data.set_index('timestamp').resample('D')['value'].sum()
        high_value_days = daily_sum[daily_sum > DAILY_HIGH_VALUE_THRESHOLD]

        for day, total in high_value_days.items():
             results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Daily High Value',
                    details=f"Day {day.date()} has total consumption {total} kWh, which exceeds the threshold of {DAILY_HIGH_VALUE_THRESHOLD} kWh."
                )
            )
            
        if not results:
            logging.info(f"High value check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='High Value Check'))
            
        return results

    def check_negative_values(self, meter_id, data):
        """Clause 3.4: Check for negative values based on meter type."""
        logging.info(f"Running negative value check for meter {meter_id}")
        results = []

        # This logic should be enhanced to check meter type (import/export)
        # For now, assuming import meters where negative values are invalid.
        negative_values = data[data['value'] < 0]

        for index, row in negative_values.iterrows():
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Negative Value',
                    details=f"Interval at {row['timestamp']} has negative value {row['value']} kWh."
                )
            )

        if not results:
            logging.info(f"Negative value check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='Negative Value Check'))

        return results

    def check_abnormal_trends(self, meter_id, data):
        """Clause 3.5: Check for abnormal daily sum deviation."""
        logging.info(f"Running abnormal trend check for meter {meter_id}")
        results = []

        # Threshold (to be made configurable)
        ABNORMAL_TREND_THRESHOLD = 4.0  # 400%

        daily_sums = data.set_index('timestamp').resample('D')['value'].sum()

        # Need at least two days to compare
        if len(daily_sums) < 2:
            logging.info("Not enough data for abnormal trend check.")
            return [ValidationResult(status='pass', rule_name='Abnormal Trend Check')]

        # Compare each day to the previous one
        previous_day_sum = daily_sums.iloc[0]
        for day, current_day_sum in daily_sums.items():
            if day == daily_sums.index[0]:
                continue # Skip the first day

            if previous_day_sum > 0: # Avoid division by zero
                deviation = abs(current_day_sum - previous_day_sum) / previous_day_sum
                if deviation > ABNORMAL_TREND_THRESHOLD:
                    results.append(
                        ValidationResult(
                            status='fail',
                            rule_name='Abnormal Trend',
                            details=f"Abnormal trend detected for {day.date()}. Daily sum changed by {deviation:.1%} from previous day."
                        )
                    )
            
            previous_day_sum = current_day_sum

        if not results:
            logging.info(f"Abnormal trend check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='Abnormal Trend Check'))
        
        return results

    def check_invalid_datetime(self, meter_id, data):
        """Clause 3.6: Check for invalid timestamps or duplicates."""
        logging.info(f"Running invalid datetime check for meter {meter_id}")
        results = []

        # 1. Check for future dates
        now = datetime.now()
        future_dates = data[data['timestamp'] > now]
        for index, row in future_dates.iterrows():
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Future Timestamp',
                    details=f"Timestamp {row['timestamp']} is in the future."
                )
            )

        # 2. Check for duplicate timestamps
        duplicates = data[data.duplicated(subset=['timestamp'], keep=False)]
        if not duplicates.empty:
            # Report one failure for the entire set of duplicates
            results.append(
                ValidationResult(
                    status='fail',
                    rule_name='Duplicate Timestamp',
                    details=f"Found {len(duplicates) - 1} duplicate timestamps. First duplicate at {duplicates.iloc[0]['timestamp']}"
                )
            )

        # 3. Check for out-of-range timestamps
        # This requires a defined valid range, which is not yet specified.
        # Placeholder for this logic.

        if not results:
            logging.info(f"Invalid datetime check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='Invalid Datetime Check'))

        return results

    def check_daily_sum_thresholds(self, meter_id, data):
        """Clause 3.7: Check daily sum against thresholds."""
        logging.info(f"Running daily sum threshold check for meter {meter_id}")
        results = []

        # Thresholds (to be made configurable)
        DAILY_SUM_MIN_THRESHOLD = 0      # kWh
        DAILY_SUM_MAX_THRESHOLD = 10000  # kWh

        daily_sums = data.set_index('timestamp').resample('D')['value'].sum()

        for day, total in daily_sums.items():
            if not (DAILY_SUM_MIN_THRESHOLD <= total <= DAILY_SUM_MAX_THRESHOLD):
                results.append(
                    ValidationResult(
                        status='fail',
                        rule_name='Daily Sum Threshold',
                        details=f"Day {day.date()} has total consumption {total} kWh, which is outside the acceptable range of {DAILY_SUM_MIN_THRESHOLD}-{DAILY_SUM_MAX_THRESHOLD} kWh."
                    )
                )

        if not results:
            logging.info(f"Daily sum threshold check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='Daily Sum Threshold Check'))
            
        return results

    def check_monthly_sum_variance(self, meter_id, data):
        """Clause 3.8: Check monthly sum variance."""
        logging.info(f"Running monthly sum variance check for meter {meter_id}")
        results = []

        # Threshold (to be made configurable)
        MONTHLY_SUM_VARIANCE_THRESHOLD = 5.0  # 500%

        # This check requires historical data. For now, we'll work with the provided data.
        monthly_sums = data.set_index('timestamp').resample('M')['value'].sum()

        if len(monthly_sums) < 2:
            logging.info("Not enough data for monthly sum variance check.")
            return [ValidationResult(status='pass', rule_name='Monthly Sum Variance Check')]

        previous_month_sum = monthly_sums.iloc[0]
        for month, current_month_sum in monthly_sums.items():
            if month == monthly_sums.index[0]:
                continue # Skip first month
            
            if previous_month_sum > 0:
                variance = abs(current_month_sum - previous_month_sum) / previous_month_sum
                if variance > MONTHLY_SUM_VARIANCE_THRESHOLD:
                    results.append(
                        ValidationResult(
                            status='fail',
                            rule_name='Monthly Sum Variance',
                            details=f"Monthly sum for {month.strftime('%Y-%m')} changed by {variance:.1%} from previous month."
                        )
                    )
            
            previous_month_sum = current_month_sum
        
        if not results:
            logging.info(f"Monthly sum variance check passed for meter {meter_id}")
            results.append(ValidationResult(status='pass', rule_name='Monthly Sum Variance Check'))

        return results


    def estimate_hhr(self, meter_id, data):
        """
        Run estimation logic based on the HHR Estimation Policy.

        Args:
            meter_id (int): The ID of the meter.
            data (pd.DataFrame): DataFrame with missing values to be estimated.
        
        Returns:
            pd.DataFrame: DataFrame with estimated values filled in.
        """
        logging.info(f"Starting HHR estimation for meter {meter_id}")
        
        # Ensure data is a dataframe and has the expected columns
        if not isinstance(data, pd.DataFrame) or not {'timestamp', 'value'}.issubset(data.columns):
            raise ValueError("Data must be a pandas DataFrame with 'timestamp' and 'value' columns.")

        # Sort by timestamp and set as index
        data = data.sort_values(by='timestamp').set_index('timestamp')
        
        # 1. Interpolation for small gaps (fewer than 4 trading periods)
        # A gap of < 4 periods means at most 3 consecutive NaNs.
        estimated_data = data.interpolate(method='linear', limit=3, limit_direction='both')

        # 2. Copy from previous patterns (placeholder)
        if estimated_data['value'].isnull().any():
            logging.info("Gaps remaining after interpolation. Pattern matching to be implemented.")

        # 3. Average consumption value (placeholder)

        # 4. General consumption profile (placeholder)
        
        return estimated_data.reset_index()


    def validate_nhh(self, meter_id):
        # ... (to be implemented later)
        logging.info(f"Running NHH validation for meter {meter_id}...")
        return "Validated" 