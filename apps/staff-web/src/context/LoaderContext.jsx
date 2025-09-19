// src/context/LoaderContext.js
import { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';

const LoaderContext = createContext();

export const LoaderProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  return (
    <LoaderContext.Provider value={{ loading, setLoading }}>
      {children}
    </LoaderContext.Provider>
  );
};

LoaderProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export const useLoader = () => useContext(LoaderContext);

// Export the context itself for direct useContext usage
export { LoaderContext };
