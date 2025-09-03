#!/usr/bin/env python
"""
Test runner script for billing engine implementation.
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner


def run_billing_tests():
    """Run all billing-related tests."""
    
    # Configure Django settings if not already configured
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
        django.setup()
    
    # Get the Django test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Define test modules to run
    test_modules = [
        'finance.billing.tests.test_services',
        'finance.billing.tests.test_views',
        'finance.invoices.tests.test_services',
        'finance.tests.test_integration',
    ]
    
    print("🧪 Running Billing Engine Tests")
    print("=" * 50)
    
    # Run tests
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    run_billing_tests()
