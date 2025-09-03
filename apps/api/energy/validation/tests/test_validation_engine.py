import pandas as pd
from datetime import datetime, timedelta
from django.test import TestCase
from energy.validation.validation_engine import ValidationEngine

class ValidationEngineTests(TestCase):
    def setUp(self):
        self.engine = ValidationEngine()

    def test_high_value_check(self):
        """Test the high value validation check."""
        timestamps = pd.to_datetime(pd.date_range(start='2024-01-01', periods=48, freq='30min'))
        values = [10.5] * 48
        values[5] = 101  # Exceeds interval threshold
        data = pd.DataFrame({'timestamp': timestamps, 'value': values})
        
        results = self.engine.check_high_values('MTR1', data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, 'fail')
        self.assertEqual(results[0].rule_name, 'Interval High Value')

    def test_negative_value_check(self):
        """Test the negative value validation check."""
        timestamps = pd.to_datetime(pd.date_range(start='2024-01-01', periods=48, freq='30min'))
        values = [10.5] * 48
        values[10] = -1
        data = pd.DataFrame({'timestamp': timestamps, 'value': values})
        
        results = self.engine.check_negative_values('MTR2', data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, 'fail')

    def test_abnormal_trend_check(self):
        """Test the abnormal trend validation check."""
        timestamps = pd.to_datetime(pd.date_range(start='2024-01-01', periods=96, freq='30min'))
        values = [10] * 96
        values[72] = 51 # Day 2 sum is 510, Day 1 sum is 480. Change is < 400%
        
        # This will fail. Day 2 sum is now much larger
        values[73] = 600

        data = pd.DataFrame({'timestamp': timestamps, 'value': values})
        
        results = self.engine.check_abnormal_trends('MTR3', data)
        self.assertTrue(any(r.status == 'fail' for r in results))

    def test_missing_values_check(self):
        """Test the missing values validation check."""
        timestamps = pd.to_datetime(['2024-01-01 00:00', '2024-01-01 00:30', '2024-01-01 01:30'])
        values = [10, 11, 12]
        data = pd.DataFrame({'timestamp': timestamps, 'value': values})
        
        results = self.engine.check_missing_values('MTR4', data)
        self.assertTrue(any(r.status == 'fail' for r in results))
        self.assertIn('missing intervals', results[0].details)

    def test_estimation_interpolation(self):
        """Test the interpolation estimation for small gaps."""
        timestamps = pd.to_datetime(pd.date_range(start='2024-01-01', periods=5, freq='30min'))
        values = [10, None, None, 13, 14] # 2 missing values
        data = pd.DataFrame({'timestamp': timestamps, 'value': values})
        
        estimated_data = self.engine.estimate_hhr('MTR5', data)
        self.assertFalse(estimated_data['value'].isnull().any())
        self.assertAlmostEqual(estimated_data['value'][1], 11.0)
        self.assertAlmostEqual(estimated_data['value'][2], 12.0) 