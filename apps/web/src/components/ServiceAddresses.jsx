import { useState } from 'react';

const ServiceAddresses = () => {
  const [addresses, setAddresses] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [newAddress, setNewAddress] = useState('');

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const handleAddAddress = (event) => {
    event.preventDefault();
    if (newAddress && !addresses.includes(newAddress)) {
      setAddresses([...addresses, newAddress]);
      setNewAddress('');
    }
  };

  const filteredAddresses = addresses.filter((address) =>
    address.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">Service Addresses</h2>

      {/* Search Bar */}
      <div className="mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search addresses"
          className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Address List */}
      <div className="space-y-2 mb-4">
        {filteredAddresses.length > 0 ? (
          filteredAddresses.map((address, index) => (
            <div key={index} className="p-2 border border-gray-300 rounded-md">
              {address}
            </div>
          ))
        ) : (
          <p className="text-gray-500">No addresses found.</p>
        )}
      </div>

      {/* Add Address Form */}
      <form onSubmit={handleAddAddress}>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newAddress}
            onChange={(e) => setNewAddress(e.target.value)}
            placeholder="Enter new address"
            className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition"
          >
            Add
          </button>
        </div>
      </form>
    </div>
  );
};

export default ServiceAddresses;
