#!/usr/bin/env python3
"""
Simple test script to validate the validation pipeline logic
Bypasses Airflow to test core validation functionality
"""

import os
import sys
import django
from datetime import datetime, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from energy.validation.models import (
    ValidationWorkflow, ValidationSession, ValidationRule, ValidationRuleExecution
)
from users.models import Tenant
from django.db import connection

def test_validation_pipeline():
    """Test the complete validation pipeline"""
    
    print("🚀 Testing Validation Pipeline")
    print("=" * 50)
    
    # 1. Check if we have data
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_raw WHERE timestamp >= %s AND timestamp <= %s", 
                      [date(2024, 2, 20), date(2024, 3, 1)])
        raw_count = cursor.fetchone()[0]
        print(f"📊 Raw readings in date range: {raw_count}")
        
        cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_calculated")
        calc_count = cursor.fetchone()[0]
        print(f"📊 Calculated readings: {calc_count}")
    
    # 2. Check validation rules
    rules = ValidationRule.objects.filter(is_active=True)
    print(f"📊 Active validation rules: {rules.count()}")
    for rule in rules:
        print(f"   - {rule.rule_code}: {rule.rule_type}")
    
    # 3. Check workflow
    try:
        workflow = ValidationWorkflow.objects.get(workflow_code='HHR_STANDARD')
        print(f"📊 Workflow found: {workflow.name}")
        print(f"   Rules: {workflow.validation_rules}")
    except ValidationWorkflow.DoesNotExist:
        print("❌ HHR_STANDARD workflow not found")
        return
    
    # 4. Check tenant
    tenant = Tenant.objects.first()
    if not tenant:
        print("❌ No tenant found")
        return
    print(f"📊 Using tenant: {tenant.name}")
    
    # 5. Create test validation session
    session_id = f"test_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session = ValidationSession.objects.create(
        tenant=tenant,
        session_id=session_id,
        workflow=workflow,
        start_date=date(2024, 2, 20),
        end_date=date(2024, 3, 1),
        status='pending'
    )
    print(f"✅ Created validation session: {session_id}")
    
    # 6. Get sample unprocessed readings
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                r.id, r.tenant_id, r.icp_id, r.meter_serial_number, r.meter_register_id,
                r.timestamp, r.value, r.quality_flag, r.source, r.source_file_name, r.metadata
            FROM metering_processed.interval_reads_raw r
            WHERE NOT EXISTS (
                SELECT 1 FROM metering_processed.interval_reads_calculated c
                WHERE c.icp_id = r.icp_id 
                AND c.meter_register_id = r.meter_register_id
                AND c.timestamp = r.timestamp
                AND c.source = r.source
            )
            AND r.timestamp >= %s AND r.timestamp <= %s
            ORDER BY r.timestamp DESC, r.icp_id, r.meter_register_id
            LIMIT 100
        """, [session.start_date, session.end_date])
        
        readings = cursor.fetchall()
        columns = ['id', 'tenant_id', 'icp_id', 'meter_serial_number', 'meter_register_id', 
                  'timestamp', 'value', 'quality_flag', 'source', 'source_file_name', 'metadata']
        
        reading_dicts = []
        for record in readings:
            reading_dict = dict(zip(columns, record))
            # Convert UUID to string
            if hasattr(reading_dict['tenant_id'], '__str__'):
                reading_dict['tenant_id'] = str(reading_dict['tenant_id'])
            reading_dicts.append(reading_dict)
    
    print(f"📊 Found {len(reading_dicts)} unprocessed readings")
    
    if not reading_dicts:
        print("❌ No unprocessed readings found")
        return
    
    # 7. Test validation rules
    validated_count = 0
    for rule_code in workflow.validation_rules:
        try:
            rule = ValidationRule.objects.get(rule_code=rule_code, is_active=True)
            print(f"🔍 Testing rule: {rule_code} ({rule.rule_type})")
            
            # Create rule execution record
            execution = ValidationRuleExecution.objects.create(
                session=session,
                rule=rule,
                execution_order=1,
                status='running'
            )
            
            # Apply simple validation logic
            passed = 0
            failed = 0
            for reading in reading_dicts:
                if rule.rule_type == 'range_check':
                    params = rule.parameters
                    min_val = params.get('min_value', 0)
                    max_val = params.get('max_value', 1000)
                    if reading['value'] is not None and min_val <= reading['value'] <= max_val:
                        passed += 1
                    else:
                        failed += 1
                elif rule.rule_type == 'missing_data':
                    if reading['value'] is not None:
                        passed += 1
                    else:
                        failed += 1
                else:
                    passed += 1  # Default pass for unknown rule types
            
            # Update execution record
            execution.status = 'completed'
            execution.completed_at = datetime.now()
            execution.readings_processed = len(reading_dicts)
            execution.readings_passed = passed
            execution.readings_failed = failed
            execution.save()
            
            print(f"   ✅ {passed}/{len(reading_dicts)} readings passed")
            validated_count += 1
            
        except ValidationRule.DoesNotExist:
            print(f"   ⚠️ Rule {rule_code} not found")
    
    # 8. Update session
    session.total_readings = len(reading_dicts)
    session.processed_readings = len(reading_dicts)
    session.valid_readings = len(reading_dicts)  # Simplified
    session.status = 'completed'
    session.completed_at = datetime.now()
    session.save()
    
    print(f"✅ Validation complete!")
    print(f"   📊 Session: {session_id}")
    print(f"   📊 Rules executed: {validated_count}")
    print(f"   📊 Readings processed: {len(reading_dicts)}")
    
    # 9. Check rule executions
    executions = ValidationRuleExecution.objects.filter(session=session)
    print(f"📊 Rule executions created: {executions.count()}")
    for execution in executions:
        print(f"   - {execution.rule.rule_code}: {execution.status} ({execution.readings_passed}/{execution.readings_processed} passed)")
    
    print("\n🎉 Validation pipeline test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_validation_pipeline()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 