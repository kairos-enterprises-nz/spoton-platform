import json
from django.test import TestCase, Client
from django.urls import reverse
from users.models import Tenant
from web_support.address_plans.models import Address


class AddressAPIFixTest(TestCase):
    """Test that the address API works correctly after the tenant-aware fix"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            contact_email='test@example.com'
        )
        
        # Create test addresses
        self.addresses = [
            Address.objects.create(
                tenant=self.tenant,
                address_id=1,
                source_dataset='test',
                change_id=1,
                full_address='123 Auckland Street, Auckland Central, Auckland',
                town_city='Auckland',
                suburb_locality='Auckland Central'
            ),
            Address.objects.create(
                tenant=self.tenant,
                address_id=2,
                source_dataset='test',
                change_id=2,
                full_address='456 Queen Street, Auckland Central, Auckland',
                town_city='Auckland',
                suburb_locality='Auckland Central'
            ),
            Address.objects.create(
                tenant=self.tenant,
                address_id=3,
                source_dataset='test',
                change_id=3,
                full_address='789 Wellington Road, Wellington Central, Wellington',
                town_city='Wellington',
                suburb_locality='Wellington Central'
            )
        ]
    
    def test_address_lookup_with_auck_query(self):
        """Test that the API returns Auckland addresses for 'auck' query"""
        response = self.client.get('/api/web/address/?query=auck')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)
        
        # Check that all results contain Auckland addresses
        for result in data['results']:
            self.assertIn('full_address', result)
            # Should contain either 'Auckland' or match the fuzzy search
            address = result['full_address'].lower()
            self.assertTrue(
                'auckland' in address or 'auck' in address,
                f"Address '{result['full_address']}' doesn't seem to match 'auck' query"
            )
    
    def test_address_lookup_with_queen_query(self):
        """Test that the API returns Queen Street addresses for 'queen' query"""
        response = self.client.get('/api/web/address/?query=queen')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)
        
        # Check that results contain Queen Street addresses
        found_queen = False
        for result in data['results']:
            if 'queen' in result['full_address'].lower():
                found_queen = True
                break
        
        self.assertTrue(found_queen, "Expected to find Queen Street addresses")
    
    def test_address_lookup_with_wellington_query(self):
        """Test that the API returns Wellington addresses for 'wellington' query"""
        response = self.client.get('/api/web/address/?query=wellington')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)
        
        # Check that results contain Wellington addresses
        found_wellington = False
        for result in data['results']:
            if 'wellington' in result['full_address'].lower():
                found_wellington = True
                break
        
        self.assertTrue(found_wellington, "Expected to find Wellington addresses")
    
    def test_address_lookup_empty_query(self):
        """Test that the API returns an error for empty query"""
        response = self.client.get('/api/web/address/?query=')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No query provided.')
    
    def test_address_lookup_no_results(self):
        """Test that the API returns empty results for non-existent addresses"""
        response = self.client.get('/api/web/address/?query=nonexistentaddress12345')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 0)
    
    def test_address_lookup_across_all_tenants(self):
        """Test that the API searches across all tenants (not just current tenant)"""
        # Create another tenant with an address
        other_tenant = Tenant.objects.create(
            name='Other Tenant',
            slug='other-tenant',
            contact_email='other@example.com'
        )
        
        other_address = Address.objects.create(
            tenant=other_tenant,
            address_id=4,
            source_dataset='test',
            change_id=4,
            full_address='999 Unique Street, Special City, Special Region',
            town_city='Special City',
            suburb_locality='Special City'
        )
        
        # Search for the unique address
        response = self.client.get('/api/web/address/?query=unique street')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)
        
        # Should find the address from the other tenant
        found_unique = False
        for result in data['results']:
            if 'unique street' in result['full_address'].lower():
                found_unique = True
                break
        
        self.assertTrue(found_unique, "Expected to find address from other tenant")
    
    def test_address_summary_api(self):
        """Test that the address summary API also works correctly"""
        response = self.client.get('/api/web/address-summary/?query=auckland street')
        
        # Should return 200 or 404 depending on exact match
        self.assertIn(response.status_code, [200, 404])
        
        if response.status_code == 200:
            data = json.loads(response.content)
            self.assertIn('status', data) 