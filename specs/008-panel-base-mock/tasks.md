# Tasks: Panel completo — adoptar el front externo con correcciones

**Entrada**: `spec.md`, `plan.md`, `data-model.md`, `quickstart.md`, `diseno-visual.md`, `inventario-front-externo.md` (esta carpeta). **IDs**: G0, G1, G2, G3, G4, G5, G5b, G6, G7, G8, G9, G11, G12, G14, G15, G17; parcial G10/J7.

**Enmienda del 2026-11-10.** 17 tareas activas en 5 bloques (máximo 25 y 5), numeradas **T024–T040** para no chocar con las del histórico. Formato: `- [ ] T### [P] [US#] Descripción con ruta`. `[P]` = en paralelo (archivos distintos, sin depender de una tarea sin terminar). Cada tarea lleva **Prueba** y **Cubre**. Todo el código nuevo o portado sigue FR-027 (docstrings con la plantilla de 03 §7.4, identificadores en inglés, lógica pura separada del I/O).

**Fuente del código**: `_import-front/globo-lab/` (ignorado por git; se conserva como fuente hasta T040, donde se borra). **No se copia**: `node_modules/`, `dist/`, `.git/`, `.claude/`, `prototipo-mapa/`, `package-lock.json`, `src/config.json`.

## Histórico (hecho con el diseño anterior; no cuenta como activo, no se reabre)

- [x] T001 Proyecto en `frontend/` con versiones exactas y lock (base de T024).
- [x] T002 Tipos del contrato y `format.ts` (`src/shared/types/contract.ts`, `src/shared/lib/format.ts`).
- [x] T003 Mock sintético `frontend/mock/{base,truncated,replay,empty}.json` con `scripts/generate-mock.mjs` (se amplía en T028).
- [x] T004 Validador de conformidad `tests/support/validateEventsResponse.ts` y `tests/mock.test.ts` (se amplía en T038).
- [x] T005 Prototipos de mapa · [x] T006 Medición (`docs/evidencias/panel-base-mock/prototipo-mapa.md`) · [x] T022 Prototipo del prisma hexagonal (`prototipo-hexagonal.md`): conservadas como evidencia.
- [x] T007 `react-globe.gl` 2.38.0 instalada y `frontend/prototipo-mapa/` borrado.

**Tareas anteriores sustituidas** (ya no activas): T008 → T027; T009 → T030, T031; T010 → T026; T011, T013, T014, T015, T016, T017, T023 → T024, T025, T026, T033, T037 (el front ya trae banner, ficha, leyenda, globo, integración y diseño móvil); T012 → T024 (copia de `paises.geojson` y su SHA) y T037; T018–T021 → T039, T040.

## Bloque 1 — Portar y limpiar (G0, G2, G14, G17)

- [x] T024 **Portar el código del front externo** a `frontend/src/` con la estructura y el mapa de portado de `plan.md`. Añadir `zustand` 5.0.8, `three` 0.187.0 y `@types/three` 0.187.0 **exactos** (sin `h3-js`) y regenerar el lock; `vite.config.ts` con `server: { port: 4200, strictPort: true, proxy: { '/api': … } }`; copiar `data/catalogo/paises.geojson` a `public/datos/paises.geojson` con `scripts/copy-countries.mjs` (verifica el SHA-256 `6866c877…c977f` y falla si no coincide) y cargarlo desde `/datos/paises.geojson`; `src/store/` sin el `README.md` de reserva. Estructura **tal cual la del front externo** (P1). Todavía con el `config.json` compilado del origen (se sustituye en T027).
  - **Prueba**: `npm ci`, `tsc --noEmit` y `npm run build` salen con 0; `npm run dev` sirve en el 4200 y un segundo arranque falla; el SHA coincide. Captura del globo con el mock (`dataSource: "mock"` en el `config.json` compilado) como referencia «antes» para T025. Salidas en `docs/evidencias/panel-base-mock/`.
  - **Cubre**: G0, G2, G14; FR-001, FR-002, FR-016, FR-019, FR-020, FR-028.

- [x] T025 **Limpiar y ajustar a los estándares**: quitar `formatMadrid`, `formatMadridTime` y su prueba; no declarar ni importar `h3-js`; asegurar que solo `GlobeView` importa `react-globe.gl` y `three` y que `shared/` no importa de `components/`; **borrar las capas apagadas del globo** (arcos, densidad por celdas, mapa de calor y marcadores) con sus ajustes de `appearance.ts` y el estilo `.quake-marker` de `index.css`, sin cambiar nada visible (P5); añadir docstrings en español con la plantilla de 03 §7.4 a toda función o componente exportado; revisar identificadores en inglés. **No** se borra `_import-front/`: T028 y T029 lo usan como fuente (zonas y servidor simulado del mock).
  - **Prueba**: `npm run build` y `npm test` en 0; `grep -rn "formatMadrid\|h3-js" frontend/src frontend/tests frontend/package.json` sin resultados; ningún `import` de `components/` dentro de `shared/`; `grep -rn "showArcs\|showHexBin\|showHeatmap\|showMarkers" frontend/src` sin resultados; captura «después» del globo (mismo escenario y misma cámara que la «antes» de T024) sin diferencias visibles.
  - **Cubre**: FR-027, FR-028, FR-031; SC-013, SC-017.

- [x] T026 [P] **Simbología en cinco clases y nulos correctos**: `src/shared/lib/symbology.ts` con las cinco clases de profundidad (cortes 10/35/70/300, colores de `spec.md`), `colorForEvent` y `Legend.tsx` con las cinco clases y su rango escrito más el ND; en `GlobeView` quitar `magOf = mag ?? 0`: anillos y etiquetas solo con `mag !== null` y por encima del umbral, barra ND gris de altura mínima, tooltip «ND».
  - **Prueba**: pruebas de T038 sobre `depthClassFor`/`colorFor`; captura de la leyenda y de un evento de magnitud nula (sin anillo ni etiqueta).
  - **Cubre**: G2; FR-017, FR-018; SC-005, SC-006.

## Bloque 2 — Configuración y mock (G15)

- [x] T027 **Configuración en tiempo de ejecución**: `public/config.json` (`mode: "api"`, `apiBaseUrl: "/api"`, `refreshSeconds: 60`, `timeoutMs: 15000`), `src/shared/lib/validateConfig.ts` (pura: valida los cuatro campos y devuelve el que falla), `src/shared/api/loadConfig.ts` (`fetch` del archivo), `src/components/ConfigGate.tsx` (carga, mensaje de error que nombra el campo, o el panel) en `main.tsx`; sustituir todos los usos de `src/config.json` por la config cargada (`refreshSeconds`, `timeoutMs`, `apiBaseUrl`); el umbral de desactualizado pasa a la constante `STALE_THRESHOLD_SECONDS = 300` de `feedHealth.ts`; borrar `src/config.json`.
  - **Prueba**: pruebas de T038 para el validador; `npm run build` y editar `dist/config.json` (`mode: "otro"`) muestra un mensaje que nombra `mode`.
  - **Cubre**: G15, G11; FR-003, FR-004; SC-002.

- [x] T028 [P] **Escenarios del mock**: ampliar `scripts/generate-mock.mjs` (semilla fija, sin dependencias) para regenerar `frontend/mock/{base,truncated,replay,empty}.json` y crear `realistic.json` (unos 400 eventos por zonas, fechas relativas a «ahora»); `replay` con **todas** las fechas dentro de 2025; casos de borde repartidos (magnitud nula y negativa, profundidad nula y negativa, `place` nulo, `magType` nulo, sin país); todo `is_synthetic: true`, `id` `mock-…`, `place` «Sintético: …», sin ids reales de USGS.
  - **Prueba**: dos ejecuciones del generador dan el mismo SHA-256; los cinco archivos pasan el validador de T004 (ya hecho; T038 lo amplía a los cinco escenarios).
  - **Cubre**: G15; FR-006, FR-007; SC-004.

- [x] T029 **Servidor simulado y exclusión de producción**: `frontend/mock/backend.ts` con `__MOCK_BACKEND__`, que responde `eventos`, `estadisticas` y `salud` sobre un escenario (`?scenario=`; desconocido → `base` con aviso en la consola de desarrollo; `realistic` filtra por `start`, `end`, `min_mag`, `country_id`; los demás se devuelven tal cual); `src/shared/api/dataSource.ts` lo carga con `import('@mock/backend')` solo con `config.mode === 'mock'`; alias `@mock` en `vite.config.ts` hacia `mock/backend.ts` en `development`/`test` y hacia `src/shared/api/mockUnavailable.ts` (lanza «mock no disponible en este build») en `production`; añadir `mock/` a `tsconfig.json`; quitar de la interfaz y del store el selector `source` (mock/api) y el banner de origen manual; el banner «DATOS SINTÉTICOS» sale de `is_synthetic`.
  - **Prueba**: `npm run build` y `grep -r __MOCK_BACKEND__ dist` y `grep -r "Sintético:" dist` sin resultados; `npm run preview` con `mode: "mock"` muestra el mensaje; en desarrollo los cinco escenarios cargan; la interfaz no ofrece control de origen.
  - **Cubre**: G15; FR-005, FR-008; SC-003, SC-004.

## Bloque 3 — Capa de datos (G6, G7, G9, G11, G12)

- [ ] T030 **Petición, parseo y cliente**: `src/shared/api/requests.ts` (pura: filtros del store → parámetros; `live` con ventana de horas o rango UTC; **`replay` con `start=2025-01-01T00:00:00.000Z` y `end=2026-01-01T00:00:00.000Z`**; `country_id` solo `none` o tres letras), `src/shared/api/parse.ts` (pura: guarda de forma de `EventsResponse`, `StatsResponse` y `HealthResponse`; los nulos se conservan; `ApiError` con código `invalid_response`) y `src/shared/api/client.ts` (`apiBaseUrl` y `timeoutMs` de la config, cuerpo de error del contrato).
  - **Prueba**: pruebas de T038 (parseo y nulos, ventana de replay).
  - **Cubre**: G1, G6, G12; FR-010, FR-011, FR-014; SC-009.

- [ ] T031 **Hook de datos**: `src/shared/hooks/useObservatory.ts` con TanStack Query: refresco cada `refreshSeconds` sin solapar peticiones, `retry: false`, última lectura conservada y marcada como antigua (`updatedAt`), estados `loading`/`ready`/`empty`/`error`; replay con `features: []` es `empty`, no error; cambiar un filtro limpia la selección; store `src/store/filters.ts` con `mode`, `hours`, `dateFrom`, `dateTo`, `minMag`, `country` (sin `source`). En `mode=replay` el selector de periodo queda desactivado y muestra «2025».
  - **Prueba**: con el mock `realistic`, un cambio de filtro cambia globo, tabla y estadísticas a la vez; `replay` vacío muestra el estado vacío sin error.
  - **Cubre**: G6, G7, G9, G11; FR-012, FR-013, FR-014.

- [ ] T032 [P] **Auditoría de cálculos en el cliente**: rehacer la lista del plan sobre el código ya portado (buscar `length`, `reduce`, `Math.`, restas de timestamps, `filter` y recuentos en `src/`), aplicar las acciones (rótulo «mostrados», totales de la API, quitar `máx.` y «+N países más» o rotularlos) y escribir `docs/evidencias/panel-base-mock/auditoria-calculos-cliente.md` con la lista final y el veredicto de cada línea. La fila 7 (retraso de ingesta) **queda aceptada (P3)**: se calcula en el panel con `generated` y `last_ingestion`, se rotula «hace X min» con la nota «calculado en el panel» (en el desplegable del estado y en el aviso de desactualizado) y no hay cambio de contrato.
  - **Prueba**: ningún recuento propio sin «mostrados»; los totales visibles salen de `metadata` o `stats`; la lista está guardada.
  - **Cubre**: G12; FR-029; SC-011.

- [ ] T033 [P] **Avisos y banner de replay**: en `StatusBanners` añadir el aviso de **truncado** («Mostrando N de M eventos», con `metadata.count` y `metadata.total`), poner **REPRODUCCIÓN** como texto del aviso de modo replay, y el mensaje «Sin eventos reproducidos» para un replay vacío; la tabla y las listas muestran «mostrados» (T032).
  - **Prueba**: escenarios `truncated`, `replay` y `empty` del mock; captura de cada aviso.
  - **Cubre**: G12 (`truncated`), G10 (parcial), J7 (parcial); FR-015, FR-024.

## Bloque 4 — Conexión con la API real y atribución (G1, G7, G9, G11, G14)

- [ ] T034 **Levantar el stack y conectar**: `docker compose up -d` (sin cambiar el contrato ni la API), comprobar `GET /api/salud`, `GET /api/eventos` y `GET /api/estadisticas` con `curl`, `npm run dev` en el 4200 con `mode: "api"`; contrastar las respuestas reales con el mock (campos, nulos, orden, `truncated`, `comparison`) en `docs/evidencias/panel-base-mock/contraste-mock-api.md` y corregir el mock o el front (**nunca el contrato**; si el contrato y la API divergen, se avisa al alumno). Si el stack no arranca o no hay eventos, se detiene y se pregunta.
  - **Prueba**: el panel muestra eventos reales con el proxy de Vite; el documento de contraste está guardado.
  - **Cubre**: G1; FR-010; SC-007.

- [ ] T035 **Verificación con datos reales**: cambiar periodo, magnitud y país y comprobar que globo, lista, tabla, estadísticas y estado cambian a la vez y que `stats.total` coincide con `metadata.total` con los mismos filtros; truncado visible si lo hay; comparación con 2025 si el histórico (`006`) está cargado (si no, se anota); replay con la API real (vacío esperado, sin error y con el banner). Capturas con los filtros visibles.
  - **Prueba**: capturas y una tabla `filtros → total del globo, de la tabla y de las estadísticas` en `docs/evidencias/panel-base-mock/`.
  - **Cubre**: G3, G4, G5, G5b, G6, G8, G12; FR-021, FR-022; SC-007, SC-009.

- [ ] T036 **Fallo provocado, recuperación y refresco**: con la API levantada, parar el servicio `api` y, aparte, PostgreSQL (503 `database_unavailable`); comprobar en un ciclo de refresco el aviso, la última lectura marcada como antigua con su hora, que nunca sale «0 eventos», que con la API apagada desde el arranque dice «sin datos», y que al volver se recupera sin recargar; medir que no hay peticiones solapadas y que el timeout corta a `timeoutMs`.
  - **Prueba**: capturas y pestaña de red guardadas.
  - **Cubre**: G7, G9, G11, G12 (`last_ingestion`); FR-023; SC-008.

- [ ] T037 [P] **Atribución visible**: componente `src/components/Attribution.tsx` con «Sismos: USGS · Fronteras: Natural Earth (dominio público) · Globo: react-globe.gl y three (MIT) · Sin textura», de al menos 11 px y contraste ≥ 4,5 : 1; escritorio abajo a la derecha por encima del cajón de estadísticas; móvil en franja fija en el pie, fuera de las hojas; quitar la línea de 9 px del desplegable del estado.
  - **Prueba**: capturas a 375 y 1280 px donde se lee sin pulsar nada.
  - **Cubre**: G11, G14; FR-025; SC-010.

## Bloque 5 — Tests, evidencias y cierre

- [ ] T038 **Pruebas automáticas**: en `frontend/tests/`: parseo y nulos (`parse.ts`), validación de config (`validateConfig.ts`), clases de profundidad y altura (`symbology.ts`: cortes 10/35/70/300, negativas, nula, magnitud nula), ventana de replay y parámetros (`requests.ts`), `format.ts` (sin Madrid), y conformidad de los **cinco** escenarios con el validador de T004 (más el archivo estropeado, que debe fallar).
  - **Prueba**: `npm test` en 0 desde un clon limpio.
  - **Cubre**: FR-009, FR-030; SC-004, SC-005, SC-009, SC-015.

- [ ] T039 **Verificación y evidencias**: desde un clon limpio, `npm ci`, `npm run build` y `npm test` con sus códigos de salida; `dist/` de producción sin mock (SC-003); `sha256sum` de `paises.geojson` (SC-014); recorrido con el mock (cinco escenarios) y con la API real a 375, 768 y 1280 px con una ficha abierta: `scrollWidth <= innerWidth` y cero errores en la consola (corregir lo que falle); capturas en `docs/evidencias/panel-base-mock/`.
  - **Prueba**: archivos de evidencia guardados; SC-001 a SC-003, SC-012 y SC-013 cumplidos.
  - **Cubre**: G0, G15, G17; FR-001, FR-026; SC-001, SC-003, SC-012, SC-013, SC-014.

- [ ] T040 **README y cierre documental** (§16): `frontend/README.md` (ejecutar, `config.json`, `?scenario=`, mock solo en desarrollo, **material reutilizado** con Natural Earth y su ruta, `react-globe.gl` y `three`, límites conocidos); una línea en el `README.md` de la raíz; `CODEMAP.md` con las rutas reales de `frontend/` (las filas **previstas** del 2026-11-10 pasan a reales y se confirma la estructura de 03 §7.5); marcar en `01-checklist-requisitos.md` los IDs con evidencia (G0–G9, G11, G12 salvo `metadata.mode`, G14, G15, G17) y **no** marcar G10, G13, G16 ni G18; anotar el cierre y la lista de cálculos del cliente en `bitacora.md`; borrar `_import-front/` y su línea de `.gitignore`. Detenerse y esperar revisión: sin commit ni merge.
  - **Prueba**: cada ruta de `CODEMAP.md` existe; SC-016 cumplido.
  - **Cubre**: G0–G9, G11, G12, G14, G15, G17; SC-016.

## Dependencias

```
T024 ─ T025 ─ T026
  │      └─ T027 ─┬─ T029 (+T028) ─┐
  │               └─ T030 ─ T031 ──┼─ T032, T033
  └─ T028 (generador; fuente: _import-front)│
                                    └─ T034 ─ T035
                                         └─── T036
T037 (tras T025) · T038 (tras T026, T027, T028, T030) · T039 (tras T035, T036, T037, T038) · T040
```

- T025 necesita T024; T026 y T027 necesitan T025; T028 puede empezar ya (usa el generador de T003 y `_import-front/` como fuente de las zonas; no se borra hasta T040).
- T029 necesita T027 y T028; T030 necesita T027; T031 necesita T029 y T030; T032 y T033 necesitan T031.
- T034 necesita T031–T033 **y el stack de Compose levantado**; T035 y T036 necesitan T034.
- T037 necesita T025; T038 necesita T026, T027, T028 y T030; T039 necesita T035–T038; T040 va la última.

## Paralelo

T028 con T024–T027; T026 y T027 entre sí tras T025; T032 y T033 entre sí; T037 con el bloque 3 o 4; T035 y T036 entre sí.

## Estrategia

Primero el código portado funcionando (T024–T026) y luego las correcciones de fondo en orden de riesgo: configuración y mock fuera de producción (bloque 2), capa de datos (bloque 3) y conexión real (bloque 4). Lo más delicado es T029 (que el mock no entre en producción) y T034 (que la API real devuelva lo que el panel espera).

## Preguntas para el alumno

**Ninguna pendiente.** P1–P6 fueron respondidas el 2026-11-10 y están aplicadas (detalle en `spec.md`, «Respuestas del alumno a P1–P6»): **P1** estructura de `src/` la del front externo (T024, T025; documentada en `CODEMAP.md` y 03 §7.5); **P2** comparación en el cajón inferior y G5b reformulado (T035); **P3** retraso de ingesta calculado en el panel y rotulado «hace X min» (T032); **P4** sin Chart.js; **P5** borrar las capas apagadas del globo sin cambio visible (T025); **P6** valores por defecto aceptados, sin choques con las normas (T027, T031).
