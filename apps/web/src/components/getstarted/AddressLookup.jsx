import { useState, useEffect } from "react";
import { searchAddress } from "../../services/addressService";
import { CheckIcon, XMarkIcon, MagnifyingGlassIcon } from "@heroicons/react/20/solid";
import PropTypes from "prop-types";

const AddressLookup = ({ onAddressSelected, initialAddress, value, selectedServices }) => {
  const [addressQuery, setAddressQuery] = useState(initialAddress?.full_address || value?.full_address || "");
  const [addressResults, setAddressResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [isGreenTickVisible, setIsGreenTickVisible] = useState(!!(initialAddress || value));
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState(null);

  // Update addressQuery when initialAddress or value changes
  useEffect(() => {
    if (initialAddress?.full_address) {
      setAddressQuery(initialAddress.full_address);
      setIsGreenTickVisible(true);
    } else if (value?.full_address) {
      setAddressQuery(value.full_address);
      setIsGreenTickVisible(true);
    }
  }, [initialAddress, value]);

  // Debounced address search
  const handleAddressSearch = (e) => {
    const value = e.target.value;
    setAddressQuery(value);
    setIsGreenTickVisible(false);
    setSearchError(null);
    if (searchTimeout) clearTimeout(searchTimeout);
    if (value.length < 3) {
      setAddressResults([]);
      setSearchError(null);
      return;
    }
    setLoading(true);
    const timeoutId = setTimeout(async () => {
      try {
        const response = await searchAddress(value);
        setAddressResults(response.results);
        
        if (!response.success) {
          setSearchError(response.error);
        } else if (response.isEmpty) {
          setSearchError('no_results');
        } else {
          setSearchError(null);
        }
      } catch {
        setAddressResults([]);
        setSearchError('service_unavailable');
      } finally {
        setLoading(false);
      }
    }, 1000);
    setSearchTimeout(timeoutId);
  };

  const handleSelectAddress = (address) => {
    setAddressQuery(address.full_address);
    setAddressResults([]);
    setIsGreenTickVisible(true);
    setIsInputFocused(false);
    onAddressSelected(address);
  };

  const clearAddress = () => {
    setAddressQuery("");
    setAddressResults([]);
    setIsGreenTickVisible(false);
    setSearchError(null);
    onAddressSelected(null);
  };

  // Dynamic heading logic
  let heading = "Let's get started — check what plans are available at your address";
  if ((selectedServices?.electricity || selectedServices?.broadband) && value?.full_address) {
    heading = `Your Address:`;
  }

  return (
    <div className="relative px-2 sm:px-4 md:px-6 max-w-2xl mx-auto w-full">
      <div className="text-sm sm:text-base ml-1 sm:ml-2 font-semibold text-slate-300 text-left mb-2 sm:mb-2">
        {heading}
      </div>
      <div className="relative address-search-container">
        <div className="relative flex items-center">
          <MagnifyingGlassIcon className="absolute left-3 h-4 sm:h-5 w-4 sm:w-5 text-gray-400" />
          <input
            type="text"
            value={addressQuery}
            onChange={handleAddressSearch}
            onFocus={() => setIsInputFocused(true)}
            placeholder="Enter your street address here"
            className="w-full p-3 pl-9 sm:pl-10 text-sm sm:text-base border text-secondary-darkgray border-gray-300 bg-gray-50 rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-primary-turquoise"
          />
          {addressQuery && (
            <button
              onClick={clearAddress}
              className="absolute right-10 sm:right-12 text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-4 sm:h-5 w-4 sm:w-5" />
            </button>
          )}
          {loading && (
            <div className="absolute right-3 flex items-center">
              <div className="h-4 sm:h-5 w-4 sm:w-5 border-2 text-secondary-darkgray border-t-primary-turquoise border-gray-200 rounded-full animate-spin" />
            </div>
          )}
          {isGreenTickVisible && !loading && (
            <CheckIcon className="absolute right-3 h-5 sm:h-6 w-5 sm:w-6 text-green-500" />
          )}
        </div>
        {Array.isArray(addressResults) &&
          addressResults.length > 0 &&
          addressQuery.length >= 3 &&
          isInputFocused && (
            <ul className="absolute z-10 w-full mt-1 max-h-60 overflow-y-auto bg-white text-secondary-darkgray border border-gray-300 rounded-lg shadow-md">
              {addressResults.map((address, idx) => (
                <li
                  key={address.full_address || idx}
                  onClick={() => handleSelectAddress(address)}
                  className="cursor-pointer p-2 sm:p-3 hover:bg-gray-100 transition-colors text-sm sm:text-base"
                >
                  {address.full_address}
                </li>
              ))}
            </ul>
          )}
        {searchError && addressQuery.length >= 3 && !loading && isInputFocused && (
          <div className="absolute z-10 w-full mt-1 bg-white text-secondary-darkgray border border-gray-300 rounded-lg shadow-md">
            <div className="p-3 sm:p-4 text-center">
              {searchError === 'no_results' && (
                <>
                  <div className="text-sm sm:text-base text-gray-600 mb-2">
                    No addresses found for "{addressQuery}"
                  </div>
                  <div className="text-xs sm:text-sm text-gray-500">
                    Try a different search term or check your spelling. Make sure to include the street number and name.
                  </div>
                </>
              )}
              {searchError === 'service_unavailable' && (
                <>
                  <div className="text-sm sm:text-base text-red-600 mb-2">
                    Address lookup service unavailable
                  </div>
                  <div className="text-xs sm:text-sm text-gray-500">
                    The address lookup service is currently experiencing issues. Please try again later.
                  </div>
                </>
              )}
              {searchError === 'request_failed' && (
                <>
                  <div className="text-sm sm:text-base text-orange-600 mb-2">
                    Address lookup failed
                  </div>
                  <div className="text-xs sm:text-sm text-gray-500">
                    There was an issue searching for addresses. Please check your connection and try again.
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

AddressLookup.propTypes = {
  onAddressSelected: PropTypes.func.isRequired,
  initialAddress: PropTypes.object,
  value: PropTypes.object,
  selectedServices: PropTypes.object,
};

export default AddressLookup;
