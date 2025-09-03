"""
Plausibility Check Engine for Meter Data

This module implements basic plausibility checks to identify potentially invalid
meter readings before comprehensive validation. These checks flag obvious data
quality issues for further processing.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from energy.metering.timescale_models import MeterRawInterval, MeterRawDaily
from users.models import Tenant

logger = logging.getLogger(__name__)


class PlausibilityFlag(Enum):
    """Plausibility check flags"""
    MISSING_VALUE = 'missing_value'
    ZERO_VALUE = 'zero_value'
    HIGH_VALUE = 'high_value'
    NEGATIVE_VALUE = 'negative_value'
    FUTURE_DATE = 'future_date'
    DUPLICATE_READING = 'duplicate_reading'
    INVALID_TIMESTAMP = 'invalid_timestamp'
    EXTREME_VARIANCE = 'extreme_variance'


@dataclass
class PlausibilityResult:
    """Result of plausibility checks"""
    icp_id: str
    register_code: str
    read_at: datetime
    original_kwh: Optional[Decimal]
    flags: Set[PlausibilityFlag] = field(default_factory=set)
    warnings: List[str] = field(default_factory=list)
    severity: str = 'info'  # info, warning, error
    requires_review: bool = False
    
    def add_flag(self, flag: PlausibilityFlag, message: str, severity: str = 'warning'):
        """Add a plausibility flag with message"""
        self.flags.add(flag)
        self.warnings.append(message)
        
        # Update severity (error > warning > info)
        if severity == 'error' or (severity == 'warning' and self.severity == 'info'):
            self.severity = severity
            
        if severity == 'error':
            self.requires_review = True


class PlausibilityEngine:
    """Engine for performing plausibility checks on meter data"""
    
    def __init__(self):
        # Configurable thresholds
        self.interval_high_threshold = Decimal('100.0')  # kWh per 30-min interval
        self.daily_high_threshold = Decimal('1500.0')    # kWh per day
        self.zero_tolerance_hours = 24  # Hours of zero readings before flagging
        self.future_tolerance_minutes = 60  # Minutes in future allowed
        
    def check_interval_readings(self, readings: List[MeterRawInterval]) -> List[PlausibilityResult]:
        """
        Perform plausibility checks on interval readings
        """
        results = []
        
        for reading in readings:
            result = PlausibilityResult(
                icp_id=reading.icp_id,
                register_code=reading.register_code,
                read_at=reading.read_at,
                original_kwh=reading.kwh
            )
            
            # Check for missing values
            if reading.kwh is None:
                result.add_flag(
                    PlausibilityFlag.MISSING_VALUE,
                    "Missing kWh value",
                    'error'
                )
            else:
                # Check for negative values
                if reading.kwh < 0:
                    result.add_flag(
                        PlausibilityFlag.NEGATIVE_VALUE,
                        f"Negative consumption: {reading.kwh} kWh",
                        'error'
                    )
                
                # Check for zero values
                if reading.kwh == 0:
                    result.add_flag(
                        PlausibilityFlag.ZERO_VALUE,
                        "Zero consumption detected",
                        'warning'
                    )
                
                # Check for high values
                if reading.kwh > self.interval_high_threshold:
                    result.add_flag(
                        PlausibilityFlag.HIGH_VALUE,
                        f"High consumption: {reading.kwh} kWh (threshold: {self.interval_high_threshold})",
                        'warning'
                    )
            
            # Check for future dates
            if reading.read_at > timezone.now() + timedelta(minutes=self.future_tolerance_minutes):
                result.add_flag(
                    PlausibilityFlag.FUTURE_DATE,
                    f"Future timestamp: {reading.read_at}",
                    'error'
                )
            
            # Check for invalid timestamps (e.g., not on 30-minute boundaries)
            if reading.read_at.minute % 30 != 0 or reading.read_at.second != 0:
                result.add_flag(
                    PlausibilityFlag.INVALID_TIMESTAMP,
                    f"Invalid timestamp for interval data: {reading.read_at}",
                    'warning'
                )
            
            results.append(result)
        
        # Check for duplicates across all readings
        self._check_duplicates(results)
        
        return results
    
    def check_daily_readings(self, readings: List[MeterRawDaily]) -> List[PlausibilityResult]:
        """
        Perform plausibility checks on daily readings
        """
        results = []
        
        for reading in readings:
            result = PlausibilityResult(
                icp_id=reading.icp_id,
                register_code=reading.register_code,
                read_at=datetime.combine(reading.read_date, datetime.min.time()),
                original_kwh=reading.kwh
            )
            
            # Check for missing values
            if reading.kwh is None:
                result.add_flag(
                    PlausibilityFlag.MISSING_VALUE,
                    "Missing kWh value",
                    'error'
                )
            else:
                # Check for negative values
                if reading.kwh < 0:
                    result.add_flag(
                        PlausibilityFlag.NEGATIVE_VALUE,
                        f"Negative consumption: {reading.kwh} kWh",
                        'error'
                    )
                
                # Check for zero values
                if reading.kwh == 0:
                    result.add_flag(
                        PlausibilityFlag.ZERO_VALUE,
                        "Zero consumption detected",
                        'warning'
                    )
                
                # Check for high values
                if reading.kwh > self.daily_high_threshold:
                    result.add_flag(
                        PlausibilityFlag.HIGH_VALUE,
                        f"High consumption: {reading.kwh} kWh (threshold: {self.daily_high_threshold})",
                        'warning'
                    )
            
            # Check for future dates
            if reading.read_date > timezone.now().date():
                result.add_flag(
                    PlausibilityFlag.FUTURE_DATE,
                    f"Future date: {reading.read_date}",
                    'error'
                )
            
            results.append(result)
        
        # Check for duplicates across all readings
        self._check_duplicates(results)
        
        return results
    
    def check_consecutive_zeros(self, readings: List[MeterRawInterval]) -> List[PlausibilityResult]:
        """
        Check for consecutive zero readings that might indicate meter issues
        """
        results = []
        
        # Group readings by meter
        meter_readings = {}
        for reading in readings:
            key = (reading.icp_id, reading.register_code)
            if key not in meter_readings:
                meter_readings[key] = []
            meter_readings[key].append(reading)
        
        # Check each meter for consecutive zeros
        for (icp_id, register_code), meter_data in meter_readings.items():
            # Sort by timestamp
            meter_data.sort(key=lambda x: x.read_at)
            
            zero_count = 0
            zero_start = None
            
            for reading in meter_data:
                if reading.kwh == 0:
                    if zero_count == 0:
                        zero_start = reading.read_at
                    zero_count += 1
                else:
                    # Check if we had a significant run of zeros
                    if zero_count > 0:
                        zero_duration_hours = zero_count * 0.5  # 30-minute intervals
                        if zero_duration_hours >= self.zero_tolerance_hours:
                            result = PlausibilityResult(
                                icp_id=icp_id,
                                register_code=register_code,
                                read_at=zero_start,
                                original_kwh=Decimal('0')
                            )
                            result.add_flag(
                                PlausibilityFlag.ZERO_VALUE,
                                f"Consecutive zero readings for {zero_duration_hours} hours",
                                'warning'
                            )
                            results.append(result)
                    
                    zero_count = 0
                    zero_start = None
            
            # Check if we ended with zeros
            if zero_count > 0:
                zero_duration_hours = zero_count * 0.5
                if zero_duration_hours >= self.zero_tolerance_hours:
                    result = PlausibilityResult(
                        icp_id=icp_id,
                        register_code=register_code,
                        read_at=zero_start,
                        original_kwh=Decimal('0')
                    )
                    result.add_flag(
                        PlausibilityFlag.ZERO_VALUE,
                        f"Consecutive zero readings for {zero_duration_hours} hours (ongoing)",
                        'warning'
                    )
                    results.append(result)
        
        return results
    
    def check_extreme_variance(self, readings: List[MeterRawInterval]) -> List[PlausibilityResult]:
        """
        Check for extreme variance in consumption patterns
        """
        results = []
        
        # Group readings by meter and sort by time
        meter_readings = {}
        for reading in readings:
            key = (reading.icp_id, reading.register_code)
            if key not in meter_readings:
                meter_readings[key] = []
            meter_readings[key].append(reading)
        
        for (icp_id, register_code), meter_data in meter_readings.items():
            meter_data.sort(key=lambda x: x.read_at)
            
            # Check for extreme jumps between consecutive readings
            for i in range(1, len(meter_data)):
                current = meter_data[i]
                previous = meter_data[i-1]
                
                if current.kwh is None or previous.kwh is None:
                    continue
                
                # Skip if readings are not consecutive (more than 1 hour apart)
                time_diff = current.read_at - previous.read_at
                if time_diff > timedelta(hours=1):
                    continue
                
                # Calculate variance
                if previous.kwh > 0:
                    variance_ratio = abs(current.kwh - previous.kwh) / previous.kwh
                    
                    # Flag extreme variance (>1000% change)
                    if variance_ratio > 10:
                        result = PlausibilityResult(
                            icp_id=icp_id,
                            register_code=register_code,
                            read_at=current.read_at,
                            original_kwh=current.kwh
                        )
                        result.add_flag(
                            PlausibilityFlag.EXTREME_VARIANCE,
                            f"Extreme variance: {variance_ratio:.1%} change from {previous.kwh} to {current.kwh}",
                            'warning'
                        )
                        results.append(result)
        
        return results
    
    def _check_duplicates(self, results: List[PlausibilityResult]):
        """
        Check for duplicate readings (same meter, register, timestamp)
        """
        seen_readings = set()
        
        for result in results:
            reading_key = (result.icp_id, result.register_code, result.read_at)
            
            if reading_key in seen_readings:
                result.add_flag(
                    PlausibilityFlag.DUPLICATE_READING,
                    f"Duplicate reading for {result.icp_id} {result.register_code} at {result.read_at}",
                    'error'
                )
            else:
                seen_readings.add(reading_key)
    
    def apply_plausibility_flags(self, readings: List[MeterRawInterval], results: List[PlausibilityResult]):
        """
        Apply plausibility flags to the raw reading records
        """
        # Create a lookup for results
        result_lookup = {}
        for result in results:
            key = (result.icp_id, result.register_code, result.read_at)
            result_lookup[key] = result
        
        # Update readings with flags
        for reading in readings:
            key = (reading.icp_id, reading.register_code, reading.read_at)
            if key in result_lookup:
                result = result_lookup[key]
                
                # Update raw_data with plausibility flags
                if not reading.raw_data:
                    reading.raw_data = {}
                
                reading.raw_data['plausibility_flags'] = [flag.value for flag in result.flags]
                reading.raw_data['plausibility_warnings'] = result.warnings
                reading.raw_data['plausibility_severity'] = result.severity
                reading.raw_data['requires_review'] = result.requires_review
                
                # Update raw_quality based on severity
                if result.severity == 'error':
                    reading.raw_quality = 'error'
                elif result.severity == 'warning' and reading.raw_quality == 'raw':
                    reading.raw_quality = 'suspect'
    
    def get_plausibility_summary(self, results: List[PlausibilityResult]) -> Dict[str, Any]:
        """
        Generate summary statistics for plausibility check results
        """
        total_readings = len(results)
        flagged_readings = len([r for r in results if r.flags])
        
        flag_counts = {}
        for flag in PlausibilityFlag:
            flag_counts[flag.value] = len([r for r in results if flag in r.flags])
        
        severity_counts = {
            'info': len([r for r in results if r.severity == 'info']),
            'warning': len([r for r in results if r.severity == 'warning']),
            'error': len([r for r in results if r.severity == 'error'])
        }
        
        return {
            'total_readings': total_readings,
            'flagged_readings': flagged_readings,
            'flag_rate': flagged_readings / total_readings if total_readings > 0 else 0,
            'flag_counts': flag_counts,
            'severity_counts': severity_counts,
            'requires_review': len([r for r in results if r.requires_review])
        } 