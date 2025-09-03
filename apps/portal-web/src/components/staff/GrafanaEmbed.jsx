import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getEmbedUrl, openServiceWithAuth } from '../../utils/serviceAuth';

const GrafanaEmbed = ({ 
  dashboardUid, 
  height = '600px', 
  theme = 'dark',
  refresh = '30s',
  from = 'now-24h',
  to = 'now',
  panelId = null,
  title = 'Grafana Dashboard'
}) => {
  const [grafanaUrl, setGrafanaUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Construct Grafana embed URL with auto-login
    const path = `d/${dashboardUid}`;
    const params = {
      theme,
      refresh,
      from,
      to,
      orgId: 1,
      kiosk: 'tv' // Hide Grafana UI elements for embedding
    };
    
    if (panelId) {
      params.viewPanel = panelId;
    }
    
    const embedUrl = getEmbedUrl('grafana', path, params);
    
    setGrafanaUrl(embedUrl);
    setIsLoading(false);
  }, [dashboardUid, theme, refresh, from, to, panelId]);

  const handleIframeLoad = () => {
    setIsLoading(false);
    setError(null);
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setError('Failed to load Grafana dashboard. Please ensure Grafana is running.');
  };

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">{title}</h3>
          <p className="mt-1 text-sm text-gray-500">{error}</p>
          <div className="mt-6">
            <button
              onClick={() => openServiceWithAuth('grafana')}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Open Grafana Directly
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <div className="mt-1 flex items-center space-x-4">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Live Data
          </span>
          <span className="text-sm text-gray-500">Auto-refresh: {refresh}</span>
          <button
            onClick={() => window.open(grafanaUrl.replace('kiosk=tv', ''), '_blank')}
            className="text-sm text-indigo-600 hover:text-indigo-500"
          >
            Open in Grafana
          </button>
        </div>
      </div>
      
      <div className="relative" style={{ height }}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
              <span className="text-sm text-gray-600">Loading dashboard...</span>
            </div>
          </div>
        )}
        
        <iframe
          src={grafanaUrl}
          width="100%"
          height="100%"
          frameBorder="0"
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          className={isLoading ? 'opacity-0' : 'opacity-100'}
          title={title}
          sandbox="allow-scripts allow-same-origin allow-forms"
        />
      </div>
    </div>
  );
};

GrafanaEmbed.propTypes = {
  dashboardUid: PropTypes.string.isRequired,
  height: PropTypes.string,
  theme: PropTypes.oneOf(['light', 'dark']),
  refresh: PropTypes.string,
  from: PropTypes.string,
  to: PropTypes.string,
  panelId: PropTypes.number,
  title: PropTypes.string
};

export default GrafanaEmbed; 