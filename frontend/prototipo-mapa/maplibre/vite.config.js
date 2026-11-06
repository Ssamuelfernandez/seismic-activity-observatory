import '../scripts/copy-data.mjs' // copia el mock y las fronteras a public/data
import { defineConfig } from 'vite'

export default defineConfig({
  root: 'maplibre',
  publicDir: '../public',
  server: { port: 5182, strictPort: true, host: '127.0.0.1' },
  preview: { port: 5182, strictPort: true, host: '127.0.0.1' },
  build: { outDir: '../dist-maplibre', emptyOutDir: true },
})
