// MUST BE FIRST: Disable console logs in production
import './utils/consoleOverride.js';

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './index.css';
import './styles/main.css';
import { AuthProvider } from './context/AuthContext.jsx';
import { LoaderProvider } from './context/LoaderContext.jsx';

// Import debug utility in development
if (import.meta.env.DEV) {
  import('./utils/debugLocalStorage.js');
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <LoaderProvider>
          <App />
        </LoaderProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
