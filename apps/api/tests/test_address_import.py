import os
import tempfile
import csv
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from users.models import Tenant
from web_support.address_plans.models import Address


class AddressImportTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            contact_email='test@example.com'
        )
        
    def create_test_csv(self, data):
        """Create a temporary CSV file with test data"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        if data:
            writer = csv.DictWriter(temp_file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        temp_file.close()
        return temp_file.name
    
    def test_import_with_valid_tenant(self):
        """Test importing addresses with a valid tenant"""
        test_data = [
            {
                'address_id': '1',
                'source_dataset': 'test',
                'change_id': '1',
                'full_address': '123 Test Street',
                'town_city': 'Test City',
                'suburb_locality': 'Test Suburb',
                'gd2000_xcoord': '1234567.89',
                'gd2000_ycoord': '9876543.21',
                'shape_X': '1234567.89',
                'shape_Y': '9876543.21'
            },
            {
                'address_id': '2',
                'source_dataset': 'test',
                'change_id': '2',
                'full_address': '456 Another Street',
                'town_city': 'Test City',
                'suburb_locality': 'Test Suburb',
                'gd2000_xcoord': '',  # Test empty string handling
                'gd2000_ycoord': '',
                'shape_X': '',
                'shape_Y': ''
            }
        ]
        
        csv_file = self.create_test_csv(test_data)
        
        try:
            # Test import with valid tenant
            call_command('import_csv', csv_file, '--tenant', self.tenant.slug)
            
            # Verify addresses were created
            addresses = Address.objects.all_tenants().filter(tenant=self.tenant)
            self.assertEqual(addresses.count(), 2)
            
            # Verify first address
            addr1 = addresses.get(address_id=1)
            self.assertEqual(addr1.full_address, '123 Test Street')
            self.assertEqual(addr1.town_city, 'Test City')
            self.assertEqual(addr1.tenant, self.tenant)
            self.assertIsNotNone(addr1.gd2000_xcoord)
            self.assertIsNotNone(addr1.gd2000_ycoord)
            
            # Verify second address (with empty coordinates)
            addr2 = addresses.get(address_id=2)
            self.assertEqual(addr2.full_address, '456 Another Street')
            self.assertIsNone(addr2.gd2000_xcoord)
            self.assertIsNone(addr2.gd2000_ycoord)
            
        finally:
            os.unlink(csv_file)
    
    def test_import_with_invalid_tenant(self):
        """Test importing addresses with an invalid tenant"""
        test_data = [
            {
                'address_id': '1',
                'source_dataset': 'test',
                'change_id': '1',
                'full_address': '123 Test Street',
                'town_city': 'Test City'
            }
        ]
        
        csv_file = self.create_test_csv(test_data)
        
        try:
            # Test import with invalid tenant
            with self.assertRaises(CommandError) as context:
                call_command('import_csv', csv_file, '--tenant', 'nonexistent-tenant')
            
            self.assertIn('does not exist', str(context.exception))
            
        finally:
            os.unlink(csv_file)
    
    def test_import_with_shared_addresses(self):
        """Test importing addresses marked as shared"""
        test_data = [
            {
                'address_id': '1',
                'source_dataset': 'test',
                'change_id': '1',
                'full_address': '123 Shared Street',
                'town_city': 'Shared City'
            }
        ]
        
        csv_file = self.create_test_csv(test_data)
        
        try:
            # Test import with shared flag
            call_command('import_csv', csv_file, '--tenant', self.tenant.slug, '--shared')
            
            # Verify address was created and marked as shared
            address = Address.objects.all_tenants().get(address_id=1)
            self.assertTrue(address.is_shared)
            self.assertEqual(address.tenant, self.tenant)
            
        finally:
            os.unlink(csv_file)
    
    def test_import_with_missing_file(self):
        """Test importing with a missing CSV file"""
        with self.assertRaises(CommandError) as context:
            call_command('import_csv', 'nonexistent.csv', '--tenant', self.tenant.slug)
        
        self.assertIn('not found', str(context.exception))
    
    def test_import_with_empty_file(self):
        """Test importing with an empty CSV file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.close()
        
        try:
            with self.assertRaises(CommandError) as context:
                call_command('import_csv', temp_file.name, '--tenant', self.tenant.slug)
            
            self.assertIn('empty', str(context.exception))
            
        finally:
            os.unlink(temp_file.name)
    
    def test_import_duplicate_addresses(self):
        """Test importing duplicate addresses (should be ignored)"""
        test_data = [
            {
                'address_id': '1',
                'source_dataset': 'test',
                'change_id': '1',
                'full_address': '123 Test Street',
                'town_city': 'Test City'
            },
            {
                'address_id': '1',  # Duplicate
                'source_dataset': 'test',
                'change_id': '1',
                'full_address': '123 Test Street',
                'town_city': 'Test City'
            }
        ]
        
        csv_file = self.create_test_csv(test_data)
        
        try:
            # Import first time
            call_command('import_csv', csv_file, '--tenant', self.tenant.slug)
            
            # Verify only one address was created
            addresses = Address.objects.all_tenants().filter(tenant=self.tenant)
            self.assertEqual(addresses.count(), 1)
            
            # Import again (should ignore duplicates)
            call_command('import_csv', csv_file, '--tenant', self.tenant.slug)
            
            # Verify still only one address
            addresses = Address.objects.all_tenants().filter(tenant=self.tenant)
            self.assertEqual(addresses.count(), 1)
            
        finally:
            os.unlink(csv_file.name)
    
    def test_batch_processing(self):
        """Test batch processing with custom batch size"""
        test_data = [
            {
                'address_id': str(i),
                'source_dataset': 'test',
                'change_id': str(i),
                'full_address': f'{i} Test Street',
                'town_city': 'Test City'
            }
            for i in range(1, 6)  # 5 addresses
        ]
        
        csv_file = self.create_test_csv(test_data)
        
        try:
            # Test with batch size of 2
            call_command('import_csv', csv_file, '--tenant', self.tenant.slug, '--batch-size', '2')
            
            # Verify all addresses were created
            addresses = Address.objects.all_tenants().filter(tenant=self.tenant)
            self.assertEqual(addresses.count(), 5)
            
        finally:
            os.unlink(csv_file) 