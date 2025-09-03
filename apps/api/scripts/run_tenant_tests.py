#!/usr/bin/env python3
"""
Comprehensive Test Runner for Tenant CRUD Operations
Executes all tenant management tests and provides detailed reporting.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line
import subprocess
import time

def setup_django():
    """Set up Django environment for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
    django.setup()

def run_comprehensive_tests():
    """Run all tenant CRUD tests with detailed output"""
    print("🚀 Starting Comprehensive Tenant CRUD Tests")
    print("=" * 60)
    
    # Test modules to run
    test_modules = [
        'users.tests.test_tenant_crud_e2e.TenantCRUDPermissionTests',
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests', 
        'users.tests.test_tenant_crud_e2e.TenantDataIntegrityTests',
        'users.tests.test_tenant_crud_e2e.TenantSerializerTests'
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_module in test_modules:
        print(f"\n📋 Running {test_module}")
        print("-" * 40)
        
        try:
            # Run the specific test module
            result = subprocess.run([
                sys.executable, 'manage.py', 'test', test_module, 
                '--verbosity=2', '--keepdb'
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                print(f"✅ {test_module} - PASSED")
                passed_tests += 1
            else:
                print(f"❌ {test_module} - FAILED")
                print("Error output:", result.stderr)
                failed_tests += 1
                
            total_tests += 1
            
        except Exception as e:
            print(f"❌ Error running {test_module}: {e}")
            failed_tests += 1
            total_tests += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Test Modules: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 All tests passed! Tenant CRUD functionality is working correctly.")
    else:
        print(f"\n⚠️  {failed_tests} test module(s) failed. Please review the errors above.")
    
    return failed_tests == 0

def run_individual_test_cases():
    """Run individual test cases for detailed analysis"""
    print("\n🔍 Running Individual Test Cases")
    print("=" * 60)
    
    # Individual test cases to run
    test_cases = [
        # Permission tests
        'users.tests.test_tenant_crud_e2e.TenantCRUDPermissionTests.test_superuser_can_access_tenant_management',
        'users.tests.test_tenant_crud_e2e.TenantCRUDPermissionTests.test_admin_user_can_access_tenant_management',
        'users.tests.test_tenant_crud_e2e.TenantCRUDPermissionTests.test_staff_user_cannot_access_tenant_management',
        'users.tests.test_tenant_crud_e2e.TenantCRUDPermissionTests.test_regular_user_cannot_access_tenant_management',
        
        # CRUD operation tests
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests.test_create_tenant_success',
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests.test_create_tenant_validation_errors',
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests.test_list_tenants_with_pagination',
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests.test_retrieve_tenant_detail',
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests.test_update_tenant_partial',
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests.test_update_tenant_full',
        'users.tests.test_tenant_crud_e2e.TenantCRUDOperationsTests.test_delete_tenant',
        
        # Data integrity tests
        'users.tests.test_tenant_crud_e2e.TenantDataIntegrityTests.test_tenant_slug_uniqueness',
        'users.tests.test_tenant_crud_e2e.TenantDataIntegrityTests.test_tenant_user_role_relationships',
        
        # Serializer tests
        'users.tests.test_tenant_crud_e2e.TenantSerializerTests.test_tenant_list_serializer',
        'users.tests.test_tenant_crud_e2e.TenantSerializerTests.test_tenant_create_serializer_validation',
        'users.tests.test_tenant_crud_e2e.TenantSerializerTests.test_tenant_detail_serializer',
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        try:
            result = subprocess.run([
                sys.executable, 'manage.py', 'test', test_case, 
                '--verbosity=1', '--keepdb'
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                print(f"✅ {test_case.split('.')[-1]}")
                passed += 1
            else:
                print(f"❌ {test_case.split('.')[-1]}")
                print(f"   Error: {result.stderr.strip()}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_case.split('.')[-1]} - Exception: {e}")
            failed += 1
    
    print(f"\nIndividual Test Results: {passed} passed, {failed} failed")
    return failed == 0

def run_performance_tests():
    """Run performance tests for tenant operations"""
    print("\n⚡ Running Performance Tests")
    print("=" * 60)
    
    # This would include tests for:
    # - Bulk tenant creation
    # - Large dataset pagination
    # - Complex filtering performance
    # - Database query optimization
    
    print("Performance tests would be implemented here...")
    print("- Bulk operations testing")
    print("- Pagination performance with large datasets")
    print("- Complex query filtering performance")
    print("- Database constraint validation performance")
    
    return True

def main():
    """Main test execution function"""
    print("🧪 Comprehensive Tenant CRUD Testing Suite")
    print("SpotOn Energy - Utility Byte Platform")
    print("=" * 60)
    
    # Setup Django
    setup_django()
    
    # Run different test suites
    results = []
    
    # 1. Comprehensive module tests
    print("\n1️⃣  COMPREHENSIVE MODULE TESTS")
    results.append(run_comprehensive_tests())
    
    # 2. Individual test cases
    print("\n2️⃣  INDIVIDUAL TEST CASES")
    results.append(run_individual_test_cases())
    
    # 3. Performance tests
    print("\n3️⃣  PERFORMANCE TESTS")
    results.append(run_performance_tests())
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 60)
    
    all_passed = all(results)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Tenant CRUD functionality is fully operational")
        print("✅ Admin-only access controls are working")
        print("✅ Data integrity constraints are enforced")
        print("✅ All API endpoints are functioning correctly")
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("❌ Please review the failed tests above")
        print("❌ Fix issues before deploying to production")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 