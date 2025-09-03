/* eslint-env jest */
/* global describe, test, beforeEach, expect, jest */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UserDetailModal from '../components/staff/UserDetailModal';
import AccountDetailModal from '../components/staff/AccountDetailModal';
import staffApiService from '../services/staffApi';

// Mock the staff API service
jest.mock('../services/staffApi');

// Mock data
const mockUser = {
  id: 'user-123',
  first_name: 'John',
  last_name: 'Smith',
  email: 'john.smith@example.com',
  user_number: 'U001',
  phone: '+64 21 123 4567',
  is_active: true,
  is_staff: false,
  is_superuser: false,
  is_verified: true,
  user_type: 'residential',
  tenant: {
    id: 'tenant-123',
    name: 'ACME Energy Solutions'
  },
  created_at: '2023-01-01T00:00:00Z',
  last_login: '2023-12-01T10:30:00Z'
};

const mockAccount = {
  id: 'account-123',
  account_number: 'ACC000001',
  account_type: 'residential',
  status: 'active',
  billing_cycle: 'monthly',
  billing_day: 1,
  current_balance: 0.00,
  credit_limit: 1000.00,
  tenant: {
    id: 'tenant-123',
    name: 'ACME Energy Solutions'
  },
  primary_user: {
    id: 'user-123',
    first_name: 'John',
    last_name: 'Smith',
    email: 'john.smith@example.com',
    phone: '+64 21 123 4567',
    is_active: true
  },
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-12-01T10:30:00Z'
};

const mockUserAccounts = [
  {
    id: 'account-123',
    account_number: 'ACC000001',
    account_type: 'residential',
    status: 'active',
    connections: [
      { service_type: 'electricity' },
      { service_type: 'broadband' }
    ]
  }
];

const mockUserContracts = [
  {
    id: 'contract-123',
    contract_number: 'CON000001',
    contract_type: 'electricity',
    status: 'active'
  }
];

const mockAccountUsers = [
  {
    id: 'user-123',
    first_name: 'John',
    last_name: 'Smith',
    email: 'john.smith@example.com',
    is_active: true,
    role: 'primary'
  }
];

const mockAccountContracts = [
  {
    id: 'contract-123',
    contract_number: 'CON000001',
    contract_type: 'electricity',
    status: 'active',
    start_date: '2023-01-01',
    monthly_value: 150.00
  }
];

const mockAccountAddresses = [
  {
    id: 'address-123',
    address_type: 'service',
    address_line1: '123 Main Street',
    address_line2: 'Unit 5',
    city: 'Auckland',
    postal_code: '1010',
    country: 'New Zealand',
    is_primary: true
  }
];

describe('UserDetailModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('displays user information correctly', async () => {
    staffApiService.getUser.mockResolvedValue(mockUser);
    staffApiService.getUserAccounts.mockResolvedValue({ results: mockUserAccounts });
    staffApiService.getUserContracts.mockResolvedValue({ results: mockUserContracts });

    render(
      <UserDetailModal
        isOpen={true}
        onClose={jest.fn()}
        userId="user-123"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('john.smith@example.com')).toBeInTheDocument();
      expect(screen.getByText('U001')).toBeInTheDocument();
      expect(screen.getByText('+64 21 123 4567')).toBeInTheDocument();
      expect(screen.getByText('ACME Energy Solutions')).toBeInTheDocument();
    });
  });

  test('displays associated accounts in accounts tab', async () => {
    staffApiService.getUser.mockResolvedValue(mockUser);
    staffApiService.getUserAccounts.mockResolvedValue({ results: mockUserAccounts });
    staffApiService.getUserContracts.mockResolvedValue({ results: mockUserContracts });

    render(
      <UserDetailModal
        isOpen={true}
        onClose={jest.fn()}
        userId="user-123"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Smith')).toBeInTheDocument();
    });

    // Click on accounts tab
    const accountsTab = screen.getByText('Accounts');
    fireEvent.click(accountsTab);

    await waitFor(() => {
      expect(screen.getByText('ACC000001')).toBeInTheDocument();
      expect(screen.getByText('residential')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
    });
  });

  test('displays associated contracts in contracts tab', async () => {
    staffApiService.getUser.mockResolvedValue(mockUser);
    staffApiService.getUserAccounts.mockResolvedValue({ results: mockUserAccounts });
    staffApiService.getUserContracts.mockResolvedValue({ results: mockUserContracts });

    render(
      <UserDetailModal
        isOpen={true}
        onClose={jest.fn()}
        userId="user-123"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Smith')).toBeInTheDocument();
    });

    // Click on contracts tab
    const contractsTab = screen.getByText('Contracts');
    fireEvent.click(contractsTab);

    await waitFor(() => {
      expect(screen.getByText('CON000001')).toBeInTheDocument();
      expect(screen.getByText('electricity')).toBeInTheDocument();
    });
  });

  test('handles loading state correctly', () => {
    staffApiService.getUser.mockImplementation(() => new Promise(() => {})); // Never resolves
    staffApiService.getUserAccounts.mockResolvedValue({ results: [] });
    staffApiService.getUserContracts.mockResolvedValue({ results: [] });

    render(
      <UserDetailModal
        isOpen={true}
        onClose={jest.fn()}
        userId="user-123"
      />
    );

    expect(screen.getByText('Loading user data...')).toBeInTheDocument();
  });

  test('handles error state correctly', async () => {
    staffApiService.getUser.mockRejectedValue(new Error('Failed to load user'));
    staffApiService.getUserAccounts.mockResolvedValue({ results: [] });
    staffApiService.getUserContracts.mockResolvedValue({ results: [] });

    render(
      <UserDetailModal
        isOpen={true}
        onClose={jest.fn()}
        userId="user-123"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load user')).toBeInTheDocument();
      expect(screen.getByText('Try again')).toBeInTheDocument();
    });
  });

  test('displays empty state when no accounts found', async () => {
    staffApiService.getUser.mockResolvedValue(mockUser);
    staffApiService.getUserAccounts.mockResolvedValue({ results: [] });
    staffApiService.getUserContracts.mockResolvedValue({ results: [] });

    render(
      <UserDetailModal
        isOpen={true}
        onClose={jest.fn()}
        userId="user-123"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Smith')).toBeInTheDocument();
    });

    // Click on accounts tab
    const accountsTab = screen.getByText('Accounts');
    fireEvent.click(accountsTab);

    await waitFor(() => {
      expect(screen.getByText('No accounts found')).toBeInTheDocument();
    });
  });
});

describe('AccountDetailModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('displays account information correctly', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: mockAccountUsers });
    staffApiService.getAccountContracts.mockResolvedValue({ results: mockAccountContracts });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: mockAccountAddresses });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('john.smith@example.com')).toBeInTheDocument();
      expect(screen.getByText('ACME Energy Solutions')).toBeInTheDocument();
    });
  });

  test('displays associated users in users tab', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: mockAccountUsers });
    staffApiService.getAccountContracts.mockResolvedValue({ results: mockAccountContracts });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: mockAccountAddresses });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
    });

    // Click on users tab
    const usersTab = screen.getByText('Users');
    fireEvent.click(usersTab);

    await waitFor(() => {
      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('john.smith@example.com')).toBeInTheDocument();
      expect(screen.getByText('primary')).toBeInTheDocument();
    });
  });

  test('displays associated contracts in contracts tab', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: mockAccountUsers });
    staffApiService.getAccountContracts.mockResolvedValue({ results: mockAccountContracts });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: mockAccountAddresses });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
    });

    // Click on contracts tab
    const contractsTab = screen.getByText('Contracts');
    fireEvent.click(contractsTab);

    await waitFor(() => {
      expect(screen.getByText('CON000001')).toBeInTheDocument();
      expect(screen.getByText('electricity')).toBeInTheDocument();
    });
  });

  test('displays associated addresses in addresses tab', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: mockAccountUsers });
    staffApiService.getAccountContracts.mockResolvedValue({ results: mockAccountContracts });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: mockAccountAddresses });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
    });

    // Click on addresses tab
    const addressesTab = screen.getByText('Addresses');
    fireEvent.click(addressesTab);

    await waitFor(() => {
      expect(screen.getByText('service')).toBeInTheDocument();
      expect(screen.getByText('123 Main Street')).toBeInTheDocument();
      expect(screen.getByText('Unit 5')).toBeInTheDocument();
      expect(screen.getByText('Auckland, 1010')).toBeInTheDocument();
      expect(screen.getByText('Primary')).toBeInTheDocument();
    });
  });

  test('handles empty state when no users found', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: [] });
    staffApiService.getAccountContracts.mockResolvedValue({ results: [] });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: [] });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
    });

    // Click on users tab
    const usersTab = screen.getByText('Users');
    fireEvent.click(usersTab);

    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
  });

  test('handles empty state when no contracts found', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: [] });
    staffApiService.getAccountContracts.mockResolvedValue({ results: [] });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: [] });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
    });

    // Click on contracts tab
    const contractsTab = screen.getByText('Contracts');
    fireEvent.click(contractsTab);

    await waitFor(() => {
      expect(screen.getByText('No contracts found')).toBeInTheDocument();
    });
  });

  test('handles empty state when no addresses found', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: [] });
    staffApiService.getAccountContracts.mockResolvedValue({ results: [] });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: [] });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
    });

    // Click on addresses tab
    const addressesTab = screen.getByText('Addresses');
    fireEvent.click(addressesTab);

    await waitFor(() => {
      expect(screen.getByText('No addresses found')).toBeInTheDocument();
    });
  });

  test('displays summary cards with correct counts', async () => {
    staffApiService.getAccountUsers.mockResolvedValue({ results: mockAccountUsers });
    staffApiService.getAccountContracts.mockResolvedValue({ results: mockAccountContracts });
    staffApiService.getAccountAddresses.mockResolvedValue({ results: mockAccountAddresses });

    render(
      <AccountDetailModal
        isOpen={true}
        onClose={jest.fn()}
        account={mockAccount}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Account #ACC000001')).toBeInTheDocument();
      expect(screen.getByText('1', { selector: '.text-2xl.font-bold.text-blue-600' })).toBeInTheDocument(); // Users count
      expect(screen.getByText('1', { selector: '.text-2xl.font-bold.text-green-600' })).toBeInTheDocument(); // Contracts count
      expect(screen.getByText('1', { selector: '.text-2xl.font-bold.text-purple-600' })).toBeInTheDocument(); // Addresses count
    });
  });
}); 