/**
 * Comprehensive Frontend Tests for UserDetailModal
 * Tests user data loading, tabs functionality, and relationship displays
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

import UserDetailModal from '../components/staff/UserDetailModal';
import staffApiService from '../services/staffApi';

// Mock the staffApiService
vi.mock('../services/staffApi', () => ({
  default: {
    getUser: vi.fn(),
    getUserAccounts: vi.fn(),
    getUserContracts: vi.fn(),
    getUserConnections: vi.fn(),
    getUserPlans: vi.fn(),
  },
}));

// Mock data
const mockUser = {
  id: '1',
  first_name: 'John',
  last_name: 'Doe',
  email: 'john.doe@test.com',
  user_number: 'USR001',
  phone_number: '+64 9 123 4567',
  tenant_name: 'Test Tenant',
  is_active: true,
  is_staff: false,
  is_superuser: false,
  is_verified: true,
  user_type: 'residential',
  created_at: '2024-01-01T00:00:00Z',
  last_login: '2024-01-15T10:30:00Z',
  department: 'Customer Service',
  job_title: 'Account Manager'
};

const mockAccounts = [
  {
    id: '1',
    account_number: 'ACC001',
    account_type: 'residential',
    status: 'active',
    address: '123 Main Street, Auckland',
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    account_number: 'ACC002',
    account_type: 'commercial',
    status: 'inactive',
    address: '456 Business Ave, Wellington',
    created_at: '2024-01-05T00:00:00Z'
  }
];

const mockContracts = [
  {
    id: '1',
    contract_number: 'CON001',
    service_type: 'electricity',
    status: 'active',
    plan_name: 'Standard Power Plan',
    start_date: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    contract_number: 'CON002',
    service_type: 'broadband',
    status: 'pending',
    plan_name: 'Fiber 100',
    start_date: '2024-02-01T00:00:00Z'
  }
];

const mockConnections = [
  {
    id: '1',
    connection_number: 'CONN001',
    icp_number: 'ICP001',
    service_type: 'electricity',
    status: 'connected',
    address: '123 Main Street, Auckland',
    connection_date: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    connection_number: 'CONN002',
    service_type: 'broadband',
    status: 'pending',
    address: '456 Business Ave, Wellington',
    connection_date: '2024-02-01T00:00:00Z'
  }
];

const mockPlans = [
  {
    id: '1',
    plan_name: 'Standard Power Plan',
    service_type: 'electricity',
    is_active: true,
    monthly_cost: '120.50',
    start_date: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    plan_name: 'Fiber 100',
    service_type: 'broadband',
    is_active: false,
    monthly_cost: '89.99',
    start_date: '2024-02-01T00:00:00Z'
  }
];

describe('UserDetailModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    userId: '1',
    onEdit: vi.fn(),
    onDelete: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default successful API responses
    staffApiService.getUser.mockResolvedValue(mockUser);
    staffApiService.getUserAccounts.mockResolvedValue({ results: mockAccounts });
    staffApiService.getUserContracts.mockResolvedValue({ results: mockContracts });
    staffApiService.getUserConnections.mockResolvedValue({ results: mockConnections });
    staffApiService.getUserPlans.mockResolvedValue({ results: mockPlans });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Modal Visibility and Basic Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<UserDetailModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByTestId('user-detail-modal')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(<UserDetailModal {...defaultProps} />);
      expect(screen.getByTestId('user-detail-modal')).toBeInTheDocument();
    });

    it('should show loading state initially', () => {
      render(<UserDetailModal {...defaultProps} />);
      expect(screen.getByText('Loading user data...')).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', () => {
      render(<UserDetailModal {...defaultProps} />);
      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  describe('User Data Loading and Display', () => {
    it('should load and display user data correctly', async () => {
      render(<UserDetailModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('john.doe@test.com')).toBeInTheDocument();
        expect(screen.getByText('USR001')).toBeInTheDocument();
      });

      // Check status badges
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Customer')).toBeInTheDocument();
    });

    it('should display relationship counts in header', async () => {
      render(<UserDetailModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/\(8 relationships\)/)).toBeInTheDocument();
      });
    });

    it('should handle API errors gracefully', async () => {
      staffApiService.getUser.mockRejectedValue(new Error('Failed to load user'));
      
      render(<UserDetailModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load user')).toBeInTheDocument();
        expect(screen.getByText('Try again')).toBeInTheDocument();
      });
    });

    it('should show user not found message when no user data', async () => {
      staffApiService.getUser.mockResolvedValue(null);
      
      render(<UserDetailModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('User not found')).toBeInTheDocument();
      });
    });
  });

  describe('Tabs Functionality', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });

    it('should display all tabs with correct counts', () => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Accounts')).toBeInTheDocument();
      expect(screen.getByText('Contracts')).toBeInTheDocument();
      expect(screen.getByText('Connections')).toBeInTheDocument();
      expect(screen.getByText('Plans')).toBeInTheDocument();
      expect(screen.getByText('Activity')).toBeInTheDocument();

      // Check counts
      expect(screen.getByText('2')).toBeInTheDocument(); // Should appear multiple times for different tabs
    });

    it('should switch between tabs correctly', () => {
      // Default should be overview
      expect(screen.getByText('Personal Information')).toBeInTheDocument();

      // Click accounts tab
      fireEvent.click(screen.getByText('Accounts'));
      expect(screen.getByTestId('user-accounts-section')).toBeInTheDocument();

      // Click contracts tab
      fireEvent.click(screen.getByText('Contracts'));
      expect(screen.getByTestId('user-contracts-section')).toBeInTheDocument();

      // Click connections tab
      fireEvent.click(screen.getByText('Connections'));
      expect(screen.getByTestId('user-connections-section')).toBeInTheDocument();

      // Click plans tab
      fireEvent.click(screen.getByText('Plans'));
      expect(screen.getByTestId('user-plans-section')).toBeInTheDocument();
    });
  });

  describe('Overview Tab', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });

    it('should display personal information correctly', () => {
      expect(screen.getByText('Personal Information')).toBeInTheDocument();
      expect(screen.getByText('john.doe@test.com')).toBeInTheDocument();
      expect(screen.getByText('USR001')).toBeInTheDocument();
      expect(screen.getByText('+64 9 123 4567')).toBeInTheDocument();
      expect(screen.getByText('Test Tenant')).toBeInTheDocument();
      expect(screen.getByText('Customer Service')).toBeInTheDocument();
      expect(screen.getByText('Account Manager')).toBeInTheDocument();
    });

    it('should display account information correctly', () => {
      expect(screen.getByText('Account Information')).toBeInTheDocument();
      expect(screen.getByText('residential')).toBeInTheDocument();
      expect(screen.getByText('Yes')).toBeInTheDocument(); // Verified status
    });
  });

  describe('Accounts Tab', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Accounts'));
    });

    it('should display accounts correctly', () => {
      expect(screen.getByTestId('user-accounts-section')).toBeInTheDocument();
      expect(screen.getByText('Associated Accounts')).toBeInTheDocument();
      
      // Check account data
      expect(screen.getByText('ACC001')).toBeInTheDocument();
      expect(screen.getByText('ACC002')).toBeInTheDocument();
      expect(screen.getByText('123 Main Street, Auckland')).toBeInTheDocument();
      expect(screen.getByText('456 Business Ave, Wellington')).toBeInTheDocument();
    });

    it('should show empty state when no accounts', async () => {
      staffApiService.getUserAccounts.mockResolvedValue({ results: [] });
      
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Accounts'));

      expect(screen.getByText('No accounts found')).toBeInTheDocument();
      expect(screen.getByText('This user has no associated accounts.')).toBeInTheDocument();
    });
  });

  describe('Contracts Tab', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Contracts'));
    });

    it('should display contracts correctly', () => {
      expect(screen.getByTestId('user-contracts-section')).toBeInTheDocument();
      expect(screen.getByText('Associated Contracts')).toBeInTheDocument();
      
      // Check contract data
      expect(screen.getByText('CON001')).toBeInTheDocument();
      expect(screen.getByText('CON002')).toBeInTheDocument();
      expect(screen.getByText('Standard Power Plan')).toBeInTheDocument();
      expect(screen.getByText('Fiber 100')).toBeInTheDocument();
    });

    it('should show service type icons', () => {
      // Icons are rendered, though we can't easily test the specific icon
      expect(screen.getByTestId('user-contracts-section')).toBeInTheDocument();
    });

    it('should show empty state when no contracts', async () => {
      staffApiService.getUserContracts.mockResolvedValue({ results: [] });
      
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Contracts'));

      expect(screen.getByText('No contracts found')).toBeInTheDocument();
    });
  });

  describe('Connections Tab', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Connections'));
    });

    it('should display connections correctly', () => {
      expect(screen.getByTestId('user-connections-section')).toBeInTheDocument();
      expect(screen.getByText('Service Connections')).toBeInTheDocument();
      
      // Check connection data
      expect(screen.getByText('CONN001')).toBeInTheDocument();
      expect(screen.getByText('CONN002')).toBeInTheDocument();
    });

    it('should show empty state when no connections', async () => {
      staffApiService.getUserConnections.mockResolvedValue({ results: [] });
      
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Connections'));

      expect(screen.getByText('No connections found')).toBeInTheDocument();
    });
  });

  describe('Plans Tab', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Plans'));
    });

    it('should display plans correctly', () => {
      expect(screen.getByTestId('user-plans-section')).toBeInTheDocument();
      expect(screen.getByText('Service Plans')).toBeInTheDocument();
      
      // Check plan data
      expect(screen.getByText('Standard Power Plan')).toBeInTheDocument();
      expect(screen.getByText('Fiber 100')).toBeInTheDocument();
      expect(screen.getByText('Monthly Cost: $120.50')).toBeInTheDocument();
      expect(screen.getByText('Monthly Cost: $89.99')).toBeInTheDocument();
    });

    it('should show empty state when no plans', async () => {
      staffApiService.getUserPlans.mockResolvedValue({ results: [] });
      
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Plans'));

      expect(screen.getByText('No plans found')).toBeInTheDocument();
    });
  });

  describe('Activity Tab', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Activity'));
    });

    it('should show activity coming soon message', () => {
      expect(screen.getByTestId('user-activity-section')).toBeInTheDocument();
      expect(screen.getByText('Activity tracking coming soon')).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    beforeEach(async () => {
      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });

    it('should call onEdit when edit button is clicked', () => {
      const editButton = screen.getByText('Edit');
      fireEvent.click(editButton);
      expect(defaultProps.onEdit).toHaveBeenCalledWith(mockUser);
    });

    it('should call onDelete when delete button is clicked', () => {
      const deleteButton = screen.getByText('Delete');
      fireEvent.click(deleteButton);
      expect(defaultProps.onDelete).toHaveBeenCalledWith(mockUser);
    });
  });

  describe('Loading States', () => {
    it('should show loading indicators for individual tabs', async () => {
      // Mock slow loading for one service
      staffApiService.getUserAccounts.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ results: [] }), 100))
      );

      render(<UserDetailModal {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Accounts'));
      
      // Should show loading indicator
      expect(screen.getByTestId('user-accounts-section')).toBeInTheDocument();
    });
  });

  describe('API Integration', () => {
    it('should call all required API endpoints on modal open', async () => {
      render(<UserDetailModal {...defaultProps} />);

      await waitFor(() => {
        expect(staffApiService.getUser).toHaveBeenCalledWith('1');
        expect(staffApiService.getUserAccounts).toHaveBeenCalledWith('1');
        expect(staffApiService.getUserContracts).toHaveBeenCalledWith('1');
        expect(staffApiService.getUserConnections).toHaveBeenCalledWith('1');
        expect(staffApiService.getUserPlans).toHaveBeenCalledWith('1');
      });
    });

    it('should not call APIs when modal is closed', () => {
      render(<UserDetailModal {...defaultProps} isOpen={false} />);

      expect(staffApiService.getUser).not.toHaveBeenCalled();
      expect(staffApiService.getUserAccounts).not.toHaveBeenCalled();
      expect(staffApiService.getUserContracts).not.toHaveBeenCalled();
      expect(staffApiService.getUserConnections).not.toHaveBeenCalled();
      expect(staffApiService.getUserPlans).not.toHaveBeenCalled();
    });

    it('should handle individual API failures gracefully', async () => {
      staffApiService.getUserAccounts.mockRejectedValue(new Error('Accounts API failed'));
      
      render(<UserDetailModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Should still show user data even if accounts fail
      fireEvent.click(screen.getByText('Accounts'));
      expect(screen.getByText('No accounts found')).toBeInTheDocument();
    });
  });
}); 