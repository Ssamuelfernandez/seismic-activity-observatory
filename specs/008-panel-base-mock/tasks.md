# Tasks: Panel base con mock y mapa

**Entrada**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md` (esta carpeta). **IDs**: G0, G2, G11 (parcial), G12 (`magType`), G14, G15, G17.

21 tareas en 5 bloques (máximo 25 y 5). Formato: `- [ ] T### [P] [US#] Descripción con ruta`. `[P]` = se puede hacer en paralelo (archivos distintos, sin depender de una tarea sin terminar). Cada tarea lleva **Prueba** y **Cubre**.

**Estructura de `src/` decidida (D3, opción C, alumno 2026-11-05).** Las rutas siguen `plan.md`. Las tareas que dependen de **D1** (librería del mapa; candidatas `react-globe.gl` y MapLibre, elección final del alumno en `T007`) son solo `T007` y `T015`. **D2** (Zustand, alumno 2026-11-05) se instala en `009`: aquí no genera instalación, solo se reserva la carpeta (`T001`).

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

- [ ] T005 **Montaje del prototipo.** Candidatas confirmadas por el alumno (2026-11-05): `react-globe.gl` y MapLibre GL JS; se instalan **solo** en `frontend/prototipo-mapa/` (con su propio `package.json`, fuera del lock del proyecto). Montar una página mínima por candidata que cargue `mock/truncated.json`, con círculos por magnitud/profundidad, fronteras de `data/catalogo/paises.geojson`, clic para abrir una ficha mínima y atribución visible. Sin pulir estilo.
  - **Prueba**: las páginas arrancan y pintan los 5 000 eventos.
  - **Cubre**: G2; D1; SC-012 (parte).

- [ ] T006 Medir con los criterios de la spec (D1) en cada candidata, en PC y a 375 px: tiempo hasta pintar los 5 000 (ref. ≤ 3 s), fluidez al mover y ampliar, pulsar un círculo pequeño y abrir la ficha, uso en 375 px, atribución legible, peso del build comprimido (kB). Escribir la tabla en `docs/evidencias/panel-base-mock/prototipo-mapa.md` con una recomendación de una frase (G17 pesa a favor del 2D). Si ninguna cumple, probar Leaflet con canvas antes de bloquear.
  - **Prueba**: la tabla tiene todos los criterios rellenos para cada candidata, con la fecha y el equipo de medida.
  - **Cubre**: G2, G17; D1; SC-012.

- [ ] T007 **DECISIÓN D1 del alumno** y aplicación: con la tabla de `T006`, el alumno decide la librería (decisión final suya; el diseñador no la cierra). Entonces: anotar la decisión y la versión (`npm view <paquete> version`) en `plan.md` (D1: de «candidatas decididas» a «Decidido por el alumno, <fecha>») y en la spec, instalar **solo la elegida** en `frontend/` con versión exacta y lock, y borrar `frontend/prototipo-mapa/`.
  - **Prueba**: `npm ci && npm run build` sigue en 0; `frontend/package.json` contiene una sola librería de mapa; `frontend/prototipo-mapa/` no existe.
  - **Cubre**: G0, G2; FR-001, FR-013; D1.

## Bloque 3 — Configuración, capa de datos y símbolos (independiente de D1)

- [ ] T008 [P] [US4] Configuración en tiempo de ejecución: `public/config.json` (`mode: "mock"`, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`; sin secretos), `src/config/validateConfig.ts` (pura: valida los cuatro campos y devuelve el campo que falla), `src/config/loadConfig.ts` (`fetch` de `config.json`) y una pantalla de error que nombra el campo. `refreshSeconds` y `timeoutMs` se validan y no se aplican.
  - **Prueba**: `tests/config.test.ts`: válido; `mode: "otro"` → error con campo `mode`; `refreshSeconds` 0 o texto → error con su campo; falta de archivo → mensaje. Manual: editar `dist/config.json` y recargar (US4, `quickstart.md` §4).
  - **Cubre**: G15; FR-003, FR-004; SC-011 (mitad), US4.

- [ ] T009 [US4] Capa de datos única: `src/api/loadEvents.ts` (con `mode: "mock"` carga el archivo del caso con `import.meta.glob` en modo `?url`, caso por `?scenario=` con `base` por defecto; con `mode: "api"` devuelve «api no disponible» sin pedir nada ni caer al mock), `src/api/useEvents.ts` (hook con TanStack Query) y proveedor de `QueryClient` en `src/main.tsx`. Estados según `data-model.md` (`loading`, `ready`, `empty`, `error`, `api-unavailable`).
  - **Prueba**: `tests/loadEvents.test.ts` con las funciones puras de selección de caso y de modo (api → no disponible; escenario desconocido → `base`). Manual: `/?scenario=truncated` carga 5 000 eventos.
  - **Cubre**: G15; FR-005, FR-007; SC-011 (mitad).

- [ ] T010 [P] Símbolos del mapa (lógica pura, V1–V4): `src/features/map/lib/symbology.ts` con `radiusFor`, `depthClassFor`, `colorFor` y `symbolFor` (ND de magnitud: radio 5, sin relleno, contorno de 2 px; ND de profundidad: gris `#9CA3AF`; magnitud acotada entre 0 y 8; cortes 10/35/70/300) y las constantes de la leyenda.
  - **Prueba**: `tests/symbology.test.ts`: radios para M −0,06 / 0 / 2 / 4 / 6 / 8 / 9 (3, 3, 6, 9, 12, 15, 15); clase en 9,99 / 10 / 34,99 / 35 / 69,99 / 70 / 299,99 / 300, en negativas y en nula; magnitud nula → símbolo hueco; nunca radio 0.
  - **Cubre**: G2; FR-011, FR-015; SC-005, SC-013.

- [ ] T011 [US1] Estructura de pantalla: `src/App.tsx` y `src/features/map/components/Banner.tsx` con el banner «DATOS SINTÉTICOS (MOCK)» (visible si `mode` es `mock` o algún evento tiene `is_synthetic`), los mensajes de estado («Modo api: la conexión con la API todavía no está disponible», «Sin eventos en el intervalo», error de carga del mock) y un hueco para el mapa; muestra `metadata.count` y `total` tal cual, sin calcular. Tailwind.
  - **Prueba**: manual con los cuatro casos y `mode: "api"`: banner y mensajes correctos; sin «NaN» ni «undefined».
  - **Cubre**: G15; FR-005, FR-009; SC-007, SC-011.

## Bloque 4 — Mapa, ficha y leyenda (G2, G12 `magType`, G14)

- [ ] T012 [P] [US1] Fronteras y atribuciones: copiar `data/catalogo/paises.geojson` a `frontend/public/datos/paises.geojson` con un paso documentado (script `frontend/scripts/copy-countries.mjs` que copia y verifica el SHA-256 `6866c877…c977f`, y falla si no coincide); texto de atribución de Natural Earth en una constante compartida.
  - **Prueba**: `sha256sum` de ambos archivos coincide con `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`; el script falla con una copia alterada.
  - **Cubre**: G14; FR-012, FR-016; SC-009.

- [ ] T013 [P] [US2] Ficha del evento: `src/features/map/components/EventCard.tsx` (descripción del lugar, «Magnitud 5,4 (mww)», profundidad en km, `time` y `updated` en UTC, país o «Sin país asignado», etiqueta «Sintético», enlace a USGS solo si hay `url`; nulos → «ND» o los textos de `data-model.md`; negativos tal cual). Botón de cerrar de ≥ 44 × 44 px, alcanzable con teclado, cierre con Esc. Panel de 320 px desde `md`, hoja inferior ≤ 50 % con scroll interno por debajo.
  - **Prueba**: manual sobre los eventos de `base` (`mww`, `magType` nulo, magnitud nula, sin país, −0,06 / −0,01, `place` nulo): coinciden con US2; consola sin errores. La lógica de texto ya se prueba en `T002`.
  - **Cubre**: G2, G12 (`magType`), G17; FR-014, FR-019; SC-004, SC-005, SC-006.

- [ ] T014 [P] [US1] Leyenda: `src/features/map/components/Legend.tsx` con «Tamaño = magnitud» (3 círculos de ejemplo: M 2, 4, 6), «Color = profundidad (km)» (cinco clases con rango escrito y color), «ND: sin magnitud», «ND: sin profundidad». Tarjeta abajo a la izquierda desde `md`; por debajo, botón «Leyenda» de ≥ 44 × 44 px. Usa las constantes de `T010`.
  - **Prueba**: manual a 1280 y 375 px: contenido completo; el orden de las clases se conserva en la captura en escala de grises.
  - **Cubre**: G2, G17; FR-015, FR-017, FR-019.

- [ ] T015 [US1] **(depende de D1 = T007)** Componente de mapa aislado `src/features/map/MapView.tsx` con la librería decidida. Entrada: `events`, `selectedId`; salida: `onSelect` (contrato de `data-model.md`). Fondo sin clave, fronteras desde `/datos/paises.geojson`, un círculo por feature con `symbolFor` (T010), dibujo por magnitud descendente (los pequeños encima), clic o toque abre la selección, atribución del fondo y de Natural Earth fija en la esquina inferior derecha fuera de la leyenda. Si faltan las fronteras: se pintan los círculos y se avisa. Si la librería no admite algún detalle visual (contorno de ND), usar el equivalente más cercano y anotarlo en una línea.
  - **Prueba**: manual con `base`: círculos = nº de features; ND hueco visible; clases distinguibles. Con `truncated`: 5 000 círculos en ≤ 3 s y ficha abre al pulsar. Ningún archivo fuera de `features/map` importa la librería de mapa; solo se usa `MapView`.
  - **Cubre**: G2, G14; FR-011, FR-013, FR-016; SC-002, SC-010, SC-012.

- [ ] T016 [US1] Integrar en `App.tsx`: `useEvents` → `MapView` + `EventCard` + `Legend` + `Banner`; el evento seleccionado es estado local de `App` (no hay store de filtros). Caso `empty`: mapa con fronteras y el mensaje. Esc cierra la ficha.
  - **Prueba**: recorrido de `quickstart.md` §3 con los cuatro casos y consola sin errores.
  - **Cubre**: G2, G12 (`magType`), G15; FR-005, FR-014; SC-002, SC-004, SC-006.

## Bloque 5 — Responsive, evidencias y cierre (G17, §16)

- [ ] T017 [US3] Revisión responsive: ajustar clases de Tailwind para que no haya scroll horizontal a 375, 768 y 1280 px en los cuatro casos, con leyenda abierta y con ficha abierta; la ficha se desplaza dentro de sí misma; la atribución sigue visible.
  - **Prueba**: en consola `document.documentElement.scrollWidth <= window.innerWidth` devuelve `true` en las 12 combinaciones de ancho y caso con ficha y leyenda abiertas.
  - **Cubre**: G17, G11 (atribución y leyenda); FR-016, FR-018, FR-019; SC-003.

- [ ] T018 Capturas y comprobaciones visuales en `docs/evidencias/panel-base-mock/`: `base` a 1280 px, `base` a 375 px con ficha, `truncated` a 375 px, `empty`, mensaje de modo api, mensaje de `mode` inválido, ficha con `mww` y con `magType` nulo; nota con el resultado de la consola (cero errores) y de `scrollWidth`.
  - **Prueba**: los archivos existen y se leen las dos atribuciones sin pulsar nada en 375 y 1280 px.
  - **Cubre**: G2, G12 (`magType`), G17; SC-003, SC-004, SC-005, SC-006, SC-010, SC-011.

- [ ] T019 Salidas de verificación en `docs/evidencias/panel-base-mock/`: `npm ci`, `npm run build` y `npm test` desde un clon limpio (con códigos de salida), `npm run dev` con HTTP 200, `sha256sum` de `paises.geojson`, y comprobación de que `frontend/` no tiene Dockerfile, compose, filtros, tabla, gráficos ni replay.
  - **Prueba**: todos los códigos en 0 y SHA coincidente; `quickstart.md` §1, §2, §5 y §8 cumplidos.
  - **Cubre**: G0, G14, G15; SC-001, SC-008, SC-009, SC-013, SC-014.

- [ ] T020 `frontend/README.md`: cómo ejecutar (`npm ci`, `dev`, `build`, `preview`, `test`), `config.json` y `?scenario=`, aviso de mock sintético, **material reutilizado** (Natural Earth `paises.geojson` y su ruta, dominio público, 1:110 m; librería y fondo del mapa con su licencia, atribución) para G14 y M2, y los límites conocidos de `plan.md`. Una línea en el `README.md` de la raíz que enlace al del frontend.
  - **Prueba**: el README nombra el origen de `paises.geojson` y las dos atribuciones; los comandos copiados funcionan.
  - **Cubre**: G11 (parcial), G14, G15; FR-012, FR-016; SC-015.

- [ ] T021 Cierre documental (constitución §16): actualizar `CODEMAP.md` (filas de `frontend/` con las rutas reales de la estructura decidida; sustituir las filas previstas que citan `frontend/src/app/core/...` si ya no aplican) y marcar en `docs/planificacion/01-checklist-requisitos.md` G0, G2, G14, G15, G17 y G12 solo para `magType`. **No** marcar G11 como hecho (P3) y anotar su avance parcial. Anotar el cierre en `specs/008-panel-base-mock/bitacora.md`. Detenerse y esperar revisión: sin commit ni merge.
  - **Prueba**: cada ruta de `CODEMAP.md` existe; `SC-015` cumplido.
  - **Cubre**: G0, G2, G11 (parcial), G12, G14, G15, G17; FR-006; SC-015.

## Dependencias

```
T001 ─┬─ T002 ─┐
      ├─ T003 ─┼─ T004
      │        └─ T005 ─ T006 ─ T007 ──────────┐   (Bloque 2: PRONTO, en paralelo al 3)
      ├─ T008 ─ T009 ─ T011 ─┐
      ├─ T010 ───────────────┤
      └─ T012, T013, T014 ───┴─ T015 (necesita T007, T010, T012) ─ T016 ─ T017 ─ T018 ─ T019 ─ T020 ─ T021
```

- `T009` necesita `T003` (archivos del mock) y `T008`.
- `T013` necesita `T002`; `T014` necesita `T010`.
- El Bloque 3 y las tareas `T012`–`T014` no dependen de D1: avanzan mientras el alumno decide la librería.

## Paralelo

`T002`, `T003` tras `T001`; `T008`, `T010`, `T012`, `T013`, `T014` entre sí; el Bloque 2 completo en paralelo con el Bloque 3.

## Estrategia

MVP = Bloques 1–4 con el caso `base` (US1 y US2). Después `truncated`, responsive (US3) y configuración (US4, ya cubierta en el Bloque 3). El Bloque 2 va **primero** porque D1 es el único riesgo real de la feature.

## Preguntas para el alumno

Pendiente solo la elección final de **D1** (librería del mapa), que el alumno toma en `T007` con la tabla de `T006` delante. Bloquea solo `T007` y `T015`.

Resueltas (alumno, 2026-11-05): D2 Zustand (se instala en `009`); D3 opción C; Q1 candidatas `react-globe.gl` y MapLibre confirmadas; Q2 `?scenario=` desconocido cae a `base` con aviso en consola; Q3 capturas manuales; Q4 mock en `frontend/mock/` con `?url` (si falla `T003`, `public/mock/` y corregir 03 §7.5); Q5 TypeScript 6.0.3.
