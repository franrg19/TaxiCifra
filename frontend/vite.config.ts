import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // En desarrollo, Vite reenvía las peticiones /api al backend: para el navegador,
    // frontend y API están en el mismo origen y no hay problemas de CORS
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
