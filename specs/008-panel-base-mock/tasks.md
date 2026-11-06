# Tasks: Panel base con mock y mapa

**Entrada**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md` (esta carpeta). **IDs**: G0, G2, G11 (parcial), G12 (`magType`), G14, G15, G17.

23 tareas en 5 bloques (máximo 25 y 5). Formato: `- [ ] T### [P] [US#] Descripción con ruta`. `[P]` = se puede hacer en paralelo (archivos distintos, sin depender de una tarea sin terminar). Cada tarea lleva **Prueba** y **Cubre**.

**Revisión del 2026-11-06 (cambio de diseño HUD del alumno).** `T001`–`T006` están hechas y no se reabren. Se ajustan `T007` y `T010` a `T021`, y se añaden `T022` (prototipo del prisma hexagonal, en el Bloque 2) y `T023` (tokens y esqueleto HUD, en el Bloque 3); los números nuevos van al final para no renumerar. Pasa de 21 a 23 tareas; quedan 2 libres. Lo invalidado está en `spec.md` («Cambio de diseño del alumno»).

**Respuestas del alumno del 2026-11-06.** D1 = `react-globe.gl` queda decidida (P6): `T007` pasa a aplicar esa decisión, sigue sin ejecutarse y conserva su dependencia de `T022` (ver la tarea). Criterio de `T022`: el prisma de 6 caras aceptable «de cerca» es bueno; malla propia solo si queda claramente mal. P9 se decide en `T022` con la medida. La feature del mapa 2D se nombra `panel-mapa-2d`. Siguen 23 tareas en 5 bloques; `T001`–`T006` no cambian.

**Estructura de `src/` decidida (D3, opción C, alumno 2026-11-05).** Las rutas siguen `plan.md`. Las tareas que dependen de **D1** (decidida por el alumno el 2026-11-06: `react-globe.gl`) son solo `T007` (instalación) y `T015`. **D2** (Zustand, alumno 2026-11-05) se instala en `009`: aquí no genera instalación, solo se reserva la carpeta (`T001`). MapLibre y el mapa 2D son la feature `panel-mapa-2d`: no se instalan ni se implementan aquí.

**Regla de versiones (alumno 2026-11-05).** Si alguna versión fijada en `plan.md` no se puede instalar en `T001`, se usa la estable anterior y se anota en `plan.md` y en la evidencia de `T001`.

**Pruebas ligeras** (sin fuzz, sin exhaustivas, sin auditorías): config, mock conforme al contrato, escala de radio/color/ND y formato. Lo raro se anota como límite conocido en una línea.

## Bloque 1 — Esqueleto y mock sintético (G0, G15)

- [x] T001 Crear el proyecto en `frontend/` con las versiones **exactas** de `plan.md` (TypeScript 6.0.3; si alguna versión no se puede instalar, la estable anterior, anotándolo en `plan.md` y en la evidencia) (Node 24.18.0 en `.nvmrc` y `engines`; React, TypeScript, Vite, Tailwind con `@tailwindcss/vite`, TanStack Query, Vitest); `package-lock.json`; alias `@/` → `src/`; `build.assetsInlineLimit: 0`; scripts `dev`, `build`, `preview`, `test`; carpeta reservada `src/store/README.md` (una línea: «Reservada para el store de filtros (Zustand), feature 009»); `.gitignore` de `node_modules` y `dist`. **No** instalar librería de mapa ni de store.
  - **Prueba**: `npm ci && npm run build` termina con código 0 desde un clon limpio y deja `dist/`; `npm run dev` responde HTTP 200; `npm ls typescript` muestra 6.0.3 (o la anotación de la versión anterior usada).
  - **Cubre**: G0; FR-001, FR-002, FR-006; SC-001.

- [x] T002 [P] Tipos del contrato y formato: `src/shared/types/contract.ts` (tipos de `api.md` §3.2 y §3.4, ver `data-model.md`) y `src/shared/lib/format.ts` (ND para nulos, decimal con coma, «AAAA-MM-DD HH:mm UTC» desde ms, «Sin país asignado», «Sin descripción»). Con docstrings en español (03 §7.4).
  - **Prueba**: `tests/format.test.ts` (Vitest): nulo → «ND» y nunca «0»; −0,06 → «−0,06»; ms conocido → fecha UTC esperada; sin país → texto fijo.
  - **Cubre**: G2, G12 (`magType`); FR-007, FR-014; SC-005, SC-013.

- [x] T003 Generar el mock sintético: `scripts/generate-mock.mjs` (semilla fija, sin dependencias) y los cuatro archivos `mock/base.json` (~30 features con todos los casos de FR-008), `mock/truncated.json` (5 000 features, `count` 5000, `total` 6213, `truncated` true, `next_cursor` no nulo), `mock/replay.json` (pocas, `metadata.mode: "replay"`) y `mock/empty.json`. Todo `is_synthetic: true`, `id` `mock-…`, `place` «Sintético: …», sin ids reales de USGS. Comprobar en este punto que Vite emite los JSON como archivos aparte en `dist/assets/` (P4); si no, aplicar el plan B de `plan.md` y avisar al alumno.
  - **Prueba**: ejecutar el script dos veces da archivos idénticos; `npm run build` deja los cuatro JSON como archivos en `dist/assets/` y el JS principal no crece con los 5 000 eventos.
  - **Cubre**: G15; FR-008, FR-009; SC-007 (parte).

- [x] T004 Comprobación de conformidad del mock: `tests/support/validateEventsResponse.ts` (lista de errores según `api.md` §3.2 y §3.4: campos, tipos, nulos permitidos, tiempos enteros, `Point` con coordenadas finitas, `is_synthetic` verdadero, prefijo `mock-`, `count === features.length`) y `tests/mock.test.ts`, más un archivo estropeado de prueba en `tests/fixtures/bad-response.json`.
  - **Prueba**: pasa con los cuatro archivos y **falla** con el estropeado; verifica que el 100 % de las features cumple `is_synthetic` y `mock-`.
  - **Cubre**: G15; FR-010; SC-007, SC-008.

## Bloque 2 — Prototipo de la librería del mapa (D1, PRONTO)

Depende de `T001` y `T003`. Puede hacerse en paralelo con el Bloque 3.

- [x] T005 **Montaje del prototipo.** Candidatas confirmadas por el alumno (2026-11-05): `react-globe.gl` y MapLibre GL JS; se instalan **solo** en `frontend/prototipo-mapa/` (con su propio `package.json`, fuera del lock del proyecto). Montar una página mínima por candidata que cargue `mock/truncated.json`, con círculos por magnitud/profundidad, fronteras de `data/catalogo/paises.geojson`, clic para abrir una ficha mínima y atribución visible. Sin pulir estilo.
  - **Prueba**: las páginas arrancan y pintan los 5 000 eventos.
  - **Cubre**: G2; D1; SC-012 (parte).

- [x] T006 Medir con los criterios de la spec (D1) en cada candidata, en PC y a 375 px: tiempo hasta pintar los 5 000 (ref. ≤ 3 s), fluidez al mover y ampliar, pulsar un círculo pequeño y abrir la ficha, uso en 375 px, atribución legible, peso del build comprimido (kB). Escribir la tabla en `docs/evidencias/panel-base-mock/prototipo-mapa.md` con una recomendación de una frase (G17 pesa a favor del 2D). Si ninguna cumple, probar Leaflet con canvas antes de bloquear.
  - **Prueba**: la tabla tiene todos los criterios rellenos para cada candidata, con la fecha y el equipo de medida.
  - **Cubre**: G2, G17; D1; SC-012.
  - *Nota 2026-11-06 (superada por el cambio de diseño)*: la recomendación de una frase (MapLibre por G17) ya no decide esta feature, porque el 2D pasa a `panel-mapa-2d`. La tabla se conserva como evidencia; sus datos del globo (37 fps, 0 de 4 pulsaciones a 6 px, 612 kB) se reevalúan en `T022` con prismas hexagonales.

- [x] T022 [US1] **Prototipo corto del prisma hexagonal y las celdas hexagonales** (dentro de `frontend/prototipo-mapa/globe/`, sin tocar `frontend/src/`; usa `mock/truncated.json` y `data/catalogo/paises.geojson`): capa de puntos con `pointResolution = 6` y altura según V1, color según V2 y ND gris; capa `hexPolygonsData` con los continentes sin `ADM0_A3 = ATA` (probar resolución 3 y 4); fondo negro sin textura ni atmósfera. Medir contra SC-012 y los criterios de `T006`: tiempo hasta pintar (≤ 3 s), fotogramas al mover (≥ 30 fps), pulsar un prisma pequeño a 0, 3 y 6 px del centro (con y sin selección del más cercano mediante `getScreenCoords`), lectura del prisma de 6 caras **de cerca** (y a escala de globo, solo como dato), color visible frente al token, número de celdas, y 375 px. Escribir el resultado y la decisión de parámetros (resolución, anchura 0,45° u otra, selección del más cercano sí o no) en `docs/evidencias/panel-base-mock/prototipo-hexagonal.md` con capturas.
  - **Prueba**: la tabla de `prototipo-hexagonal.md` tiene todos los criterios medidos con fecha y equipo; las capturas muestran el prisma a 1280 y 375 px; si algo no cumple, queda anotado el plan B elegido. **Criterio decidido por el alumno (2026-11-06):** prisma de 6 caras que se ve bien de cerca = bueno, aunque a escala de globo no se distinga como hexágono; malla propia (`customLayerData`) solo si queda claramente mal. **P9** (cómo hacer pulsable el prisma pequeño) se decide aquí con la medida, empezando por la selección del más cercano; el resultado se anota en `prototipo-hexagonal.md` y en `spec.md`.
  - **Cubre**: G2, G17; FR-011, FR-012; SC-012. Depende de `T003` y `T006`. Tiene que estar hecha antes de `T007` (que borra el prototipo donde se hace) y de `T015`.

- [ ] T007 **Aplicar D1 = `react-globe.gl`** (decisión ya tomada, «Decidido por el alumno, 2026-11-06», P6; **no ejecutada**): anotar la versión (`npm view react-globe.gl version`) en `plan.md` y en la spec, instalar **solo `react-globe.gl`** en `frontend/` con versión exacta y lock (**sin MapLibre**) y borrar `frontend/prototipo-mapa/`. **Conserva su dependencia de `T022`** por dos motivos: borra la carpeta donde `T022` hace el prototipo (no puede borrarse antes de validar el prisma) y la versión que se fija debe ser la que `T022` validó. `T022` va ANTES.
  - **Prueba**: `npm ci && npm run build` sigue en 0; `frontend/package.json` contiene `react-globe.gl` y ninguna otra librería de mapa; `frontend/prototipo-mapa/` no existe.
  - **Cubre**: G0, G2; FR-001, FR-013; D1 (aplicación). Depende de `T022`.

## Bloque 3 — Configuración, capa de datos, símbolos y tokens HUD (independiente de D1)

- [ ] T008 [P] [US4] Configuración en tiempo de ejecución: `public/config.json` (`mode: "mock"`, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`; sin secretos), `src/config/validateConfig.ts` (pura: valida los cuatro campos y devuelve el campo que falla), `src/config/loadConfig.ts` (`fetch` de `config.json`) y una pantalla de error que nombra el campo. `refreshSeconds` y `timeoutMs` se validan y no se aplican.
  - **Prueba**: `tests/config.test.ts`: válido; `mode: "otro"` → error con campo `mode`; `refreshSeconds` 0 o texto → error con su campo; falta de archivo → mensaje. Manual: editar `dist/config.json` y recargar (US4, `quickstart.md` §4).
  - **Cubre**: G15; FR-003, FR-004; SC-011 (mitad), US4.

- [ ] T009 [US4] Capa de datos única: `src/api/loadEvents.ts` (con `mode: "mock"` carga el archivo del caso con `import.meta.glob` en modo `?url`, caso por `?scenario=` con `base` por defecto; con `mode: "api"` devuelve «api no disponible» sin pedir nada ni caer al mock), `src/api/useEvents.ts` (hook con TanStack Query) y proveedor de `QueryClient` en `src/main.tsx`. Estados según `data-model.md` (`loading`, `ready`, `empty`, `error`, `api-unavailable`).
  - **Prueba**: `tests/loadEvents.test.ts` con las funciones puras de selección de caso y de modo (api → no disponible; escenario desconocido → `base`). Manual: `/?scenario=truncated` carga 5 000 eventos.
  - **Cubre**: G15; FR-005, FR-007; SC-011 (mitad).

- [ ] T010 [P] Símbolos del prisma (lógica pura, V1–V4, revisada el 2026-11-06): `src/features/map/lib/symbology.ts` con `heightFor` (máx(0,010; 0,0125 × clamp(M, 0, 8))), `depthClassFor`, `colorFor` y `symbolFor` (ND de magnitud: barra gris `#8A93A0` de altura mínima 0,010; ND de profundidad: gris; cortes 10/35/70/300; rampa de V2) y las constantes de la leyenda y de la anchura (0,45°).
  - **Prueba**: `tests/symbology.test.ts`: alturas para M −0,06 / 0 / 0,8 / 2 / 4 / 6 / 8 / 9 (0,010; 0,010; 0,010; 0,025; 0,050; 0,075; 0,100; 0,100); clase en 9,99 / 10 / 34,99 / 35 / 69,99 / 70 / 299,99 / 300, en negativas y en nula; magnitud nula → barra gris de altura mínima; nunca altura 0; la rampa tiene contraste ≥ 3 : 1 sobre `#000000` y su luminancia relativa desciende de la clase 1 a la 5 (SC-016).
  - **Cubre**: G2, G16 (contexto); FR-011, FR-015, FR-017; SC-005, SC-013, SC-016.

- [ ] T011 [US1] Cabecera, banner y estados dentro del esqueleto de `T023`: `src/App.tsx` y `src/features/map/components/Banner.tsx` con el banner «DATOS SINTÉTICOS (MOCK)» en la cabecera (visible si `mode` es `mock` o algún evento tiene `is_synthetic`), los mensajes de estado («Modo api: la conexión con la API todavía no está disponible», «Sin eventos en el intervalo», error de carga del mock) y un hueco para el globo; muestra `metadata.count` y `total` tal cual, sin calcular. Solo clases de los tokens HUD.
  - **Prueba**: manual con los cuatro casos y `mode: "api"`: banner y mensajes correctos; sin «NaN» ni «undefined»; los textos usan los tokens.
  - **Cubre**: G15; FR-005, FR-009, FR-020; SC-007, SC-011. Depende de `T009` y `T023`.

- [ ] T023 [P] [US3] **Tokens y esqueleto HUD** (`diseno-visual.md`): bloque `@theme` en `src/index.css` con los tokens (fondo, superficie, celdas, líneas, texto, acento naranja, gris ND, rampa `depth-1`…`depth-5`, fuente, etiquetas de 11 px en mayúsculas, bordes de 1 px, tamaño táctil de 44 px) y `src/shared/layout/AppShell.tsx` con cabecera, zona del globo, dos columnas reservadas (marco vacío con «RESERVADO», solo desde `lg`) y hueco de la ficha (panel lateral desde `md`, cajón inferior por debajo). Sin contenido en las columnas.
  - **Prueba**: `tests/tokens.test.ts`: `src/index.css` define todos los tokens de `diseno-visual.md`; los valores `depth-1`…`depth-5` y el gris ND coinciden con las constantes de `symbology.ts`; no hay colores hexadecimales en `src/` fuera de `index.css` y `symbology.ts`. Manual: el esqueleto vacío a 375, 768 y 1280 px sin scroll horizontal (`scrollWidth <= innerWidth`) y con las columnas solo desde 1024 px.
  - **Cubre**: G2, G17; FR-018, FR-020; SC-003 (parte), SC-016. Depende de `T001` y `T010`.

## Bloque 4 — Globo, ficha y leyenda (G2, G12 `magType`, G14)

- [ ] T012 [P] [US1] Datos de los continentes y atribuciones: copiar `data/catalogo/paises.geojson` a `frontend/public/datos/paises.geojson` con un paso documentado (script `frontend/scripts/copy-countries.mjs` que copia y verifica el SHA-256 `6866c877…c977f`, y falla si no coincide); función pura que entrega a la capa de celdas la lista de países **sin `ADM0_A3 = ATA`** (el archivo copiado no se modifica); texto de atribución de Natural Earth, de la librería y «Fondo: negro, sin textura» en una constante compartida.
  - **Prueba**: `sha256sum` de ambos archivos coincide con `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`; el script falla con una copia alterada; `tests/countries.test.ts`: la lista filtrada tiene un país menos que el archivo y no contiene `ATA`.
  - **Cubre**: G14; FR-012, FR-016; SC-009.

- [ ] T013 [P] [US2] Ficha en panel lateral: `src/features/map/components/EventCard.tsx` (descripción del lugar, «Magnitud 5,4 (mww)», profundidad en km, `time` y `updated` en UTC, país o «Sin país asignado», etiqueta «Sintético», enlace a USGS solo si hay `url`; nulos → «ND» o los textos de `data-model.md`; negativos tal cual) y botón «Ver en mapa 2D» siempre visible (`aria-disabled`, focalizable, aviso «Mapa 2D: próximamente (feature panel-mapa-2d)» al activarlo; sin navegar ni pedir nada). Botón de cerrar y «Ver en mapa 2D» de ≥ 44 × 44 px, alcanzables con teclado, cierre con Esc. Panel lateral de 20 rem anclado a la derecha del globo desde `md`; cajón inferior ≤ 50 % con scroll interno por debajo; solo tokens HUD.
  - **Prueba**: manual sobre los eventos de `base` (`mww`, `magType` nulo, magnitud nula, sin país, −0,06 / −0,01, `place` nulo): coinciden con US2; el botón «Ver en mapa 2D» está en todas las fichas y muestra el aviso (SC-017); consola sin errores. La lógica de texto ya se prueba en `T002`. Depende de `T002` y `T023`.
  - **Cubre**: G2, G12 (`magType`), G17; FR-014, FR-019, FR-021; SC-004, SC-005, SC-006, SC-017.

- [ ] T014 [P] [US1] Leyenda y atribución en el esqueleto: `src/features/map/components/Legend.tsx` con «TAMAÑO = MAGNITUD» (prismas de ejemplo M 2, 4, 6), «COLOR = PROFUNDIDAD (KM)» (cinco clases con rango escrito y color), «ND: sin magnitud», «ND: sin profundidad», y la línea de atribución fija abajo a la derecha del globo, fuera de la leyenda y de la ficha. Tarjeta abajo a la izquierda desde `md`; por debajo, botón «Leyenda» en la cabecera de ≥ 44 × 44 px. Usa las constantes de `T010` y `T012`.
  - **Prueba**: manual a 1280 y 375 px: contenido completo; el orden de las clases se conserva en la captura en escala de grises; la atribución se lee sin pulsar nada (SC-010). Depende de `T010`, `T012` y `T023`.
  - **Cubre**: G2, G11 (parcial), G14, G17; FR-015, FR-016, FR-017, FR-019; SC-010.

- [ ] T015 [US1] **(depende de D1 = T007, T022 y T023)** Componente de globo aislado `src/features/map/GlobeView.tsx` con `react-globe.gl`. Entrada: `events`, `selectedId`; salida: `onSelect` (contrato de `data-model.md`). Fondo negro sin textura, celdas hexagonales de los continentes desde `/datos/paises.geojson` (sin Antártida, parámetros de `T022`), un prisma hexagonal por feature (`pointResolution = 6`, altura y color de `symbolFor` de `T010`), clic o toque abre la selección (con selección del prisma más cercano si `T022` lo decidió), prisma seleccionado resaltado en naranja, atribución en el sitio de `T014`. Si faltan los continentes: se pintan los prismas y se avisa. Ningún archivo fuera de `features/map` importa la librería.
  - **Prueba**: manual con `base`: prismas = nº de features; ND gris de altura mínima visible; clases distinguibles. Con `truncated`: 5 000 prismas en ≤ 3 s, ≥ 30 fps al mover y la ficha abre al pulsar un prisma pequeño. Ningún archivo fuera de `features/map` importa `react-globe.gl`; solo se usa `GlobeView`.
  - **Cubre**: G2, G14; FR-011, FR-012, FR-013, FR-016; SC-002, SC-010, SC-012.

- [ ] T016 [US1] Integrar en `App.tsx`: `useEvents` → `AppShell` con `GlobeView` + `EventCard` + `Legend` + `Banner`; el evento seleccionado es estado local de `App` (no hay store de filtros). Caso `empty`: globo con continentes y el mensaje. Esc cierra la ficha.
  - **Prueba**: recorrido de `quickstart.md` §3 con los cuatro casos y consola sin errores.
  - **Cubre**: G2, G12 (`magType`), G15; FR-005, FR-014, FR-020; SC-002, SC-004, SC-006.

## Bloque 5 — Responsive, evidencias y cierre (G17, §16)

- [ ] T017 [US3] Revisión responsive del esqueleto HUD: ajustar clases de Tailwind para que no haya scroll horizontal a 375, 768 y 1280 px en los cuatro casos, con leyenda abierta y con ficha abierta; ficha como cajón inferior (< 768 px) y como panel lateral (≥ 768 px) con scroll interno; columnas reservadas solo desde 1024 px y sin tapar la ficha; la atribución sigue visible.
  - **Prueba**: en consola `document.documentElement.scrollWidth <= window.innerWidth` devuelve `true` en las 12 combinaciones de ancho y caso con ficha y leyenda abiertas.
  - **Cubre**: G17, G11 (atribución y leyenda); FR-016, FR-018, FR-019, FR-020; SC-003.

- [ ] T018 Capturas y comprobaciones visuales en `docs/evidencias/panel-base-mock/`: `base` a 1280 px (con las columnas reservadas y el panel lateral de ficha), `base` a 375 px con el cajón de ficha, `truncated` a 375 px, `empty`, mensaje de modo api, mensaje de `mode` inválido, ficha con `mww` y con `magType` nulo, ficha del evento ND con «Ver en mapa 2D» visible, captura de la leyenda en escala de grises; nota con el resultado de la consola (cero errores) y de `scrollWidth`.
  - **Prueba**: los archivos existen y se lee la atribución sin pulsar nada en 375 y 1280 px; el botón «Ver en mapa 2D» se ve en las capturas de ficha.
  - **Cubre**: G2, G12 (`magType`), G16 (contexto), G17; SC-003, SC-004, SC-005, SC-006, SC-010, SC-011, SC-017.

- [ ] T019 Salidas de verificación en `docs/evidencias/panel-base-mock/`: `npm ci`, `npm run build` y `npm test` desde un clon limpio (con códigos de salida), `npm run dev` con HTTP 200, `sha256sum` de `paises.geojson`, y comprobación de que `frontend/` no tiene Dockerfile, compose, filtros, tabla, gráficos, replay ni MapLibre (`package.json` solo con `react-globe.gl` como librería de mapa).
  - **Prueba**: todos los códigos en 0 y SHA coincidente; `quickstart.md` §1, §2, §5 y §8 cumplidos.
  - **Cubre**: G0, G14, G15; SC-001, SC-008, SC-009, SC-013, SC-014, SC-016, SC-017.

- [ ] T020 `frontend/README.md`: cómo ejecutar (`npm ci`, `dev`, `build`, `preview`, `test`), `config.json` y `?scenario=`, aviso de mock sintético, **material reutilizado** (Natural Earth `paises.geojson` y su ruta, dominio público, 1:110 m; `react-globe.gl` con su licencia y atribución; fondo negro sin textura; los tokens HUD y un enlace a `specs/008-panel-base-mock/diseno-visual.md`) para G14 y M2, y los límites conocidos de `plan.md`. Una línea en el `README.md` de la raíz que enlace al del frontend.
  - **Prueba**: el README nombra el origen de `paises.geojson` y la atribución de la librería; los comandos copiados funcionan.
  - **Cubre**: G11 (parcial), G14, G15; FR-012, FR-016; SC-015.

- [ ] T021 Cierre documental (constitución §16): actualizar `CODEMAP.md` (filas de `frontend/` con las rutas reales de la estructura decidida; sustituir las filas previstas que citan `frontend/src/app/core/...` si ya no aplican) y marcar en `docs/planificacion/01-checklist-requisitos.md` G0, G2, G14, G15, G17 y G12 solo para `magType`. **No** marcar G11 como hecho (P3) y anotar su avance parcial. **No** marcar G18 (es de `panel-mapa-2d`). Actualizar en 01, 02 y 03 los textos de F8a/G0/G2/§0 que aún dicen «popup», «círculos» o «mapa» para que coincidan con el globo HUD y con la librería confirmada en `T007`. La fila de `CODEMAP.md` de `diseno-visual.md` ya existe. Anotar el cierre en `specs/008-panel-base-mock/bitacora.md`. Detenerse y esperar revisión: sin commit ni merge.
  - **Prueba**: cada ruta de `CODEMAP.md` existe; `SC-015` cumplido.
  - **Cubre**: G0, G2, G11 (parcial), G12, G14, G15, G17; FR-006; SC-015.

## Dependencias

```
T001 ─┬─ T002 ─┐
      ├─ T003 ─┼─ T004
      │        └─ T005 ─ T006 ─ T022 ─ T007 ───────┐   (Bloque 2: PRONTO, en paralelo al 3)
      ├─ T008 ─ T009 ─────────────────────┐
      ├─ T010 ─ T023 ─ T011 (+T009) ──────┤
      └─ T012, T013, T014 (+T023) ────────┴─ T015 (necesita T007, T022, T010, T012, T023) ─ T016 ─ T017 ─ T018 ─ T019 ─ T020 ─ T021
```

- `T009` necesita `T003` (archivos del mock) y `T008`.
- `T023` necesita `T010` (la rampa de la prueba); `T011`, `T013` y `T014` necesitan `T023`.
- `T013` necesita además `T002`; `T014` necesita `T010` y `T012`.
- `T022` necesita `T003` y `T006`; `T007` necesita `T022` (validar el prisma y la versión antes de borrar el prototipo); la decisión D1 ya está tomada.
- El Bloque 3 y las tareas `T012`–`T014` no dependen de D1: avanzan mientras se hace `T022`.

## Paralelo

`T002`, `T003` tras `T001`; `T008`, `T010`, `T012` entre sí; `T013`, `T014` entre sí tras `T023`; el Bloque 2 completo (`T022` incluida) en paralelo con el Bloque 3.

## Estrategia

MVP = Bloques 1–4 con el caso `base` (US1 y US2). Después `truncated`, responsive (US3) y configuración (US4, ya cubierta en el Bloque 3). El Bloque 2 va **primero** porque el globo hexagonal (`T022`) es el único riesgo real de la feature.

## Preguntas para el alumno

Detalle en `spec.md` («Preguntas para el alumno»). Pendiente de decidir: **P9**, que se resuelve en `T022` con la medida (cómo hacer pulsable el prisma pequeño).

Resueltas (alumno, 2026-11-06): **P6** `react-globe.gl` (D1; `T007` solo la aplica); **P13** la feature del mapa 2D se llama `panel-mapa-2d`; **color** rampa cálida por profundidad (anillos pulsantes fuera de esta feature); **criterio del prisma** (de cerca vale; malla propia solo si queda claramente mal); **P7, P8, P10, P11, P12** se mantienen las opciones aplicadas (botón «Ver en mapa 2D» visible y desactivado con aviso «próximamente» en `T013`; marcos «RESERVADO» desde 1024 px en `T023`; ficha superpuesta al globo; valores por defecto de V1 y V2; `diseno-visual.md` en `specs/008-panel-base-mock/`).

Resueltas (alumno, 2026-11-05): D2 Zustand (se instala en `009`); D3 opción C; Q1 candidatas `react-globe.gl` y MapLibre confirmadas; Q2 `?scenario=` desconocido cae a `base` con aviso en consola; Q3 capturas manuales; Q4 mock en `frontend/mock/` con `?url` (si falla `T003`, `public/mock/` y corregir 03 §7.5); Q5 TypeScript 6.0.3.
