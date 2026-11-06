import '../scripts/copy-data.mjs' // copia el mock y las fronteras a public/data
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Prototipo T022 (prisma hexagonal y celdas): puerto propio, distinto de 5181 y 5182.
export default defineConfig({
  root: 'globe-hex',
  publicDir: '../public',
  plugins: [react()],
  server: { port: 5183, strictPort: true, host: '127.0.0.1' },
  preview: { port: 5183, strictPort: true, host: '127.0.0.1' },
  build: { outDir: '../dist-globe-hex', emptyOutDir: true },
})
