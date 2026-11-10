# Implementation Plan: Panel completo — adoptar el front externo con correcciones

**Branch**: `008-panel-base-mock` | **Date**: 2026-11-05 · **Enmendado**: 2026-11-10 (P1–P6 respondidas el mismo día) | **Spec**: `specs/008-panel-base-mock/spec.md`
**Requisitos**: G0, G1, G2, G3, G4, G5, G5b, G6, G7, G8, G9, G11, G12 (`magType`, `country_id`, `country_name`, `truncated`, `last_ingestion`), G14, G15, G17; parcial G10/J7. Fuera: G13, G16, G18.

Solo documentos de diseño (constitución §19). Los contratos (`api.md`, `docs/enunciado/CONTRATO-API.md`) se citan, no se copian ni se modifican. El inventario del código a portar está en `inventario-front-externo.md`.

## Resumen

El alumno aporta un front completo (`globo-lab`) y lo quiere **tal como se ve**. El trabajo no es diseñar un panel, es **portarlo a `frontend/` conservando su estructura, limpiarlo y corregirlo** en los puntos de fondo: configuración en tiempo de ejecución, mock fuera de producción, profundidad en cinco clases, atribución visible, cálculos en el cliente y capas apagadas del globo; y **conectarlo a la API real**. La apariencia no se toca (`diseno-visual.md`).

Cinco bloques (`tasks.md`): 1 portar y limpiar; 2 configuración y mock; 3 capa de datos; 4 conexión con la API real y atribución; 5 tests, evidencias y cierre. Es trabajo de clase: se corrige lo que incumple un criterio, un contrato o la constitución; lo raro va como límite conocido.

## Qué retira esta enmienda del plan anterior

El prototipo y las capas hexagonales (T005, T006, T022 quedan como evidencia), las celdas de continentes, el prisma de 6 caras, la ficha en panel lateral con borde, las columnas «RESERVADO», el botón «Ver en mapa 2D», los 4 JSON como único mecanismo del mock, el estado `api-unavailable`, la regla «Zustand se instala en 009», la estructura `features/` y SC-014. Se conservan: D1 (`react-globe.gl` 2.38.0), el SHA-256 de `paises.geojson`, el mock `base/truncated/replay/empty` generado en T003 (se amplía), el validador de conformidad de T004 y `format.ts`/`contract.ts` de T002.

## Decisiones (todas tomadas)

| Id | Decisión | Estado |
|---|---|---|
| D1 | Librería del globo: `react-globe.gl` 2.38.0 | Aplicada (T007). `three` 0.187.0 y `@types/three` 0.187.0 se declaran explícitamente (el código importa `three`) |
| D2 | Store único de filtros: Zustand 5.0.8 | Entra aquí (constitución §17) |
| D3 | Estructura de `src/`: **la del front externo** (`components/`, `shared/{api,hooks,lib,types}`, `store/`) | **Alumno, 2026-11-10 (P1)**; sustituye a la opción C. Documentada en `CODEMAP.md` y 03 §7.5 |
| D4 | Mock en `frontend/mock/`, carga bajo demanda, fuera del build de producción | Alumno, 2026-11-10 |
| D5 | Cálculos del cliente: auditoría y rótulo «mostrados»; retraso de ingesta calculado en el panel y rotulado «hace X min» | Alumno, 2026-11-10 (P3) |
| D6 | Comparación histórica en el cajón inferior; G5b reformulado como decisión propia | Alumno, 2026-11-10 (P2) |
| D7 | Sin Chart.js (barras en HTML y CSS) | Alumno, 2026-11-10 (P4) |
| D8 | Borrar las capas apagadas del globo (arcos, densidad por celdas, mapa de calor, marcadores) sin cambio visible | Alumno, 2026-11-10 (P5) |
| D9 | Valores por defecto de la spec aceptados (config, escenario `base`, umbral de 300 s, colores intermedios de profundidad); sin choques con las normas | Alumno, 2026-11-10 (P6) |

Regla de versiones (2026-11-05): si una versión fijada no se puede instalar, se usa la estable anterior y se anota aquí y en la evidencia de T024.

## Technical Context

| Pieza | Versión | Nota |
|---|---|---|
| Node | 24.18.0 | `frontend/.nvmrc` y `engines` |
| React / React DOM | 19.3.1 | |
| TypeScript | 6.0.3 | |
| Vite / `@vitejs/plugin-react` | 8.3.6 / 6.2.1 | |
| Tailwind / `@tailwindcss/vite` | 4.3.4 | Sin `tailwind.config.js` |
| TanStack Query | 5.106.1 | Refresco, estados y caché |
| `react-globe.gl` | 2.38.0 | Ya instalada |
| **`three`, `@types/three`** | 0.187.0 | **Nuevas, declaradas** |
| **Zustand** | 5.0.8 | **Nueva** |
| Vitest / `@types/node` | 5.1.0 / 24.19.2 | |

Todas **exactas** (sin `^`) y con `package-lock.json` (§11). Comprobadas el 2026-11-09: son las del front externo, con `tsc --noEmit` en 0 y 12 pruebas en verde. **No** se instalan `h3-js` (lo trae `react-globe.gl` como dependencia suya; no se declara ni se importa), Chart.js, MapLibre ni Playwright.

**Almacenamiento:** ninguno. **Pruebas:** Vitest para lógica pura (config, petición, parseo, profundidad, mock, formato) más verificación visual con capturas. **Plataforma:** navegador moderno en PC y móvil de 375 px. **Restricciones:** sin secretos (§10), mock separado y etiquetado (§7), el frontend no calcula estadísticas (§17), sin lenguaje de predicción ni riesgo (§21).

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| §5 Nulos | Magnitud nula = barra ND gris sin anillo ni etiqueta (se quita `mag ?? 0`); ficha «ND»; el parseo conserva los nulos; negativos tal cual |
| §7 Sintético separado | El mock está en `frontend/mock/`, fuera del build de producción, sin selector en la interfaz; en modo `api` no hay camino a datos sintéticos. Banner y `is_synthetic` en el mock |
| §10 Secretos | `config.json` sin secretos; sin claves ni textura remota |
| §11 Versiones | Exactas + lock + `.nvmrc` + `engines` |
| §13 Idioma | Identificadores en inglés; docstrings y comentarios en español (plantilla 03 §7.4) |
| §14 Una responsabilidad | Lógica pura (`validateConfig`, `requests`, `parse`, `symbology`, `feedHealth`) en archivos aparte del I/O y del dibujo |
| §15 Contratos únicos | Se cita `api.md`; `contract.ts` transcribe tipos, no reglas; si mock y API divergen se corrige el mock o el front, **nunca el contrato** |
| §16 Cierre | Evidencias, README del frontend y `CODEMAP.md` (T038–T040) |
| §17 Sin estadísticas | Auditoría de cálculos (abajo); `stats` y totales de la API; un solo store de filtros |
| §19 Una feature, plan sin código | Este plan solo tiene documentos; la enmienda de alcance la decide el alumno y se refleja en 01, 02 y 03 |
| §21 Sin predicción | Textos descriptivos |

Sin violaciones. La enmienda cambia el alcance por decisión expresa del alumno (§19) y la fusión de features ya estaba prevista en 03 §4. P6: ningún valor por defecto choca con la constitución ni con 01 (G1, G11, G13).

## Estructura del proyecto (D3: la del front externo)

```
frontend/
  .nvmrc, package.json, package-lock.json, tsconfig.json, vite.config.ts
  README.md                       # cómo ejecutar, material reutilizado, atribuciones
  public/
    config.json                   # mode, apiBaseUrl, refreshSeconds, timeoutMs
    datos/paises.geojson          # copia byte a byte de data/catalogo/ (SHA-256 en SC-014)
  mock/                           # SOLO desarrollo y pruebas; fuera del build de producción
    base.json, truncated.json, replay.json, empty.json, realistic.json
    backend.ts                    # servidor simulado: /eventos, /estadisticas, /salud sobre un escenario
  scripts/
    generate-mock.mjs             # generador determinista (semilla fija)
    copy-countries.mjs            # copia paises.geojson y verifica el SHA-256
  tests/                          # Vitest + support/validateEventsResponse.ts + fixtures/
  src/
    main.tsx, App.tsx, index.css  # @theme con los tokens (diseno-visual.md §2)
    components/                   # GlobeView, Grain, Legend, EventCard, SidebarParts, FiltersBar, FiltersPanel,
                                  # EventsTable, RecentEvents, StatsPanel, StatsDrawer, FeedStatus, StatusBanners,
                                  # AppShell, ConfigGate (nuevo), Attribution (nuevo)
      mobile/                     # MobileLayout, MobileEventsList
    shared/
      api/                        # client.ts, requests.ts (puro), parse.ts (puro), loadConfig.ts, dataSource.ts, mockUnavailable.ts
      hooks/                      # useObservatory.ts, useCountries.ts, useMediaQuery.ts, useNow.ts
      lib/                        # format, symbology, appearance, color, tokens, feedHealth, validateConfig (puro)
      types/contract.ts           # tipos de api.md §3 y §5
    store/filters.ts              # Zustand: mode, hours, dateFrom, dateTo, minMag, country
```

**Mapa de portado** (origen `_import-front/globo-lab/src/` → destino `frontend/src/`):

| Origen | Destino |
|---|---|
| Todo `src/` salvo lo de las dos filas siguientes | Igual (misma ruta) |
| `config.json` | **Se sustituye** por `public/config.json` + `shared/lib/validateConfig.ts` + `shared/api/loadConfig.ts` + `components/ConfigGate.tsx` (T027) |
| `shared/api/mock.ts` | `frontend/mock/backend.ts` (servidor simulado, fuera de `src/`) |
| `data/paises.geojson` | `public/datos/paises.geojson` (copia verificada, T024) |
| `prototipo-mapa/`, `.claude/`, `dist/`, `.git/`, `node_modules/`, `package-lock.json`, `BITACORA.md` | **No se portan** |

Reglas de importación: `shared/` no importa de `components/`; `components/` usa `shared/` y `store/`; `App.tsx` y `components/mobile/MobileLayout.tsx` componen. `GlobeView` es el único archivo que importa `react-globe.gl` y `three`. El resto de `components/` se organiza por responsabilidad (un componente por archivo).

## Recorrido de los datos

```
public/config.json ──► validateConfig ──► ConfigGate (error con el campo | panel)
                                │ mode
                 ┌──────────────┴───────────────┐
                 ▼ api                          ▼ mock (solo desarrollo)
         shared/api/client (fetch, timeoutMs)   mock/backend (escenario JSON, ?scenario=)
                 └──────────────┬───────────────┘
                                ▼ parse (forma + nulos intactos)
                 useObservatory (TanStack Query, refreshSeconds, última lectura)
                                ▲ requests (filtros del store → parámetros; ventana de replay)
                         store/filters (Zustand)
                                ▼
     globo · lista · tabla · estadísticas · estado y avisos · atribución
```

## Diseño por pieza

**Configuración (FR-003, FR-004).** `public/config.json` se pide con `fetch` al arrancar (`loadConfig`). `validateConfig` (pura) devuelve `{ ok: true, config }` o `{ ok: false, field, message }`. `ConfigGate` muestra la carga, el error (nombrando el campo) o el panel. `refreshSeconds` y `timeoutMs` ya se **aplican**. El umbral de «desactualizado» (300 s) pasa a una constante de `feedHealth.ts`. Se elimina `src/config.json`.

**Mock fuera de producción (FR-005 a FR-009).** El código del servidor simulado y los JSON viven en `frontend/mock/`. `dataSource.ts` lo carga con `import('@mock/backend')` **solo** si `config.mode === 'mock'`. En `vite.config.ts` el alias `@mock` apunta a `mock/backend.ts` en los modos `development` y `test` y a `src/shared/api/mockUnavailable.ts` (lanza «mock no disponible en este build») en `production`, de modo que `vite build` no empaqueta el servidor ni los JSON (que `backend.ts` carga con `import.meta.glob` en modo `?url`). Comprobación (SC-003): `grep -r __MOCK_BACKEND__ dist` y `grep -r "Sintético:" dist`, sin resultados. Plan B si Vite aún arrastra el glob: sacar `backend.ts` a un paquete de pruebas fuera de `src/` y cargarlo solo con `import.meta.env.DEV`. Nota: en el front externo el selector de origen solo se veía en desarrollo (`import.meta.env.DEV`), pero el mock iba dentro del bundle; esa es la parte que se corrige.

**Escenarios (FR-006).** Se amplía `scripts/generate-mock.mjs`. `base`, `truncated`, `replay` y `empty` salen de T003 (se ajusta `replay` para que **todas** sus fechas caigan dentro de 2025: hoy una es de 2024-12-31). `realistic` toma las zonas y la distribución del mock en memoria del front externo (unos 400 eventos, semilla fija, fechas relativas a «ahora») y le añade los casos de borde (magnitud nula y negativa, profundidad nula y negativa, `place` nulo, `magType` nulo, sin país). `backend.ts` responde `eventos`, `estadisticas` (con histogramas de profundidad de cinco tramos, `by_hour`, `by_country`, `comparison` o `null` en replay) y `salud`. Los escenarios fijos (`base`, `truncated`, `replay`, `empty`) se devuelven tal cual, sin aplicar el periodo; `realistic` aplica `start`, `end`, `min_mag` y `country_id`. Esto es un **servidor simulado**: el cálculo está permitido aquí y solo aquí.

**Capa de datos (FR-010 a FR-015).** `requests.ts` (pura) convierte los filtros del store en parámetros: `live` con ventana de horas (el `start` se calcula al pedir, no en la clave de la caché) o rango de fechas UTC (`end` = día final + 1 día); **`replay` con `start=2025-01-01T00:00:00.000Z` y `end=2026-01-01T00:00:00.000Z`** (constantes `REPLAY_START`/`REPLAY_END`, el `reference_period` de `api.md` §5) y el periodo del filtro desactivado. `country_id` solo si es `none` o tres letras. `parse.ts` (pura) comprueba la forma de `EventsResponse`, `StatsResponse` y `HealthResponse` y conserva los nulos; si no cuadra, lanza `ApiError` con el código `invalid_response`. `client.ts` aplica `timeoutMs` con `AbortSignal.timeout` y mapea los errores al cuerpo del contrato. `useObservatory` usa TanStack Query con `refetchInterval: refreshSeconds × 1000` (una consulta en vuelo no se duplica, así que no se solapan), `retry: false`, `placeholderData: keepPreviousData` (la última lectura buena sigue visible y `updatedAt` la marca como antigua) y la salud cada 30 s. Un replay con `features: []` es el estado `empty`, no un error.

**Simbología (FR-017, FR-018).** `symbology.ts`: `DEPTH_CLASSES` pasa de 3 a 5 clases con los cortes 10/35/70/300 y los colores de `spec.md`; `heightFor` no cambia; `colorForEvent` y la leyenda usan las cinco clases. En `GlobeView` desaparece `magOf = mag ?? 0`: los anillos y etiquetas solo se generan para eventos con `mag !== null` y `mag ≥ umbral`; el tooltip muestra «ND». La barra ND es gris `#8a93a0` de altura mínima.

**Globo (FR-016, FR-031).** No cambia su aspecto ni sus parámetros. Se mueve el código tal cual, se documenta (docstrings), se corrigen los nulos y se **borran las capas apagadas**: arcos (`arcsData` y `arcs`), densidad por celdas (`hexBinPointsData`), mapa de calor (`heatmapsData`) y marcadores HTML (`htmlElementsData`, `makeMarker`), con sus campos de `Appearance` (`showArcs`, `arc*`, `showHexBin`, `hexBin*`, `showHeatmap`, `heat*`, `showMarkers`, `marker*`) y el estilo `.quake-marker` de `index.css`. Se conservan los anillos, las etiquetas, la tierra (incluida su rama `hex`, apagada pero fuera de la lista de P5) y el selector de pilar más cercano (18 px). Comprobación (SC-017): capturas del globo antes y después, sin diferencias.

**Atribución (FR-025).** Componente `components/Attribution.tsx`: línea fija de 11 px con «Sismos: USGS · Fronteras: Natural Earth (dominio público) · Globo: react-globe.gl y three (MIT) · Sin textura». Escritorio: abajo a la derecha, con `z-index` por encima del cajón de estadísticas. Móvil: franja fija en el pie del diseño, fuera de las hojas. Se retira la línea de 9 px del desplegable del estado.

**Avisos y estado (FR-015, FR-023, FR-024).** `StatusBanners` gana el aviso de **truncado** («Mostrando N de M eventos», con `metadata.count` y `metadata.total`; hoy el truncado solo aparece como «Sí/No» en el desplegable) y el texto del aviso de reproducción pasa a «REPRODUCCIÓN». Un replay vacío muestra «Sin eventos reproducidos». El retraso de ingesta sigue calculándose en el panel (`feedHealth.ts`, `generated − last_ingestion`) y se rotula «hace X min» con la nota «calculado en el panel» (P3).

**Desarrollo (FR-002).** `vite.config.ts`: `server: { port: 4200, strictPort: true, proxy: { '/api': process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000' } }`. El CORS de la API no existe aún; el proxy lo evita en desarrollo.

## Auditoría de cálculos en el cliente (lista inicial; T032 la rehace sobre el código portado)

| # | Dónde | Qué calcula | Veredicto | Acción |
|---|---|---|---|---|
| 1 | `RecentEvents` | `${recent.length} de ${events.length}` | Recuento propio | «mostrados N» y, si hay `metadata`, el total de la API |
| 2 | `EventsTable` | `{events.length} eventos` | Recuento propio | «mostrados N · total M (API)» |
| 3 | `MobileEventsList` | `Todos · {events.length}` | Recuento propio | Igual que 2 |
| 4 | `StatsPanel` | `+{items.length − countries.length} países más` | Resta de longitudes | Rótulo «mostrados 6 de N países» o quitar |
| 5 | `StatsPanel` | `máx. {maxHour}` (máximo de `by_hour`) | Derivado de cifras de la API | Quitar el rótulo (la barra sigue escalando) |
| 6 | `StatsPanel` | Altura de barras (`count / max`) | Escala visual | Se acepta |
| 7 | `feedHealth.ingestionLag` | `generated − last_ingestion` y umbral 300 s | Diferencia de timestamps de la API + umbral | **Aceptado (P3)**: rotulado «hace X min» y nota «calculado en el panel»; sin cambio de contrato |
| 8 | `FeedStatus` | `formatAge(now − ingestion)` («Última ingesta hace…») | Formato relativo con el reloj del navegador | Se acepta (formatear un timestamp) |
| 9 | `StatusBanners` | `formatAge(now − updatedAt)` | Hora de la última consulta propia del panel | Se acepta |
| 10 | `useObservatory` | `start = now − horas`; `end = día + 1 d` | Construcción de la petición | Se acepta |
| 11 | `GlobeView` | Filtrar anillos y etiquetas por magnitud; `magOf` null→0 | Selección visual; **null→0 incumple §5** | Corregir (T026) |
| 12 | `RecentEvents`/`EventsTable` | Ordenar por fecha o columna | Presentación | Se acepta |
| 13 | `FeedStatus` | `Mostrados {count} de {total}` | Valores de `metadata` | Se acepta (ya viene de la API) |
| 14 | `StatsPanel` | `stats.total`, `n_recent`, `variation_pct`, `diff_abs`… | Valores de la API | Se acepta (formatear) |
| 15 | `mock/backend` (antes `shared/api/mock.ts`) | Filtros y estadísticas del servidor simulado | Es el servidor | Se acepta **solo** fuera de `src/` y del build de producción (T029) |

## Límites conocidos (una línea cada uno)

- G16 no cubierta; foco de teclado y tamaño táctil sin trabajar.
- Con 5 000 eventos, la selección del pilar más cercano recorre todos en cada movimiento: rendimiento sin medir.
- El periodo en `replay` es fijo (2025).
- El umbral de «desactualizado» es una constante del código.
- Sin datos de replay reales hasta `013`; aquí solo el vacío real y el escenario `replay` del mock.
- La rama `hex` de la tierra del globo (apagada) se queda: no estaba en la lista de P5.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Vite arrastra el mock al build de producción | Alias por modo (T029) y comprobación en `dist/` (T039); plan B en «Mock fuera de producción» |
| Borrar las capas apagadas cambia algo visible | Capturas antes y después con el mismo escenario y cámara (T024, T025; SC-017) |
| La API real devuelve algo que el mock no cubre (campos, nulos, orden) | T034 contrasta mock y API y corrige el mock o el front, nunca el contrato |
| No hay datos reales suficientes (ingesta recién levantada, sin histórico) | T034 lo detecta antes de T035; sin histórico, la comparación se prueba con `realistic` y se anota |
| Copiar el front arrastra código que incumple estándares (docstrings, importaciones inversas) | T025 los ajusta antes de seguir |
| El stack de Compose no está levantado al llegar al bloque 4 | T034 empieza por `docker compose up` y comprueba `/api/salud`; si no arranca, se detiene y se pregunta |
