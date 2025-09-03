"""
Register-Based Estimation System

This module implements estimation using daily register reads to calculate 
daily consumption and distribute it across missing or invalid intervals.

The system follows this approach:
1. Get daily register reads (start/end readings, consumption)
2. Identify missing/invalid intervals for that day
3. Calculate consumption per interval based on daily total
4. Distribute consumption using time-of-use patterns
5. Validate that estimated intervals sum to register consumption
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

import pandas as pd
from django.db import connection

logger = logging.getLogger(__name__)


class EstimationMethod(Enum):
    """Estimation methods in order of preference"""
    REGISTER_DISTRIBUTION = "register_distribution"
    REGISTER_INTERPOLATION = "register_interpolation"
    PATTERN_MATCHING = "pattern_matching"
    GENERIC_PROFILE = "generic_profile"


class GapType(Enum):
    """Types of gaps that need estimation"""
    MISSING_INTERVALS = "missing_intervals"
    INVALID_INTERVALS = "invalid_intervals"
    SUSPECT_INTERVALS = "suspect_intervals"
    FAILED_VALIDATION = "failed_validation"


@dataclass
class RegisterRead:
    """Daily register read data"""
    icp_id: str
    meter_register_id: str
    reading_date: date
    start_reading: Decimal
    end_reading: Decimal
    consumption: Decimal
    read_type: str
    quality_flag: str
    source: str


@dataclass
class IntervalGap:
    """Represents a gap in interval data that needs estimation"""
    icp_id: str
    meter_register_id: str
    timestamp: datetime
    gap_type: GapType
    original_value: Optional[Decimal] = None
    original_quality_flag: Optional[str] = None


@dataclass
class EstimationResult:
    """Result of estimation for a single interval"""
    icp_id: str
    meter_register_id: str
    timestamp: datetime
    estimated_value: Decimal
    method: EstimationMethod
    confidence: float
    source_register_date: date
    daily_consumption: Decimal
    intervals_in_day: int
    audit_trail: Dict


class DailyConsumptionCalculator:
    """Calculates daily consumption from register reads"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.DailyConsumptionCalculator')
    
    def get_register_reads(self, icp_id: str, meter_register_id: str, 
                          start_date: date, end_date: date) -> List[RegisterRead]:
        """Get register reads for a date range"""
        query = """
        SELECT 
            connection_id as icp_id,
            register_code as meter_register_id,
            reading_date,
            start_reading,
            end_reading,
            consumption,
            read_type,
            quality_flag,
            source
        FROM metering_processed.daily_register_reads
        WHERE connection_id = %s 
            AND register_code = %s
            AND reading_date BETWEEN %s AND %s
        ORDER BY reading_date
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [icp_id, meter_register_id, start_date, end_date])
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
        
        return [RegisterRead(**dict(zip(columns, row))) for row in rows]
    
    def calculate_daily_consumption(self, register_read: RegisterRead) -> Decimal:
        """Calculate daily consumption from register read"""
        if register_read.consumption is not None:
            return register_read.consumption
        
        # Fallback: calculate from start/end readings
        if register_read.start_reading is not None and register_read.end_reading is not None:
            return register_read.end_reading - register_read.start_reading
        
        return Decimal('0')
    
    def validate_consumption(self, register_read: RegisterRead, 
                           interval_sum: Decimal, tolerance: Decimal = Decimal('5.0')) -> bool:
        """Validate that interval sum matches register consumption"""
        daily_consumption = self.calculate_daily_consumption(register_read)
        difference = abs(interval_sum - daily_consumption)
        return difference <= tolerance


class GapDetector:
    """Detects gaps in interval data that need estimation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.GapDetector')
    
    def get_intervals_for_day(self, icp_id: str, meter_register_id: str, 
                             target_date: date) -> List[Dict]:
        """Get all intervals for a specific day"""
        query = """
        SELECT 
            id,
            timestamp,
            value,
            metadata
        FROM metering_processed.interval_reads_final
        WHERE connection_id = %s 
            AND register_code = %s
            AND DATE(timestamp) = %s
        ORDER BY timestamp
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [icp_id, meter_register_id, target_date])
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def identify_gaps(self, icp_id: str, meter_register_id: str, 
                     target_date: date) -> List[IntervalGap]:
        """Identify gaps that need estimation"""
        intervals = self.get_intervals_for_day(icp_id, meter_register_id, target_date)
        gaps = []
        
        # Expected intervals: 48 per day (30-minute intervals)
        expected_timestamps = []
        start_time = datetime.combine(target_date, datetime.min.time())
        for i in range(48):
            expected_timestamps.append(start_time + timedelta(minutes=30*i))
        
        # Find missing intervals
        existing_timestamps = {interval['timestamp'] for interval in intervals}
        for expected_ts in expected_timestamps:
            if expected_ts not in existing_timestamps:
                gaps.append(IntervalGap(
                    icp_id=icp_id,
                    meter_register_id=meter_register_id,
                    timestamp=expected_ts,
                    gap_type=GapType.MISSING_INTERVALS
                ))
        
        # Find invalid/suspect intervals
        for interval in intervals:
            if interval['final_quality_flag'] in ['E', 'S', 'N']:
                gap_type = GapType.INVALID_INTERVALS
                if interval['final_quality_flag'] == 'S':
                    gap_type = GapType.SUSPECT_INTERVALS
                elif interval['final_quality_flag'] == 'N':
                    gap_type = GapType.FAILED_VALIDATION
                
                gaps.append(IntervalGap(
                    icp_id=icp_id,
                    meter_register_id=meter_register_id,
                    timestamp=interval['timestamp'],
                    gap_type=gap_type,
                    original_value=interval['value_final'],
                    original_quality_flag=interval['final_quality_flag']
                ))
        
        return gaps


class ConsumptionDistributor:
    """Distributes daily consumption across intervals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.ConsumptionDistributor')
    
    def get_time_of_use_profile(self, icp_id: str, meter_register_id: str) -> Dict[int, float]:
        """Get time-of-use profile for consumption distribution"""
        # Default uniform distribution (can be enhanced with historical patterns)
        return {hour: 1.0/24 for hour in range(24)}
    
    def distribute_consumption(self, daily_consumption: Decimal, 
                             gaps: List[IntervalGap],
                             target_date: date) -> List[EstimationResult]:
        """Distribute daily consumption across gaps"""
        if not gaps:
            return []
        
        # Get time-of-use profile
        icp_id = gaps[0].icp_id
        meter_register_id = gaps[0].meter_register_id
        tou_profile = self.get_time_of_use_profile(icp_id, meter_register_id)
        
        # Calculate weights for each gap based on time of day
        total_weight = 0
        gap_weights = {}
        
        for gap in gaps:
            hour = gap.timestamp.hour
            # Each hour has 2 intervals (30-minute periods)
            weight = tou_profile.get(hour, 1.0/24) / 2
            gap_weights[gap.timestamp] = weight
            total_weight += weight
        
        # Distribute consumption proportionally
        results = []
        for gap in gaps:
            if total_weight > 0:
                proportion = gap_weights[gap.timestamp] / total_weight
                estimated_value = daily_consumption * Decimal(str(proportion))
                # Round to 4 decimal places
                estimated_value = estimated_value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            else:
                estimated_value = Decimal('0')
            
            result = EstimationResult(
                icp_id=gap.icp_id,
                meter_register_id=gap.meter_register_id,
                timestamp=gap.timestamp,
                estimated_value=estimated_value,
                method=EstimationMethod.REGISTER_DISTRIBUTION,
                confidence=0.85,  # High confidence when using register reads
                source_register_date=target_date,
                daily_consumption=daily_consumption,
                intervals_in_day=len(gaps),
                audit_trail={
                    'gap_type': gap.gap_type.value,
                    'original_value': str(gap.original_value) if gap.original_value else None,
                    'original_quality_flag': gap.original_quality_flag,
                    'distribution_weight': gap_weights[gap.timestamp],
                    'total_weight': total_weight,
                    'proportion': gap_weights[gap.timestamp] / total_weight if total_weight > 0 else 0
                }
            )
            results.append(result)
        
        return results


class RegisterBasedEstimationEngine:
    """Main engine for register-based estimation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.RegisterBasedEstimationEngine')
        self.consumption_calculator = DailyConsumptionCalculator()
        self.gap_detector = GapDetector()
        self.consumption_distributor = ConsumptionDistributor()
    
    def estimate_for_day(self, icp_id: str, meter_register_id: str, 
                        target_date: date) -> List[EstimationResult]:
        """Estimate missing intervals for a specific day using register reads"""
        try:
            # Get register read for the day
            register_reads = self.consumption_calculator.get_register_reads(
                icp_id, meter_register_id, target_date, target_date
            )
            
            if not register_reads:
                self.logger.warning(f"No register read found for {icp_id}-{meter_register_id} on {target_date}")
                return []
            
            register_read = register_reads[0]
            daily_consumption = self.consumption_calculator.calculate_daily_consumption(register_read)
            
            if daily_consumption <= 0:
                self.logger.warning(f"Invalid daily consumption {daily_consumption} for {icp_id}-{meter_register_id} on {target_date}")
                return []
            
            # Identify gaps
            gaps = self.gap_detector.identify_gaps(icp_id, meter_register_id, target_date)
            
            if not gaps:
                self.logger.info(f"No gaps found for {icp_id}-{meter_register_id} on {target_date}")
                return []
            
            # Distribute consumption across gaps
            results = self.consumption_distributor.distribute_consumption(
                daily_consumption, gaps, target_date
            )
            
            self.logger.info(f"Estimated {len(results)} intervals for {icp_id}-{meter_register_id} on {target_date}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error estimating for {icp_id}-{meter_register_id} on {target_date}: {e}")
            return []
    
    def estimate_for_date_range(self, icp_id: str, meter_register_id: str,
                               start_date: date, end_date: date) -> List[EstimationResult]:
        """Estimate missing intervals for a date range"""
        all_results = []
        current_date = start_date
        
        while current_date <= end_date:
            results = self.estimate_for_day(icp_id, meter_register_id, current_date)
            all_results.extend(results)
            current_date += timedelta(days=1)
        
        return all_results
    
    def validate_estimation(self, results: List[EstimationResult]) -> Dict:
        """Validate that estimated intervals sum to register consumption"""
        if not results:
            return {'valid': True, 'message': 'No results to validate'}
        
        # Group by date
        by_date = {}
        for result in results:
            date_key = result.source_register_date
            if date_key not in by_date:
                by_date[date_key] = {
                    'results': [],
                    'daily_consumption': result.daily_consumption
                }
            by_date[date_key]['results'].append(result)
        
        validation_results = {}
        all_valid = True
        
        for date_key, data in by_date.items():
            estimated_sum = sum(r.estimated_value for r in data['results'])
            daily_consumption = data['daily_consumption']
            difference = abs(estimated_sum - daily_consumption)
            
            is_valid = difference <= Decimal('0.1')  # 0.1 kWh tolerance
            if not is_valid:
                all_valid = False
            
            validation_results[str(date_key)] = {
                'valid': is_valid,
                'estimated_sum': float(estimated_sum),
                'daily_consumption': float(daily_consumption),
                'difference': float(difference),
                'interval_count': len(data['results'])
            }
        
        return {
            'valid': all_valid,
            'by_date': validation_results,
            'total_intervals': len(results)
        } 