// MUST BE FIRST: Disable console logs in production
import './utils/consoleOverride.js';

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import { AuthProvider } from './context/AuthContext';
import { LoaderProvider } from './context/LoaderContext';
import './styles/main.css';

// Initialize environment-specific utilities
import logger from './utils/logger.js';
import errorHandler from './utils/errorHandler.js';

// Log initialization info (UAT only)
logger.uatOnly('SpotOn Portal App initializing...', {
  environment: typeof __ENVIRONMENT__ !== 'undefined' ? __ENVIRONMENT__ : 'development',
  timestamp: new Date().toISOString()
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <LoaderProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </LoaderProvider>
    </BrowserRouter>
  </React.StrictMode>
);
