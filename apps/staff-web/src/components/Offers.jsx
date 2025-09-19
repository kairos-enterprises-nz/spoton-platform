import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

// Use the centralized API client instead of hardcoded URL
import apiClient from '../services/apiClient';

export default function Offers() {
  const { user, accessToken } = useAuth();
  const navigate = useNavigate();

  // State for managing form data
  const [serviceAddresses, setServiceAddresses] = useState([]);
  const [utilities, setUtilities] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState('');
  const [selectedUtility, setSelectedUtility] = useState('');
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) {
  navigate('/login');
    }

    // Fetch service addresses and utility types when the component mounts
    const fetchData = async () => {
      try {
        // Fetch service addresses
        const responseAddresses = await apiClient.get('/service-addresses/');
        setServiceAddresses(responseAddresses.data);

        // Fetch utilities types (electricity, gas, etc.)
        const responseUtilities = await apiClient.get('/utilities/');
        setUtilities(responseUtilities.data);
      } catch (error) {
        setError('Failed to fetch data. Please try again later.');
      }
    };

    fetchData();
  }, [user, accessToken, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setOffers([]); // Clear previous offers

    try {
      // Request offers based on selected address and utility
      const responseOffers = await apiClient.post('/offers/', {
        address: selectedAddress,
        utility: selectedUtility,
      });
      setOffers(responseOffers.data); // Set the received offers
    } catch (error) {
      setError('Error fetching offers. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Request Offers</h1>

      {error && <div className="text-red-500 mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Service Address Dropdown */}
        <div>
          <label htmlFor="service-address" className="block text-sm font-medium text-gray-700">
            Service Address
          </label>
          <select
            id="service-address"
            name="service-address"
            className="mt-1 block w-full p-2 border border-gray-300 rounded-md"
            value={selectedAddress}
            onChange={(e) => setSelectedAddress(e.target.value)}
            required
          >
            <option value="">Select Service Address</option>
            {serviceAddresses.map((address) => (
              <option key={address.id} value={address.id}>
                {address.address_line_1}, {address.city}, {address.state}
              </option>
            ))}
          </select>
        </div>

        {/* Utility Type Dropdown */}
        <div>
          <label htmlFor="utility-type" className="block text-sm font-medium text-gray-700">
            Utility Type
          </label>
          <select
            id="utility-type"
            name="utility-type"
            className="mt-1 block w-full p-2 border border-gray-300 rounded-md"
            value={selectedUtility}
            onChange={(e) => setSelectedUtility(e.target.value)}
            required
          >
            <option value="">Select Utility</option>
            {utilities.map((utility) => (
              <option key={utility.id} value={utility.id}>
                {utility.name}
              </option>
            ))}
          </select>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-700 disabled:bg-gray-300"
          disabled={loading}
        >
          {loading ? 'Fetching Offers...' : 'Request Offers'}
        </button>
      </form>

      {/* Displaying Offers */}
      {offers.length > 0 && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold">Offers</h2>
          <ul className="mt-4 space-y-4">
            {offers.map((offer) => (
              <li key={offer.id} className="p-4 border border-gray-300 rounded-md">
                <div className="flex justify-between">
                  <span className="font-semibold">{offer.provider}</span>
                  <span className="text-gray-500">{offer.price}</span>
                </div>
                <div className="mt-2">{offer.description}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
