# Research: Panel base con mock y mapa

Formato: decisión, motivo, alternativas. Decisiones del alumno aplicadas el 2026-11-05. Solo la elección final de la librería del mapa (R7) sigue abierta, en `T007`.

## R1. Versiones (comprobadas con `npm view <paquete> version`, 2026-11-05)

- **Decisión**: Node 24.18.0; React/React DOM 19.3.1; TypeScript 6.0.3 (decidido por el alumno, 2026-11-05); Vite 8.3.6; `@vitejs/plugin-react` 6.2.1; Tailwind 4.3.4 + `@tailwindcss/vite` 4.3.4; `@tanstack/react-query` 5.106.1; Vitest 5.1.0; `@types/react` y `@types/react-dom` 19.3.0; `@types/node` 24.19.2. Exactas en `package.json` + `package-lock.json`; `.nvmrc` y `engines`.
- **Motivo**: son las estables vigentes; el equipo ya tiene Node 24.18.0; Vite 8 (`^22.12 || ^24 || >=26`) y Vitest 5.1.0 (peer `vite ^6.4 || ^7 || ^8`) lo admiten; `@vitejs/plugin-react` 6.2.1 pide `vite ^8`; `@tailwindcss/vite` 4.3.4 admite Vite 8.
- **Alternativas**: TypeScript 7.0.2 (descartada por decisión del alumno); `@types/node` 26 (descartada: no coincide con Node 24).
- **TypeScript 6.0.3**: comprobado con `npm view typescript@6.0.3 version` (existe). Vite 8.3.6, Vitest 5.1.0, `@vitejs/plugin-react` 6.2.1, `@tailwindcss/vite` 4.3.4, TanStack Query 5.106.1 y `@types/node` 24.19.2 no declaran peer de `typescript`, así que no hay otros paquetes que ajustar.
- **Regla**: si una versión no se puede instalar en `T001`, se usa la estable anterior y se anota en `plan.md`.

## R2. TanStack Query en esta feature

- **Decisión**: sí. Se usa para cargar el mock (`useEvents`).
- **Motivo**: la spec (Assumptions) lo pide desde G0 y así `panel-conexion-api` solo añade la rama de la API. No se usa refetch ni timeout aún.
- **Alternativa**: `fetch` + `useEffect` (descartada: habría que rehacer el hook en `012`).

## R3. Dónde vive el mock (P4) — decidido por el alumno, 2026-11-05

- **Decisión**: JSON en `frontend/mock/` (como 03 §7.5), importados con `import.meta.glob('/mock/*.json', { query: '?url', import: 'default' })`; `build.assetsInlineLimit: 0`.
- **Motivo**: no cambia 03 y los 5 000 eventos quedan fuera del JavaScript. Se comprueba en `T003`; si falla, `public/mock/` y se corrige 03 §7.5.
- **Alternativas**: `frontend/public/mock/` (más simple, sirve tal cual, pero obliga a corregir 03 §7.5); `import` normal de JSON (descartada: mete ~1,5 MB en el bundle).

## R4. Generación del mock

- **Decisión**: `frontend/scripts/generate-mock.mjs` con generador pseudoaleatorio de semilla fija, sin dependencias; los JSON generados se versionan. `base` se escribe con casos concretos fijos (no aleatorios) para los casos raros y se completa hasta ~30; `truncated` tiene 5 000 features de coordenadas y magnitudes variadas, con un porcentaje pequeño de nulos y negativos; `total` 6 213, `next_cursor` una cadena opaca de ejemplo.
- **Motivo**: reproducible, revisable en Git y sin copiar identificadores reales de USGS.
- **Alternativa**: JSON escrito a mano (inviable para 5 000).

## R5. Comprobación de conformidad del mock (FR-010)

- **Decisión**: función pura `validateEventsResponse(json)` en `tests/support/`, que devuelve lista de errores; el test la aplica a los cuatro archivos y a un archivo estropeado (debe fallar). Comprueba: los ocho campos de `metadata` y los once de `properties` (`api.md` §3.2 y §3.4), tipos, nulos solo donde el contrato los permite, tiempos enteros, `Point` con tres coordenadas finitas (la tercera puede ser `null`), `is_synthetic === true`, `id` con prefijo `mock-`, `count === features.length`.
- **Motivo**: solo prueba la forma; no redefine el contrato (§15).

## R6. Escalas y símbolos

- **Decisión**: V1–V4 de la spec tal cual (radio 3 + 1,5 × clamp(M, 0, 8); viridis de cinco clases con cortes 10/35/70/300; ND magnitud = contorno sin relleno de 5 px; ND profundidad = gris `#9CA3AF`).
- **Motivo**: son los valores por defecto de la spec y coinciden con los cortes de histograma de la API (`api.md` §5.1). Si la librería elegida no admite el contorno discontinuo o el hueco, se usa el equivalente más cercano y se anota en la tarea.

## R7. Prototipo del mapa (D1) — candidatas decididas; elección final del alumno en `T007`

- **Criterios** (los de la spec, mismos para cada candidata, con `truncated.json`): tiempo hasta pintar 5 000 círculos (ref. ≤ 3 s), fluidez al mover/ampliar, pulsar un círculo pequeño y abrir la ficha, uso en 375 px, atribución legible, peso del build (kB comprimidos).
- **Ejecución**: carpeta temporal `frontend/prototipo-mapa/` con su propio `package.json`, **fuera del lock del proyecto**, que se borra tras decidir. Candidatas confirmadas por el alumno (2026-11-05): A (`react-globe.gl`) y B (MapLibre GL JS).
- **Resultado**: tabla en `docs/evidencias/panel-base-mock/prototipo-mapa.md` y decisión del alumno anotada en `plan.md`.
- **Alternativa**: decidir sin prototipo (descartada: la spec pide probar con 5 000 eventos).

## R8. Fondo del mapa y atribución

- **Decisión**: se fija con la elección final de D1 en `T007` (depende de la librería). Requisitos fijos: sin clave, atribución visible siempre fuera de la tarjeta de leyenda (V5), Natural Earth para fronteras. Q4/Q2/P5 resueltas: sin cambios aquí. Si se usan teselas OSM, respetar su política de uso (sin carga masiva; es una práctica de clase).

## R9. Capturas y comprobación a 375 px

- **Decisión (alumno, 2026-11-05, Q3)**: capturas manuales con las herramientas del navegador (emulación de dispositivo 375 × 667) y comprobación del scroll con una línea en la consola (`scrollWidth <= innerWidth`) anotada en la evidencia.
- **Motivo**: proporcionalidad; evita instalar Playwright para una feature de dos semanas.
- **Alternativa**: Playwright como dependencia de desarrollo (más repetible, pero añade peso y alcance). Descartada por el alumno.

## R10. Alias de importación

- **Decisión**: alias `@/` → `src/` en `tsconfig` y `vite.config`.
- **Motivo**: mover carpetas por D3 solo cambia imports. Coste de configuración mínimo.
