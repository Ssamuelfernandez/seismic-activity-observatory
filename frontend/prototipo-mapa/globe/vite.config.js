import '../scripts/copy-data.mjs' // copia el mock y las fronteras a public/data
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  root: 'globe',
  publicDir: '../public',
  plugins: [react()],
  server: { port: 5181, strictPort: true, host: '127.0.0.1' },
  preview: { port: 5181, strictPort: true, host: '127.0.0.1' },
  build: { outDir: '../dist-globe', emptyOutDir: true },
})
