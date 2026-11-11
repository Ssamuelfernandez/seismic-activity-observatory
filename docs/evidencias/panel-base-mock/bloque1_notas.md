# Bloque 1 (T001 a T004): notas de la ejecución

Fecha: 2026-11-05. Equipo: Windows 11, Node 24.18.0 en `C:\Program Files\nodejs`.

## Versiones (T001)
Se instalaron las doce versiones exactas de `plan.md` sin ajustes; ninguna tuvo que sustituirse por la estable anterior. `npm ls typescript` muestra 6.0.3 (`T001_npm_ls_typescript.txt`). `npm ci` sin avisos de peer y con 0 vulnerabilidades (`T001_npm_ci.txt`).

## Aviso de entorno: Node 20.13.1 dentro de los scripts de npm
`node -v` en la terminal da 24.18.0, pero los scripts de `npm run ...` ejecutan Node 20.13.1, porque existe `C:\Users\Samuel\node_modules\node\bin\node.exe` (paquete `node` instalado en la carpeta de usuario) y npm antepone los `node_modules/.bin` de las carpetas superiores al PATH. Vite avisa («You are using Node.js 20.13.1») pero funciona. Por eso se guardan las dos salidas: con `npm run` (T001_npm_run_build.txt, T002_T004_npm_test.txt) y con Node 24 invocado directamente (`T002_T004_vitest_node24.txt`, `T003_build_node24.txt`). No se ha tocado nada fuera del repo.

## T003: Vite emite los JSON como archivos aparte
Para comprobarlo antes de existir la capa de datos (T009) se añadió de forma temporal `src/api/mockFiles.ts` con `import.meta.glob('../../mock/*.json', { query: '?url', import: 'default', eager: true })` y se importó desde `main.tsx`. Resultado (`T003_build_con_glob_url.txt`, `T003_build_node24.txt`): `dist/assets/` contiene `base-*.json` (17 kB), `empty-*.json`, `replay-*.json` y `truncated-*.json` (1 673 kB) como archivos; el JS principal pesa 219,8 kB y no contiene los eventos. El plan B (`public/mock/`) no hace falta. La comprobación temporal se retiró; T009 crea el uso real.

## T003: determinismo
`T003_sha256_mock_corrida1.txt` y `T003_sha256_mock_corrida2.txt` son idénticos (dos ejecuciones de `node scripts/generate-mock.mjs`).

## T001: servidor de desarrollo
`T001_dev_http.txt`: `GET /` y `GET /src/main.tsx` responden HTTP 200.
