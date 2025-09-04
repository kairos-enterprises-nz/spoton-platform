import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  const isUAT = process.env.VITE_ENVIRONMENT === 'uat'
  const isLive = process.env.VITE_ENVIRONMENT === 'live'
  
  return {
    plugins: [
      react(),
      tailwindcss()
    ],
    server: {
      host: '0.0.0.0',
      port: 3002,
      // Allow *.spoton.co.nz (covers live.spoton.co.nz, uat.spoton.co.nz, etc.)
      allowedHosts: ['.spoton.co.nz'],
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Cache-Control'
      },
        hmr: {
          port: 3002
        },
      watch: {
        usePolling: true,
        interval: 1000
      }
    },
    preview: {
      host: '0.0.0.0',
      port: 3002,
      // Allow *.spoton.co.nz (covers live.spoton.co.nz, uat.spoton.co.nz, etc.)
      allowedHosts: ['.spoton.co.nz'],
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Cache-Control'
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: isUAT, // Source maps only for UAT, not Live
      minify: isProduction,
      rollupOptions: {
        input: './index.html',
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            ui: ['@headlessui/react', '@heroicons/react', 'framer-motion'],
            auth: ['keycloak-js'],  // jwt-decode removed
            charts: ['recharts']
          }
        }
      }
    },
    define: {
      __APP_TYPE__: JSON.stringify('staff'),
      __ENVIRONMENT__: JSON.stringify(process.env.VITE_ENVIRONMENT || 'development'),
      __ENABLE_CONSOLE_LOGS__: JSON.stringify(isUAT || !isProduction), // Console logs only in UAT and dev
      __IS_PRODUCTION__: JSON.stringify(isLive),
      __IS_UAT__: JSON.stringify(isUAT)
    },
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom', 'keycloak-js', 'recharts']
    },
    esbuild: {
      drop: isLive ? ['console', 'debugger'] : [], // Remove console logs in Live production
      pure: isLive ? ['console.log', 'console.warn', 'console.error'] : []
    }
  }
}) 