import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Figma asset aliases  
      'figma:asset/2d76d3ed895b0324df0b5302921cd6c50e5b7a9e.png': '/2d76d3ed895b0324df0b5302921cd6c50e5b7a9e.png',
      'figma:asset/da9550dcbe65c2aac03f4ad82653151f4edb368e.png': '/da9550dcbe65c2aac03f4ad82653151f4edb368e.png',
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})

