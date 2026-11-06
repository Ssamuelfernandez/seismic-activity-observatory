# Implementation Plan: Panel base con mock y mapa

**Branch**: `008-panel-base-mock` | **Date**: 2026-11-05 (revisado el 2026-11-06 por el cambio de diseño HUD del alumno) | **Spec**: `specs/008-panel-base-mock/spec.md`
**Requisitos**: G0, G2, G11 (parcial), G12 (solo `magType`), G14, G15, G17.

Solo documentos de diseño (constitución §19): este plan, `research.md`, `data-model.md` y `quickstart.md`. No hay código, Dockerfile ni compose. Los contratos (`specs/001-contratos-y-modelo/contracts/api.md` y `docs/enunciado/CONTRATO-API.md`) se citan, no se copian ni se modifican.

## Resumen

Frontend nuevo en `frontend/` (React + TypeScript + Vite + Tailwind) que, en modo `mock`, pinta un globo HUD sobre fondo negro con los continentes como celdas hexagonales (sin Antártida) y un prisma hexagonal por evento (largo = magnitud, color = profundidad, ND en gris de altura mínima), un panel lateral de ficha con `magType` (cajón inferior en móvil) y leyenda, sobre cuatro archivos de mock sintético conformes al contrato. `config.json` se lee en tiempo de ejecución. Nada de filtros, tabla, gráficos, estado del sistema, replay, mapa 2D ni conexión real (fuera de alcance).

Es trabajo de clase de unas dos semanas: se evita todo lo que no pida la spec.

## Cambio de diseño del alumno (2026-11-06)

Dirección HUD oscura, esqueleto (cabecera, globo, columnas reservadas, panel lateral de ficha), globo con celdas y prismas hexagonales, ficha como panel lateral, botón «Ver en mapa 2D» siempre visible (el mapa 2D es la feature nueva `panel-mapa-2d`, G18) y rampa de profundidad cálida. Detalle y lista de lo invalidado en `spec.md` («Cambio de diseño del alumno») y en `diseno-visual.md`.

**Qué invalida en este plan**: el `MapView` genérico (pasa a `GlobeView`); la ficha como popup u hoja inferior; ND hueco; viridis; el orden de dibujo «mayor primero»; el límite «el fondo necesita Internet»; la fuente del fondo y su atribución (R8); y D1 como decisión abierta entre dos librerías (decidida por el alumno el 2026-11-06: `react-globe.gl`; `T007` aplica la instalación).

### Capas de `react-globe.gl` elegidas (comprobadas leyendo `node_modules` del prototipo, `react-globe.gl` 2.38.0 sobre `three-globe` 2.45.6; sin instalar nada)

| Elemento | Capa | Parámetros relevantes (de la documentación del paquete) | Riesgo |
|---|---|---|---|
| Continentes en celdas hexagonales | `hexPolygonsData` (polígonos «hexed», celdas H3) | `hexPolygonResolution` (0 a 15, por defecto 3), `hexPolygonMargin` (hueco entre celdas), `hexPolygonColor`, `hexPolygonAltitude`; `hexPolygonUseDots: false` | Resolución alta = más celdas y más tiempo de arranque; se mide en `T022` (empezar en 3 y probar 4) |
| Antártida oculta | Filtrar la entrada de la capa quitando `ADM0_A3 = ATA` | — | Ninguno; es filtrar una lista. El archivo copiado no se modifica |
| Sismos como prismas hexagonales | `pointsData` con `pointResolution = 6` (cilindro de 6 segmentos radiales = prisma hexagonal), `pointAltitude` (largo, fracción del radio), `pointRadius` (grados), `pointColor` | `pointResolution` es un número **global**, no un accesor; `pointsMerge` debe ser `false` para poder pulsar cada punto | Ver abajo |
| Fondo negro | `backgroundColor` negro, `globeImageUrl` sin textura, `showAtmosphere: false` | — | Sin textura, la esfera queda negra y los hexágonos son lo único visible: comprobar contraste en `T022` |
| Pulsado | `onPointClick` (solo con `pointsMerge: false`) y `getScreenCoords` para elegir el punto más cercano | Sin tolerancia de clic propia | `T006` midió 0 de 4 a 6 px |

**Cuál usaría:** `pointsData` con `pointResolution = 6` para los prismas y `hexPolygonsData` para las celdas. No se fija sin comprobarlo: el cilindro de 6 segmentos *debería* verse como prisma hexagonal con tapa hexagonal, pero la documentación solo dice «segmentos radiales», no «hexágono». Se deja como **prototipo corto de una tarea** (`T022`), antes de tocar el código real.

**Riesgos del prisma hexagonal (para el prototipo `T022`)**:

1. **Forma**: un cilindro de 6 segmentos puede verse con un vértice o una cara hacia delante y girar según la latitud; **Criterio decidido por el alumno (2026-11-06):** si el prisma de 6 caras se ve bien de cerca en `T022`, es bueno aunque a escala de globo no se distinga como hexágono. Plan B, solo si queda claramente mal: capa `customLayerData` con una malla propia (más trabajo y fuera de las capas de «puntos»).
2. **Rendimiento**: `T006` midió ≈ 37 fps con 5 000 puntos de 12 lados sin fusionar; con 6 lados hay menos triángulos, pero se suman las celdas hexagonales. Criterio de `T022`: ≥ 30 fps al mover; si no, bajar `hexPolygonResolution` o `hexPolygonCurvatureResolution`.
3. **Pulsado**: sin tolerancia propia (0 de 4 a 6 px en `T006`) y el prisma de 0,45° de radio mide ≈ 3 px de ancho a 375 px con el globo entero a la vista. Mitigación: ensanchar el prisma y elegir el evento más cercano al clic con `getScreenCoords` (P9). Solo elige qué ficha abrir, no calcula estadísticas.
4. **Color real**: la iluminación de la escena oscurece los lados del prisma; el color visible puede no cumplir el contraste calculado para el token. Se comprueba en una captura (`T022`).
5. **Materiales**: `pointsMerge: true` iría más rápido pero no admite clic por punto; no es opción.

## Decisiones del alumno (2026-11-05)

Decidido por el alumno, 2026-11-05. D2 y D3 están cerradas; D1 la decidió el alumno el 2026-11-06 (`react-globe.gl`); `T007` la aplica.

| Id | Decisión | Estado | Qué depende de ella | Cómo se aplica |
|---|---|---|---|---|
| **D1** | Librería del globo/mapa | **TOMADA — Decidido por el alumno, 2026-11-06 (P6): `react-globe.gl`** en esta feature y MapLibre en la feature nueva `panel-mapa-2d` (candidatas fijadas el 2026-11-05). La aplicación (solo `react-globe.gl`) es `T007`, que **no está ejecutada** y va después de `T022` porque borra el prototipo que `T022` usa y porque la versión que se fija debe ser la validada. | Solo `T015` (`GlobeView`) y la instalación de la librería (`T007`) | La tabla de `T006` se conserva como evidencia. Todo lo demás (config, datos, ficha, leyenda, escalas, tokens HUD) no depende de D1. Ficha y leyenda son componentes HTML que no usan la librería. |
| **D2** | Store de filtros | **Decidido por el alumno, 2026-11-05: Zustand.** Se instala en `009`, no aquí | Nada en esta feature | **No se instala.** Solo se reserva `src/store/` con un `README.md` de una línea (FR-006) que nombra Zustand. El estado de «evento seleccionado» es estado local de React en `App`, no un store de filtros. |
| **D3** | Estructura de `src/` | **Decidido por el alumno, 2026-11-05: opción C** (03 §7.5 + `features/<x>/{components,hooks,lib}`, tipos en `shared/`, una feature no importa de otra) | Rutas de archivos de las tareas | La estructura de la tabla de abajo es la definitiva. Se mantiene el alias `@/` → `src/`. |

Hasta `T007` **no se instala** ninguna librería de mapa en `frontend/`; las dos candidatas solo se instalan en `frontend/prototipo-mapa/` (Q1). `T022` (prototipo del prisma hexagonal) también se hace dentro de `frontend/prototipo-mapa/`. En `T007` se consulta `npm view react-globe.gl version` y se registra aquí su versión exacta (el prototipo usó 2.38.0), se instala solo esa librería en `frontend/` con lock y se borra el prototipo. **MapLibre no se instala en esta feature.**

### Otras respuestas del alumno (2026-11-05)

- **Q2**: un `?scenario=` desconocido cae a `base` con aviso en consola de desarrollo.
- **Q3**: capturas manuales (sin Playwright).
- **Q4**: se mantiene el plan para el mock (`frontend/mock/` con `?url`); `T003` comprueba la carga bajo demanda y, si falla, se pasa a `public/mock/` y se corrige 03 §7.5.
- **Q5**: TypeScript **6.0.3** (sustituye a 7.0.2).
- **P2**: no hay aviso de truncado ni banner de REPRODUCCIÓN en esta feature.
- **P3**: G11 no se marca hasta `panel-conexion-api`.
- **P5**: se confirma el selector `?scenario=`.

### Regla de versiones no instalables

Si alguna versión fijada de la tabla no se puede instalar en `T001` (no existe, peer incompatible o fallo de `npm ci`), se usa la **versión estable anterior** y se anota en `plan.md` (tabla de versiones) y en la salida de `T001`. No se sube a una versión no comprobada.

## Technical Context

**Lenguaje y herramientas (fijados, comprobados con `npm view` el 2026-11-05):**

| Pieza | Versión estable | Nota |
|---|---|---|
| Node | 24.18.0 | LTS en uso en el equipo; Vite 8 y Vitest 5 lo admiten (`^22.12 \|\| ^24 \|\| >=26`). Se declara en `frontend/.nvmrc` y en `engines` de `package.json` |
| React / React DOM | 19.3.1 | |
| TypeScript | 6.0.3 | Decidido por el alumno, 2026-11-05 (Q5). Comprobado con `npm view typescript@6.0.3 version`; ninguna de las demás piezas declara peer de `typescript`, así que no hay otros ajustes |
| Vite | 8.3.6 | Con `@vitejs/plugin-react` 6.2.1 (su peer pide `vite ^8`) |
| Tailwind CSS | 4.3.4 | Con `@tailwindcss/vite` 4.3.4 (sin `tailwind.config.js`; breakpoints por defecto) |
| TanStack Query | 5.106.1 | **Sí entra en esta feature** (Assumptions de la spec): carga del mock mediante hooks que `panel-conexion-api` reutiliza |
| Vitest | 5.1.0 | Tests unitarios ligeros, entorno `node` |
| `@types/react`, `@types/react-dom` | 19.3.0 | |
| `@types/node` | 24.19.2 | Serie 24 para coincidir con Node 24 (los tests leen los JSON con `fs`) |

Todas se fijan **exactas** (sin `^`) en `package.json` y con `package-lock.json` (constitución §11). `npm ci` es el comando de instalación. Regla: si una versión no se puede instalar en `T001`, se usa la estable anterior y se anota aquí.

**Fuera de alcance en esta feature:** Chart.js (llega en `010`), librería de store (Zustand, D2, se instala en `009`), librería del globo hasta aplicar D1 en `T007` (luego solo `react-globe.gl`), MapLibre y el mapa 2D (feature `panel-mapa-2d`), eslint/prettier (no pedidos por la spec), Playwright (las capturas se hacen a mano con las herramientas del navegador; ver `quickstart.md`), Docker/despliegue (§19, features `015`).

**Almacenamiento:** ninguno; archivos estáticos (`frontend/mock/*.json`, `public/datos/paises.geojson`).
**Pruebas:** Vitest para lógica pura (config, mock conforme al contrato, escala de radio/color/ND, formato) + verificación visual con capturas.
**Plataforma objetivo:** navegador moderno en PC (principal) y móvil de 375 px (G17).
**Rendimiento:** 5 000 prismas y las celdas de los continentes pintados en ≤ 3 s y ≥ 30 fps al mover (a confirmar con `T022`, SC-012).
**Restricciones:** sin secretos (§10), mock separado y etiquetado (§7), el frontend no calcula estadísticas (§17), sin lenguaje de predicción ni riesgo (§21).

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| §5 Nulos | ND en gris propio y barra de altura mínima fija; nunca 0. Ficha: «ND». Magnitud/profundidad negativas se muestran tal cual |
| §7 Sintético separado | Cuatro marcas (banner, ficha, `is_synthetic`, `mock-`/«Sintético:»). El modo `api` no cae al mock |
| §10 Secretos | `config.json` sin secretos; fondo negro sin textura, sin claves |
| §11 Versiones | Exactas + lock + `.nvmrc` + `engines` |
| §13 Idioma | Identificadores en inglés; comentarios y docs en español; textos de interfaz en español |
| §14 Una responsabilidad | Lógica pura (`lib/`) separada de lectura/dibujo |
| §15 Contratos únicos | Se cita `api.md`; el validador del mock lo comprueba, no lo redefine |
| §16 Cierre | Evidencias, README del frontend y `CODEMAP.md` (tareas `T018`–`T021`) |
| §17 Sin estadísticas | `count`/`total` salen de `metadata`; las celdas hexagonales y la elección del prisma más cercano al clic son presentación, no cálculo |
| §19 Una feature, plan sin código | Este plan solo tiene documentos |
| §21 Sin predicción | Textos descriptivos |

Sin violaciones. Se vuelve a comprobar tras el diseño: sin cambios.

## Estructura del proyecto (D3 opción C, decidida)

```
frontend/
  .nvmrc                       # 24.18.0
  package.json, package-lock.json, tsconfig*.json, vite.config.ts   # alias @/ -> src/
  README.md                    # cómo ejecutar, material reutilizado (M2), atribuciones
  public/
    config.json                # mode, apiBaseUrl, refreshSeconds, timeoutMs
    datos/paises.geojson       # copia byte a byte de data/catalogo/ (SHA-256 en SC-009)
  mock/                        # base.json, truncated.json, replay.json, empty.json (SINTÉTICO)
  scripts/generate-mock.mjs    # generador determinista del mock (semilla fija)
  scripts/copy-countries.mjs   # copia paises.geojson desde data/catalogo/ y verifica el SHA-256
  tests/                       # Vitest: config, mock, symbology, format
  src/
    main.tsx, App.tsx
    index.css                  # Tailwind + bloque @theme con los tokens HUD (diseno-visual.md)
    config/                    # lectura y validación de config.json
    api/                       # fuente de eventos (mock|api) y hook useEvents (TanStack Query)
    store/                     # RESERVADA para el store de filtros (Zustand, D2); solo README.md
    features/map/
      GlobeView.tsx            # contrato de aislamiento (entrada: events, selectedId; salida: onSelect)
      components/              # EventCard (panel lateral / cajón de ficha), Legend, Banner
      hooks/
      lib/                     # symbology.ts (altura, clase, color, ND): lógica pura
    shared/
      layout/AppShell.tsx      # esqueleto: cabecera, globo, columnas reservadas, hueco de ficha
      types/contract.ts        # tipos de api.md §3
      lib/format.ts            # ND, decimales con coma, fecha UTC
```

`CODEMAP.md` se escribe al final (`T021`) con la estructura ya decidida.

## Recorrido de los datos

```
API real (feature 007, GET /api/eventos)         [llega después: panel-conexion-api]
        │
        ▼
Capa de datos  src/api/  ── fuente `mock` (EXISTE en esta feature) ── fuente `api` (mensaje «no disponible»)
        │   elige por config.json (mode) y, solo en mock, por ?scenario=
        ▼
Hook useEvents (TanStack Query)                  [existe; el mismo hook sirve a la API real]
        │
        ▼
Store de filtros  src/store/                     [llega después: 009, Zustand (D2); hoy solo carpeta]
        │
        ▼
Componentes: AppShell, GlobeView, EventCard (panel lateral), Legend, Banner  [existen aquí]; tabla, gráficos, estado [llegan en 009–011]; mapa 2D [feature panel-mapa-2d, con los mismos eventos ya cargados]
```

- Existe ya: `config/`, fuente mock, `useEvents`, mapa, ficha, leyenda, banner.
- Llega después: filtros y store (`009`), gráficos (`010`), estado del sistema (`011`), conexión real y refresco/timeout (`012`), replay (`013`).
- **El frontend no calcula estadísticas**: dibuja lo que trae el JSON y enseña `metadata.count`/`total` tal cual (§17).
- **El mock va etiquetado como sintético** en banner, ficha, `is_synthetic: true` y prefijo `mock-` (§7).

## Diseño por pieza

**Configuración (FR-003, FR-004, US4).** `public/config.json` se pide con `fetch` al arrancar (no se compila en el JS). Un validador puro comprueba `mode` ∈ {`mock`,`api`}, `apiBaseUrl` texto, `refreshSeconds` y `timeoutMs` enteros positivos, y devuelve el nombre del campo que falla. Si falta o es inválido, se muestra el mensaje y no se monta el mapa. `refreshSeconds` y `timeoutMs` se leen y validan pero no se aplican (P3).

**Mock (FR-008 a FR-010) y P4.** *Decidido por el alumno, 2026-11-05 (Q4):* los JSON viven en `frontend/mock/` como dice 03, y el código los pide con `import.meta.glob` en modo `?url`. Vite emite cada JSON como archivo aparte en `dist/assets/` y el JS solo lleva su URL, de modo que los 5 000 eventos no engordan el bundle y 03 §7.5 no cambia. Se desactiva el inline de assets pequeños (`build.assetsInlineLimit: 0`) para que los cuatro sean ficheros. `T003` valida la idea en cuanto existe; **plan B** si no funciona: mover a `frontend/public/mock/` y corregir la línea de 03 §7.5 (aviso al alumno, es un cambio de documento de planificación). Los JSON los genera `scripts/generate-mock.mjs` con semilla fija (reproducible) y se versionan.

**Capa de datos (FR-005, FR-007).** Una función `loadEvents(config, scenario)` decide: `mock` → carga el archivo del caso; `api` → devuelve el estado «api no disponible» sin pedir nada. `useEvents` la envuelve con TanStack Query. Estados de pantalla: `loading`, `ready`, `empty` (features vacías), `error`, `api-unavailable` (ver `data-model.md`).

**Tokens y esqueleto HUD (FR-020).** Los tokens de `diseno-visual.md` se declaran una vez en el bloque `@theme` de `src/index.css`; `AppShell` coloca cabecera, globo, dos columnas reservadas (≥ 1024 px, marco vacío con «RESERVADO») y el hueco de la ficha. Es lo primero del Bloque 3 (`T023`) para que todo lo demás herede los tokens.

**Símbolos (V1–V4, lógica pura).** `heightFor(mag)`: máx(0,010; 0,0125 × clamp(mag, 0, 8)); nula → 0,010. `depthClassFor(depth)`: cortes 10/35/70/300 (negativas en la clase 1; nula → ND). `colorFor`: los colores de V2 son constantes; ND gris. Estas funciones son las que se prueban, junto con el contraste de la rampa sobre negro.

**Globo (FR-011 a FR-016, FR-013).** Contrato de aislamiento: `GlobeView({ events, selectedId, onSelect })`, sin conocer config, mock, ficha ni leyenda. Dentro: fondo negro, celdas hexagonales de los continentes desde `paises.geojson` sin la Antártida, un prisma hexagonal por feature (capa de puntos de 6 lados; ver tabla de capas), selección del prisma más cercano al clic si `T022` lo exige, atribución fija. Depende de D1 (`T007`) y del resultado de `T022` (`T015`).

**Ficha, leyenda, banner (FR-014, FR-015, FR-019, FR-021, V5, V6).** Componentes HTML/Tailwind independientes de la librería. Ficha: panel lateral de 20 rem anclado al borde derecho del globo desde `md`, cajón inferior (≤ 50 % de altura, scroll interno) por debajo; cierra con botón (≥ 44 × 44 px) y Esc; incluye el botón «Ver en mapa 2D» (`aria-disabled`, aviso «próximamente»). Leyenda: tarjeta desde `md`, botón «Leyenda» en la cabecera por debajo.

**Responsive (FR-018, G17).** Breakpoints de Tailwind por defecto; columnas reservadas solo desde `lg`. Comprobación con `document.documentElement.scrollWidth <= window.innerWidth` en 375, 768 y 1280 px en los cuatro casos.

## Límites conocidos (una línea cada uno)

- Con 5 000 prismas el globo rinde menos que un mapa 2D (≈ 37 fps medidos en `T006`) y el prisma pequeño es difícil de pulsar; se revalida en `T022`.
- El fondo es negro sin textura: no hay atribución de fondo y no se necesita Internet para el fondo.
- La luz de la escena puede oscurecer el color de los prismas respecto al token; se comprueba en captura.
- El caso `truncated` no avisa del truncado (llega con `009`) y el `replay` no muestra aviso (llega con `013`).
- Las fronteras 1:110 m son simplificadas; no sirven para delimitar jurisdicción.
- `refreshSeconds` y `timeoutMs` se leen pero no se aplican hasta `012`.
- El mock no es la API: solo cubre la forma del contrato, no su comportamiento (filtros, cursor).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El prisma hexagonal no se lee, no se pulsa o no llega a 30 fps con 5 000 eventos | `T022` lo mide antes de `T007` y `T015`; planes B en la tabla de riesgos del prisma (menos celdas, selección del más cercano al clic y, solo si la forma queda claramente mal de cerca, malla propia). Si nada cumple, se vuelve a preguntar al alumno (el 2D es otra feature) |
| Alguna versión fijada no se puede instalar en `T001` | Usar la estable anterior y anotarla (regla de versiones) |
| `import.meta.glob ?url` no emite JSON como archivo | Plan B (Q4): `public/mock/` y corregir 03 §7.5 (aviso al alumno) |
| Teselas de fondo con política de uso restrictiva | Ya no aplica desde el 2026-11-06: fondo negro sin teselas ni textura |
