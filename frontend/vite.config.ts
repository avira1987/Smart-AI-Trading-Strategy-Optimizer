import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allow access from local network
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Configure proxy to handle requests properly
        configure: (proxy, _options) => {
          proxy.on('error', (err, req, res) => {
            console.error('Proxy error:', err)
          })
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Log proxy requests for debugging (only in development)
            // Note: import.meta.env is not available in vite.config.ts context
            // So we always log in dev server (which is only used in development)
            console.log(`[Proxy] ${req.method} ${req.url} -> http://localhost:8000${req.url}`)
          })
        },
      },
    },
  },
})

