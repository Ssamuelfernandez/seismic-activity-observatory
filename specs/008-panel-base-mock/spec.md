# Feature Specification: Panel base con mock y mapa

**Feature Branch**: `008-panel-base-mock`

**Created**: 2026-11-05

**Status**: Draft (specify + clarify hechos; decisiones del alumno aplicadas el 2026-11-05; solo queda la elección final de la librería del mapa, D1, en la tarea T007)

**Input**: User description: «Frontend desde cero en `frontend/` con React + TypeScript + Vite + Tailwind, versiones estables fijadas con lock. Cubre solo: esqueleto del proyecto; `config.json` en tiempo de ejecución (`mode` mock|api, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`); mock sintético y etiquetado conforme al contrato (casos: magnitud nula, sin país, truncado, replay, intervalo vacío); y el mapa con fronteras desde `paises.geojson`, círculos (tamaño ∝ magnitud, color ∝ profundidad, nulos como ND), ficha con `magType` y leyenda. Fuera de alcance: filtros, tabla, gráficos, conexión real con la API, estado, replay y despliegue.» Requisito añadido por el alumno: pensado para PC, pero responsive y usable en móvil (G17).

> Nota de numeración: `03-procedimiento-ejecucion.md` §4 llama a esta feature `008-panel-base-mock` (F8a). Contratos de referencia, sin modificar: `specs/001-contratos-y-modelo/contracts/api.md` (forma del mock; sobre todo §1, §3.2 y §3.4) y `docs/enunciado/CONTRATO-API.md` (solo lectura). Esta spec no repite sus tablas: las cita.

**Requisitos del checklist que cubre**: G0, G2, G11 (parcial, ver P3), G14, G15, G12 (solo `magType`) y G17 (nuevo, decisión propia). G16 se tiene en cuenta como contexto (el color no es el único canal), pero su cierre (tabla accesible, foco) es de `009-panel-filtros-tabla`.

## Clarifications

### Session 2026-11-05

Respuestas con la opción recomendada (la herramienta no puede preguntar al alumno). Lo que toca contratos o alcance, o no se justifica con la constitución, el enunciado o los contratos, va a «Preguntas para el alumno» con decisión provisional. Las tres decisiones de herramientas (mapa, store, estructura) están en «Decisiones del alumno»: D2 y D3 decididas el 2026-11-05; D1 con candidatas decididas y elección final en la tarea T007.

- Q: ¿Cómo se elige el caso del mock (base, truncado, replay, vacío) sin añadir campos a `config.json`? → A: Con el parámetro de la URL `?scenario=base|truncated|replay|empty`, solo en modo `mock`; sin parámetro, `base`. `config.json` conserva los cuatro campos del brief y nada más.
- Q: ¿Qué hace el panel en modo `api` en esta feature? → A: Muestra un mensaje claro «Modo api: la conexión con la API todavía no está disponible» y no pinta ningún evento. No cae a los datos del mock en silencio (constitución §7: sintético separado de lo real). La conexión real es `panel-conexion-api`.
- Q: ¿Cómo se etiqueta el mock como sintético? → A: En cuatro sitios: (1) banner permanente «DATOS SINTÉTICOS (MOCK)» visible mientras `mode` sea `mock` o algún evento cargado tenga `is_synthetic: true`; (2) etiqueta «Sintético» en la ficha de cada evento con `is_synthetic: true`; (3) `is_synthetic: true` en todas las `properties` del JSON (campo del contrato, `api.md` §3.4); (4) `id` con prefijo `mock-` y `place` que empieza por «Sintético:». No se añaden campos a `metadata` (contrato cerrado).
- Q: ¿El caso `replay` del mock muestra algo especial en pantalla? → A: No. El archivo existe, cumple el contrato (`metadata.mode: "replay"`) y se pinta como los demás; el banner «REPRODUCCIÓN» (G10) y el uso de `metadata.mode` (G12) son de la feature `replay`. Ver P2.
- Q: ¿Qué hace el mapa con un caso `truncated`? → A: Pinta los eventos recibidos (5 000 de un total de 6 213). No muestra aviso de truncado ni calcula nada sobre la muestra (G12 `truncated` es de `009`). Límite conocido de una línea. Ver P2.
- Q: ¿Qué se ve con el intervalo vacío (`features: []`)? → A: El mapa con fronteras y un mensaje «Sin eventos en el intervalo» (no un error, no un mapa en blanco). Es lo que fija el contrato (HTTP 200 con lista vacía).
- Q: ¿Dónde se guarda `paises.geojson` en el frontend? → A: Copia byte a byte en `frontend/public/datos/paises.geojson` (ruta que cita `FUENTES-Y-LICENCIAS.md`), desde `data/catalogo/paises.geojson`. El SHA-256 de la copia debe ser `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f` (el mismo que el original, comprobado el 2026-11-05).
- Q: ¿Cómo se dibujan los círculos que se solapan (5 000 eventos)? → A: Los de mayor magnitud primero y los de menor encima, para que los pequeños sigan siendo pulsables. Es un orden de dibujo, no un cálculo estadístico (constitución §17).
- Q: ¿Qué cifras muestra la pantalla sobre el número de eventos? → A: Solo `metadata.count` y `metadata.total` tal como llegan del JSON. El frontend no cuenta, no agrupa ni promedia.
- Q: ¿Idioma de la interfaz? → A: Español. Identificadores del código en inglés, comentarios y documentación en español (constitución §13). Sin lenguaje de predicción ni de riesgo en ningún texto (constitución §21).
- Q: ¿Qué hace el panel si `config.json` falta o es inválido? → A: Muestra un mensaje que dice qué campo falla y no arranca el mapa. No inventa valores por defecto en silencio. Se lee en tiempo de ejecución (no se compila dentro del JS), para que G13 pueda cambiarlo sin recompilar.
- Q: ¿Los valores `refreshSeconds` y `timeoutMs` se usan ya? → A: Se leen y validan (enteros positivos) pero no se aplican: no hay peticiones reales. Su uso (refresco sin solapar, timeout) es de `panel-conexion-api`. Ver P3.

## User Scenarios & Testing *(mandatory)*

El «usuario» es quien evalúa el panel en el navegador (PC o móvil) y el propio alumno que desarrolla las siguientes features contra el mock. No hay API real, filtros ni tabla.

### User Story 1 - Ver el mapa de eventos del mock (Priority: P1)

Al abrir el panel en modo `mock` se ve un mapa con las fronteras de los países y un círculo por evento: más grande cuanto mayor es la magnitud, de un color que depende de la profundidad. Hay una leyenda, la atribución de las fuentes y el banner de datos sintéticos.

**Why this priority**: es el núcleo de G2 y la base visual de todo el panel.

**Independent Test**: arrancar el panel con `config.json` en `mock`, abrir `/` y comprobar la captura: fronteras, círculos con tamaños y colores distintos, leyenda, atribución y banner visibles.

**Acceptance Scenarios**:

1. **Given** `mode: "mock"` y caso `base`, **When** se abre el panel, **Then** hay un círculo por cada feature del JSON, las fronteras se dibujan desde `paises.geojson` y se ven leyenda, atribución y banner «DATOS SINTÉTICOS (MOCK)».
2. **Given** dos eventos de magnitudes 2 y 6, **When** se comparan sus círculos, **Then** el de magnitud 6 es más grande, y dos eventos de profundidad 5 km y 150 km tienen colores distintos de la leyenda.
3. **Given** un evento con magnitud nula, **When** se dibuja, **Then** aparece con el símbolo ND de la leyenda (no con tamaño de magnitud 0) y su ficha dice «ND».
4. **Given** el caso `empty`, **When** se abre el panel, **Then** se ve el mapa con fronteras y el mensaje «Sin eventos en el intervalo».

---

### User Story 2 - Consultar la ficha de un evento (Priority: P1)

Al pulsar (clic o toque) un círculo se abre una ficha con los datos del evento, incluido el tipo de magnitud (`magType`), y se puede cerrar.

**Why this priority**: G2 exige la ficha y G12 pide usar `magType` en ella.

**Independent Test**: pulsar un evento con `magType: "mww"` y otro con `magType: null`; leer las fichas.

**Acceptance Scenarios**:

1. **Given** un evento con `mag: 5.4` y `magType: "mww"`, **When** se pulsa, **Then** la ficha muestra «Magnitud 5,4 (mww)», profundidad en km, hora del evento y de la última actualización en UTC, país y la etiqueta «Sintético».
2. **Given** un evento con `magType: null`, **When** se abre su ficha, **Then** el tipo de magnitud se muestra como «ND».
3. **Given** un evento con `country_id` y `country_name` nulos, **When** se abre su ficha, **Then** el país es «Sin país asignado» y no hay error en la consola.
4. **Given** un evento con magnitud negativa (−0,06) y profundidad negativa (−0,01), **When** se abre su ficha, **Then** se muestran esos valores tal cual (no se omiten ni se pasan a 0).
5. **Given** una ficha abierta, **When** se pulsa el botón de cerrar o la tecla Esc, **Then** la ficha se cierra.

---

### User Story 3 - Usar el panel desde el móvil (Priority: P2)

Quien abre el panel en un móvil (375 px de ancho) ve el mapa, la leyenda y la ficha sin desplazarse en horizontal.

**Why this priority**: requisito G17 del alumno; el uso principal es PC, por eso P2.

**Independent Test**: emular 375 × 667 px y comprobar que no hay scroll horizontal con la leyenda abierta y con una ficha abierta; guardar captura.

**Acceptance Scenarios**:

1. **Given** una ventana de 375 px, **When** se abre el panel en cualquiera de los cuatro casos, **Then** el ancho del contenido no supera el de la ventana (sin scroll horizontal).
2. **Given** 375 px y una ficha abierta, **When** se lee, **Then** la ficha cabe en pantalla (se desplaza en vertical dentro de sí misma si hace falta) y la atribución sigue visible.
3. **Given** 1280 px, **When** se abre el panel, **Then** la leyenda se ve desplegada sobre el mapa; a 375 px se abre desde un botón «Leyenda».

---

### User Story 4 - Cambiar entre mock y api con `config.json` (Priority: P2)

El alumno edita `config.json` (sin recompilar) para pasar de `mock` a `api`, y escoge el caso del mock con `?scenario=`.

**Why this priority**: G15 pide el selector; sin él las features siguientes no pueden pasar a la API.

**Independent Test**: construir el panel, editar `dist/config.json` y recargar.

**Acceptance Scenarios**:

1. **Given** el panel construido, **When** se cambia `mode` a `api` y se recarga, **Then** se ve el mensaje de modo api no disponible y ningún evento.
2. **Given** `mode: "mock"`, **When** se abre `/?scenario=truncated`, **Then** se cargan 5 000 eventos con `metadata.total` 6 213.
3. **Given** un `config.json` con `mode: "otro"`, **When** se abre el panel, **Then** aparece un mensaje que nombra el campo `mode` y no se muestra el mapa.

---

### Edge Cases

- Evento con profundidad nula: círculo con el color ND de la leyenda; ficha «ND». Nunca 0 (constitución §5).
- Magnitud o profundidad negativas: válidas. La magnitud negativa usa el radio mínimo; el valor real va en la ficha.
- `place` nulo: la ficha muestra «Sin descripción».
- `url` nula (el mock sintético no apunta a USGS): la ficha no muestra enlace; si existe, abre USGS en pestaña nueva.
- Si falla la carga del mock: mensaje visible, no pantalla en blanco. Si falla la carga de `paises.geojson`: se pintan los círculos y se avisa de que faltan las fronteras.
- Eventos con coordenadas casi idénticas: ver Clarifications (orden de dibujo).
- Límites conocidos (una línea cada uno): el fondo del mapa necesita Internet; el caso `truncated` no avisa del truncado (llega con `009`); las fronteras son 1:110 m, simplificadas (`FUENTES-Y-LICENCIAS.md`), no sirven para delimitar jurisdicción.

## Requirements *(mandatory)*

### Functional Requirements

**Proyecto y configuración (G0, G15)**

- **FR-001**: Debe existir un proyecto web en `frontend/` con React, TypeScript, Vite y Tailwind, con las dependencias y la versión de Node fijadas (archivo de bloqueo y versión de runtime declarada, constitución §11). Las versiones concretas son las estables vigentes el día del plan y se anotan allí.
- **FR-002**: `npm ci`, `npm run dev` y `npm run build` deben funcionar desde un clon limpio del repositorio, sin pasos manuales ni secretos (constitución §10). El build deja el resultado en `dist/`.
- **FR-003**: El panel debe leer `config.json` en tiempo de ejecución, con los campos `mode` (`mock` o `api`), `apiBaseUrl`, `refreshSeconds` y `timeoutMs`. Cambiar el archivo en `dist/` cambia el comportamiento sin recompilar. No contiene secretos.
- **FR-004**: Un `config.json` ausente o con un valor inválido debe producir un mensaje que nombre el campo, no un error mudo ni valores inventados.
- **FR-005**: En modo `api` el panel debe mostrar el mensaje de «no disponible» definido en Clarifications y ningún evento. En modo `mock`, los datos salen del mock y nunca se mezclan con datos reales (constitución §7).
- **FR-006**: El proyecto debe tener las carpetas de la estructura elegida (ver D3), incluida la reservada para el store de filtros, **sin lógica de filtros**. La tabla, los gráficos, el estado del sistema y el replay no existen todavía.
- **FR-007**: Los datos pasan por un único punto de acceso que decide mock o api según `config.json`, de modo que `panel-conexion-api` solo añada la rama de la API sin tocar el mapa. La lógica pura (escalas de tamaño y color, formato de valores y de fechas) debe estar separada de la que lee ficheros o dibuja (constitución §14).

**Mock sintético (G15)**

- **FR-008**: Debe haber cuatro casos del mock, cada uno conforme a `api.md` §3 (todos los campos de `metadata` y los once de `properties`; fechas en ms Unix UTC; coordenadas `[lon, lat, profundidad_km]`; geometría `Point` válida):
  - `base`: unas 30 features sintéticas repartidas por el mundo que incluyen al menos un evento de cada tipo: magnitud nula; profundidad nula; magnitud negativa; profundidad negativa; `country_id`/`country_name` nulos (en el mar); `magType` nulo; `place` nulo; `magType` distintos (`ml`, `mb`, `mww`…); y uno por cada clase de profundidad de la leyenda.
  - `truncated`: 5 000 features con `metadata.count: 5000`, `total: 6213`, `truncated: true` y un `next_cursor` no nulo (la escala del máximo de la API, `api.md` §3.2). Sirve también como datos del prototipo de la decisión D1.
  - `replay`: pocas features con `metadata.mode: "replay"`.
  - `empty`: `features: []`, `count: 0`, `total: 0`, `truncated: false`.
- **FR-009**: Todo el mock está etiquetado como sintético según Clarifications (banner, ficha, `is_synthetic: true` en todas las features, prefijo `mock-` y «Sintético:»). Ningún evento del mock copia un identificador real de USGS.
- **FR-010**: Una comprobación automática debe verificar que los cuatro archivos cumplen la forma de `api.md` (campos presentes, tipos, nulos solo donde se permiten, `is_synthetic` verdadero, sin NaN/Infinity ni 0 de relleno) y que `count` es igual al número de features.

**Mapa (G2, G14, G11 parcial)**

- **FR-011**: El mapa debe dibujar un círculo por feature, usando solo los valores del JSON, con las reglas visuales de «Decisiones visuales por defecto».
- **FR-012**: El mapa debe dibujar las fronteras a partir de `paises.geojson`, copiado sin modificar y con el SHA-256 de Clarifications. Se documenta como material reutilizado (Natural Earth, dominio público) en el README del frontend (G14, M2).
- **FR-013**: El mapa debe estar aislado en un componente cuya entrada es la lista de eventos y cuya salida es el evento seleccionado (03 §7.5), de modo que cambiar de librería no afecte al resto.
- **FR-014**: Pulsar un círculo abre la ficha del evento (comportamiento de las historias 2 y 3); la ficha muestra al menos: descripción del lugar, magnitud con `magType`, profundidad en km, `time` y `updated` en UTC, país o «Sin país asignado», etiqueta «Sintético» si procede y enlace a USGS si hay `url`. Los valores nulos se muestran como «ND» (o los textos indicados), nunca como 0.
- **FR-015**: La leyenda debe estar visible (en móvil, tras un botón) e incluir: ejemplos de tamaño con su magnitud, las cinco clases de profundidad con su rango escrito y su color, y el símbolo ND de magnitud y de profundidad.
- **FR-016**: La atribución del fondo del mapa (OpenStreetMap u otra fuente de textura, según la librería elegida) y la de las fronteras (Natural Earth) deben estar visibles de forma permanente, también a 375 px, sin necesidad de pulsar nada (G11, G14). El fondo no puede requerir claves ni secretos en el frontend (constitución §10).
- **FR-017**: Los círculos distinguen la profundidad por color y la magnitud por tamaño; la profundidad también se lee en número en la ficha y por rangos escritos en la leyenda, y el orden de las clases se conserva al ver la captura en escala de grises (G16, contexto).

**Responsive (G17)**

- **FR-018**: La interfaz debe usar los breakpoints de Tailwind. Debe verse y usarse en 375 px, 768 px y 1280 px de ancho sin scroll horizontal, también con la leyenda abierta y con la ficha abierta. En pantallas estrechas la ficha ocupa el ancho disponible; en anchas es un panel flotante sobre el mapa.
- **FR-019**: Los controles pulsables (cerrar ficha, abrir leyenda) deben medir al menos 44 × 44 px en pantallas táctiles y ser alcanzables con el teclado.

### Key Entities

- **Evento**: feature GeoJSON del contrato (`api.md` §3.4): posición `[lon, lat, profundidad]` y once propiedades; magnitud, `magType`, profundidad, `place`, `country_id` y `country_name` pueden ser nulos.
- **Respuesta de eventos**: `FeatureCollection` con `metadata` (`generated`, `last_ingestion`, `mode`, `count`, `total`, `truncated`, `next_cursor`, `null_mag_excluded`) y la lista de eventos.
- **Configuración del panel**: los cuatro campos de `config.json`.
- **Caso del mock**: uno de `base`, `truncated`, `replay`, `empty`.

## Decisiones del alumno

Decidido por el alumno, 2026-11-05 (D2 y D3; D1 solo en parte). Son decisiones de herramientas, no cambian los requisitos de arriba.

### D1 — Librería del mapa: candidatas decididas por el alumno (2026-11-05); elección final en T007

La librería es libre (el profesor lo confirmó el 2-nov-2026). Lo que ya pide la spec: círculos con tamaño y color por dato, ficha, fronteras desde GeoJSON, atribución visible, 5 000 eventos, uso en 375 px (FR-011 a FR-019).

| Opción | Pros | Contras |
|---|---|---|
| A. `react-globe.gl` (globo 3D, WebGL) | Es la candidata del brief; vistosa; puntos y polígonos ya incluidos; 5 000 puntos son asumibles en WebGL. | Un globo 3D es más difícil de leer y de pulsar en un móvil pequeño; librería pesada (incluye three.js); la textura de fondo tiene su propia licencia que atribuir. |
| B. MapLibre GL JS (mapa 2D, WebGL) | Colores y radios por dato se declaran en la propia capa; rinde bien con muchos puntos; buen manejo táctil; ventana de ficha sencilla. | Necesita elegir una fuente de fondo (teselas OSM raster con su política de uso, u otra gratuita sin clave); más configuración inicial. |
| C. Leaflet | La más ligera y conocida; el ejemplo del paquete la usaba; teselas OSM directas. | 5 000 círculos pueden ir lentos si no se usa el dibujado en canvas; no hay globo; menos control del estilo por dato. |

Prototipo corto (tareas `T005`–`T006` del plan, **no se hace ahora**): cargar el caso `truncated` (5 000 eventos) en las candidatas y medir con los mismos criterios: tiempo hasta pintar los 5 000 (referencia 3 s, revisable), fluidez al desplazar y ampliar, pulsar un círculo pequeño y abrir la ficha, uso en 375 px, atribución legible y peso del build (kB comprimidos). **Decidido por el alumno, 2026-11-05:** prototipar A (`react-globe.gl`) y B (MapLibre GL JS). La decisión final la toma el alumno en `T007` con la tabla de `T006` delante; la librería **no queda cerrada** hasta entonces. G17 (PC primero, móvil usable) pesa a favor del 2D. Leaflet (C) solo entra si ninguna de las dos cumple.

### D2 — Librería del store de filtros: Decidido por el alumno, 2026-11-05 (Zustand)

El store único de filtros (constitución §17, G6) se usa en `009` y siguientes. Aquí solo se reserva la carpeta (FR-006); la librería se decide ahora para que el plan pueda fijarla, pero **no se instala hasta `009`** (Zustand) (evitar una dependencia sin uso).

| Opción | Pros | Contras |
|---|---|---|
| A. Zustand | Muy pequeña, sin proveedor, el componente solo se vuelve a dibujar con lo que lee, fácil de probar. | Dependencia extra; menos convenciones impuestas que Redux. |
| B. Redux Toolkit | Estándar muy documentado; herramientas de depuración. | Más código y conceptos para un store con tres o cuatro filtros; dependencia más pesada. |
| C. Context + `useReducer` (sin librería) | Cero dependencias; suficiente para pocos filtros. | Cada cambio vuelve a dibujar todos los consumidores salvo que se separe en varios contextos; mapa y gráficos pesados lo notan. |
| D. Jotai | Átomos pequeños y reactividad fina. | Filtros que dependen entre sí piden más diseño; modelo mental distinto al «store único». |

**Decidido por el alumno, 2026-11-05:** A (Zustand). Motivo: es el menor esfuerzo para un único estado compartido con mapa de 5 000 puntos, y mantiene todo en un solo objeto, como pide §17.

### D3 — Estructura de `src/`: Decidido por el alumno, 2026-11-05 (opción C)

La base documentada es la de 03 §7.5: `api/`, `config/`, `store/`, `features/`, `shared/`. Variantes:

| Opción | Pros | Contras |
|---|---|---|
| A. Tal cual 03 §7.5 | Ya documentada en 03, el roadmap y `CODEMAP.md`; sin trabajo extra. | Dentro de `features/<x>/` no hay convención de subcarpetas; puede crecer desordenada. |
| B. Por feature (cada feature con su `components/`, `hooks/`, `api/` y tipos; solo `core/` compartido) | Cada función visual vive junta y se borra o cambia sin tocar el resto. | Se aparta de 03 y del roadmap (habría que actualizarlos); los tipos del contrato los usan mapa, tabla y gráficos, así que `core/` crece. |
| C. A + convención interna: `features/<x>/{components,hooks,lib}`, tipos del contrato en `shared/`, y regla de que una feature no importa de otra | Mantiene 03 §7.5 y añade orden donde hace falta; separa la lógica pura (`lib/`, FR-007). | Convención extra que hay que respetar y documentar en `CODEMAP.md`. |

**Decidido por el alumno, 2026-11-05:** C. En todas las opciones se mantienen las reglas ya fijadas: mock en `frontend/mock/` (`public/mock/` solo si falla la comprobación de la tarea T003, ver P4), `config.json` en `public/`, y el mapa como componente aislado (FR-013).

## Decisiones visuales por defecto, revisables

Valores concretos para poder implementar y revisar. El alumno puede cambiarlos al revisar spec o plan; no bloquean. Si la librería elegida no admite alguno (p. ej. contorno discontinuo), el plan propone el equivalente más cercano.

- **V1 — Escala de tamaño** *(por defecto, revisable)*: radio en píxeles = 3 + 1,5 × M, con M acotada entre 0 y 8. Da 3 px (M ≤ 0, incluidas las negativas) a 15 px (M ≥ 8); M 2, 4 y 6 son 6, 9 y 12 px. La leyenda muestra esos tres ejemplos.
- **V2 — Escala de profundidad** *(por defecto, revisable)*: cinco clases con los mismos cortes que los histogramas de la API (`api.md` §5.1), para que mapa y gráficos futuros usen los mismos rangos:

  | Clase | Profundidad (km) | Color |
  |---|---|---|
  | 1 | < 10 (incluye negativas) | `#FDE725` amarillo |
  | 2 | 10 a < 35 | `#5EC962` verde |
  | 3 | 35 a < 70 | `#21918C` verde azulado |
  | 4 | 70 a < 300 | `#3B528B` azul |
  | 5 | ≥ 300 | `#440154` morado oscuro |
  | ND | profundidad nula | `#9CA3AF` gris |

  Motivo: es la paleta viridis, pensada para ser legible en protanopía y deuteranopía y con luminosidad que desciende de forma monótona (se conserva el orden en escala de grises). Los círculos llevan un contorno de 1 px que contrasta con el fondo (claro sobre fondo oscuro, oscuro sobre fondo claro) para que las clases 4 y 5 no se pierdan.
- **V3 — ND de magnitud** *(por defecto, revisable)*: círculo de radio fijo 5 px, **sin relleno** (solo contorno de 2 px), con el color de profundidad en el contorno; en la leyenda: «ND: sin magnitud». Se distingue por forma, no por color.
- **V4 — ND de profundidad** *(por defecto, revisable)*: relleno gris `#9CA3AF`; en la leyenda: «ND: sin profundidad». Si falta también la magnitud, vale V3 con contorno gris.
- **V5 — Leyenda** *(por defecto, revisable)*: tarjeta en la esquina inferior izquierda del mapa a partir de `md`; por debajo, botón «Leyenda» que la abre sobre el mapa. Contenido en este orden: «Tamaño = magnitud» (3 círculos), «Color = profundidad (km)» (5 clases + ND). La atribución queda fuera de la tarjeta, en la esquina inferior derecha, siempre visible.
- **V6 — Ficha** *(por defecto, revisable)*: panel flotante de 320 px de ancho sobre el mapa a partir de `md`; por debajo, hoja inferior a todo el ancho de hasta el 50 % de la altura. Números con coma decimal; fechas «AAAA-MM-DD HH:mm UTC».
- **V7 — Breakpoints**: los de Tailwind por defecto (`sm` 640, `md` 768, `lg` 1024). Comprobación en 375, 768 y 1280 px.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde un clon limpio, `npm ci` y `npm run build` terminan con código 0 y dejan `dist/`; `npm run dev` sirve la página con HTTP 200. Se guarda la salida como evidencia.
- **SC-002**: En el caso `base`, el número de círculos dibujados es igual al número de features del archivo y los eventos de las cuatro clases de profundidad y de ND se distinguen en la captura.
- **SC-003**: A 375 × 667 px, en los cuatro casos y con la leyenda y una ficha abiertas, el ancho del contenido es menor o igual que el de la ventana (cero scroll horizontal). Lo mismo a 768 y 1280 px. Se guarda captura a 375 px.
- **SC-004**: La ficha de un evento con `magType: "mww"` muestra «mww»; la de uno con `magType: null` muestra «ND». Comprobado en navegador.
- **SC-005**: El evento de magnitud nula se dibuja con el símbolo V3 y su ficha dice «ND»; en ninguna pantalla aparecen «NaN», «undefined» ni un 0 en lugar de un valor nulo.
- **SC-006**: El evento sin país abre su ficha con «Sin país asignado» y la consola del navegador muestra cero errores durante el recorrido completo de los cuatro casos.
- **SC-007**: El banner «DATOS SINTÉTICOS (MOCK)» está visible en los cuatro casos; el 100 % de las features de los cuatro archivos tiene `is_synthetic: true` y `id` con prefijo `mock-`.
- **SC-008**: La comprobación automática del mock (FR-010) pasa en los cuatro archivos y falla si se estropea un campo (probado con un archivo malo).
- **SC-009**: `sha256sum frontend/public/datos/paises.geojson` coincide con `6866c877…c977f` y con `data/catalogo/paises.geojson`.
- **SC-010**: Las dos atribuciones (fondo y Natural Earth) se leen en la captura a 375 px y a 1280 px sin pulsar nada.
- **SC-011**: Editar `dist/config.json` (`mode: "api"`) y recargar cambia la pantalla al mensaje de modo api sin recompilar; un `mode` inválido muestra un mensaje que nombra `mode`.
- **SC-012**: El caso `truncated` (5 000 eventos) pinta todos los círculos en 3 s o menos en el equipo del alumno (valor de referencia, a confirmar con el prototipo de D1) y permite abrir la ficha de un círculo.
- **SC-013**: Las pruebas automáticas de la lógica pura (radio por magnitud incluida la negativa y la nula, clase de profundidad en los cortes 10/35/70/300 y en negativas y nula, formato de ND y de fechas UTC) pasan.
- **SC-014**: No existe en el panel ningún filtro, tabla, gráfico, indicador de estado ni código de replay; el árbol de `frontend/` no incluye Dockerfile ni configuración de despliegue.
- **SC-015**: Al cerrar la feature existen evidencias en `docs/evidencias/panel-base-mock/`, el README del frontend (con el origen de `paises.geojson` y las atribuciones) y `CODEMAP.md` actualizado (constitución §16).

## Assumptions

- Node y las dependencias son las estables vigentes el día del plan; se fijan allí (G0). El entorno de desarrollo tiene Node 24.x (comprobado: v24.18.0); si el plan elige otra versión de Node, la declara y la documenta.
- TanStack Query forma parte del proyecto desde G0 y se usa también para cargar el mock, para que `panel-conexion-api` reutilice los mismos hooks. Chart.js entra en `010`, no antes.
- El mock no es una API: es un archivo estático por caso. El plan decide cómo se sirve (en `public/` o `frontend/mock/` con carga bajo demanda) para que los 5 000 eventos no engorden el JavaScript del build (ver P4).
- `data/catalogo/paises.geojson` sigue siendo la única fuente; la copia en `frontend/public/datos/` se hace con un paso documentado, no a mano en cada cambio.
- No hay claves de API ni secretos; el fondo del mapa se obtiene de una fuente pública sin clave (depende de D1) y requiere Internet.
- G11 queda **parcialmente** cubierto (leyenda, atribución y lectura de `refreshSeconds`/`timeoutMs`); el refresco sin solapar y el timeout real se completan en `panel-conexion-api` (P3).
- Una sola ventana de datos por vez: no hay paginación en el panel (el `next_cursor` del caso `truncated` solo está presente para ser fiel al contrato).

## Preguntas para el alumno

Pendiente: solo la elección final de D1 (librería del mapa), en la tarea `T007`.

Resueltas (alumno, 2026-11-05):

- **P1 (G17 en el checklist)**: añadida la fila G17 (responsive, «Decisión propia», prueba «captura a 375 px sin scroll horizontal») al bloque G de `01-checklist-requisitos.md`, a su tabla de mapeo y a la fila 008 de 03 §4, con una línea en los historiales de revisión (checklist rev. 5, 03 rev. 6). No se tocó `docs/enunciado/`. Sin objeción del alumno en esta ronda.
- **P2**: Decidido por el alumno, 2026-11-05: no hay aviso de truncado ni banner de REPRODUCCIÓN en esta feature; con `truncated` y `replay` la pantalla solo lleva el banner de sintético. G10 y G12 (`truncated`, `mode`) llegan con `009` y `replay`.
- **P3**: Decidido por el alumno, 2026-11-05: G11 no se marca hasta cerrar `panel-conexion-api`.
- **P4**: Decidido por el alumno, 2026-11-05 (Q4): los JSON viven en `frontend/mock/` y se cargan bajo demanda (`?url`); `T003` lo comprueba y, si falla, se usa `public/mock/` y se corrige 03 §7.5.
- **P5**: Decidido por el alumno, 2026-11-05: se mantiene el selector `?scenario=`; un valor desconocido cae a `base` con aviso en consola de desarrollo (Q2).
- **Otras**: capturas manuales, sin Playwright (Q3); TypeScript 6.0.3 (Q5); si una versión fijada no se puede instalar en `T001`, se usa la estable anterior y se anota.
