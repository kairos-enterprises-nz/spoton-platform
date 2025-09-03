#!/usr/bin/env python3
"""
Test script to validate proper estimation logic with the example:
12 Jun register read - 2568
13 Jun register read - 2575
7 kWh should be distributed across intervals
"""

import os
import django
from datetime import date, datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.db import transaction
from energy.validation.proper_estimation_engine import ProperEstimationEngine
from energy.metering.models import MeterCalcInterval, MeterCalcDaily
from energy.connections.models import ConnectionDetails
from users.models import Tenant


def create_test_data():
    """Create test data for the estimation example."""
    print("Creating test data...")
    
    # Get or create tenant
    tenant = Tenant.objects.first()
    if not tenant:
        print("No tenant found. Please create a tenant first.")
        return None
    
    icp_id = "TEST0001234EXAMPLE"
    
    # Create connection details
    connection_details, created = ConnectionDetails.objects.get_or_create(
        tenant=tenant,
        icp_id=icp_id,
        effective_from=date(2024, 6, 1),
        defaults={
            'average_daily_kwh': Decimal('25.0'),
            'connection_type': 'residential',
            'load_profile': 'RES',
            'data_source': 'CS_FILE'
        }
    )
    
    # Create some existing intervals for June 12, 2024 with gaps
    test_date = date(2024, 6, 12)
    base_datetime = datetime.combine(test_date, datetime.min.time())
    
    # Clear existing test data
    MeterCalcInterval.objects.filter(
        tenant=tenant,
        icp_id=icp_id,
        timestamp__date=test_date
    ).delete()
    
    # Create partial interval data (missing some intervals to simulate gaps)
    valid_intervals = []
    for i in range(48):
        timestamp = base_datetime + timedelta(minutes=30 * i)
        
        # Create gaps in certain periods (simulate missing data)
        if i in [10, 11, 12, 13, 20, 21, 22, 30, 31]:  # 9 missing intervals
            continue
            
        # Create valid interval
        interval = MeterCalcInterval.objects.create(
            tenant=tenant,
            icp_id=icp_id,
            timestamp=timestamp,
            value=Decimal('0.3'),  # Low values to simulate underestimation
            quality_flag='V'
        )
        valid_intervals.append(interval)
    
    print(f"Created {len(valid_intervals)} valid intervals with 9 gaps")
    
    # Calculate current total
    current_total = sum(interval.value for interval in valid_intervals)
    print(f"Current total consumption: {current_total} kWh")
    
    return tenant.id, icp_id, test_date


def test_estimation_hierarchy():
    """Test the estimation hierarchy with the example data."""
    print("\n" + "="*50)
    print("TESTING ESTIMATION HIERARCHY")
    print("="*50)
    
    # Create test data
    result = create_test_data()
    if not result:
        return
    
    tenant_id, icp_id, test_date = result
    
    # Register consumption difference: 2575 - 2568 = 7 kWh
    register_consumption = Decimal('7.0')
    
    print(f"\nTest scenario:")
    print(f"- ICP: {icp_id}")
    print(f"- Date: {test_date}")
    print(f"- Register consumption to distribute: {register_consumption} kWh")
    
    # Initialize estimation engine
    engine = ProperEstimationEngine(tenant_id)
    
    # Run estimation
    print(f"\nRunning estimation...")
    estimation_result = engine.estimate_missing_intervals(
        icp_id=icp_id,
        target_date=test_date,
        register_consumption=register_consumption
    )
    
    print(f"\nEstimation Result:")
    print(f"- Success: {estimation_result['success']}")
    print(f"- Method: {estimation_result.get('method', 'N/A')}")
    print(f"- Confidence: {estimation_result.get('confidence', 'N/A')}")
    print(f"- Gaps filled: {estimation_result.get('gaps_filled', 0)}")
    
    if estimation_result.get('validation_passed') is not None:
        print(f"- Validation passed: {estimation_result['validation_passed']}")
        print(f"- Total consumption: {estimation_result['total_consumption']} kWh")
        print(f"- Register consumption: {estimation_result['register_consumption']} kWh")
        print(f"- Difference: {estimation_result['difference']} kWh")
    
    # Show estimated values
    if 'estimated_values' in estimation_result:
        print(f"\nEstimated values:")
        for i, value in enumerate(estimation_result['estimated_values'][:5]):  # Show first 5
            print(f"  {value['timestamp']}: {value['value']:.4f} kWh ({value['method']})")
        if len(estimation_result['estimated_values']) > 5:
            print(f"  ... and {len(estimation_result['estimated_values']) - 5} more")
    
    return estimation_result


def test_different_gap_sizes():
    """Test estimation with different gap sizes to verify hierarchy."""
    print("\n" + "="*50)
    print("TESTING DIFFERENT GAP SIZES")
    print("="*50)
    
    tenant_id = Tenant.objects.first().id
    icp_id = "TEST0001234GAPS"
    
    # Test scenarios with different gap sizes
    test_scenarios = [
        {'gaps': 2, 'expected_method': 'interpolation'},
        {'gaps': 6, 'expected_method': 'pattern_matching'},
        {'gaps': 20, 'expected_method': 'average_consumption'},
    ]
    
    for scenario in test_scenarios:
        print(f"\nTesting {scenario['gaps']} gaps...")
        
        test_date = date(2024, 6, 13)
        base_datetime = datetime.combine(test_date, datetime.min.time())
        
        # Clear existing data
        MeterCalcInterval.objects.filter(
            tenant_id=tenant_id,
            icp_id=icp_id,
            timestamp__date=test_date
        ).delete()
        
        # Create intervals with specific number of gaps
        for i in range(48):
            timestamp = base_datetime + timedelta(minutes=30 * i)
            
            # Create gaps at the beginning
            if i < scenario['gaps']:
                continue
                
            # Create valid interval
            MeterCalcInterval.objects.create(
                tenant_id=tenant_id,
                icp_id=icp_id,
                timestamp=timestamp,
                value=Decimal('0.2'),
                quality_flag='V'
            )
        
        # Run estimation
        engine = ProperEstimationEngine(tenant_id)
        result = engine.estimate_missing_intervals(
            icp_id=icp_id,
            target_date=test_date,
            register_consumption=Decimal('5.0')
        )
        
        print(f"  Expected method: {scenario['expected_method']}")
        print(f"  Actual method: {result.get('method', 'N/A')}")
        print(f"  Success: {result['success']}")
        print(f"  Gaps filled: {result.get('gaps_filled', 0)}")
        
        # Verify method matches expectation
        if result.get('method') == scenario['expected_method']:
            print(f"  ✓ Correct method applied")
        else:
            print(f"  ✗ Method mismatch!")


def analyze_estimation_accuracy():
    """Analyze the accuracy of the estimation."""
    print("\n" + "="*50)
    print("ANALYZING ESTIMATION ACCURACY")
    print("="*50)
    
    tenant_id = Tenant.objects.first().id
    icp_id = "TEST0001234EXAMPLE"
    test_date = date(2024, 6, 12)
    
    # Get all intervals for the test date
    intervals = MeterCalcInterval.objects.filter(
        tenant_id=tenant_id,
        icp_id=icp_id,
        timestamp__date=test_date
    ).order_by('timestamp')
    
    print(f"Total intervals: {intervals.count()}")
    
    # Analyze by quality flag
    quality_counts = {}
    quality_totals = {}
    
    for interval in intervals:
        flag = interval.quality_flag
        quality_counts[flag] = quality_counts.get(flag, 0) + 1
        quality_totals[flag] = quality_totals.get(flag, Decimal('0')) + (interval.value or Decimal('0'))
    
    print(f"\nQuality flag analysis:")
    for flag, count in quality_counts.items():
        total = quality_totals[flag]
        avg = total / count if count > 0 else 0
        print(f"  {flag}: {count} intervals, {total:.4f} kWh total, {avg:.4f} kWh avg")
    
    # Total consumption
    total_consumption = sum(interval.value for interval in intervals if interval.value)
    print(f"\nTotal consumption: {total_consumption:.4f} kWh")
    print(f"Target (register): 7.0000 kWh")
    print(f"Difference: {abs(total_consumption - Decimal('7.0')):.4f} kWh")
    
    # Expected vs actual intervals
    print(f"\nInterval completeness:")
    print(f"  Expected: 48 intervals")
    print(f"  Actual: {intervals.count()} intervals")
    print(f"  Completeness: {intervals.count()/48*100:.1f}%")


if __name__ == "__main__":
    print("PROPER ESTIMATION ENGINE TEST")
    print("="*50)
    
    try:
        # Test main estimation hierarchy
        result = test_estimation_hierarchy()
        
        # Test different gap sizes
        test_different_gap_sizes()
        
        # Analyze accuracy
        analyze_estimation_accuracy()
        
        print("\n" + "="*50)
        print("TEST COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc() 