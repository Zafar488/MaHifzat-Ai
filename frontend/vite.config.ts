import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Vite 8 bundles with Rolldown, which does not support Rollup's
        // object-form `manualChunks`. The equivalent is `codeSplitting.groups`,
        // producing the same react-vendor / query-vendor / chart-vendor chunks.
        codeSplitting: {
          groups: [
            {
              name: 'react-vendor',
              test: /[\\/]node_modules[\\/](react|react-dom|react-router|react-router-dom|scheduler)[\\/]/,
            },
            {
              name: 'query-vendor',
              test: /[\\/]node_modules[\\/]@tanstack[\\/](react-query|query-core)[\\/]/,
            },
            {
              name: 'chart-vendor',
              test: /[\\/]node_modules[\\/](recharts|victory-vendor|d3-[a-z-]+|internmap)[\\/]/,
            },
          ],
        },
      },
    },
  },
})
