import { fileURLToPath, URL } from 'node:url';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';

// Configuración de Vite: alias `@/` -> `src/`, sin inline de assets y servidor de desarrollo fijo en el 4200 (G0, FR-002).
// El alias `@mock/backend` apunta al servidor simulado en desarrollo y pruebas, y a un módulo que falla en
// producción: así el mock y sus JSON no entran en `dist/` (G15, FR-005; constitución §7).
export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@mock/backend': fileURLToPath(new URL(mode === 'production' ? './src/shared/api/mockUnavailable.ts' : './mock/backend.ts', import.meta.url)),
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    assetsInlineLimit: 0,
  },
  // En desarrollo `/api` se reenvía a la API (aún no implementa CORS). Destino configurable
  // con API_PROXY_TARGET; por defecto el puerto publicado por Compose.
  server: {
    port: 4200,
    strictPort: true,
    proxy: { '/api': process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000' },
  },
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
  },
}));
