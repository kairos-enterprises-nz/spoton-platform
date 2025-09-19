"""
Enhanced Estimation Engine with Register-Based Estimation

This module provides sophisticated estimation methods for missing or invalid meter readings,
with register-based consumption distribution as the primary approach.
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

import pandas as pd
from django.db import connection

from .register_based_estimation import (
    RegisterBasedEstimationEngine,
    EstimationMethod,
    EstimationResult,
    GapType
)

logger = logging.getLogger(__name__)


class EstimationContext:
    """Context information for estimation"""
    
    def __init__(self, icp_id: str, meter_register_id: str, timestamp: datetime):
        self.icp_id = icp_id
        self.meter_register_id = meter_register_id
        self.timestamp = timestamp
        self.target_date = timestamp.date()
        self.hour = timestamp.hour
        self.minute = timestamp.minute
        
        # Additional context
        self.original_value = None
        self.original_quality_flag = None
        self.validation_failure_reason = None
        self.neighboring_values = []
        self.historical_patterns = {}
        self.customer_type = None
        self.meter_read_data = None


class EstimationEngine:
    """
    Enhanced estimation engine with multiple estimation methods:
    1. Register-based consumption distribution (PRIMARY)
    2. Interpolation for small gaps
    3. Pattern matching from historical data
    4. Generic consumption profiles
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.EstimationEngine')
        self.register_engine = RegisterBasedEstimationEngine()
        
    def estimate_missing_intervals(self, gaps: List[Dict]) -> List[EstimationResult]:
        """
        Estimate missing intervals using register-based approach as primary method
        
        Args:
            gaps: List of gap dictionaries with keys: icp_id, meter_register_id, timestamp, gap_type
            
        Returns:
            List of EstimationResult objects
        """
        if not gaps:
            return []
            
        self.logger.info(f"Starting estimation for {len(gaps)} gaps")
        
        # Group gaps by ICP and date for efficient processing
        gaps_by_icp_date = {}
        for gap in gaps:
            icp_id = gap['icp_id']
            meter_register_id = gap['meter_register_id']
            timestamp = gap['timestamp']
            target_date = timestamp.date()
            
            key = (icp_id, meter_register_id, target_date)
            if key not in gaps_by_icp_date:
                gaps_by_icp_date[key] = []
            gaps_by_icp_date[key].append(gap)
        
        all_results = []
        
        # Process each ICP/date combination
        for (icp_id, meter_register_id, target_date), icp_gaps in gaps_by_icp_date.items():
            self.logger.info(f"Processing {len(icp_gaps)} gaps for {icp_id}-{meter_register_id} on {target_date}")
            
            # Try register-based estimation first
            register_results = self.register_engine.estimate_for_day(
                icp_id, meter_register_id, target_date
            )
            
            if register_results:
                # Validate register-based results
                validation = self.register_engine.validate_estimation(register_results)
                if validation['valid']:
                    self.logger.info(f"Register-based estimation successful for {icp_id}-{meter_register_id} on {target_date}")
                    all_results.extend(register_results)
                    continue
                else:
                    self.logger.warning(f"Register-based estimation validation failed for {icp_id}-{meter_register_id} on {target_date}")
            
            # Fallback to other methods if register-based fails
            fallback_results = self._apply_fallback_methods(icp_gaps, icp_id, meter_register_id, target_date)
            all_results.extend(fallback_results)
        
        self.logger.info(f"Completed estimation: {len(all_results)} intervals estimated")
        return all_results
    
    def _apply_fallback_methods(self, gaps: List[Dict], icp_id: str, 
                               meter_register_id: str, target_date: date) -> List[EstimationResult]:
        """Apply fallback estimation methods when register-based fails"""
        results = []
        
        for gap in gaps:
            context = EstimationContext(
                icp_id=icp_id,
                meter_register_id=meter_register_id,
                timestamp=gap['timestamp']
            )
            
            # Try interpolation for small gaps
            if self._is_small_gap(gap, gaps):
                result = self._interpolate_value(context)
                if result:
                    results.append(result)
                    continue
            
            # Try pattern matching
            result = self._pattern_match_value(context)
            if result:
                results.append(result)
                continue
            
            # Use generic profile as last resort
            result = self._generic_profile_value(context)
            if result:
                results.append(result)
        
        return results
    
    def _is_small_gap(self, gap: Dict, all_gaps: List[Dict]) -> bool:
        """Check if this is part of a small gap (< 4 consecutive intervals)"""
        timestamp = gap['timestamp']
        consecutive_count = 1
        
        # Count consecutive gaps
        for other_gap in all_gaps:
            if other_gap['timestamp'] == timestamp + timedelta(minutes=30):
                consecutive_count += 1
            elif other_gap['timestamp'] == timestamp - timedelta(minutes=30):
                consecutive_count += 1
        
        return consecutive_count < 4
    
    def _interpolate_value(self, context: EstimationContext) -> Optional[EstimationResult]:
        """Interpolate value for small gaps"""
        try:
            # Get neighboring values
            query = """
            SELECT timestamp, value
            FROM metering_processed.interval_reads_final
            WHERE connection_id = %s AND register_code = %s
                AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp
            """
            
            start_time = context.timestamp - timedelta(hours=2)
            end_time = context.timestamp + timedelta(hours=2)
            
            with connection.cursor() as cursor:
                cursor.execute(query, [context.icp_id, context.meter_register_id, start_time, end_time])
                neighbors = cursor.fetchall()
            
            if len(neighbors) >= 2:
                # Simple linear interpolation
                before_values = [row for row in neighbors if row[0] < context.timestamp]
                after_values = [row for row in neighbors if row[0] > context.timestamp]
                
                if before_values and after_values:
                    before_val = before_values[-1][1]  # Last value before gap
                    after_val = after_values[0][1]     # First value after gap
                    
                    # Linear interpolation
                    estimated_value = (before_val + after_val) / 2
                    
                    return EstimationResult(
                        icp_id=context.icp_id,
                        meter_register_id=context.meter_register_id,
                        timestamp=context.timestamp,
                        estimated_value=Decimal(str(estimated_value)),
                        method=EstimationMethod.REGISTER_INTERPOLATION,
                        confidence=0.75,
                        source_register_date=context.target_date,
                        daily_consumption=Decimal('0'),  # Not applicable for interpolation
                        intervals_in_day=1,
                        audit_trail={
                            'method': 'linear_interpolation',
                            'before_value': float(before_val),
                            'after_value': float(after_val),
                            'neighbor_count': len(neighbors)
                        }
                    )
        
        except Exception as e:
            self.logger.error(f"Error in interpolation for {context.icp_id}-{context.meter_register_id}: {e}")
        
        return None
    
    def _pattern_match_value(self, context: EstimationContext) -> Optional[EstimationResult]:
        """Pattern match from historical data"""
        try:
            # Get historical values for same time of day from previous weeks
            query = """
            SELECT value, timestamp
            FROM metering_processed.interval_reads_final
            WHERE connection_id = %s AND register_code = %s
                AND EXTRACT(hour FROM timestamp) = %s
                AND EXTRACT(minute FROM timestamp) = %s
                AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp DESC
            LIMIT 10
            """
            
            # Look back 4 weeks
            start_time = context.timestamp - timedelta(weeks=4)
            end_time = context.timestamp - timedelta(days=1)
            
            with connection.cursor() as cursor:
                cursor.execute(query, [
                    context.icp_id, context.meter_register_id,
                    context.hour, context.minute,
                    start_time, end_time
                ])
                historical_values = cursor.fetchall()
            
            if historical_values:
                # Use median of historical values
                values = [row[0] for row in historical_values]
                median_value = sorted(values)[len(values) // 2]
                
                return EstimationResult(
                    icp_id=context.icp_id,
                    meter_register_id=context.meter_register_id,
                    timestamp=context.timestamp,
                    estimated_value=Decimal(str(median_value)),
                    method=EstimationMethod.PATTERN_MATCHING,
                    confidence=0.65,
                    source_register_date=context.target_date,
                    daily_consumption=Decimal('0'),  # Not applicable for pattern matching
                    intervals_in_day=1,
                    audit_trail={
                        'method': 'historical_pattern_matching',
                        'historical_count': len(historical_values),
                        'median_value': float(median_value),
                        'value_range': [float(min(values)), float(max(values))]
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error in pattern matching for {context.icp_id}-{context.meter_register_id}: {e}")
        
        return None
    
    def _generic_profile_value(self, context: EstimationContext) -> Optional[EstimationResult]:
        """Use generic consumption profile"""
        try:
            # Simple time-of-day profile (can be enhanced with customer segmentation)
            hourly_profile = {
                0: 0.8, 1: 0.7, 2: 0.6, 3: 0.6, 4: 0.6, 5: 0.7,
                6: 0.9, 7: 1.2, 8: 1.4, 9: 1.3, 10: 1.2, 11: 1.1,
                12: 1.0, 13: 1.0, 14: 1.0, 15: 1.0, 16: 1.1, 17: 1.3,
                18: 1.5, 19: 1.6, 20: 1.4, 21: 1.2, 22: 1.0, 23: 0.9
            }
            
            # Get average consumption for this ICP
            query = """
            SELECT AVG(value) as avg_consumption
            FROM metering_processed.interval_reads_final
            WHERE connection_id = %s AND register_code = %s
                AND timestamp >= %s
            """
            
            lookback_date = context.timestamp - timedelta(days=30)
            
            with connection.cursor() as cursor:
                cursor.execute(query, [context.icp_id, context.meter_register_id, lookback_date])
                result = cursor.fetchone()
            
            if result and result[0]:
                avg_consumption = result[0]
                profile_factor = hourly_profile.get(context.hour, 1.0)
                estimated_value = avg_consumption * profile_factor
                
                return EstimationResult(
                    icp_id=context.icp_id,
                    meter_register_id=context.meter_register_id,
                    timestamp=context.timestamp,
                    estimated_value=Decimal(str(estimated_value)),
                    method=EstimationMethod.GENERIC_PROFILE,
                    confidence=0.45,
                    source_register_date=context.target_date,
                    daily_consumption=Decimal('0'),  # Not applicable for generic profile
                    intervals_in_day=1,
                    audit_trail={
                        'method': 'generic_time_of_day_profile',
                        'avg_consumption': float(avg_consumption),
                        'profile_factor': profile_factor,
                        'hour': context.hour
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error in generic profile for {context.icp_id}-{context.meter_register_id}: {e}")
        
        return None
    
    def get_estimation_summary(self, results: List[EstimationResult]) -> Dict:
        """Get summary of estimation results"""
        if not results:
            return {'total': 0, 'by_method': {}, 'avg_confidence': 0}
        
        by_method = {}
        total_confidence = 0
        
        for result in results:
            method = result.method.value
            if method not in by_method:
                by_method[method] = {'count': 0, 'total_confidence': 0}
            
            by_method[method]['count'] += 1
            by_method[method]['total_confidence'] += result.confidence
            total_confidence += result.confidence
        
        # Calculate average confidence by method
        for method_data in by_method.values():
            method_data['avg_confidence'] = method_data['total_confidence'] / method_data['count']
        
        return {
            'total': len(results),
            'by_method': by_method,
            'avg_confidence': total_confidence / len(results) if results else 0
        } 