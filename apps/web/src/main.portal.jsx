import React from 'react';
import ReactDOM from 'react-dom/client';
import { AuthProvider } from './context/AuthContext';
import { LoaderProvider } from './context/LoaderContext';
import { BrowserRouter } from 'react-router-dom';
import PortalRoutes from './PortalRoutes';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <LoaderProvider>
        <AuthProvider>
          <div className="app-container">
            <main className="main-content">
              <PortalRoutes />
            </main>
          </div>
        </AuthProvider>
      </LoaderProvider>
    </BrowserRouter>
  </React.StrictMode>
);
