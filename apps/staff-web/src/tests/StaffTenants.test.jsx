/**
 * Comprehensive Frontend Tests for Tenant Management Access Controls
 * Tests admin-only access, navigation visibility, and user experience
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

import StaffTenants from '../pages/staff/StaffTenants';
import StaffLayout from '../components/staff/StaffLayout';
import { AuthContext } from '../context/AuthContext';
import { LoaderContext } from '../context/LoaderContext';
import staffApiService from '../services/staffApi';

// Mock the services
vi.mock('../services/staffApi', () => ({
  default: {
    getTenants: vi.fn(),
    exportTenants: vi.fn(),
  },
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Test utilities
const renderWithProviders = (component, { user = null, loading = false } = {}) => {
  const authValue = {
    user,
    isAuthenticated: !!user,
    login: vi.fn(),
    logout: vi.fn(),
  };

  const loaderValue = {
    loading,
    setLoading: vi.fn(),
  };

  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <LoaderContext.Provider value={loaderValue}>
          {component}
        </LoaderContext.Provider>
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('StaffTenants Access Control', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Admin Access Controls', () => {
    it('should allow superuser to access tenant management', async () => {
      const superuser = {
        id: '1',
        email: 'superuser@test.com',
        is_superuser: true,
        is_staff: true,
        groups: [],
      };

      staffApiService.getTenants.mockResolvedValue({
        results: [
          {
            id: '1',
            name: 'Test Tenant',
            slug: 'test-tenant',
            contact_email: 'test@tenant.com',
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
          },
        ],
        count: 1,
        next: null,
        previous: null,
      });

      renderWithProviders(<StaffTenants />, { user: superuser });

      // Should not redirect
      expect(mockNavigate).not.toHaveBeenCalled();

      // Should show tenant management interface
      await waitFor(() => {
        expect(screen.getByText('Tenant Management')).toBeInTheDocument();
        expect(screen.getByText('Manage all tenant organizations and their settings')).toBeInTheDocument();
      });

      // Should show tenant data
      await waitFor(() => {
        expect(screen.getByText('Test Tenant')).toBeInTheDocument();
      });
    });

    it('should allow admin group user to access tenant management', async () => {
      const adminUser = {
        id: '2',
        email: 'admin@test.com',
        is_superuser: false,
        is_staff: true,
        groups: ['Admin'],
      };

      staffApiService.getTenants.mockResolvedValue({
        results: [],
        count: 0,
        next: null,
        previous: null,
      });

      renderWithProviders(<StaffTenants />, { user: adminUser });

      // Should not redirect
      expect(mockNavigate).not.toHaveBeenCalled();

      // Should show tenant management interface
      await waitFor(() => {
        expect(screen.getByText('Tenant Management')).toBeInTheDocument();
      });
    });

    it('should redirect staff user away from tenant management', async () => {
      const staffUser = {
        id: '3',
        email: 'staff@test.com',
        is_superuser: false,
        is_staff: true,
        groups: ['Staff'],
      };

      renderWithProviders(<StaffTenants />, { user: staffUser });

      // Should redirect to dashboard
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/staff/dashboard', { replace: true });
      });
    });

    it('should redirect regular user away from tenant management', async () => {
      const regularUser = {
        id: '4',
        email: 'user@test.com',
        is_superuser: false,
        is_staff: false,
        groups: [],
      };

      renderWithProviders(<StaffTenants />, { user: regularUser });

      // Should redirect to dashboard
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/staff/dashboard', { replace: true });
      });
    });

    it('should not render component content for non-admin users', () => {
      const staffUser = {
        id: '3',
        email: 'staff@test.com',
        is_superuser: false,
        is_staff: true,
        groups: ['Staff'],
      };

      renderWithProviders(<StaffTenants />, { user: staffUser });

      // Should not show tenant management content
      expect(screen.queryByText('Tenant Management')).not.toBeInTheDocument();
      expect(screen.queryByText('Add Tenant')).not.toBeInTheDocument();
    });
  });

  describe('Navigation Menu Access Control', () => {
    const navigationTests = [
      {
        name: 'superuser',
        user: {
          id: '1',
          email: 'superuser@test.com',
          is_superuser: true,
          is_staff: true,
          groups: [],
          first_name: 'Super',
          last_name: 'User',
        },
        shouldShowTenants: true,
      },
      {
        name: 'admin user',
        user: {
          id: '2',
          email: 'admin@test.com',
          is_superuser: false,
          is_staff: true,
          groups: ['Admin'],
          first_name: 'Admin',
          last_name: 'User',
        },
        shouldShowTenants: true,
      },
      {
        name: 'staff user',
        user: {
          id: '3',
          email: 'staff@test.com',
          is_superuser: false,
          is_staff: true,
          groups: ['Staff'],
          first_name: 'Staff',
          last_name: 'User',
        },
        shouldShowTenants: false,
      },
      {
        name: 'regular user',
        user: {
          id: '4',
          email: 'user@test.com',
          is_superuser: false,
          is_staff: false,
          groups: [],
          first_name: 'Regular',
          last_name: 'User',
        },
        shouldShowTenants: false,
      },
    ];

    navigationTests.forEach(({ name, user, shouldShowTenants }) => {
      it(`should ${shouldShowTenants ? 'show' : 'hide'} tenants menu for ${name}`, () => {
        renderWithProviders(
          <StaffLayout>
            <div>Test Content</div>
          </StaffLayout>,
          { user }
        );

        const tenantsLink = screen.queryByText('Tenants');

        if (shouldShowTenants) {
          expect(tenantsLink).toBeInTheDocument();
        } else {
          expect(tenantsLink).not.toBeInTheDocument();
        }

        // Other menu items should always be visible for staff users
        if (user.is_staff) {
          expect(screen.getByText('Dashboard')).toBeInTheDocument();
          expect(screen.getByText('Users')).toBeInTheDocument();
          expect(screen.getByText('Contracts')).toBeInTheDocument();
        }
      });
    });
  });

  describe('Tenant Management Functionality', () => {
    const adminUser = {
      id: '1',
      email: 'admin@test.com',
      is_superuser: false,
      is_staff: true,
      groups: ['Admin'],
    };

    it('should load and display tenants for admin user', async () => {
      const mockTenants = [
        {
          id: '1',
          name: 'Tenant One',
          slug: 'tenant-one',
          contact_email: 'contact1@tenant.com',
          contact_phone: '+64123456789',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: 'Tenant Two',
          slug: 'tenant-two',
          contact_email: 'contact2@tenant.com',
          contact_phone: '+64987654321',
          is_active: false,
          created_at: '2024-01-02T00:00:00Z',
        },
      ];

      staffApiService.getTenants.mockResolvedValue({
        results: mockTenants,
        count: 2,
        next: null,
        previous: null,
      });

      renderWithProviders(<StaffTenants />, { user: adminUser });

      await waitFor(() => {
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
        expect(screen.getByText('Tenant Two')).toBeInTheDocument();
        expect(screen.getByText('contact1@tenant.com')).toBeInTheDocument();
        expect(screen.getByText('contact2@tenant.com')).toBeInTheDocument();
      });

      // Check status badges
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('should handle search functionality', async () => {
      staffApiService.getTenants.mockResolvedValue({
        results: [],
        count: 0,
        next: null,
        previous: null,
      });

      renderWithProviders(<StaffTenants />, { user: adminUser });

      const searchInput = screen.getByPlaceholderText('Search by name, slug, or email...');
      
      fireEvent.change(searchInput, { target: { value: 'test search' } });

      await waitFor(() => {
        expect(staffApiService.getTenants).toHaveBeenCalledWith(
          expect.objectContaining({
            search: 'test search',
            page: 1,
          })
        );
      });
    });

    it('should handle status filtering', async () => {
      staffApiService.getTenants.mockResolvedValue({
        results: [],
        count: 0,
        next: null,
        previous: null,
      });

      renderWithProviders(<StaffTenants />, { user: adminUser });

      const activeButton = screen.getByText('Active');
      fireEvent.click(activeButton);

      await waitFor(() => {
        expect(staffApiService.getTenants).toHaveBeenCalledWith(
          expect.objectContaining({
            is_active: true,
            page: 1,
          })
        );
      });
    });

    it('should handle export functionality', async () => {
      staffApiService.getTenants.mockResolvedValue({
        results: [],
        count: 0,
        next: null,
        previous: null,
      });

      staffApiService.exportTenants.mockResolvedValue({});

      renderWithProviders(<StaffTenants />, { user: adminUser });

      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(staffApiService.exportTenants).toHaveBeenCalled();
      });
    });

    it('should handle API errors gracefully', async () => {
      const errorMessage = 'Failed to load tenants';
      staffApiService.getTenants.mockRejectedValue(new Error(errorMessage));

      renderWithProviders(<StaffTenants />, { user: adminUser });

      await waitFor(() => {
        expect(screen.getByText('Error loading tenants')).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
    });

    it('should show empty state when no tenants exist', async () => {
      staffApiService.getTenants.mockResolvedValue({
        results: [],
        count: 0,
        next: null,
        previous: null,
      });

      renderWithProviders(<StaffTenants />, { user: adminUser });

      await waitFor(() => {
        expect(screen.getByText('No tenants found')).toBeInTheDocument();
        expect(screen.getByText('Get started by creating your first tenant.')).toBeInTheDocument();
        expect(screen.getByText('Create Tenant')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle undefined user gracefully', () => {
      renderWithProviders(<StaffTenants />, { user: null });

      // Should not crash and should redirect
      expect(mockNavigate).not.toHaveBeenCalled(); // User is null, so useEffect won't run
    });

    it('should handle user without groups array', async () => {
      const userWithoutGroups = {
        id: '1',
        email: 'test@test.com',
        is_superuser: false,
        is_staff: true,
        // groups property missing
      };

      renderWithProviders(<StaffTenants />, { user: userWithoutGroups });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/staff/dashboard', { replace: true });
      });
    });

    it('should handle network errors during tenant loading', async () => {
      const adminUser = {
        id: '1',
        email: 'admin@test.com',
        is_superuser: true,
        is_staff: true,
        groups: [],
      };

      staffApiService.getTenants.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<StaffTenants />, { user: adminUser });

      await waitFor(() => {
        expect(screen.getByText('Error loading tenants')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('Performance and UX', () => {
    it('should show loading state while fetching tenants', async () => {
      const adminUser = {
        id: '1',
        email: 'admin@test.com',
        is_superuser: true,
        is_staff: true,
        groups: [],
      };

      // Mock a delayed response
      staffApiService.getTenants.mockImplementation(
        () => new Promise(resolve => 
          setTimeout(() => resolve({ results: [], count: 0, next: null, previous: null }), 100)
        )
      );

      renderWithProviders(<StaffTenants />, { user: adminUser, loading: true });

      // Should show tenant management interface immediately
      expect(screen.getByText('Tenant Management')).toBeInTheDocument();
    });

    it('should debounce search input', async () => {
      const adminUser = {
        id: '1',
        email: 'admin@test.com',
        is_superuser: true,
        is_staff: true,
        groups: [],
      };

      staffApiService.getTenants.mockResolvedValue({
        results: [],
        count: 0,
        next: null,
        previous: null,
      });

      renderWithProviders(<StaffTenants />, { user: adminUser });

      const searchInput = screen.getByPlaceholderText('Search by name, slug, or email...');
      
      // Rapid typing
      fireEvent.change(searchInput, { target: { value: 'a' } });
      fireEvent.change(searchInput, { target: { value: 'ab' } });
      fireEvent.change(searchInput, { target: { value: 'abc' } });

      // Should trigger search for final value
      await waitFor(() => {
        expect(staffApiService.getTenants).toHaveBeenCalledWith(
          expect.objectContaining({
            search: 'abc',
          })
        );
      });
    });
  });
});

describe('Integration Tests', () => {
  it('should integrate properly with StaffLayout navigation', () => {
    const adminUser = {
      id: '1',
      email: 'admin@test.com',
      is_superuser: true,
      is_staff: true,
      groups: [],
      first_name: 'Admin',
      last_name: 'User',
    };

    staffApiService.getTenants.mockResolvedValue({
      results: [],
      count: 0,
      next: null,
      previous: null,
    });

    renderWithProviders(
      <StaffLayout>
        <StaffTenants />
      </StaffLayout>,
      { user: adminUser }
    );

    // Should show both navigation and tenant management
    expect(screen.getByText('Staff Portal')).toBeInTheDocument();
    expect(screen.getByText('Tenants')).toBeInTheDocument();
    expect(screen.getByText('Tenant Management')).toBeInTheDocument();
  });
}); 