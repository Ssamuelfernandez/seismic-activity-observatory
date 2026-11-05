# Verificación panel-base-mock, Bloque 1 (T001–T004) — G0, G15, G12 (magType)
Pruebas ejecutadas por mí con Node 24.18.0 directo (`node node_modules/vite/bin/vite.js`, `node node_modules/vitest/vitest.mjs`; `npm run` usaría Node 20.13.1 por el paquete `node` de C:\Users\Samuel\node_modules).
- T001 VERIFICADA: `npm ci` (0 vulnerabilidades), `tsc` 6.0.3, build OK (JS 219,6 kB), versiones exactas sin ^, `.nvmrc` y `engines` 24.18.0, alias `@/`, `assetsInlineLimit: 0`, `src/store/README.md` con la frase pedida, sin librería de mapa ni store. `npm run dev` HTTP 200 no reejecutado: me fío de `T001_dev_http.txt`.
- T002 VERIFICADA: tipos de `contract.ts` coinciden con api.md §3.2/§3.4 (8 campos de metadata, 11 de properties); Vitest 16/16 en verde.
- T003 VERIFICADA: regenerar el mock da SHA-256 idénticos; 4 JSON con base=30, truncated=5000/6213/truncated true/next_cursor no nulo, replay mode=replay (6), empty=0; ids `mock-`, `is_synthetic` true, place «Sintético:» (o null, permitido). Vite emitiendo JSON aparte: el archivo temporal se retiró y no lo reproduje; me fío de `T003_build_node24.txt` (JS principal sin eventos).
- T004 VERIFICADA: `mock.test.ts` pasa con los 4 archivos y falla con `bad-response.json` (mode, count, is_synthetic) y con un nulo ilegal.
- Alcance: `git diff --stat` solo toca CODEMAP.md (+5 filas, correctas); contratos, enunciado y sql/001_schema.sql sin cambios. Evidencia en docs/evidencias/panel-base-mock/. Sin secretos ni atribución a Claude.
- Hallazgos bloqueantes/importantes: ninguno.
- Límite conocido: T003 (emisión de JSON en dist) se apoya en evidencia del implementador; la reproducirá T009.
