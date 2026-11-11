# Verificación Bloque 1 (T024–T026) de panel-base-mock

Ejecutado en una copia limpia (sin node_modules) fuera del repo; Node v24.18.0.
- (1) `npm ci` 0, `tsc --noEmit` 0, `npm run build` 0 (solo aviso de chunk >500 kB), `npm test` 0: 2 ficheros, 19 tests pasan.
- (2) El puerto 4200 ya lo ocupaba el PID 28544 (un dev server previo): `curl` a `/` y a `/datos/paises.geojson` da 200, y mi arranque falló con "Port 4200 is already in use" (strictPort confirmado). No pude probar un primer arranque limpio.
- (3) SHA-256 de `public/datos/paises.geojson` = 6866c877…c977f. Con una copia alterada, `copy-countries.mjs` sale con código 1 y muestra esperado/obtenido.
- (4) `package.json`: versiones exactas; zustand 5.0.8, three y @types/three 0.187.0; sin `h3-js` directo (solo transitivo de react-globe.gl→three-globe, ok); sin `node` ni `tsc` ajenos en package.json, lock ni node_modules (`npx tsc` bajó `tsc@2.0.4` solo a la caché de npx).
- (5) Greps: `formatMadrid|h3-js` y `showArcs|showHexBin|showHeatmap|showMarkers|quake-marker` sin resultados; solo `GlobeView` importa react-globe.gl/three; `shared/` no importa de `components/`.
- (6) Diff con globo-lab: solo capas borradas, `mag ?? 0` sustituido por `hasMag`/`MagPoint`, ND en tooltip/color, ruta del geojson y docstrings. APPEARANCE, rama hex, anillos, etiquetas y pilar intactos.
- (7) Simbología (script temporal): 9.99→#ffd23f, 10→#ff963a, 34.99→#ff963a, 35→#ff5a36, 69.99→#ff5a36, 70→#d7539a, 299.99→#d7539a, 300→#b04cff, −0.01→#ffd23f, null→#8a93a0. Correcto. Anillos y etiquetas filtran con `hasMag`.
- (8) Docstrings con la plantilla §7.4 en las funciones muestreadas (symbology, GlobeView, copy-countries). (9) Todas las rutas de CODEMAP existen salvo `frontend/mock/backend.ts`, que figura como "previsto". (10) `git diff --stat` de enunciado, contratos y `sql/001_schema.sql` vacío.
- Hallazgos bloqueantes o importantes: ninguno.
- Incidencia mía: mi primer `npm ci` dentro de `frontend/` falló con EPERM porque el dev server del 4200 tenía archivos abiertos, y dejó `frontend/node_modules` incompleto (está ignorado por git). Solución: parar el dev server y ejecutar `npm ci`.
- Pendiente del alumno (sin navegador): captura «antes» de T024, captura «después» de T025, y leyenda y barra ND de magnitud nula de T026. Quedan sin verificar visualmente: el aspecto del globo tras quitar las capas, los cinco colores en la leyenda y el prisma gris mínimo.

T024: verificada
T025: verificada
T026: verificada
