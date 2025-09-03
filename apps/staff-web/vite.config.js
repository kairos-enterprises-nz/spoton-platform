import { defineConfig } from 'vite'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const __filename = fileURLToPath(import.meta.url)
  const __dirname = path.dirname(__filename)
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
        hmr: false,
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
        output: {
          // Force new hashes for assets to bust browser cache
          assetFileNames: '[name]-[hash].[ext]',
          chunkFileNames: '[name]-[hash].js',
          entryFileNames: '[name]-[hash].js',
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            ui: ['@headlessui/react', '@heroicons/react', 'framer-motion'],
            auth: ['keycloak-js'],  // jwt-decode removed
            charts: ['recharts']
          }
        }
      }
    },
    resolve: {
      alias: {
        '@spoton/ui': path.resolve(__dirname, '../../../packages/ui/src')
      }
    },
    define: {
      __APP_TYPE__: JSON.stringify('staff'),
      // Normalize fallback to 'uat' only
      __ENVIRONMENT__: JSON.stringify(process.env.VITE_ENVIRONMENT || 'uat'),
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