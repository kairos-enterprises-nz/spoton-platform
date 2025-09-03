from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from users.models import Tenant

User = get_user_model()

class StaffAPIEndpointTests(APITestCase):
    """
    End-to-end tests for the staff API endpoints, covering versioning,
    authentication, and permissions.
    """

    def setUp(self):
        """Set up the test environment."""
        self.client = APIClient()
        
        # Create a default tenant
        self.tenant = Tenant.objects.create(name="Default Tenant", slug="default")

        # Create a staff user
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            first_name="Staff",
            last_name="User",
            is_staff=True,
            tenant=self.tenant
        )

        # Create a non-staff user
        self.non_staff_user = User.objects.create_user(
            email="customer@example.com",
            password="password123",
            first_name="Customer",
            last_name="User",
            is_staff=False,
            tenant=self.tenant
        )

    def test_staff_can_access_versioned_endpoint(self):
        """Ensure staff users can access the v1 endpoint."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('tenant-list')
        response = self.client.get(f"/api/staff/v1{url}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('version', response.data)
        self.assertIn('api_version', response.data['version'])

    def test_staff_can_access_legacy_endpoint(self):
        """Ensure staff users can access the legacy (non-versioned) endpoint."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('tenant-list')
        response = self.client.get(f"/api/staff{url}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_staff_user_denied_access(self):
        """Ensure non-staff users receive a 403 Forbidden error."""
        self.client.force_authenticate(user=self.non_staff_user)
        url = reverse('tenant-list')
        response = self.client.get(f"/api/staff/v1{url}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_denied_access(self):
        """Ensure unauthenticated users receive a 401 Unauthorized error."""
        url = reverse('tenant-list')
        response = self.client.get(f"/api/staff/v1{url}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_endpoint_returns_user_data(self):
        """Ensure the profile endpoint returns correct data for the authenticated user."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('staff-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.staff_user.email)

"""
To run these tests:
python manage.py test users.tests.test_staff_api_e2e
""" 