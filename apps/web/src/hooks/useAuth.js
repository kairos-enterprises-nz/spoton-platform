// src/hooks/useAuth.js
import { useContext } from 'react';
// Import AuthContext directly from where AuthProvider is defined and AuthContext is created and exported
import AuthContext from '../context/AuthContext'; // Changed from 'authContextDefinition'

export const useAuth = () => {
  const context = useContext(AuthContext);

  // CRITICAL: Check against null, because createContext(null) is the default
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider. The context value is null.');
  }
  return context;
};