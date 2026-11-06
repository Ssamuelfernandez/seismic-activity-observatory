# Feature Specification: Panel base con mock y mapa

**Feature Branch**: `008-panel-base-mock`

**Created**: 2026-11-05

**Status**: Draft (specify + clarify hechos; decisiones del alumno aplicadas el 2026-11-05; **cambio de diseño visual HUD del alumno aplicado el 2026-11-06**; respuestas visuales del alumno aplicadas el 2026-11-06: D1 = `react-globe.gl` decidida; su instalación sigue en la tarea T007, que no está ejecutada)

**Input**: User description: «Frontend desde cero en `frontend/` con React + TypeScript + Vite + Tailwind, versiones estables fijadas con lock. Cubre solo: esqueleto del proyecto; `config.json` en tiempo de ejecución (`mode` mock|api, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`); mock sintético y etiquetado conforme al contrato (casos: magnitud nula, sin país, truncado, replay, intervalo vacío); y el mapa con fronteras desde `paises.geojson`, círculos (tamaño ∝ magnitud, color ∝ profundidad, nulos como ND), ficha con `magType` y leyenda. Fuera de alcance: filtros, tabla, gráficos, conexión real con la API, estado, replay y despliegue.» Requisito añadido por el alumno: pensado para PC, pero responsive y usable en móvil (G17). **Desde el 2026-11-06** los «círculos» pasan a ser prismas hexagonales sobre un globo con estética HUD (ver «Cambio de diseño del alumno»); el resto del brief no cambia. El mapa 2D queda fuera y se registra como la feature nueva `panel-mapa-2d` (G18).

> Nota de numeración: `03-procedimiento-ejecucion.md` §4 llama a esta feature `008-panel-base-mock` (F8a). Contratos de referencia, sin modificar: `specs/001-contratos-y-modelo/contracts/api.md` (forma del mock; sobre todo §1, §3.2 y §3.4) y `docs/enunciado/CONTRATO-API.md` (solo lectura). Esta spec no repite sus tablas: las cita.

**Requisitos del checklist que cubre**: G0, G2, G11 (parcial, ver P3), G14, G15, G12 (solo `magType`) y G17 (nuevo, decisión propia). G16 se tiene en cuenta como contexto (el color no es el único canal), pero su cierre (tabla accesible, foco) es de `009-panel-filtros-tabla`. G18 (mapa 2D) **no** se cubre aquí: se registra para la feature `panel-mapa-2d`.

## Cambio de diseño del alumno (2026-11-06)

Decidido por el alumno el 2026-11-06. Sustituye a las decisiones visuales del 2026-11-05 que se indican abajo.

- **Dirección visual**: estética HUD oscura (fondo negro, líneas finas grises, etiquetas pequeñas en mayúsculas, un acento naranja), definida como tokens de Tailwind y heredada por todos los paneles. Documento: `specs/008-panel-base-mock/diseno-visual.md`.
- **Esqueleto de pantalla**: cabecera, globo central, columnas laterales reservadas para futuros paneles y panel lateral de ficha.
- **Globo**: continentes como celdas hexagonales a partir de `paises.geojson` (Antártida oculta). Sismos como prismas hexagonales (capa de puntos de 6 lados): largo ∝ magnitud. ND = barra de altura mínima fija, gris, con «ND» en la ficha.
- **Ficha**: clic en un evento abre un panel lateral (en móvil, cajón inferior). Botón «Ver en mapa 2D» en la ficha, siempre visible. El mapa 2D (MapLibre) **no se implementa aquí**: es la feature nueva `panel-mapa-2d` (roadmap F8f, checklist G18), que usa solo los eventos ya cargados y avisa si `truncated`.
- **Color**: proporcional a la profundidad, con rampa cálida para lo superficial, cumpliendo G2.

**Qué invalida** (cada punto está ya reescrito en esta spec):

| Decisión anterior (2026-11-05) | Estado |
|---|---|
| V3: ND de magnitud como círculo hueco | Invalidada: barra gris de altura mínima fija (V3) |
| V6: ficha como panel flotante o hoja inferior sobre el mapa | Invalidada: panel lateral; cajón inferior en móvil (V6) |
| V2: paleta viridis | Sustituida por una rampa cálida (V2) |
| V1: radio en píxeles 3 + 1,5 × M | Sustituida: largo del prisma ∝ magnitud (V1) |
| V5: ubicación de leyenda y atribución sobre un mapa 2D | Adaptada al nuevo esqueleto (V5) |
| Clarifications: orden de dibujo «mayor primero» para círculos solapados | Retirada: no aplica a prismas 3D |
| Límite conocido «el fondo necesita Internet» | Retirado: fondo negro sin textura ni teselas; la librería viaja en el build |
| `MapView` genérico (D1 abierta) | `GlobeView`, componente aislado |

**Consecuencia para D1** (*implícita en el cambio de diseño del alumno, 2026-11-06; decidida por él ese mismo día*): el globo central implica `react-globe.gl` como librería de esta feature y MapLibre como librería del mapa 2D de la feature nueva `panel-mapa-2d`. **Decidido por el alumno, 2026-11-06 (P6): `react-globe.gl`** (MapLibre para `panel-mapa-2d`). La tarea `T007` pasa a ser la **aplicación** de la decisión ya tomada (anotar versión, instalar solo `react-globe.gl` y borrar el prototipo) y sigue sin ejecutarse; MapLibre **no** se instala aquí.

## Clarifications

### Session 2026-11-05

Respuestas con la opción recomendada (la herramienta no puede preguntar al alumno). Lo que toca contratos o alcance, o no se justifica con la constitución, el enunciado o los contratos, va a «Preguntas para el alumno» con decisión provisional. Las tres decisiones de herramientas (mapa, store, estructura) están en «Decisiones del alumno»: D2 y D3 decididas el 2026-11-05; D1 (`react-globe.gl`) decidida el 2026-11-06 y aplicada en la tarea T007.

- Q: ¿Cómo se elige el caso del mock (base, truncado, replay, vacío) sin añadir campos a `config.json`? → A: Con el parámetro de la URL `?scenario=base|truncated|replay|empty`, solo en modo `mock`; sin parámetro, `base`. `config.json` conserva los cuatro campos del brief y nada más.
- Q: ¿Qué hace el panel en modo `api` en esta feature? → A: Muestra un mensaje claro «Modo api: la conexión con la API todavía no está disponible» y no pinta ningún evento. No cae a los datos del mock en silencio (constitución §7: sintético separado de lo real). La conexión real es `panel-conexion-api`.
- Q: ¿Cómo se etiqueta el mock como sintético? → A: En cuatro sitios: (1) banner permanente «DATOS SINTÉTICOS (MOCK)» visible mientras `mode` sea `mock` o algún evento cargado tenga `is_synthetic: true`; (2) etiqueta «Sintético» en la ficha de cada evento con `is_synthetic: true`; (3) `is_synthetic: true` en todas las `properties` del JSON (campo del contrato, `api.md` §3.4); (4) `id` con prefijo `mock-` y `place` que empieza por «Sintético:». No se añaden campos a `metadata` (contrato cerrado).
- Q: ¿El caso `replay` del mock muestra algo especial en pantalla? → A: No. El archivo existe, cumple el contrato (`metadata.mode: "replay"`) y se pinta como los demás; el banner «REPRODUCCIÓN» (G10) y el uso de `metadata.mode` (G12) son de la feature `replay`. Ver P2.
- Q: ¿Qué hace el mapa con un caso `truncated`? → A: Pinta los eventos recibidos (5 000 de un total de 6 213). No muestra aviso de truncado ni calcula nada sobre la muestra (G12 `truncated` es de `009`). Límite conocido de una línea. Ver P2.
- Q: ¿Qué se ve con el intervalo vacío (`features: []`)? → A: El globo con los continentes (celdas hexagonales) y un mensaje «Sin eventos en el intervalo» (no un error, no un mapa en blanco). Es lo que fija el contrato (HTTP 200 con lista vacía).
- Q (2026-11-06): ¿Cómo se dibujan los continentes del globo? → A: Como celdas hexagonales calculadas por la propia librería del globo a partir de `paises.geojson` (capa de polígonos «hexed»), con la Antártida (`ADM0_A3 = ATA`) excluida de la lista que se entrega a la capa. Es una representación visual: no se calcula ninguna cifra (constitución §17). El archivo sigue copiándose sin modificar; el filtrado se hace al leerlo.
- Q: ¿Dónde se guarda `paises.geojson` en el frontend? → A: Copia byte a byte en `frontend/public/datos/paises.geojson` (ruta que cita `FUENTES-Y-LICENCIAS.md`), desde `data/catalogo/paises.geojson`. El SHA-256 de la copia debe ser `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f` (el mismo que el original, comprobado el 2026-11-05).
- Q: ¿Cómo se dibujan los eventos que se solapan (5 000 eventos)? → A: *(Retirada el 2026-11-06 por el cambio de diseño: en un globo 3D con prismas no hay orden de dibujo que elegir; la altura distingue los eventos y el pulsado se resuelve en el prototipo `T022`.)* Cualquier orden o desempate es de presentación, no un cálculo estadístico (constitución §17).
- Q: ¿Qué cifras muestra la pantalla sobre el número de eventos? → A: Solo `metadata.count` y `metadata.total` tal como llegan del JSON. El frontend no cuenta, no agrupa ni promedia.
- Q: ¿Idioma de la interfaz? → A: Español. Identificadores del código en inglés, comentarios y documentación en español (constitución §13). Sin lenguaje de predicción ni de riesgo en ningún texto (constitución §21).
- Q: ¿Qué hace el panel si `config.json` falta o es inválido? → A: Muestra un mensaje que dice qué campo falla y no arranca el mapa. No inventa valores por defecto en silencio. Se lee en tiempo de ejecución (no se compila dentro del JS), para que G13 pueda cambiarlo sin recompilar.
- Q: ¿Los valores `refreshSeconds` y `timeoutMs` se usan ya? → A: Se leen y validan (enteros positivos) pero no se aplican: no hay peticiones reales. Su uso (refresco sin solapar, timeout) es de `panel-conexion-api`. Ver P3.

## User Scenarios & Testing *(mandatory)*

El «usuario» es quien evalúa el panel en el navegador (PC o móvil) y el propio alumno que desarrolla las siguientes features contra el mock. No hay API real, filtros ni tabla.

### User Story 1 - Ver el globo de eventos del mock (Priority: P1)

Al abrir el panel en modo `mock` se ve, sobre fondo negro, un globo con los continentes como celdas hexagonales (sin la Antártida) y un prisma hexagonal por evento: más largo cuanto mayor es la magnitud, de un color que depende de la profundidad. Hay cabecera, una leyenda, la atribución de las fuentes y el banner de datos sintéticos.

**Why this priority**: es el núcleo de G2 y la base visual de todo el panel.

**Independent Test**: arrancar el panel con `config.json` en `mock`, abrir `/` y comprobar la captura: continentes en celdas hexagonales, prismas con largos y colores distintos, leyenda, atribución y banner visibles.

**Acceptance Scenarios**:

1. **Given** `mode: "mock"` y caso `base`, **When** se abre el panel, **Then** hay un prisma por cada feature del JSON, los continentes se dibujan como celdas hexagonales desde `paises.geojson` sin la Antártida, y se ven la cabecera, la leyenda, la atribución y el banner «DATOS SINTÉTICOS (MOCK)».
2. **Given** dos eventos de magnitudes 2 y 6, **When** se comparan sus prismas, **Then** el de magnitud 6 es más largo, y dos eventos de profundidad 5 km y 150 km tienen colores distintos de la leyenda.
3. **Given** un evento con magnitud nula, **When** se dibuja, **Then** aparece como una barra gris de la altura mínima fija (no con la altura de magnitud 0) y su ficha dice «ND».
4. **Given** el caso `empty`, **When** se abre el panel, **Then** se ve el globo con los continentes y el mensaje «Sin eventos en el intervalo».

---

### User Story 2 - Consultar la ficha de un evento (Priority: P1)

Al pulsar (clic o toque) un prisma se abre el **panel lateral de ficha** (en móvil, un cajón inferior) con los datos del evento, incluido el tipo de magnitud (`magType`), y se puede cerrar. La ficha lleva un botón «Ver en mapa 2D», siempre visible (ver FR-021).

**Why this priority**: G2 exige la ficha y G12 pide usar `magType` en ella.

**Independent Test**: pulsar un evento con `magType: "mww"` y otro con `magType: null`; leer las fichas.

**Acceptance Scenarios**:

1. **Given** un evento con `mag: 5.4` y `magType: "mww"`, **When** se pulsa, **Then** la ficha muestra «Magnitud 5,4 (mww)», profundidad en km, hora del evento y de la última actualización en UTC, país y la etiqueta «Sintético».
2. **Given** un evento con `magType: null`, **When** se abre su ficha, **Then** el tipo de magnitud se muestra como «ND».
3. **Given** un evento con `country_id` y `country_name` nulos, **When** se abre su ficha, **Then** el país es «Sin país asignado» y no hay error en la consola.
4. **Given** un evento con magnitud negativa (−0,06) y profundidad negativa (−0,01), **When** se abre su ficha, **Then** se muestran esos valores tal cual (no se omiten ni se pasan a 0).
5. **Given** una ficha abierta, **When** se pulsa el botón de cerrar o la tecla Esc, **Then** la ficha se cierra.
6. **Given** cualquier ficha abierta, **When** se mira, **Then** el botón «Ver en mapa 2D» está visible (en la misma posición con y sin datos nulos) y, mientras `panel-mapa-2d` no exista, está marcado como no disponible (FR-021).

---

### User Story 3 - Usar el panel desde el móvil (Priority: P2)

Quien abre el panel en un móvil (375 px de ancho) ve el globo, la leyenda y la ficha (cajón inferior) sin desplazarse en horizontal; las columnas laterales reservadas no se muestran.

**Why this priority**: requisito G17 del alumno; el uso principal es PC, por eso P2.

**Independent Test**: emular 375 × 667 px y comprobar que no hay scroll horizontal con la leyenda abierta y con una ficha abierta; guardar captura.

**Acceptance Scenarios**:

1. **Given** una ventana de 375 px, **When** se abre el panel en cualquiera de los cuatro casos, **Then** el ancho del contenido no supera el de la ventana (sin scroll horizontal).
2. **Given** 375 px y una ficha abierta, **When** se lee, **Then** la ficha (cajón inferior) cabe en pantalla (se desplaza en vertical dentro de sí misma si hace falta) y la atribución sigue visible.
3. **Given** 1280 px, **When** se abre el panel, **Then** la leyenda se ve desplegada sobre el globo, las dos columnas laterales reservadas se ven como marcos vacíos y la ficha aparece como panel lateral; a 375 px la leyenda se abre desde un botón «Leyenda».

---

### User Story 4 - Cambiar entre mock y api con `config.json` (Priority: P2)

El alumno edita `config.json` (sin recompilar) para pasar de `mock` a `api`, y escoge el caso del mock con `?scenario=`.

**Why this priority**: G15 pide el selector; sin él las features siguientes no pueden pasar a la API.

**Independent Test**: construir el panel, editar `dist/config.json` y recargar.

**Acceptance Scenarios**:

1. **Given** el panel construido, **When** se cambia `mode` a `api` y se recarga, **Then** se ve el mensaje de modo api no disponible y ningún evento.
2. **Given** `mode: "mock"`, **When** se abre `/?scenario=truncated`, **Then** se cargan 5 000 eventos con `metadata.total` 6 213.
3. **Given** un `config.json` con `mode: "otro"`, **When** se abre el panel, **Then** aparece un mensaje que nombra el campo `mode` y no se muestra el globo.

---

### Edge Cases

- Evento con profundidad nula: prisma gris ND con la altura que le toque por su magnitud; ficha «ND». Nunca 0 (constitución §5).
- Magnitud nula: barra gris de altura mínima fija (V3); ficha «ND». Magnitud o profundidad negativas: válidas. La magnitud negativa usa la altura mínima; el valor real va en la ficha.
- `place` nulo: la ficha muestra «Sin descripción».
- `url` nula (el mock sintético no apunta a USGS): la ficha no muestra enlace; si existe, abre USGS en pestaña nueva.
- Si falla la carga del mock: mensaje visible, no pantalla en blanco. Si falla la carga de `paises.geojson`: se pintan los prismas sobre el globo negro y se avisa de que faltan los continentes.
- Eventos con coordenadas casi idénticas: los prismas se solapan; el prototipo `T022` decide cómo se pulsa el pequeño (ver V1 y Límites).
- Eventos en la Antártida (latitud < −60): se dibujan igualmente; solo se oculta la capa de celdas del continente.
- Límites conocidos (una línea cada uno): el caso `truncated` no avisa del truncado (llega con `009`); las fronteras son 1:110 m, simplificadas (`FUENTES-Y-LICENCIAS.md`), no sirven para delimitar jurisdicción; con 5 000 prismas el globo rinde menos que un mapa 2D y el prisma pequeño es difícil de pulsar (medido en `T006`: 37 fps al mover y 0 de 4 pulsaciones a 6 px sin tolerancia propia; se revalida en `T022`); la luz de la escena oscurece los lados de los prismas, así que el color visible puede diferir del token (se comprueba en `T022`); el fondo es negro sin textura, por lo que no hay atribución de fondo que mostrar; los anillos pulsantes sobre los eventos quedan fuera de esta feature (decisión del alumno, 2026-11-06).

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

**Globo (G2, G14, G11 parcial)**

- **FR-011**: El globo debe dibujar un prisma hexagonal (capa de puntos de 6 lados) por feature, usando solo los valores del JSON, con las reglas de «Decisiones visuales por defecto»: largo ∝ magnitud, color por clase de profundidad, ND como barra gris de altura mínima fija.
- **FR-012**: El globo debe dibujar los continentes como celdas hexagonales calculadas por la librería a partir de `paises.geojson`, copiado sin modificar y con el SHA-256 de Clarifications, **con la Antártida oculta**. Se documenta como material reutilizado (Natural Earth, dominio público) en el README del frontend (G14, M2).
- **FR-013**: El globo debe estar aislado en un componente `GlobeView` cuya entrada es la lista de eventos (y el id seleccionado) y cuya salida es el evento seleccionado (03 §7.5), de modo que cambiar de librería no afecte al resto.
- **FR-014**: Pulsar un prisma abre el **panel lateral de ficha** (en móvil, cajón inferior; historias 2 y 3); la ficha muestra al menos: descripción del lugar, magnitud con `magType`, profundidad en km, `time` y `updated` en UTC, país o «Sin país asignado», etiqueta «Sintético» si procede y enlace a USGS si hay `url`. Los valores nulos se muestran como «ND» (o los textos indicados), nunca como 0. La ficha es de contenido HTML, no un popup del globo.
- **FR-015**: La leyenda debe estar visible (en móvil, tras un botón) e incluir: ejemplos de largo con su magnitud, las cinco clases de profundidad con su rango escrito y su color, y los ND de magnitud y de profundidad (gris).
- **FR-016**: La atribución de las fronteras (Natural Earth) y de la librería del globo debe estar visible de forma permanente, también a 375 px, sin necesidad de pulsar nada (G11, G14). Como el fondo es negro y sin textura, no hay atribución de fondo; la línea dice «Fondo: negro, sin textura». Ningún recurso del globo requiere claves ni secretos (constitución §10).
- **FR-017**: Los prismas distinguen la profundidad por color y la magnitud por largo; la profundidad también se lee en número en la ficha y por rangos escritos en la leyenda, y el orden de las clases se conserva al ver la captura en escala de grises (G16, contexto).

**Diseño visual HUD y esqueleto (G2, G17)**

- **FR-020**: La interfaz debe seguir `diseno-visual.md`: tokens de Tailwind (fondo negro, líneas finas grises, etiquetas pequeñas en mayúsculas, un acento naranja) en un único bloque `@theme`, y un esqueleto con cabecera, globo central, dos columnas laterales reservadas y panel lateral de ficha. Ningún componente de esta feature escribe colores, tamaños de letra ni bordes a mano. Las columnas reservadas no tienen contenido ni funcionalidad (solo el rótulo «RESERVADO») y no se muestran por debajo de 1024 px.
- **FR-021**: La ficha incluye un botón «Ver en mapa 2D», siempre visible. En esta feature el mapa 2D no existe: el botón es focalizable, está marcado como no disponible (`aria-disabled`) y al activarlo muestra «Mapa 2D: próximamente (feature panel-mapa-2d)». No navega a ninguna parte, no hace peticiones y no importa MapLibre. *(Por defecto, revisable; ver Preguntas.)*

**Responsive (G17)**

- **FR-018**: La interfaz debe usar los breakpoints de Tailwind. Debe verse y usarse en 375 px, 768 px y 1280 px de ancho sin scroll horizontal, también con la leyenda abierta y con la ficha abierta. Por debajo de 768 px la ficha es un cajón inferior de ancho completo; desde 768 px es un panel lateral anclado al borde derecho del globo.
- **FR-019**: Los controles pulsables (cerrar ficha, abrir leyenda, «Ver en mapa 2D») deben medir al menos 44 × 44 px en pantallas táctiles y ser alcanzables con el teclado, con foco visible en naranja.

### Key Entities

- **Evento**: feature GeoJSON del contrato (`api.md` §3.4): posición `[lon, lat, profundidad]` y once propiedades; magnitud, `magType`, profundidad, `place`, `country_id` y `country_name` pueden ser nulos.
- **Respuesta de eventos**: `FeatureCollection` con `metadata` (`generated`, `last_ingestion`, `mode`, `count`, `total`, `truncated`, `next_cursor`, `null_mag_excluded`) y la lista de eventos.
- **Configuración del panel**: los cuatro campos de `config.json`.
- **Caso del mock**: uno de `base`, `truncated`, `replay`, `empty`.

## Decisiones del alumno

Decidido por el alumno, 2026-11-05 (D2 y D3) y 2026-11-06 (D1). Son decisiones de herramientas, no cambian los requisitos de arriba.

### D1 — Librería del mapa: Decidido por el alumno, 2026-11-06 (`react-globe.gl`; MapLibre para `panel-mapa-2d`)

La librería es libre (el profesor lo confirmó el 2-nov-2026). Lo que ya pide la spec: círculos con tamaño y color por dato, ficha, fronteras desde GeoJSON, atribución visible, 5 000 eventos, uso en 375 px (FR-011 a FR-019).

| Opción | Pros | Contras |
|---|---|---|
| A. `react-globe.gl` (globo 3D, WebGL) | Es la candidata del brief; vistosa; puntos y polígonos ya incluidos; 5 000 puntos son asumibles en WebGL. | Un globo 3D es más difícil de leer y de pulsar en un móvil pequeño; librería pesada (incluye three.js); la textura de fondo tiene su propia licencia que atribuir. |
| B. MapLibre GL JS (mapa 2D, WebGL) | Colores y radios por dato se declaran en la propia capa; rinde bien con muchos puntos; buen manejo táctil; ventana de ficha sencilla. | Necesita elegir una fuente de fondo (teselas OSM raster con su política de uso, u otra gratuita sin clave); más configuración inicial. |
| C. Leaflet | La más ligera y conocida; el ejemplo del paquete la usaba; teselas OSM directas. | 5 000 círculos pueden ir lentos si no se usa el dibujado en canvas; no hay globo; menos control del estilo por dato. |

Prototipo corto (tareas `T005`–`T006` del plan, **no se hace ahora**): cargar el caso `truncated` (5 000 eventos) en las candidatas y medir con los mismos criterios: tiempo hasta pintar los 5 000 (referencia 3 s, revisable), fluidez al desplazar y ampliar, pulsar un círculo pequeño y abrir la ficha, uso en 375 px, atribución legible y peso del build (kB comprimidos). **Decidido por el alumno, 2026-11-05:** prototipar A (`react-globe.gl`) y B (MapLibre GL JS). G17 (PC primero, móvil usable) pesa a favor del 2D. Leaflet (C) solo entra si ninguna de las dos cumple.

**Actualización 2026-11-06 (cambio de diseño del alumno, confirmado por él el mismo día, P6):** el globo central de la dirección HUD implica **A, `react-globe.gl`**, como librería de esta feature, y **B, MapLibre GL JS**, como librería del mapa 2D de la feature nueva `panel-mapa-2d`. La recomendación de `T006` (MapLibre por G17) deja de aplicar a esta feature, porque el 2D pasa a ser otra feature. Valoración de la tabla de `T006` frente al diseño nuevo: tiempo hasta pintar (≈ 0,4 s) y peso (612 kB) siguen siendo asumibles; la fluidez (≈ 37 fps al mover con 5 000 puntos) es el riesgo de rendimiento; el clic sin tolerancia (0 de 4 a 6 px) pesa más con un prisma hexagonal fino, y se aborda en `T022`. La tabla de `T006` se conserva como evidencia y no se reabre. **TOMADA — Decidido por el alumno, 2026-11-06 (P6): `react-globe.gl`.** `T007` aplica la decisión (versión con `npm view`, instalación exacta con lock y borrado de `frontend/prototipo-mapa/`) y va **después** de `T022`, que valida el prisma de 6 caras con ese prototipo antes de borrarlo. Criterio de `T022`: si el prisma de 6 caras se ve bien **de cerca**, es bueno aunque a escala de globo no se distinga como hexágono; solo si queda claramente mal se pasa al plan B de malla propia (`customLayerData`, dentro de la misma librería).

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

Valores concretos para poder implementar y revisar. Reescritos el 2026-11-06 por el cambio de diseño (el alumno decidió la dirección; los números son del diseñador). El alumno puede cambiarlos al revisar spec o plan; no bloquean. Si la librería no admite alguno, el plan propone el equivalente más cercano.

- **V1 — Largo del prisma** *(por defecto, revisable)*: altura (en fracción del radio del globo) = máx(0,010; 0,0125 × M), con M acotada entre 0 y 8. Da 0,010 (M ≤ 0,8, incluidas las negativas) a 0,100 (M ≥ 8); M 2, 4 y 6 son 0,025, 0,050 y 0,075. Es proporcional a la magnitud salvo el mínimo, que evita barras invisibles. Anchura fija del prisma: 0,45° de radio (el prototipo `T022` la ajusta si no se puede pulsar). La leyenda muestra los ejemplos M 2, 4 y 6.
- **V2 — Escala de profundidad** *(rampa cálida confirmada por el alumno, 2026-11-06, opción A; los valores exactos siguen revisables, P11)*: cinco clases con los mismos cortes que los histogramas de la API (`api.md` §5.1), para que globo, mapa 2D y gráficos futuros usen los mismos rangos. Rampa **cálida para lo superficial**, sobre fondo negro, ordenada por luminancia (lo más superficial, lo más claro):

  | Clase | Profundidad (km) | Color | Luminancia relativa | Contraste sobre negro |
  |---|---|---|---|---|
  | 1 | < 10 (incluye negativas) | `#FFF1A6` amarillo claro | 0,87 | 18,4 : 1 |
  | 2 | 10 a < 35 | `#FDB347` ámbar | 0,54 | 11,7 : 1 |
  | 3 | 35 a < 70 | `#F26A5A` coral | 0,30 | 7,0 : 1 |
  | 4 | 70 a < 300 | `#D2468C` magenta | 0,20 | 5,0 : 1 |
  | 5 | ≥ 300 | `#7C4DCB` violeta | 0,14 | 3,8 : 1 |
  | ND | profundidad o magnitud nula | `#8A93A0` gris | 0,29 | 6,8 : 1 |

  Motivo: pasa de amarillo a violeta con luminosidad que desciende de forma monótona, así que el orden se conserva en escala de grises y se distingue en protanopía y deuteranopía por claridad, no solo por tono; las cinco clases superan 3 : 1 sobre negro (WCAG 1.4.11). Además del color, la leyenda escribe el rango de cada clase y la ficha muestra la profundidad en km (G16: el color no es el único canal). El naranja de acento de la interfaz (`#FF7A1A`) **no** es un color de datos. Como la luz de la escena oscurece los lados, el color real en pantalla se comprueba en `T022`.
- **V3 — ND de magnitud** *(por defecto, revisable)*: barra gris `#8A93A0` de altura mínima fija (0,010, igual que el mínimo de V1) y la anchura normal; en la leyenda: «ND: sin magnitud»; en la ficha: «ND». Se distingue por el gris y por el texto de la ficha, no por la forma.
- **V4 — ND de profundidad** *(por defecto, revisable)*: prisma gris `#8A93A0` con la altura que le corresponda por su magnitud; en la leyenda: «ND: sin profundidad». Si falta también la magnitud, vale V3.
- **V5 — Leyenda y atribución** *(por defecto, revisable)*: tarjeta con borde fino en la esquina inferior izquierda del globo a partir de `md`; por debajo, botón «Leyenda» en la cabecera que la abre sobre el globo. Contenido en este orden: «TAMAÑO = MAGNITUD» (3 prismas de ejemplo), «COLOR = PROFUNDIDAD (KM)» (5 clases + ND). La atribución es una línea fija en la esquina inferior derecha del globo (Natural Earth, la librería y «Fondo: negro, sin textura»), fuera de la leyenda y de la ficha, siempre visible.
- **V6 — Ficha** *(por defecto, revisable)*: panel lateral de 20 rem anclado al borde derecho del globo a partir de `md`; por debajo, cajón inferior a todo el ancho de hasta el 50 % de la altura, con scroll interno. El prisma seleccionado se resalta en naranja. Números con coma decimal; fechas «AAAA-MM-DD HH:mm UTC».
- **V7 — Breakpoints**: los de Tailwind por defecto (`sm` 640, `md` 768, `lg` 1024). Comprobación en 375, 768 y 1280 px. Columnas reservadas desde `lg`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde un clon limpio, `npm ci` y `npm run build` terminan con código 0 y dejan `dist/`; `npm run dev` sirve la página con HTTP 200. Se guarda la salida como evidencia.
- **SC-002**: En el caso `base`, el número de prismas dibujados es igual al número de features del archivo y los eventos de las cinco clases de profundidad y de ND se distinguen en la captura.
- **SC-003**: A 375 × 667 px, en los cuatro casos y con la leyenda y una ficha abiertas, el ancho del contenido es menor o igual que el de la ventana (cero scroll horizontal). Lo mismo a 768 y 1280 px. Se guarda captura a 375 px.
- **SC-004**: La ficha de un evento con `magType: "mww"` muestra «mww»; la de uno con `magType: null` muestra «ND». Comprobado en navegador.
- **SC-005**: El evento de magnitud nula se dibuja como la barra gris de altura mínima (V3) y su ficha dice «ND»; en ninguna pantalla aparecen «NaN», «undefined» ni un 0 en lugar de un valor nulo.
- **SC-006**: El evento sin país abre su ficha con «Sin país asignado» y la consola del navegador muestra cero errores durante el recorrido completo de los cuatro casos.
- **SC-007**: El banner «DATOS SINTÉTICOS (MOCK)» está visible en los cuatro casos; el 100 % de las features de los cuatro archivos tiene `is_synthetic: true` y `id` con prefijo `mock-`.
- **SC-008**: La comprobación automática del mock (FR-010) pasa en los cuatro archivos y falla si se estropea un campo (probado con un archivo malo).
- **SC-009**: `sha256sum frontend/public/datos/paises.geojson` coincide con `6866c877…c977f` y con `data/catalogo/paises.geojson`.
- **SC-010**: La atribución (Natural Earth, librería del globo y «Fondo: negro, sin textura») se lee en la captura a 375 px y a 1280 px sin pulsar nada.
- **SC-011**: Editar `dist/config.json` (`mode: "api"`) y recargar cambia la pantalla al mensaje de modo api sin recompilar; un `mode` inválido muestra un mensaje que nombra `mode`.
- **SC-012**: El caso `truncated` (5 000 eventos) pinta todos los prismas y las celdas de los continentes en 3 s o menos en el equipo del alumno, se mueve a 30 fotogramas por segundo o más (medida de `T006`: ≈ 37 con puntos redondos de 12 lados) y permite abrir la ficha de un prisma pequeño (valores de referencia, a confirmar con `T022`).
- **SC-013**: Las pruebas automáticas de la lógica pura (radio por magnitud incluida la negativa y la nula, clase de profundidad en los cortes 10/35/70/300 y en negativas y nula, formato de ND y de fechas UTC) pasan.
- **SC-014**: No existe en el panel ningún filtro, tabla, gráfico, indicador de estado ni código de replay; el árbol de `frontend/` no incluye Dockerfile ni configuración de despliegue.
- **SC-015**: Al cerrar la feature existen evidencias en `docs/evidencias/panel-base-mock/`, el README del frontend (con el origen de `paises.geojson` y las atribuciones) y `CODEMAP.md` actualizado (constitución §16).
- **SC-016**: Los tokens de `diseno-visual.md` existen en un único bloque `@theme`; ningún componente de la feature contiene colores en hexadecimal fuera de él (salvo las constantes de profundidad de `symbology.ts`, cuyo valor coincide con los tokens); los cinco colores de la rampa y el gris ND tienen contraste ≥ 3 : 1 sobre negro y la luminancia de las cinco clases desciende de la 1 a la 5. Se prueba con una prueba automática de la rampa.
- **SC-017**: En la ficha de cualquier evento el botón «Ver en mapa 2D» está visible, tiene ≥ 44 × 44 px, se alcanza con el teclado y, al activarlo, muestra el aviso de «próximamente» sin errores en consola ni peticiones de red; el árbol de `frontend/` no importa MapLibre.

## Assumptions

- Node y las dependencias son las estables vigentes el día del plan; se fijan allí (G0). El entorno de desarrollo tiene Node 24.x (comprobado: v24.18.0); si el plan elige otra versión de Node, la declara y la documenta.
- TanStack Query forma parte del proyecto desde G0 y se usa también para cargar el mock, para que `panel-conexion-api` reutilice los mismos hooks. Chart.js entra en `010`, no antes.
- El mock no es una API: es un archivo estático por caso. El plan decide cómo se sirve (en `public/` o `frontend/mock/` con carga bajo demanda) para que los 5 000 eventos no engorden el JavaScript del build (ver P4).
- `data/catalogo/paises.geojson` sigue siendo la única fuente; la copia en `frontend/public/datos/` se hace con un paso documentado, no a mano en cada cambio.
- No hay claves de API ni secretos; desde el 2026-11-06 el fondo del globo es negro, sin textura ni teselas, por lo que no necesita Internet ni fuente que atribuir (la librería y los datos viajan en el build).
- El mapa 2D no existe en esta feature: se registra como `panel-mapa-2d` (roadmap F8f, checklist G18), que usará MapLibre, los eventos ya cargados (sin nuevas peticiones) y un aviso si `truncated`. Esta feature no instala MapLibre ni hace nada del 2D salvo el botón «Ver en mapa 2D» (FR-021).
- G11 queda **parcialmente** cubierto (leyenda, atribución y lectura de `refreshSeconds`/`timeoutMs`); el refresco sin solapar y el timeout real se completan en `panel-conexion-api` (P3).
- Una sola ventana de datos por vez: no hay paginación en el panel (el `next_cursor` del caso `truncated` solo está presente para ser fiel al contrato).

## Preguntas para el alumno

Respuestas del alumno del 2026-11-06 (cambio de diseño). Ya aplicadas en esta spec, en `plan.md`, `tasks.md` y `diseno-visual.md`.

**Pendiente (una sola):**

- **P9 — Prisma pequeño y clic.** `T006` midió 0 de 4 pulsaciones a 6 px del centro sin tolerancia. Opciones: (A) ensanchar el prisma y añadir selección del evento más cercano al clic (con `getScreenCoords` de la librería, solo para elegir qué ficha abrir, sin estadísticas); (B) solo ensanchar; (C) aceptar la dificultad y apoyarse en la tabla de `009`. **Decidido por el alumno, 2026-11-06: se decide en `T022` con la medida** (empezando por A); no hay valor provisional.

**Resueltas (alumno, 2026-11-06):**

- **P6 (D1)**: Decidido por el alumno, 2026-11-06: `react-globe.gl` (MapLibre para `panel-mapa-2d`). `T007` aplica la decisión y sigue sin ejecutarse.
- **P13**: Decidido por el alumno, 2026-11-06: la feature nueva se nombra `panel-mapa-2d`, usando el nombre y no el número (los números de 03 §4 son orientativos). Se conservan la fase F8f y el ID G18; el glosario `04-glosario-nomenclatura.md` no se tocó y no lista F8f.
- **Color (V2)**: Decidido por el alumno, 2026-11-06: rampa cálida por profundidad (opción A). Anillos pulsantes: fuera de esta feature.
- **Criterio del prisma (T022)**: Decidido por el alumno, 2026-11-06: si el prisma de 6 caras se ve bien de cerca, se da por bueno aunque a escala de globo no se distinga como hexágono; el plan B de malla propia (`customLayerData`) solo si queda claramente mal.
- **P7, P8, P10, P11, P12**: Decidido por el alumno, 2026-11-06: se mantienen las opciones aplicadas (valores por defecto, siguen siendo revisables): P7 botón «Ver en mapa 2D» visible y desactivado con aviso «próximamente»; P8 marcos «RESERVADO» desde 1024 px; P10 ficha superpuesta al globo (cajón inferior en móvil); P11 valores de V1 y V2; P12 `diseno-visual.md` se queda en `specs/008-panel-base-mock/`.

Resueltas (alumno, 2026-11-05):

- **P1 (G17 en el checklist)**: añadida la fila G17 (responsive, «Decisión propia», prueba «captura a 375 px sin scroll horizontal») al bloque G de `01-checklist-requisitos.md`, a su tabla de mapeo y a la fila 008 de 03 §4, con una línea en los historiales de revisión (checklist rev. 5, 03 rev. 6). No se tocó `docs/enunciado/`. Sin objeción del alumno en esta ronda.
- **P2**: Decidido por el alumno, 2026-11-05: no hay aviso de truncado ni banner de REPRODUCCIÓN en esta feature; con `truncated` y `replay` la pantalla solo lleva el banner de sintético. G10 y G12 (`truncated`, `mode`) llegan con `009` y `replay`.
- **P3**: Decidido por el alumno, 2026-11-05: G11 no se marca hasta cerrar `panel-conexion-api`.
- **P4**: Decidido por el alumno, 2026-11-05 (Q4): los JSON viven en `frontend/mock/` y se cargan bajo demanda (`?url`); `T003` lo comprueba y, si falla, se usa `public/mock/` y se corrige 03 §7.5.
- **P5**: Decidido por el alumno, 2026-11-05: se mantiene el selector `?scenario=`; un valor desconocido cae a `base` con aviso en consola de desarrollo (Q2).
- **Otras**: capturas manuales, sin Playwright (Q3); TypeScript 6.0.3 (Q5); si una versión fijada no se puede instalar en `T001`, se usa la estable anterior y se anota.
