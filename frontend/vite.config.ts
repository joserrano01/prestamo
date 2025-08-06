import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: true,
    hmr: false, // Deshabilitado para evitar refreshes automáticos
    cors: true,
    watch: {
      usePolling: false, // Intentar deshabilitar polling completamente
      ignored: [
        '**/node_modules/**',
        '**/.git/**',
        '**/dist/**',
        '**/build/**',
        '**/*.log',
        '**/coverage/**',
        '**/tmp/**',
        '**/.vite/**',
        '**/.DS_Store',
        '**/Thumbs.db'
      ],
    },
  },
  // Optimizaciones adicionales para desarrollo
  optimizeDeps: {
    exclude: ['fsevents'], // Excluir librerías que pueden causar problemas en Docker
  },
})
