import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // En desarrollo, Vite reenvía las peticiones /api al backend: para el navegador,
    // frontend y API están en el mismo origen y no hay problemas de CORS
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    // Los tests de componentes necesitan un navegador simulado
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
