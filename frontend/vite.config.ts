import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')
  
  // Get backend URL from environment variable, default to localhost
  // Use 127.0.0.1 instead of localhost to force IPv4 (avoids IPv6 issues)
  let backendUrl = env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
  
  // Validate backend URL
  try {
    new URL(backendUrl)
  } catch (e) {
    console.warn(`Invalid VITE_BACKEND_URL: ${backendUrl}, using default: http://127.0.0.1:8000`)
    backendUrl = 'http://127.0.0.1:8000'
  }
  
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0', // Allow access from local network and internet
      port: parseInt(env.VITE_FRONTEND_PORT || '3000'),
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
          // Configure proxy to handle requests properly
          configure: (proxy, _options) => {
            proxy.on('error', (err, req, res) => {
              console.error('Proxy error:', err)
            })
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              // Log proxy requests for debugging
              console.log(`[Proxy] ${req.method} ${req.url} -> ${backendUrl}${req.url}`)
            })
          },
        },
      },
    },
  }
})

