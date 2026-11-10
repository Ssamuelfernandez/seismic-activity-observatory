# Feature Specification: Panel completo — adoptar el front externo con correcciones

**Feature Branch**: `008-panel-base-mock` (el nombre se conserva; ya no es solo «base con mock»)

**Created**: 2026-11-05 · **Enmendada**: 2026-11-10 (decisión del alumno; sustituye al alcance anterior, incluido **SC-014**)

**Status**: Enmienda redactada, pendiente de la revisión del alumno. T001–T007 y T022 (hechas con el diseño anterior) se conservan como histórico; las demás tareas se reescriben en `tasks.md`.

**Input**: El alumno aporta un front ya desarrollado (`globo-lab`, inventariado en `inventario-front-externo.md`) y decide conservarlo **tal como se ve**, con unas correcciones obligatorias. `008` pasa a «adoptar el front externo con correcciones» y absorbe las features de filtros y tabla (`009`), gráficos y comparación (`010`), estado y fallos (`011`) y conexión con la API (`012`). La vista 2D (`panel-mapa-2d`, G18) queda aplazada. Replay (J1–J8, G10, F12) sigue siendo su feature (`013`).

> Contratos de referencia, sin modificar: `specs/001-contratos-y-modelo/contracts/api.md` (sobre todo §3 y §5) y `docs/enunciado/CONTRATO-API.md` (solo lectura). Esta spec no repite sus tablas: las cita.

## Enmienda del 2026-11-10 (qué cambia)

| Antes (spec del 2026-11-05/06) | Ahora |
|---|---|
| Solo globo, ficha, leyenda, config y mock (SC-014: sin filtros, tabla, gráficos, estado ni replay) | **SC-014 sustituido.** Entra todo el panel: filtros, tabla, estadísticas y comparación, estado del feed y fallos, banner REPRODUCCIÓN, conexión con la API real y vista de replay |
| Globo HUD con celdas hexagonales, prisma de 6 caras, fondo negro sin atmósfera, columnas «RESERVADO», botón «Ver en mapa 2D» | **Apariencia del front externo, sin cambios** (`diseno-visual.md` reescrito): países extruidos, prisma de 7 lados, atmósfera, grano, anillos, layout actual y móvil. Sin celdas hexagonales, sin columnas «RESERVADO», sin botón «Ver en mapa 2D» |
| Mapa 2D (`panel-mapa-2d`) como feature siguiente | **Aplazada** (G18) |
| Zustand pospuesto a `009` | Zustand entra aquí (store único de filtros, constitución §17) |
| Profundidad en 5 clases y rampa del diseño HUD (`#FFF1A6` … `#7C4DCB`) | Cinco clases con los cortes de la API y **el estilo de color del front** (ver «Decisiones por defecto») |
| Mock = 4 JSON estáticos servidos también en el build | Mock con cinco escenarios en `frontend/mock/`, carga bajo demanda, **fuera del build de producción** y sin selector en la interfaz |

Las decisiones visuales V1–V7 del diseño HUD anterior quedan **retiradas**; vale lo descrito en `diseno-visual.md`. Las pruebas de prototipo (T005, T006, T022) se conservan como evidencia y no se reabren.

## Cobertura de requisitos

| ID | Qué cubre `008` | Notas |
|---|---|---|
| G0 | Proyecto, versiones fijadas, `npm ci`/`dev`/`build` | Vite en 4200 con `strictPort` |
| G1 | El panel consulta **nuestra API**, nunca USGS | Con el stack levantado (bloque 4) |
| G2 | Globo, fronteras, prismas (largo ∝ magnitud, color por profundidad), leyenda, ND, ficha | Con el diseño del front externo |
| G3, G4 | Recuentos por hora UTC y por país (con «Sin país asignado»); distribuciones de magnitud y profundidad con registros sin valor | Cifras de `/api/estadisticas` |
| G5, G5b | Últimas 24 h frente a la media diaria de 2025, con aviso de periodo incompleto | En el cajón inferior de estadísticas; **G5b reformulado** en `01-checklist-requisitos.md` como decisión propia (P2, 2026-11-10) |
| G6 | Filtros de periodo, magnitud y país en un único store, coherentes entre globo, tabla y estadísticas | |
| G7, G9 | Estado del sistema; aviso si falla la API, última lectura conservada y marcada como antigua | |
| G8 | Tabla consultable de eventos | |
| G11 | Refresco con `refreshSeconds` sin solapar, `timeoutMs`, atribución y leyenda visibles | |
| G12 | `magType` (ficha), `country_id`/`country_name` (filtro, tabla, ficha), `truncated` (aviso), `last_ingestion` (estado) | `metadata.mode` se cierra en `013-replay` |
| G14, G15, G17 | Fronteras de `paises.geojson`; mock del contrato con selector en `config.json`; responsive a 375 px | |
| G10, J7 | **Parcial**: banner REPRODUCCIÓN y petición del intervalo de 2025 viajan aquí; el cierre y la prueba con datos reproducidos son de `013-replay` | |
| G13 | **No es de `008`**: la config en tiempo de ejecución lo hace posible; el despliegue y el CORS real son de `015-despliegue-tunel` | |
| G16 | **No cubierta, decisión propia** (foco de teclado y no depender solo del color) | La tabla sí existe (G8) |
| G18 | **Aplazada** (`panel-mapa-2d`) | |

## Clarifications

### Session 2026-11-10 (decisiones del alumno)

- Q: ¿Qué hace la configuración? → A: `public/config.json` con `mode` (`mock`\|`api`), `apiBaseUrl`, `refreshSeconds` y `timeoutMs`, leído en **tiempo de ejecución** y validado (campo que falla nombrado, sin valores inventados). Sustituye al `src/config.json` compilado del front externo. Cambiarlo no exige recompilar.
- Q: ¿Cómo es el mock? → A: En `frontend/mock/`, con carga bajo demanda y escenarios `base`, `truncated`, `replay`, `empty` y `realistic`; entre todos incluyen magnitud nula y negativa, `place` nulo, sin país, truncado y vacío. Etiquetado como sintético. **Fuera del build de producción** y **no activable desde la interfaz**: solo `config.json` (`mode: "mock"`, solo en desarrollo) y `?scenario=` lo seleccionan; en modo `api` no existe forma de ver datos sintéticos.
- Q: ¿Cómo se colorea la profundidad? → A: Cinco clases con los cortes de la API (`<10`, `10–35`, `35–70`, `70–300`, `≥300`, `api.md` §5.1), conservando el estilo de color actual del front.
- Q: ¿Y la atribución? → A: Visible y legible (no 9 px dentro de un desplegable): USGS, Natural Earth (`paises.geojson`), `react-globe.gl` y `three`, y cualquier textura que se use (hoy ninguna).
- Q: ¿Qué se hace con `h3-js` y las fechas de Madrid? → A: Se quita `h3-js` (no se declara ni se importa) y el código muerto de `formatMadrid*`. `three` se declara porque se importa.
- Q: ¿Qué se hace con los recuentos y cálculos del cliente? → A: Auditoría completa (`plan.md`, «Auditoría de cálculos en el cliente»). Los totales salen de la API (`metadata.count`/`total`, `stats.total`); lo que cuenta el cliente se rotula «mostrados»; formatear un timestamp de la API es válido.
- Q: ¿Y la magnitud nula? → A: Se queda nula (nada de `mag ?? 0`): sin anillo ni etiqueta, barra ND de altura mínima y gris.
- Q: ¿Cómo se comporta replay? → A: Con `mode=replay` el panel pide el intervalo de 2025 (los eventos conservan su fecha original) y una respuesta vacía es un estado vacío, no un error.
- Q: ¿Accesibilidad (G16)? → A: Fuera de alcance, «no cubierta, decisión propia».
- Q: ¿Desarrollo? → A: Vite en el puerto 4200 con `strictPort` y proxy `/api` a la API. El CORS real queda para `despliegue-tunel`.

### Respuestas del alumno a P1–P6 (2026-11-10)

- **P1 — Estructura**: se conserva la del front externo (D3). Documentada en `CODEMAP.md` y en 03 §7.5.
- **P2 — G5b**: la comparación histórica se queda en el cajón inferior; G5b reformulado como decisión propia (no prioritario; sin consultar el enunciado).
- **P3 — Retraso de ingesta**: lo calcula el panel a partir del timestamp de la última ingesta que devuelve la API y se rotula como tal («hace X min»). Los datos siguen viniendo de la API; no hay cambio de contrato.
- **P4 — Gráficos**: sin Chart.js.
- **P5 — Capas apagadas del globo**: se borran las que están apagadas y no se ven (arcos, densidad por celdas, mapa de calor, marcadores); no debe cambiar nada visible (FR-031).
- **P6 — Valores por defecto**: aceptados salvo choque con la constitución o las normas del proyecto. Comprobado: **sin choques** (`mode: "api"` por defecto cuadra con G1; `refreshSeconds` 60 y `timeoutMs` 15000 son los de G11; la config en tiempo de ejecución es compatible con G13, porque `public/config.json` sigue pudiéndose editar antes de compilar; sin secretos, §10).

## User Scenarios & Testing *(mandatory)*

El «usuario» es quien evalúa el panel en el navegador (PC o móvil) y el propio alumno. Se prueba con el mock en desarrollo y con la API real y el stack levantado.

### User Story 1 - Ver el globo con los eventos (Priority: P1)

Al abrir el panel se ve el globo con los países, un prisma por evento (largo ∝ magnitud, color por clase de profundidad), la leyenda, los eventos recientes, el estado del feed y la atribución.

**Independent Test**: abrir `/` con el mock (`base`) y con la API real; comprobar prismas, leyenda de cinco clases y atribución.

1. **Given** el escenario `base`, **When** se abre el panel, **Then** hay un prisma por cada evento, la leyenda lista cinco clases con su rango, el banner de datos sintéticos y la atribución visibles.
2. **Given** dos eventos de profundidad 5 km y 150 km, **When** se comparan, **Then** tienen colores de clases distintas; los cortes 10, 35, 70 y 300 caen en la clase superior (límite inferior inclusivo).
3. **Given** un evento de magnitud nula, **When** se dibuja, **Then** es una barra gris de altura mínima, sin anillo ni etiqueta, y su ficha dice «ND».

### User Story 2 - Consultar la ficha de un evento (Priority: P1)

Pulsar un prisma (o una fila de la lista o de la tabla) abre la ficha con descripción, magnitud con `magType`, profundidad, `time` y `updated` en UTC, país, estado, significancia y enlace a USGS si hay `url`.

1. **Given** `mag: 5.4` y `magType: "mww"`, **Then** la ficha dice «Magnitud 5,4 (mww)».
2. **Given** `magType`, `place`, país o profundidad nulos, **Then** la ficha muestra «ND», «Sin descripción», «Sin país asignado» o «ND», nunca 0 ni `undefined`.
3. **Given** magnitud −0,06 y profundidad −0,01, **Then** se muestran tal cual.

### User Story 3 - Filtrar y consultar la tabla (Priority: P1)

Los filtros de periodo, magnitud mínima y país (y el tipo de datos live/replay) están siempre visibles en la barra superior; globo, tabla y estadísticas responden al **mismo** estado.

1. **Given** la API real, **When** se cambia un filtro, **Then** globo, lista, tabla y estadísticas cambian a la vez y `stats.total` coincide con `metadata.total` de los eventos con los mismos filtros.
2. **Given** una respuesta con `metadata.truncated: true`, **Then** hay un aviso visible con «mostrados» y el total de la API.
3. **Given** la tabla abierta, **Then** muestra todos los campos del contrato, ordenable por columna, con los nulos al final.

### User Story 4 - Estadísticas y comparación con 2025 (Priority: P1)

El cajón inferior muestra el total, el recuento por hora UTC, por país (con «Sin país asignado»), las distribuciones de magnitud y profundidad con «sin valor», y la comparación de las últimas 24 h con la media diaria de 2025, con aviso de periodo reciente incompleto.

1. **Given** filtros activos, **Then** las cifras son las de `/api/estadisticas` con esos filtros; el cliente solo las pinta.
2. **Given** `variation_pct: null` (media 0), **Then** se muestra «ND».
3. **Given** `mode=replay`, **Then** la comparación dice «No disponible en modo reproducción».

### User Story 5 - Estado del sistema y fallos de la API (Priority: P1)

El estado distingue la última consulta correcta del panel, la respuesta generada, la última ingesta de USGS y el periodo consultado, y avisa de datos desactualizados, backend sin respuesta o error.

1. **Given** una API que deja de responder, **When** falla un refresco, **Then** aparece un aviso, se conserva la última lectura **marcada como antigua** con su hora, y nunca se presenta como «0 eventos».
2. **Given** que la API vuelve, **Then** el panel se recupera en el siguiente refresco sin recargar.

### User Story 6 - Vista de replay (Priority: P2)

Con `mode=replay` el panel muestra el banner «REPRODUCCIÓN» y pide el intervalo de 2025.

1. **Given** replay con eventos, **Then** se ven (conservan su fecha original) y el banner es visible.
2. **Given** replay vacío (aún no se ha reproducido nada), **Then** aparece «sin eventos reproducidos» como estado vacío, sin error y sin cifras inventadas.

### User Story 7 - Configurar y usar el mock (Priority: P1)

El alumno edita `public/config.json` (sin recompilar) para pasar de `mock` a `api`, y elige el escenario con `?scenario=`. En producción el mock no existe.

1. **Given** `mode: "api"` y la API levantada, **Then** se ven datos reales y no hay forma de pasar a datos sintéticos desde la interfaz.
2. **Given** `mode: "otro"` o un campo ausente, **Then** un mensaje nombra el campo y no arranca el panel.
3. **Given** un build de producción con `mode: "mock"`, **Then** un mensaje dice que el mock no está disponible en ese build.

### User Story 8 - Usar el panel desde el móvil (Priority: P2)

A 375 px se ve el diseño móvil del front (cabecera con filtros y estado, globo a pantalla, hojas inferiores de eventos, estadísticas y leyenda, ficha en hoja) sin scroll horizontal.

### Edge Cases

- Magnitud nula: barra ND; magnitud o profundidad negativas: válidas (altura mínima; la ficha da el valor). Profundidad nula: prisma gris con altura por su magnitud.
- Un fallo de `/api/estadisticas` o `/api/salud` no tumba el globo: cada bloque muestra su propio estado.
- `country_id` mal escrito en el filtro: no se envía (evita un 400).
- Rango de fechas propio inválido (`desde > hasta` o incompleto): se usan las últimas 24 h.
- Si falla la carga de `paises.geojson`: se pintan los prismas y se avisa de que faltan los países.
- Eventos en la Antártida: se dibujan; solo se oculta la capa del continente.
- Los eventos de `mode=replay` mantienen su fecha original; el panel nunca las cambia.
- Límites conocidos (una línea cada uno): ver sección final.

## Requirements *(mandatory)*

### Functional Requirements

**Proyecto, configuración y desarrollo (G0, G15)**

- **FR-001**: Proyecto web en `frontend/` con React, TypeScript, Vite y Tailwind, versiones exactas y `package-lock.json`, Node 24.18.0 declarado (§11). `npm ci`, `npm run dev` y `npm run build` funcionan desde un clon limpio sin secretos (§10).
- **FR-002**: `npm run dev` sirve en el puerto **4200** con `strictPort` (si está ocupado, falla en vez de cambiar de puerto) y reenvía `/api` a la API (destino por defecto `http://127.0.0.1:8000`, configurable por variable de entorno).
- **FR-003**: `public/config.json` con `mode`, `apiBaseUrl`, `refreshSeconds` y `timeoutMs`, leído en tiempo de ejecución; sin secretos; no existe un `config.json` compilado dentro del JS.
- **FR-004**: Un validador puro comprueba `mode` ∈ {`mock`,`api`}, `apiBaseUrl` texto (en modo `api` no vacío y que empiece por `/`, `http://` o `https://`), `refreshSeconds` y `timeoutMs` enteros positivos. Un archivo ausente o inválido muestra un mensaje que nombra el campo y no monta el panel.

**Mock (G15)**

- **FR-005**: El mock vive en `frontend/mock/`, se carga bajo demanda solo con `mode: "mock"` y no entra en el build de producción (ni sus datos ni su código). Con `mode: "mock"` en un build de producción el panel muestra un mensaje que lo dice.
- **FR-006**: Cinco escenarios, cada uno conforme a `api.md` §3 (los ocho campos de `metadata`, los once de `properties`, fechas en ms, `Point` válido): `base` (~30 eventos con los casos de borde), `truncated` (5 000 eventos, `count` 5000, `total` 6213, `truncated: true`, `next_cursor` no nulo), `replay` (`metadata.mode: "replay"`, fechas dentro de 2025), `empty` (`features: []`) y `realistic` (unos 400 eventos repartidos por zonas, con fechas relativas a «ahora», que admite filtros y estadísticas). Entre todos: magnitud nula, magnitud negativa, profundidad nula y negativa, `place` nulo, `magType` nulo, sin país, truncado y vacío.
- **FR-007**: Todo el mock es sintético y etiquetado: `is_synthetic: true`, `id` con prefijo `mock-`, `place` que empieza por «Sintético:» (salvo el nulo), banner permanente «DATOS SINTÉTICOS» mientras se muestre un evento sintético, y etiqueta en la ficha. Ningún id copia uno real de USGS.
- **FR-008**: El mock responde a los tres endpoints (`eventos`, `estadisticas`, `salud`) con la misma forma que la API. Su cálculo de filtros y estadísticas es el de un **servidor simulado** y vive solo en `frontend/mock/`, nunca en `src/`. La interfaz **no** tiene ningún selector de origen (mock/api).
- **FR-009**: Una comprobación automática valida los cinco escenarios contra la forma de `api.md` (campos, tipos, nulos solo donde se permiten, sin NaN ni 0 de relleno, `is_synthetic` verdadero, `count === features.length`) y falla con un archivo estropeado.

**Capa de datos y API real (G1, G6, G7, G9, G11, G12)**

- **FR-010**: Un único punto de acceso a datos decide mock o API según `config.json`; el panel nunca consulta USGS directamente. Las peticiones usan `apiBaseUrl`, un tiempo máximo `timeoutMs` y el cuerpo de error del contrato (`{"error": {"code","message"}}`).
- **FR-011**: Las respuestas se parsean con una guarda pura que comprueba la forma y **conserva los nulos** (un nulo nunca pasa a 0). Una respuesta malformada es un error visible, no un panel vacío.
- **FR-012**: Los eventos, las estadísticas y la salud se refrescan cada `refreshSeconds` sin solapar peticiones; ante un fallo se conserva la última lectura correcta, marcada como antigua y con su hora, y el panel se recupera solo.
- **FR-013**: Un único store (Zustand) con `mode` (live\|replay), periodo (horas o rango de fechas UTC), magnitud mínima y país alimenta a la vez eventos y estadísticas. Cambiar un filtro limpia la selección.
- **FR-014**: Con `mode=replay` la petición lleva `start=2025-01-01T00:00:00.000Z` y `end=2026-01-01T00:00:00.000Z` (el intervalo de referencia de `api.md` §5), la selección de periodo queda desactivada mostrando «2025» y una respuesta vacía es un estado vacío («Sin eventos reproducidos») con el banner REPRODUCCIÓN, no un error.
- **FR-015**: `truncated: true` produce un aviso visible con el número de eventos mostrados y `metadata.total`. Las estadísticas siempre salen de `/api/estadisticas`, nunca de la muestra truncada.

**Globo, símbolos y ficha (G2, G14)**

- **FR-016**: El globo (`GlobeView`, aislado: entrada `events`, `selectedId` y los ajustes visuales; salida `onSelect`) dibuja un prisma por evento con el aspecto de `diseno-visual.md`. La selección toma el pilar más cercano al clic con una tolerancia de 18 px (resuelve la P9 del diseño anterior).
- **FR-017**: Altura del prisma = máx(0,010; 0,0125 × clamp(mag, 0, 8)), multiplicada por el factor de escala del diseño; magnitud nula o negativa → altura mínima. Magnitud nula: barra gris ND `#8a93a0`, **sin anillo ni etiqueta** y sin tratarla nunca como 0. Profundidad nula: gris ND con la altura de su magnitud.
- **FR-018**: Cinco clases de profundidad con los cortes de la API (límite inferior inclusivo; las negativas caen en la primera): `<10`, `10–35`, `35–70`, `70–300`, `≥300`. La leyenda lista las cinco con su rango escrito y su color, más el gris ND.
- **FR-019**: Los países salen de `paises.geojson`, copiado byte a byte a `frontend/public/datos/paises.geojson` con un paso documentado que verifica el SHA-256 `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`, sin Antártida (`ADM0_A3 = ATA`) en la capa. Se documenta como material reutilizado.
- **FR-020**: La ficha muestra lo descrito en la historia 2. Nulos como «ND» o los textos fijos de `data-model.md`; negativos tal cual; fechas «AAAA-MM-DD HH:mm UTC» sin alterar el entero original.

**Tabla, estadísticas y estado (G3–G9, G12)**

- **FR-021**: La tabla de eventos ordenable muestra todos los campos del contrato (magnitud, tipo, profundidad, lugar, fecha UTC, país, estado, significancia). Ordenar es presentación.
- **FR-022**: Las estadísticas se pintan tal como las entrega `/api/estadisticas`: total, `by_hour` (hora UTC fija), `by_country` (con «Sin país asignado»), histogramas de magnitud y profundidad con `no_value`, y `comparison` con su aviso de periodo incompleto («ND» si `variation_pct` es nulo). Las barras escalan los valores de la API; no calculan estadísticas.
- **FR-023**: El estado distingue la última consulta correcta del panel, `generated`, `last_ingestion` y el periodo; avisa de «sin respuesta del backend», «datos antiguos», «sin datos» (que nunca se presenta como 0 eventos) y «datos desactualizados» (umbral fijo en el código, 300 s). El retraso de ingesta lo calcula el panel con los timestamps que devuelve la API (`generated`, `last_ingestion`) y se rotula como tal («hace X min», con la nota «calculado en el panel»); no hay cambio de contrato (P3).
- **FR-024**: Con `metadata.mode === "replay"` hay un banner con la palabra **REPRODUCCIÓN** visible en todo momento.

**Atribución y responsive (G11, G14, G17)**

- **FR-025**: La atribución es **permanente y legible** (texto de al menos 11 px, contraste ≥ 4,5 : 1, sin pulsar nada, a 375 px y a 1280 px, fuera de cualquier desplegable) y nombra: USGS (sismos), Natural Earth (`paises.geojson`, dominio público), `react-globe.gl` y `three` (con su licencia), y declara que no se usa textura.
- **FR-026**: A 375, 768 y 1280 px no hay scroll horizontal. Por debajo de 1024 px se usa el diseño móvil del front; desde 1024 px, el de escritorio.

**Estándares de código (03 §7)**

- **FR-027**: Identificadores en inglés; comentarios y docstrings en español con la plantilla de 03 §7.4 (qué hace, recibe, devuelve, por qué existe, ID del checklist) en toda función o componente exportado; la lógica pura separada del I/O; un componente por responsabilidad.
- **FR-028**: Se quita `h3-js` (no declarado ni importado) y `formatMadrid`/`formatMadridTime` y su test; se declaran `three` y `@types/three` porque se importan; no se copian `prototipo-mapa/`, `.claude/`, `dist/` ni `.git/` del front externo.
- **FR-029**: **El frontend no calcula estadísticas** (§17). Los totales salen de la API; lo que cuenta el cliente se rotula «mostrados»; formatear un timestamp de la API es válido. La auditoría completa está en `plan.md` y se repite al cerrar.
- **FR-030**: Pruebas automáticas de la capa de datos (parseo y nulos, validación de config, clases de profundidad, ventana de replay, conformidad del mock) además de las de `format.ts`.
- **FR-031**: Se borran del globo las capas apagadas que no se ven (arcos, densidad por celdas, mapa de calor y marcadores HTML) junto con sus ajustes en `appearance.ts` y los estilos que solo ellas usan; la apariencia visible no cambia.

### Key Entities

**Evento** y **respuesta de eventos** (`api.md` §3.2 y §3.4), **estadísticas** y **salud** (`api.md` §5), **configuración** (cuatro campos), **escenario del mock** (`base`, `truncated`, `replay`, `empty`, `realistic`) y **filtros** (`mode`, periodo, magnitud mínima, país). Detalle en `data-model.md`.

## Decisiones

### Heredadas y vigentes

- **D1 (globo)**: `react-globe.gl` 2.38.0, instalada exacta con lock (T007). `three` 0.187.0 se declara explícitamente.
- **D2 (store)**: Zustand 5.0.8 (alumno, 2026-11-05); entra en esta feature.
- **D3 (estructura de `src/`)**: **decidida por el alumno, 2026-11-10 (P1): se conserva la estructura del front externo** (`components/` con `mobile/`, `shared/{api,hooks,lib,types}` y `store/`), que sustituye a la opción C del 2026-11-05. Reglas: `shared/` no importa de `components/`; solo `GlobeView` importa `react-globe.gl` y `three`. Documentada en `CODEMAP.md` y en 03 §7.5. Alias `@/` → `src/`.
- **Mock en `frontend/mock/` con carga bajo demanda** (Q4, 2026-11-05).

### Valores por defecto (aceptados por el alumno, 2026-11-10, P6; sin choque con la constitución ni las normas)

- **Colores de profundidad** (conservan el estilo del front: las tres clases actuales son las clases 1, 3 y 5; las clases 2 y 4 son el punto medio): `<10` `#ffd23f`, `10–35` `#ff963a`, `35–70` `#ff5a36`, `70–300` `#d7539a`, `≥300` `#b04cff`; ND `#8a93a0`. Los nombres «Superficial/Intermedio/Profundo» desaparecen: la leyenda usa los rangos.
- **Umbral de desactualizado**: 300 s, constante en el código (no es un campo de `config.json`).
- **Escenario por defecto del mock**: `base`; un `?scenario=` desconocido cae a `base` con aviso en la consola de desarrollo.
- **`config.json` entregado**: `mode: "api"`, `apiBaseUrl: "/api"`, `refreshSeconds: 60`, `timeoutMs: 15000`.
- **Mecanismo de exclusión del mock**: alias de Vite según el modo de compilación; el plan lo detalla y SC-003 lo comprueba.

## Success Criteria *(mandatory)*

- **SC-001**: Desde un clon limpio, `npm ci`, `npm run build` y `npm test` salen con 0; `npm run dev` sirve en el 4200 y un segundo `npm run dev` falla (`strictPort`).
- **SC-002**: Editar `dist/config.json` cambia el comportamiento sin recompilar; un `mode` inválido o un campo ausente muestra un mensaje que lo nombra (prueba automática del validador y comprobación manual).
- **SC-003**: El build de producción no contiene los JSON del mock ni su código (búsqueda del marcador `__MOCK_BACKEND__` y del texto «Sintético:» en `dist/` sin resultados) y, con `mode: "mock"`, muestra el mensaje de «mock no disponible».
- **SC-004**: Los cinco escenarios pasan la comprobación de conformidad (FR-009), que falla con un archivo estropeado; cubren los casos de FR-006; el 100 % de las features tiene `is_synthetic: true` e `id` con prefijo `mock-`; la interfaz no ofrece ningún control para cambiar de origen.
- **SC-005**: Las clases de profundidad respetan los cortes 10/35/70/300 (incluyendo valores en el corte, negativos y nulo) y la leyenda lista las cinco con su rango.
- **SC-006**: Una magnitud nula se dibuja como barra ND sin anillo ni etiqueta; ninguna pantalla muestra «NaN», «undefined» ni un 0 en lugar de un nulo.
- **SC-007**: Con el stack levantado y `mode: "api"`: globo, tabla, estadísticas y estado muestran datos reales; al cambiar periodo, magnitud o país cambian a la vez, y `stats.total` coincide con `metadata.total` de los eventos con los mismos filtros. Capturas con los filtros visibles.
- **SC-008**: Al parar la API, en un ciclo de refresco aparece el aviso, se conserva la última lectura marcada como antigua y no se muestra «0 eventos»; al volver, se recupera sin recargar. Con la API apagada desde el arranque el panel dice «sin datos».
- **SC-009**: Con `mode=replay` la petición lleva el intervalo de 2025 (prueba automática de la construcción de la petición); un replay vacío muestra el estado vacío y el banner REPRODUCCIÓN sin error; el escenario `replay` del mock muestra sus eventos.
- **SC-010**: La atribución de FR-025 se lee sin pulsar nada a 375 y 1280 px (captura) y su texto mide al menos 11 px.
- **SC-011**: La lista de cálculos en el cliente (`auditoria-calculos-cliente.md`) está entregada y ningún recuento propio del cliente aparece sin el rótulo «mostrados»; los totales visibles salen de la API.
- **SC-012**: `scrollWidth <= innerWidth` a 375, 768 y 1280 px con el mock y con la API real, con una ficha abierta; cero errores en la consola durante el recorrido.
- **SC-013**: `package.json` no declara `h3-js` y `src/` no lo importa; declara `three` y `@types/three`; no hay `formatMadrid` en `src/` ni en `tests/`. (`h3-js` puede seguir en el lock como dependencia transitiva de `react-globe.gl`.)
- **SC-014**: `sha256sum frontend/public/datos/paises.geojson` coincide con `6866c877…c977f`; el README del frontend documenta el origen y las licencias.
- **SC-015**: Las pruebas de FR-030 pasan (parseo y nulos, config, clases de profundidad, ventana de replay, conformidad del mock, `format`).
- **SC-017**: Tras borrar las capas apagadas (FR-031), las capturas del globo antes y después (mismo escenario del mock y misma cámara) no muestran diferencias, y `showArcs`, `showHexBin`, `showHeatmap` y `showMarkers` no aparecen en `src/`.
- **SC-016**: Al cerrar existen evidencias en `docs/evidencias/panel-base-mock/`, el README del frontend y `CODEMAP.md` actualizado (§16); G16, G18, G13 y G10 no se marcan como hechos.

## Assumptions

- Node y dependencias son las ya fijadas en `plan.md`; no se añade Chart.js (las barras son propias) ni MapLibre.
- El front externo se toma de `_import-front/globo-lab/` (ignorado por git) y se conserva como fuente (también para el mock, T028 y T029) hasta el cierre (T040), donde se borra.
- La API real (feature `007`) y el stack de Compose existen; para el bloque 4 hacen falta eventos en `live` (productor/consumidor funcionando) y, para la comparación, el histórico de 2025 (`006`).
- Sin datos de replay reales hasta `013-replay`: aquí solo se comprueba el comportamiento vacío con la API real y el escenario `replay` del mock.
- El CORS de la API no está implementado: en desarrollo el proxy de Vite lo evita; el CORS real es de `015-despliegue-tunel`.
- Los valores visuales (apariencia del globo, distancias de cámara, cierre automático de la ficha a los 10 s en escritorio) son los afinados por el alumno en el front externo y no se tocan.

## Límites conocidos (una línea cada uno)

- G16 no cubierta: sin foco de teclado visible, tamaño táctil garantizado ni alternativa al color más allá de la tabla y los rangos escritos.
- Con 5 000 eventos el globo recorre todos los pilares en cada movimiento del puntero para elegir el más cercano; el rendimiento no está medido ni es criterio de aceptación.
- En `mode=replay` el periodo queda fijo en 2025; no se puede acotar por fechas dentro de él.
- Las fronteras 1:110 m son simplificadas y no sirven para delimitar jurisdicción.
- El aviso de «datos desactualizados» usa un umbral fijo de 300 s y la diferencia `generated − last_ingestion` calculada en el panel y rotulada «hace X min» (P3).
- Entre 768 y 1023 px se ve el diseño móvil.
- La rama `hex` de la tierra del globo (apagada) no se borra: no estaba en la lista de P5.

## Preguntas para el alumno

**Ninguna pendiente.** P1–P6 fueron respondidas el 2026-11-10 (ver «Respuestas del alumno a P1–P6» en Clarifications):

- **P1** estructura de `src/`: la del front externo (D3).
- **P2** G5b: la comparación se queda en el cajón inferior; G5b reformulado como decisión propia.
- **P3** retraso de ingesta: lo calcula el panel con los timestamps de la API y se rotula «hace X min».
- **P4** sin Chart.js.
- **P5** borrar las capas apagadas del globo (FR-031).
- **P6** valores por defecto aceptados, sin choques con las normas.
