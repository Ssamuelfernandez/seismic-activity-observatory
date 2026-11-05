# Implementation Plan: Panel base con mock y mapa

**Branch**: `008-panel-base-mock` | **Date**: 2026-11-05 | **Spec**: `specs/008-panel-base-mock/spec.md`
**Requisitos**: G0, G2, G11 (parcial), G12 (solo `magType`), G14, G15, G17.

Solo documentos de diseño (constitución §19): este plan, `research.md`, `data-model.md` y `quickstart.md`. No hay código, Dockerfile ni compose. Los contratos (`specs/001-contratos-y-modelo/contracts/api.md` y `docs/enunciado/CONTRATO-API.md`) se citan, no se copian ni se modifican.

## Resumen

Frontend nuevo en `frontend/` (React + TypeScript + Vite + Tailwind) que, en modo `mock`, pinta un mapa con fronteras, círculos (tamaño = magnitud, color = profundidad, ND visible), ficha con `magType` y leyenda, sobre cuatro archivos de mock sintético conformes al contrato. `config.json` se lee en tiempo de ejecución. Nada de filtros, tabla, gráficos, estado del sistema, replay ni conexión real (fuera de alcance).

Es trabajo de clase de unas dos semanas: se evita todo lo que no pida la spec.

## Decisiones del alumno (2026-11-05)

Decidido por el alumno, 2026-11-05. D2 y D3 están cerradas; D1 tiene las candidatas decididas y la elección final queda para `T007`.

| Id | Decisión | Estado | Qué depende de ella | Cómo se aplica |
|---|---|---|---|---|
| **D1** | Librería del mapa | **Candidatas decididas por el alumno (2026-11-05): `react-globe.gl` y MapLibre GL JS.** La elección final la toma el alumno en `T007`, con la tabla de `T006` delante. **No está cerrada.** | Solo `T015` (`MapView`) y la instalación de la librería (`T007`) | El prototipo va **pronto** (Bloque 2, `T005`–`T007`) y el mapa final depende de su resultado. Todo lo demás (config, datos, ficha, leyenda, escalas) no depende de D1. Ficha y leyenda son componentes HTML que no usan la librería. G17 pesa a favor del 2D (criterio de la spec). |
| **D2** | Store de filtros | **Decidido por el alumno, 2026-11-05: Zustand.** Se instala en `009`, no aquí | Nada en esta feature | **No se instala.** Solo se reserva `src/store/` con un `README.md` de una línea (FR-006) que nombra Zustand. El estado de «evento seleccionado» es estado local de React en `App`, no un store de filtros. |
| **D3** | Estructura de `src/` | **Decidido por el alumno, 2026-11-05: opción C** (03 §7.5 + `features/<x>/{components,hooks,lib}`, tipos en `shared/`, una feature no importa de otra) | Rutas de archivos de las tareas | La estructura de la tabla de abajo es la definitiva. Se mantiene el alias `@/` → `src/`. |

Hasta `T007` **no se elige ni se instala** ninguna librería de mapa en `frontend/`; las dos candidatas solo se instalan en `frontend/prototipo-mapa/` (confirmado por el alumno, Q1). Tras `T007` se consulta `npm view <paquete> version` y se registra aquí la elegida y su versión exacta.

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

**Fuera de alcance en esta feature:** Chart.js (llega en `010`), librería de store (Zustand, D2, se instala en `009`), librería de mapa hasta decidir D1, eslint/prettier (no pedidos por la spec), Playwright (las capturas se hacen a mano con las herramientas del navegador; ver `quickstart.md`), Docker/despliegue (§19, features `015`).

**Almacenamiento:** ninguno; archivos estáticos (`frontend/mock/*.json`, `public/datos/paises.geojson`).
**Pruebas:** Vitest para lógica pura (config, mock conforme al contrato, escala de radio/color/ND, formato) + verificación visual con capturas.
**Plataforma objetivo:** navegador moderno en PC (principal) y móvil de 375 px (G17).
**Rendimiento:** 5 000 círculos pintados en ≤ 3 s (referencia a confirmar con el prototipo, SC-012).
**Restricciones:** sin secretos (§10), mock separado y etiquetado (§7), el frontend no calcula estadísticas (§17), sin lenguaje de predicción ni riesgo (§21).

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| §5 Nulos | ND por forma/color propios; nunca 0. Ficha: «ND». Magnitud/profundidad negativas se muestran tal cual |
| §7 Sintético separado | Cuatro marcas (banner, ficha, `is_synthetic`, `mock-`/«Sintético:»). El modo `api` no cae al mock |
| §10 Secretos | `config.json` sin secretos; fondo del mapa sin clave |
| §11 Versiones | Exactas + lock + `.nvmrc` + `engines` |
| §13 Idioma | Identificadores en inglés; comentarios y docs en español; textos de interfaz en español |
| §14 Una responsabilidad | Lógica pura (`lib/`) separada de lectura/dibujo |
| §15 Contratos únicos | Se cita `api.md`; el validador del mock lo comprueba, no lo redefine |
| §16 Cierre | Evidencias, README del frontend y `CODEMAP.md` (tareas `T018`–`T021`) |
| §17 Sin estadísticas | `count`/`total` salen de `metadata`; el orden de dibujo no es un cálculo |
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
    config/                    # lectura y validación de config.json
    api/                       # fuente de eventos (mock|api) y hook useEvents (TanStack Query)
    store/                     # RESERVADA para el store de filtros (Zustand, D2); solo README.md
    features/map/
      MapView.tsx              # contrato de aislamiento (entrada: events; salida: onSelect)
      components/              # EventCard (ficha), Legend, Banner
      hooks/
      lib/                     # symbology.ts (radio, clase, color, ND): lógica pura
    shared/
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
Componentes: MapView, EventCard, Legend, Banner  [existen aquí]; tabla, gráficos, estado [llegan en 009–011]
```

- Existe ya: `config/`, fuente mock, `useEvents`, mapa, ficha, leyenda, banner.
- Llega después: filtros y store (`009`), gráficos (`010`), estado del sistema (`011`), conexión real y refresco/timeout (`012`), replay (`013`).
- **El frontend no calcula estadísticas**: dibuja lo que trae el JSON y enseña `metadata.count`/`total` tal cual (§17).
- **El mock va etiquetado como sintético** en banner, ficha, `is_synthetic: true` y prefijo `mock-` (§7).

## Diseño por pieza

**Configuración (FR-003, FR-004, US4).** `public/config.json` se pide con `fetch` al arrancar (no se compila en el JS). Un validador puro comprueba `mode` ∈ {`mock`,`api`}, `apiBaseUrl` texto, `refreshSeconds` y `timeoutMs` enteros positivos, y devuelve el nombre del campo que falla. Si falta o es inválido, se muestra el mensaje y no se monta el mapa. `refreshSeconds` y `timeoutMs` se leen y validan pero no se aplican (P3).

**Mock (FR-008 a FR-010) y P4.** *Decidido por el alumno, 2026-11-05 (Q4):* los JSON viven en `frontend/mock/` como dice 03, y el código los pide con `import.meta.glob` en modo `?url`. Vite emite cada JSON como archivo aparte en `dist/assets/` y el JS solo lleva su URL, de modo que los 5 000 eventos no engordan el bundle y 03 §7.5 no cambia. Se desactiva el inline de assets pequeños (`build.assetsInlineLimit: 0`) para que los cuatro sean ficheros. `T003` valida la idea en cuanto existe; **plan B** si no funciona: mover a `frontend/public/mock/` y corregir la línea de 03 §7.5 (aviso al alumno, es un cambio de documento de planificación). Los JSON los genera `scripts/generate-mock.mjs` con semilla fija (reproducible) y se versionan.

**Capa de datos (FR-005, FR-007).** Una función `loadEvents(config, scenario)` decide: `mock` → carga el archivo del caso; `api` → devuelve el estado «api no disponible» sin pedir nada. `useEvents` la envuelve con TanStack Query. Estados de pantalla: `loading`, `ready`, `empty` (features vacías), `error`, `api-unavailable` (ver `data-model.md`).

**Símbolos (V1–V4, lógica pura).** `radiusFor(mag)`: 3 + 1,5 × clamp(mag, 0, 8); nula → radio fijo de ND. `depthClass(depth)`: cortes 10/35/70/300 (negativas en la clase 1; nula → ND). Los colores de V2 son constantes. Estas funciones son las que se prueban.

**Mapa (FR-011 a FR-016, FR-013).** Contrato de aislamiento: `MapView({ events, selectedId, onSelect })`, sin conocer config, mock, ficha ni leyenda. Dentro: fondo, fronteras desde `paises.geojson`, un círculo por feature con orden de dibujo por magnitud descendente (los grandes debajo), símbolos V3/V4, atribución fija. La implementación depende de D1 (`T015`).

**Ficha, leyenda, banner (FR-014, FR-015, FR-019, V5, V6).** Componentes HTML/Tailwind independientes de la librería de mapa. Ficha: panel de 320 px a partir de `md`, hoja inferior (≤ 50 % de altura, scroll interno) por debajo; cierra con botón (≥ 44 × 44 px) y Esc. Leyenda: tarjeta desde `md`, botón «Leyenda» por debajo.

**Responsive (FR-018, G17).** Breakpoints de Tailwind por defecto. Comprobación con `document.documentElement.scrollWidth <= window.innerWidth` en 375, 768 y 1280 px en los cuatro casos.

## Límites conocidos (una línea cada uno)

- El fondo del mapa necesita Internet.
- El caso `truncated` no avisa del truncado (llega con `009`) y el `replay` no muestra aviso (llega con `013`).
- Las fronteras 1:110 m son simplificadas; no sirven para delimitar jurisdicción.
- `refreshSeconds` y `timeoutMs` se leen pero no se aplican hasta `012`.
- El mock no es la API: solo cubre la forma del contrato, no su comportamiento (filtros, cursor).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Ningún candidato de mapa cumple en 375 px | Prototipo pronto; si ambos fallan, probar Leaflet con canvas (opción C de la spec, solo si fallan las dos candidatas) antes de bloquear el resto |
| Alguna versión fijada no se puede instalar en `T001` | Usar la estable anterior y anotarla (regla de versiones) |
| `import.meta.glob ?url` no emite JSON como archivo | Plan B (Q4): `public/mock/` y corregir 03 §7.5 (aviso al alumno) |
| Teselas de fondo con política de uso restrictiva | Decidir la fuente en el prototipo y en `T007`; sin claves; atribución visible |
