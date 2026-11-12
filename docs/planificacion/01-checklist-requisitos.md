# Observatorio de actividad sísmica — Checklist de requisitos de entrega

Fuentes cruzadas: `ENUNCIADO.md` (rev. 2, 27-oct-2026), `Guia-entregables`, `FAQ-ALUMNADO.md`, `README.md`, `CONTRATO-API.md` (contrato mínimo), `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md` y el frontend de ejemplo del paquete (solo como referencia).
Documentos hermanos: `02-roadmap-implementacion.md` (orden de fases) y `03-procedimiento-ejecucion.md` (procedimiento, features de Spec Kit, constitución).
Prioridad si hay conflicto: Enunciado > Guía de entregables > FAQ (la propia FAQ y la guía dicen que "no añaden requisitos"). Este checklist es un **resumen derivado**: si choca con el enunciado, gana el enunciado.
Convención: **[OBL]** obligatorio · **[EVAL]** puntúa en rúbrica · **[OPC]** opcional · **[?]** ambiguo, confirmar con el profesor.

**Registro de cambios**
- 31-oct-2026 (rev. 2): el frontend se construye desde cero (el proyecto Angular del paquete era un ejemplo, no una base entregada).
- Nov-2026 (rev. 3): el profesor permite cambiar el framework del frontend; decisión del alumno: **React + TypeScript + Vite + Tailwind** en lugar de Angular. Mapa: `react-globe.gl` (candidata; plan B MapLibre o Leaflet). Datos: TanStack Query. Gráficos: Chart.js. Filtros: store único. El alcance de las features no cambia.
- 1-nov-2026 (rev. 3): reconciliación con 02 y 03. Añadidos `country_name` y detalles del contrato (F1–F5, F12), nota de identificadores en inglés (C5, E3), columna "Feature" en la tabla de pruebas (I), requisitos M7–M9, puntos por confirmar nuevos (§5) y **§7 de trazabilidad ID → feature de Spec Kit**.
- 2-nov-2026 (rev. 4): la librería del mapa es libre (el profesor confirmó por correo el 2-nov-2026 que Leaflet era una guía, no una obligación). Candidata: Globe.gl; alternativas: MapLibre o Leaflet. Se decide en el plan de `panel-base-mock`. Afecta a §0, G0, G2, G11, G16, M2, §5 y la introducción del bloque G (frontend).
- 5-nov-2026 (rev. 5): nuevo requisito **G17** (diseño responsive, decisión propia del alumno), asignado a `panel-base-mock`.
- 6-nov-2026 (rev. 6): cambio de diseño visual del alumno (globo HUD con prismas hexagonales y ficha en panel lateral en `panel-base-mock`; `react-globe.gl` queda implícita para el globo). Nuevo requisito **G18** (vista de mapa 2D con MapLibre), asignado a la feature nueva `panel-mapa-2d`. Los textos de G0, G2 y de §0 que dicen «candidata» o «popup» se reconcilian al cerrar `panel-base-mock`.
- 10-nov-2026 (rev. 7): **enmienda de alcance de `panel-base-mock`** (decisión del alumno): adopta el front externo con correcciones y absorbe las features `panel-filtros-tabla`, `panel-graficos-comparacion`, `panel-estado-fallos` y `panel-conexion-api` (§7). **G18** queda aplazada (`panel-mapa-2d`). **G16** (accesibilidad) queda **no cubierta, decisión propia**: la tabla existe (G8) pero no se trabaja el foco de teclado ni el no depender solo del color. La apariencia del globo y del layout es la del front externo (G2 se lee con ese diseño; **G5b se reformula** como decisión propia: la comparación va en el cajón de estadísticas, no en un panel lateral).

---

## 0. Qué es esto, en 6 líneas

1. Pipeline en Docker Compose: USGS → **productor** (Python/aiokafka) → **Kafka** → **consumidor** (Python/aiokafka) → **PostgreSQL** → **API FastAPI** → ngrok (HTTPS) → **panel React + TypeScript + Vite + Tailwind, con mapa `react-globe.gl` (candidata; plan B MapLibre o Leaflet), en Netlify (a construir desde cero)**.
2. Tres fuentes de datos: feed reciente (`all_day.geojson`), histórico 2025 (M≥4, por meses) y catálogo de países (Natural Earth, ya entregado).
3. El núcleo técnico es: **no duplicar** (id + updated), **revisiones** (la versión antigua nunca pisa a la nueva), **idempotencia** (al menos una vez + upsert) y **país por punto-en-polígono**.
4. La nota sale de 5 criterios: Extracción, Calidad, Modelado, Análisis, Reflexión. Más infraestructura **no** da más nota.
5. Entregas en 3 bloques: **repositorio**, **memoria/notebook**, **panel + defensa oral**.
6. No hay que predecir terremotos, ni usar Spark/Flink/Kubernetes/ML/cloud permanente.

---

## 1. Rúbrica → qué evidencia te la da

| Criterio | Para llegar a 9–10 hace falta | Evidencia concreta |
|---|---|---|
| Extracción | Carga + análisis de tipos | Archivos históricos, consultas guardadas, tabla de tipos/unidades, productor automático |
| Calidad | Análisis completo + acciones | Apartado en memoria/notebook: consultas + resultados antes/después + decisiones (6 dimensiones; ≥4 para notable) |
| Modelado | Modelo optimizado | Conceptual/lógico/físico, grano, claves, índices justificados con medición, país por polígono, revisiones sin duplicar |
| Análisis | Análisis + insights | Ventanas por hora UTC, distribuciones, comparación histórica equivalente, ≥3 conclusiones con cifras y filtros |
| Reflexión | Excelente + propuestas | Complejidad, mediciones en 3 tamaños, costes, 100 M registros, limitaciones, mejoras concretas |

Ponderación de la asignatura (de la sesión 8, sin cambios): test 30 % · práctico 50 % · mini-ETL 20 %.

---

## 2. Checklist por bloque

### A. Arquitectura y Docker

| ID | Requisito | Hecho cuando… | Fuente | ☐ |
|---|---|---|---|---|
| A1 | **[OBL]** 5 servicios separados en Compose: productor, Kafka, consumidor, PostgreSQL, API | `docker compose ps` los muestra healthy | Enunc. §2 | [x] |
| A2 | **[OBL]** `docker compose up --build -d` lo levanta todo | Funciona desde un clon limpio | Enunc. §2 | [x] |
| A3 | **[OBL]** Imagen reproducible por servicio Python (puede compartirse con distinto comando) | Dockerfile(s) con dependencias fijadas | Enunc. §2 | [x] |
| A4 | **[OBL]** Healthchecks y reintentos (el orden de arranque no basta) | Productor/consumidor reintentan hasta que Kafka/PG estén listos | Enunc. §2, §9 | [x] |
| A5 | **[OBL]** Volúmenes persistentes (PG, y lo necesario para originales) | Reiniciar contenedores no pierde datos | Enunc. §9 | [x] |
| A6 | **[OBL]** Retención limitada de Kafka | Parámetro configurado y documentado | Enunc. §9 | [x] |
| A7 | **[OBL]** Nombres de servicio en vez de `localhost` entre contenedores; documentar listeners de Kafka si hay acceso desde host | Config coherente con `.env.example` | Enunc. §9 · FAQ 28 | [x] |
| A8 | **[OBL]** Solo la API se expone (Kafka y PG nunca por el túnel) | Solo `127.0.0.1:8000:8000` publicado (o ngrok en la red Compose) | Enunc. §9 | [x] |
| A9 | **[OBL]** Uvicorn en `0.0.0.0:8000` dentro del contenedor (ngrok termina el HTTPS; la API recibe HTTP local) | Comprobado | Enunc. §9 · CONTRATO | [x] |
| A10 | **[OBL]** `.env.example` sin credenciales reales; variables coinciden con el código | Productor configurable por env: Kafka, topic, frecuencia | Enunc. §5, §9 | [x] |
| A11 | **[OBL]** Dependencias fijadas (`requirements.txt` / lock) | Versiones concretas | Guía 1.3 | [x] |
| A12 | El panel React **no** necesita contenedor (SPA en Netlify); ngrok en host o contenedor | — | Guía 1.2 | [x] |

### B. Extracción e ingesta

| ID | Requisito | Hecho cuando… | Fuente | ☐ |
|---|---|---|---|---|
| B1 | **[OBL]** Productor consulta el feed cada ~60 s (GET) | Log con cada ciclo | Enunc. §4.1 | [x] |
| B2 | **[OBL]** Documentar respuesta, tipos, unidades, opcionales, frecuencia, errores y latencia | Sección en memoria | Enunc. §4.1 | ☐ (pendiente: pasar docs/borradores/productor-live.md a la memoria) |
| B3 | **[OBL]** Filtrar `properties.type == "earthquake"` y **guardar el motivo de exclusión** | Tabla/log de exclusiones | Enunc. §4.1 | [x] |
| B4 | **[OBL]** Guardar el GeoJSON original + metadatos de extracción (fecha, status, latencia, nº) **antes** de transformar | Existe en PG o disco | Enunc. §5 | [x] |
| B5 | **[OBL]** Evitar guardar indefinidamente copias idénticas: **definir retención** y registrar consultas | Política escrita + implementada (p. ej. hash) | Enunc. §5 | [x] |
| B6 | **[OBL]** Comparar `id` + `updated` con **estado persistente** (no solo RAM): publicar nuevos y revisiones posteriores; omitir iguales y atrasadas | Tabla `ingest_state` sobrevive a reinicio | Enunc. §5 · FAQ 10 | [x] |
| B7 | **[OBL]** Clave Kafka = id del evento | Verificado | Enunc. §5 | [x] |
| B8 | **[OBL]** Mensaje con `source`, `ingested_at`, `mode` (live/replay) y evento original | Esquema documentado | Enunc. §5 | [x] |
| B9 | **[OBL]** Esperar confirmación (ack) de Kafka **antes** de marcar publicado | Orden en el código | Enunc. §5 | [x] |
| B10 | **[OBL]** Timeout, HTTP 429/5xx, backoff progresivo, errores de JSON; registrar error **sin borrar el estado válido anterior** | Pruebas con fallo simulado | Enunc. §5 | [x] |
| B11 | **[OBL]** Explicar la limitación: evento que sale de la ventana ≠ eliminado por USGS; reconciliación exhaustiva es ampliación | Párrafo en memoria | Enunc. §5 | ☐ (pendiente: pasar docs/borradores/productor-live.md a la memoria) |
| B12 | **[OBL]** Explicar cómo recuperar el hueco tras una parada >24 h con el catálogo histórico | Procedimiento documentado (no tiene por qué automatizarse) | Enunc. §5 | ☐ (pendiente: pasar docs/borradores/productor-live.md a la memoria) |
| B13 | **[OBL]** Histórico: 2025, mundial, M≥4, `eventtype=earthquake`, **por meses**; si un mes >20.000, subdividir **sin truncar en silencio** | Archivos + log de nº de registros por consulta | Enunc. §4.2 | [x] |
| B14 | **[OBL]** Deduplicar eventos compartidos entre intervalos (los extremos pueden incluirse en ambos) | Unicidad de `event_id` comprobada | Enunc. §4.2 | [x] |
| B15 | **[OBL]** Guardar consultas (URLs/parámetros), fecha de extracción y nº de registros; descargar una vez y reutilizar | Registro de procedencia | Enunc. §4.2 · Guía 2.3 | [x] |
| B16 | **[OBL]** Histórico procesado con **las mismas reglas** de limpieza e integración que el live (vía Kafka o lógica común en batch; documentar la elección) | Misma función de procesamiento | FAQ 21 | [x] |
| B17 | **[OBL]** El histórico no se pierde al reiniciar; procedimiento reproducible de carga | Comando documentado en README | FAQ 21 | [x] |
| B18 | Aclarar que el histórico es una instantánea a la fecha de extracción, no todas las revisiones pasadas | Párrafo | Enunc. §4.2 | ☐ |

### C. Consumidor, calidad y país

Nota de nombres: los identificadores del proyecto (tablas, columnas, topics, código) van en inglés; ver la equivalencia con la estructura orientativa del enunciado en E3.

| ID | Requisito | Hecho cuando… | Fuente | ☐ |
|---|---|---|---|---|
| C1 | **[OBL]** Validar, limpiar, enriquecer y escribir; reglas explícitas | Reglas listadas en memoria | Enunc. §6 | [x] |
| C2 | **[OBL]** Transacción PG (versión + estado actual) → commit → **después** commit del offset | `enable_auto_commit=False`; orden verificado | Enunc. §7 · FAQ 13 | [x] |
| C3 | **[OBL]** Al menos una vez + escritura idempotente (restricciones únicas + upsert). No hace falta transacción distribuida | Repetir un mensaje no cambia nada | Enunc. §7 | [x] |
| C4 | **[OBL]** Estado actual solo se actualiza si `updated` es más reciente; la versión recibida se conserva siempre sin pisar una posterior | Prueba "versión antigua tardía" | Enunc. §7 | [x] |
| C5 | **[OBL]** Cuarentena **duradera** (tabla `quarantine`) con motivo y referencia al original; no perder en silencio ni bloquear la cola | Tabla de cuarentena | Enunc. §6 · README §6 | [x] |
| C6 | **[OBL]** No rellenar nulos con 0; magnitud negativa y profundidad negativa **no** se rechazan sin investigar | Reglas justificadas | Enunc. §6 · FAQ 16 | [x] |
| C7 | **[OBL]** Fechas a UTC conservando el original (ms); separar tiempo de ocurrencia vs procesamiento | Campos distintos | Enunc. §6 | [x] |
| C8 | **[OBL]** Registrar qué transformaciones cambian datos y a cuántos registros afectan | Contadores | Enunc. §6 | [x] |
| C9 | **[OBL]** País por **punto dentro de polígono** (GeoPandas/Shapely), EPSG:4326, **no** parseando `place` | `country_id` = `ADM0_A3` | Enunc. §4.3 | [x] |
| C10 | **[OBL]** Comprobar unicidad de `ADM0_A3` antes de usarlo como ID (la validación indica 177 distintos) | Consulta/script | Enunc. §4.3 | [x] |
| C11 | **[OBL]** Documentar regla para puntos en frontera y múltiples coincidencias | Párrafo + implementación | Enunc. §4.3 · FAQ 19 | [x] |
| C12 | **[OBL]** "Sin país asignado" se conserva (no se atribuye al más cercano, no es error automático) y permanece en análisis | `country_id` nulo → etiqueta en API/panel | Enunc. §4.3 | [x] |
| C13 | **[OBL]** Casos de prueba artificiales **separados e identificados** | Marcados como sintéticos (`is_synthetic`) | Enunc. §6 | [x] |
| C14 | **[OBL, EVAL]** Apartado de calidad en memoria/notebook con código o consultas, resultados **antes/después**, decisiones y registros de ejemplo | Ver D | Enunc. §6, §12 | ☐ |
| C15 | **[OPC]** Informe de calidad automático / panel de calidad / tabla de métricas | **No** hacerlo salvo que sobre tiempo | Enunc. §6 | — |

### D. Contenido del apartado de calidad (6 dimensiones)

| Dimensión | Qué calcular (denominador explícito) | ☐ |
|---|---|---|
| Completitud | % de disponibilidad por campo (mag, magType, place, profundidad…) | ☐ |
| Unicidad | Duplicados de versión; unicidad de `event_id` en estado actual | ☐ |
| Validez | Tipos, fechas parseables, coordenadas finitas en rango, geometría Point | ☐ |
| Consistencia | Claves de país, unidades, secuencia de revisiones | ☐ |
| Actualidad | Diferencia ocurrencia → `updated` → ingesta; aclarar el efecto de revisiones antiguas | ☐ |
| Exactitud | Qué se puede/no se puede contrastar (rango ≠ exactitud física); límites del mapa simplificado | ☐ |

Reglas de redacción: indicar siempre **conjunto** (mensajes / versiones distintas / eventos actuales) y **denominador**; **no sumar** incidencias solapadas; **no inventar** errores en datos reales (los casos sintéticos van aparte); "después" no significa "sin nulos".

### E. Modelo de datos

| ID | Requisito | Hecho cuando… | Fuente | ☐ |
|---|---|---|---|---|
| E1 | **[OBL, EVAL]** Modelo conceptual, lógico y físico (3 vistas de la misma BD) | Diagramas/tablas en memoria | Enunc. §7 | [x] |
| E2 | **[OBL]** Explicar grano (qué es una fila), claves, relaciones e índices | Por tabla | Enunc. §7 | ☐ |
| E3 | Estructura orientativa del enunciado: `evento_actual` (hecho, única por `event_id`), `fecha`, `pais`, `evento_version` (única `(event_id, updated)`), estado de ingesta/cuarentena. **Identificadores del proyecto en inglés:** `current_event`, `date_dim`, `country`, `event_version`, `quarantine`, `ingest.*`. No es obligatorio copiar la estructura, sí justificar y **documentar la equivalencia** de nombres en la memoria | Equivalencia escrita | Enunc. §7 · FAQ 20 | ☐ |
| E4 | **[OBL]** Integrar terremotos con atributos del catálogo (histórico y feed no cuentan como segunda fuente) | Join país | Enunc. §7 | ☐ |
| E5 | **[OBL]** SQL de creación de tablas e índices en el repo (`sql/`) enlazado desde la memoria | Carpeta `sql/` | Guía 2.5 | [x] |
| E6 | **[OBL]** Índices justificados **por consulta concreta** y con medición antes/después | `EXPLAIN ANALYZE` / tiempos | FAQ 20 | ☐ |
| E7 | Timestamps completos conservados (para ventanas horarias) | Campo `event_time` timestamptz | FAQ 20 | [x] |

### F. API (FastAPI)

El contrato del profesor es **mínimo**: define el contenido de las respuestas (con ejemplo exacto solo para `/api/eventos`) y deja decisiones abiertas que se resuelven en `specs/001-contratos-y-modelo/contracts/api.md`: forma de `/api/salud` y `/api/estadisticas`, paginación y límite de puntos, parámetro `mode`.

| ID | Requisito | Hecho cuando… | Fuente | ☐ |
|---|---|---|---|---|
| F1 | **[OBL]** `GET /api/eventos` → HTTP 200, `Content-Type: application/json`, `FeatureCollection`; sin eventos = `features: []`; **un evento = una vez, versión actual**; por defecto últimas 24 h. Cada feature: `id`, geometría `Point` con `[lon, lat, depth_km]` y `properties` con `mag`, `magType`, `place`, `time`, `updated`, `country_id`, `country_name` | Cumple el contrato | CONTRATO | [x] |
| F2 | **[OBL]** `metadata`: `generated` (generación de la respuesta; no implica ingesta activa), `last_ingestion` (última consulta correcta a USGS), `mode`, `count`, `truncated`. Fechas en ms Unix UTC | Presentes | CONTRATO | [x] |
| F3 | **[OBL]** Filtros `start` (ISO 8601, incl.), `end` (ISO 8601, excl.), `min_mag`, `country_id` | Probados; **mag nula no cumple `min_mag`** y se cuenta aparte | CONTRATO | [x] |
| F4 | **[OBL]** `null` (nunca NaN/Infinity) para mag/profundidad/país desconocidos; geometría válida siempre en este endpoint | — | CONTRATO | [x] |
| F5 | **[OBL]** Si se trunca: `truncated: true`, total completo y paginación (**mecanismo y límite propios**, documentados: el contrato no los fija); el panel no calcula estadísticas globales sobre una muestra truncada | Límite y paginación documentados | CONTRATO | [x] |
| F6 | **[OBL]** `GET /api/salud`: estado API + fecha de última ingesta, sin credenciales (forma propia, documentada) | — | CONTRATO | [x] |
| F7 | **[OBL]** `GET /api/estadisticas`: conteos por hora UTC y por país, distribuciones, comparación histórica; con periodo, filtros, unidad y registros sin valor; **mismos filtros que el mapa** (forma propia, documentada) | — | CONTRATO | [x] |
| F8 | **[OBL]** Fallo de BD → error explícito, **nunca** "0 eventos" como resultado válido | Prueba con PG parado | CONTRATO | [x] |
| F9 | **[OBL]** CORS: origen exacto de Netlify + `http://localhost:4200`; métodos GET y OPTIONS; cabecera `ngrok-skip-browser-warning`; sin cookies | Preflight OK | CONTRATO · Enunc. §9 | [x] |
| F10 | **[OBL]** Sin rutas de administración ni secretos expuestos | — | Enunc. §9 | [x] |
| F11 | La API consulta datos **ya procesados**; no depende de que el panel esté abierto | — | FAQ 2 | [x] |
| F12 | Vista de reproducción: poder consultar el intervalo histórico y los datos aislados de replay, con `metadata.mode = "replay"` (parámetro de modo: **decisión propia**, no está en el contrato mínimo) | Parámetro/ruta de modo | FAQ 32 | [x] |

### G. Panel React (**construido desde cero**; el ejemplo del paquete solo sirve de referencia)

El frontend no viene hecho: hay que crear el proyecto React (Vite + TypeScript + Tailwind), integrar la librería de mapa elegida y desarrollar todas las vistas. Se puede avanzar **contra datos simulados (mock) que cumplan `CONTRATO-API.md`** sin esperar a la API real, y cambiar a la API en cuanto exista (G15).

| ID | Requisito | Hecho cuando… | Fuente | ☐ |
|---|---|---|---|---|
| G0 | **Crear el proyecto React + TypeScript + Vite + Tailwind** (versiones de Node y de dependencias fijadas, `package-lock.json`), con la librería de mapa elegida (candidata: `react-globe.gl`; plan B MapLibre o Leaflet; se confirma en el plan de panel-base-mock), TanStack Query para los datos, estructura por componentes/hooks/store y build de producción (`dist/`) funcionando | `npm ci && npm run dev` y `npm run build` OK desde clon limpio | Decisión propia | [x] |
| G1 | **[OBL]** Consulta **vuestra API**, no USGS | `config.json` en modo `api` | Enunc. §8 | [x] |
| G2 | **[OBL]** Mapa o globo: fondo, fronteras, círculos, ficha; tamaño ∝ magnitud, color ∝ profundidad, **leyenda**, nulos visibles como **ND** | Implementado y comprobado visualmente con datos del mock y reales | Enunc. §8 | [x] |
| G3 | **[OBL]** Recuentos por país/subregión (incl. "Sin país asignado") y por **hora UTC fija según tiempo del evento** | Gráfico/tabla | Enunc. §8 | [x] |
| G4 | **[OBL]** Distribuciones de magnitud y profundidad indicando registros sin valor | — | Enunc. §8 | [x] |
| G5 | **[OBL]** Comparación histórica: últimas 24 h M≥4 vs media diaria 2025 con **mismos filtros**, denominador con **días a cero**; aviso de periodo reciente incompleto; si media=0 → ND | Cifras + fórmula | Enunc. §8 · FAQ 23 | [x] |
| G5b | **Decisión propia (reformulada el 10-nov-2026, no prioritaria):** la comparación se muestra en el **cajón inferior de estadísticas** del panel, donde ya está en el front (antes: panel lateral junto al mapa; roadmap F8c, absorbida por `panel-base-mock`). Se compara contra la **media diaria de 2025 en la misma zona/país y con M≥4**, no contra un día concreto del año pasado | Panel visible con cifra reciente, media 2025, diferencia y % | Decisión propia | [x] |
| G6 | **[OBL]** Filtros de fecha, magnitud y país/región, **coherentes** entre mapa y gráficos | Un único store de filtros compartido | Enunc. §8 | [x] |
| G7 | **[OBL]** Estado del sistema: último acceso correcto a la API, última ingesta correcta de USGS, periodo consultado, aviso si datos desactualizados o backend caído | Distinguir "última consulta del panel / respuesta generada / última ingesta" | Enunc. §8 · FAQ 31 | [x] |
| G8 | **[OBL]** Tabla consultable de eventos (alternativa accesible al mapa y al color) | — | Enunc. §8 | [x] |
| G9 | **[OBL]** Si falla la API: aviso claro, conservar/identificar la última lectura, no presentar datos viejos como recién obtenidos | Implementado y probado (pruebas 9–10) | FAQ 35 | [x] |
| G10 | **[OBL]** Modo "REPRODUCCIÓN" claramente etiquetado | Banner visible (feature `replay`) | Enunc. §11 | [x] |
| G11 | Refresco ~60 s sin solapar peticiones; timeout (p. ej. 15 s); **atribución de la fuente del mapa base o de la textura (OSM u otra)** y leyenda visibles | Implementado | README | [x] |
| G12 | Usar en el panel los campos del contrato: `magType` (ficha), `country_id` y `country_name` (filtros, tabla, ficha), `truncated` (aviso), `last_ingestion` (estado), `metadata.mode` (modo) | Cada campo se muestra o condiciona la vista | CONTRATO | [x] |
| G13 | **[OBL]** Netlify: `config.json` con la URL HTTPS pública del túnel (incluido el prefijo `/api` si el cliente no lo añade) **antes de compilar**; no secretos en config | Build y deploy OK (marcado por el alumno; evidencia en repo: parte local, `config.json`, build sin mock, `netlify.toml`) | Enunc. §9 | [x] |
| G14 | Fronteras de países en el mapa a partir de `paises.geojson` (catálogo entregado, copiado a los assets del frontend); documentarlo como material reutilizado | Capa visible; origen indicado en README/memoria | FUENTES | [x] |
| G15 | **Mock del contrato**: JSON de ejemplo conforme a `CONTRATO-API.md` (con nulos, sin país, truncado y modo replay), partiendo del ejemplo del propio contrato, y selector en `config.json` (`mock` / `api`); **datos del mock marcados como sintéticos** | Se puede desarrollar el panel sin backend | Decisión propia | [x] |
| G16 | Accesibilidad mínima: tabla como alternativa, no depender solo del color, foco de teclado en el panel lateral; la vista de globo no sustituye a la tabla accesible | Revisado | Enunc. §8 | ☐ |
| G17 | **Diseño responsive:** el panel es sobre todo para PC, pero es usable en móvil (breakpoints de Tailwind; mapa, ficha y leyenda sin scroll horizontal a 375 px de ancho) | Captura a 375 px sin scroll horizontal | Decisión propia | [x] |
| G18 | **Vista de mapa 2D (MapLibre):** el botón «Ver en mapa 2D» de la ficha abre una vista plana con los eventos **ya cargados** (sin nuevas peticiones), con la misma paleta de profundidad y tamaño por magnitud que el globo, y un aviso visible si `truncated`. En `panel-base-mock` el botón está presente pero marcado como no disponible | Captura del mapa 2D con eventos del mock (y del caso `truncated` con su aviso); sin peticiones nuevas en la pestaña de red | Decisión propia | ☐ |

### H. Despliegue y defensa

| ID | Requisito | Hecho cuando… | Fuente | ☐ |
|---|---|---|---|---|
| H1 | **[OBL]** Panel Netlify accesible desde otro dispositivo | Probado | Guía 3.1 | [x] |
| H2 | **[OBL]** Procedimiento breve de activación para la defensa (Compose → API → túnel → comprobación de `/api/salud` pública → panel → replay) | En README | Guía 3.2 | [x] |
| H3 | **[OBL]** Túnel HTTPS (Cloudflare Tunnel con nombre; ngrok u otro servicio equivalente según el enunciado) que expone solo `http://localhost:8000`; el token o authtoken del túnel queda fuera de Git y del frontend | — | Enunc. §9 | ☐ |
| H4 | **[OBL]** Equipo, contenedores y túnel **encendidos** durante la demo | — | Enunc. §9 | ☐ |
| H5 | **[OBL]** Explicación individual oral: recorrido de un evento USGS → panel + **una decisión técnica propia** justificada | Preparado (apoyo: `CODEMAP.md`) | Guía 3.3 | ☐ |

### I. Pruebas de aceptación (las 11 del enunciado — ejecutarlas, no solo programarlas)

La columna "Feature" indica dónde se prueba por primera vez; la feature `pruebas-aceptacion` las formaliza todas con evidencia.

| # | Prueba | Resultado esperado | Evidencia | Feature | ☐ |
|---|---|---|---|---|---|
| 1 | Evento nuevo | 1 fila actual visible en API, mapa y análisis | SQL + captura | `productor-live` (real; parte productor hasta PostgreSQL hecha, ver `docs/evidencias/productor-live/prueba1_evento_nuevo.out`) + `pruebas-aceptacion` | ☐ |
| 2 | Reenviar la misma versión | No aumenta el recuento | SQL antes/después | `productor-live`, `consumidor-idempotente` | [x] |
| 3 | Versión posterior | Cambian datos actuales y agregaciones afectadas | SQL + captura | `consumidor-idempotente` | [x] |
| 4 | Versión antigua tardía | No sustituye a la reciente | Actual + historial | `consumidor-idempotente` | [x] |
| 5 | Magnitud nula | Se conserva, tratamiento documentado, se ve como **ND** | Captura | `geografia-pais` (+ panel) | ☐ |
| 6 | Coordenadas inválidas | Cuarentena + motivo; ningún punto inventado | Fila de cuarentena | `consumidor-idempotente` | [x] |
| 7 | Evento marítimo | "Sin país asignado"; sigue en el análisis | Captura | `geografia-pais` (+ panel) | ☐ |
| 8 | Reiniciar consumidor | Reanuda sin duplicar efectos ya persistidos | Logs + SQL | `consumidor-idempotente` | [x] |
| 9 | Cerrar el túnel | Panel muestra el fallo y conserva/identifica la última lectura | Captura del aviso | `despliegue-tunel` | ☐ |
| 10 | Reabrir el túnel | Se recupera automáticamente en el siguiente refresco | Captura | `despliegue-tunel` | ☐ |
| 11 | Reproducción histórica | Va por Kafka, aislada de live, etiquetada, con duplicados y revisiones controlados | Demo + SQL | `replay` | [x] |

(Son **11** pruebas porque "cerrar" y "volver a abrir" el túnel son dos casos distintos; no falta ninguna.)

### J. Replay histórico

| ID | Requisito | Fuente | ☐ |
|---|---|---|---|
| J1 | **[OBL]** Reproducción acelerada de una selección histórica **ordenada por fecha** | Enunc. §11 | [x] |
| J2 | **[OBL]** Mantener el tiempo original **y** añadir el de reproducción | Enunc. §11 | [x] |
| J3 | **[OBL]** Topic y esquema/tablas **separados** (o aislamiento equivalente) | Enunc. §11 | [x] |
| J4 | **[OBL]** Etiqueta "REPRODUCCIÓN" | Enunc. §11 | [x] |
| J5 | **[OBL]** El productor de replay **reutiliza el procesamiento del consumidor** | Enunc. §11 | [x] |
| J6 | **[OBL]** Incluye duplicados y revisiones controlados (secuencia de FAQ 12) | Enunc. §11 | [x] |
| J7 | **[OBL]** No cambiar fechas originales; la vista de replay debe consultar el intervalo de 2025, no "últimas 24 h" | FAQ 32 | [x] |
| J8 | Documentar: selección, cómo iniciar, velocidad, aislamiento, cómo se ve el modo, resultado observado | Guía 2.9 | [x] |

### K. Complejidad, mediciones, costes

| ID | Requisito | Fuente | ☐ |
|---|---|---|---|
| K1 | **[OBL, EVAL]** Justificar ≥3 operaciones: búsqueda de versiones por id, integración geográfica, agregación por ventanas; coste medio vs peor caso | Enunc. §10 | ☐ |
| K2 | **[OBL]** Medir **tiempo y memoria** con ≥3 tamaños de entrada; indicar equipo, procedimiento, unidades | Enunc. §10 | ☐ |
| K3 | **[OBL]** Comparar búsqueda secuencial vs diccionario **o** consulta sin/con índice | Enunc. §10 | ☐ |
| K4 | **[OBL]** Si replicas datos para escala: marcarlos **sintéticos**, fuera del análisis real | Enunc. §10 | ☐ |
| K5 | **[OBL]** Razonar qué pasaría con **100 millones** de registros | Enunc. §10 | ☐ |
| K6 | **[OBL]** Costes: hardware, electricidad, almacenamiento, transferencia, mantenimiento, tiempo de desarrollo; distinguir **medido vs supuesto**; cuota gratuita ≠ coste cero | Enunc. §10 | ☐ |
| K7 | **[OBL]** Propuesta de escalado + mejoras ligadas a problemas concretos (no genéricas) | Enunc. §10 · Guía 2.7 | ☐ |
| K8 | **[OPC]** ROI (solo si defines un beneficio medible; no inventar) | Enunc. §10 | ☐ |

### L. Memoria / notebook (un solo documento, no nueve)

Índice recomendado (todo en `docs/memoria.md` o `notebooks/memoria.ipynb`):

| § | Contenido | ☐ |
|---|---|---|
| 1 | Objetivo, flujo de datos, alcance (periodo, ámbito, filtros) | ☐ |
| 2 | Diccionario de datos (significado, tipo/unidad, tratamiento de ausencias; conversión ms→UTC) | ☐ |
| 3 | Procedencia y registro de consultas (URL, filtros, fecha, nº registros, hash del catálogo) | ☐ |
| 4 | Calidad (ver D) | ☐ |
| 5 | Modelo conceptual/lógico/físico + índices (con equivalencia de nombres con el enunciado, E3) | ☐ |
| 6 | Análisis y ≥3 conclusiones (periodo, ámbito, filtros, denominador, capturas con filtros visibles) | ☐ |
| 7 | Complejidad, mediciones, costes, mejoras | ☐ |
| 8 | Evidencias de las 11 pruebas (esperado / observado / evidencia / cómo repetir) | ☐ |
| 9 | Reproducción histórica | ☐ |
| 10 | Limitaciones (retiradas/fusiones de eventos, mapa simplificado, mag. por tipo, instantánea del histórico) | ☐ |

Reglas de las conclusiones: interpretar, no solo mostrar; con cifras; **sin lenguaje de predicción ni riesgo**; filtros equivalentes entre periodo reciente e histórico (si el histórico es M≥4, el reciente también).

### M. Repositorio

| ID | Requisito | ☐ |
|---|---|---|
| M1 | **[OBL]** Código: productor, consumidor, API, frontend, carga histórica y replay | ☐ |
| M2 | **[OBL]** Distinguir material reutilizado de lo desarrollado/modificado. Reutilizado: `paises.geojson` (catálogo entregado), teselas OSM, librerías (Chart.js…), la librería de mapa elegida y la textura o teselas usadas. El frontend de ejemplo del paquete **no** es base del trabajo: si se toma alguna idea o fragmento, indicarlo | ☐ |
| M3 | **[OBL]** README reproducible (requisitos y versiones, `.env`, build/up, tablas y carga histórica, estado/logs, frontend dev y publicación, ngrok y URL, pruebas y replay, parar y qué datos persisten, dónde está cada evidencia) | ☐ |
| M4 | **[OBL]** El profesor tiene acceso al repo | ☐ |
| M5 | **[OBL]** NO subir `node_modules`, secretos, authtoken ngrok, volúmenes de BD ni descargas grandes regenerables (`data/raw/`); documentar dónde van los originales y cómo regenerarlos | ☐ |
| M6 | Estructura (ver 03 §3): `README.md`, `docs/memoria.md`, `docs/evidencias/`, `docs/enunciado/` (solo lectura), `docs/planificacion/`, `sql/`, un directorio por servicio (las carpetas de servicio se crean cuando su feature se implementa) | ☐ |
| M7 | Historial de Git sin trailers de coautoría ni líneas de "generado por" herramientas (commits y PRs): constitución + `.claude/settings.json` + hook `commit-msg`; comprobado con `git log` | [x] |
| M8 | `CLAUDE.md`, `CODEMAP.md` y la constitución (`.specify/`) versionados y al día; `docs/` (entregables) separado de `specs/` (herramienta de trabajo) | [x] |
| M9 | `docs/enunciado/` incluido tal cual y **sin modificar** (el `README.md` del paquete renombrado a `README-paquete.md`); `data/catalogo/paises.geojson` con su SHA-256 verificado | [x] |

---

## 3. Qué viene hecho y qué no

| Ya entregado | Hay que construirlo |
|---|---|
| `paises.geojson` (177 entidades, SHA-256 en `FUENTES-Y-LICENCIAS.md`) | Todo el backend (Dockerfiles, `compose.yaml`, productor, consumidor, PG, API) |
| `CONTRATO-API.md` (contrato **mínimo**: `/api/eventos` con ejemplo; `/api/salud` y `/api/estadisticas` solo con su contenido) | Integración espacial en Python |
| `ENUNCIADO`, FAQ, guía de entregables, `VALIDACION.md`, `FUENTES-Y-LICENCIAS.md` | Implementar `/api/eventos`, `/api/salud`, `/api/estadisticas` y decidir lo que el contrato deja abierto |
| Ejemplo de frontend (Angular + Leaflet, 4 eventos ficticios): **solo referencia, no es tu base** | **Todo el frontend desde cero** (React + TypeScript + Vite + Tailwind): proyecto, mapa, fronteras, filtros, tabla, gráficos, comparación histórica, estado del sistema, modo replay, mock del contrato |
| — | Datos reales, histórico, replay por Kafka |
| — | Memoria, mediciones, costes, pruebas con evidencias, defensa |

Límites del material de ejemplo (de `VALIDACION.md`): nunca se probó visualmente en navegador ni con Netlify/ngrok reales. Aplica también a lo que tomes de él como idea: compruébalo tú.

---

## 4. Lo que NO tienes que hacer (ahorra tiempo)

- Spark, Flink, Kubernetes, ML, servidor cloud permanente.
- Generador automático de informes de calidad, panel de calidad en el frontend, tabla de métricas de calidad.
- Documento separado por cada apartado, ni documento aparte para la explicación individual.
- Motor cartográfico propio; certificados TLS en FastAPI; transacción distribuida Kafka–PG.
- Disponibilidad 24/7; contratar servicios; estudio empresarial; ROI.
- Reconciliación exhaustiva de eventos eliminados/fusionados (solo documentar la limitación).

---

## 5. Puntos ambiguos o por confirmar con el profesor

1. ~~Fecha de entrega y modalidad~~ **Resuelto:** trabajo **individual**, entrega el **19 de noviembre de 2026**. Al ser individual, la explicación oral (H5) la defiendes tú entero: debes poder explicar todo el flujo, no solo una parte.
2. **Dónde vive el histórico 2025**: ¿mismo esquema `live` que el feed (necesario para la comparación) o esquema propio? El enunciado no lo fija. Propuesta del roadmap: mismo esquema, columna `source`, y justificarlo.
3. **Gráficos en el panel**: no se menciona librería; asumir que una dependencia fijada (p. ej. Chart.js) es válida, o SVG propio. Confirmar si importa.
4. **Cobertura "últimas 24 h" en replay**: la vista de replay debe usar el intervalo de 2025; confirmar que el selector de modo en el panel es aceptable.
5. **Dominio ngrok**: el gratuito puede cambiar entre sesiones y `config.json` se compila en el build → comprobar si tu cuenta permite un dominio estático para no recompilar Netlify cada vez.
6. **Tamaño máximo de puntos por respuesta** (truncado/paginación): lo fijas tú, pero debe estar documentado.
7. **Inconsistencia menor**: la FAQ menciona `ENUNCIADO.md` y `README.md` del paquete; tu carpeta ya los tiene todos. La guía de entregables no está en la carpeta (solo la subiste al chat): guárdala como `Guia-entregables.md` en `docs/enunciado/`.
8. **Uso del frontend de ejemplo**: se asume que hay que desarrollar el panel desde cero y que el ejemplo es solo referencia. Si el profesor permite partir de él, G0 y parte de G2/G11 se simplifican; en ese caso indicarlo en M2.
9. **Framework del frontend y librería de mapa**: ~~librería del mapa~~ **Resuelto:** es libre (confirmación del profesor por correo, 2-nov-2026; Leaflet era una guía, no una obligación). ~~Framework~~ **Resuelto:** el profesor permite cambiar Angular por otro; decisión del alumno: React + TypeScript + Vite + Tailwind. Fijar las versiones estables vigentes (Node, React, Vite, librería de mapa) en el plan de la feature `panel-base-mock` y documentarlas.
10. **Identificadores en inglés** (tablas, columnas, topics, código) frente a los nombres en español de la estructura orientativa del enunciado (E3): se asume válido si se justifica y se documenta la equivalencia. Confirmar si importa.
11. **Decisiones propias que el contrato mínimo deja abiertas**: forma de `/api/salud` y `/api/estadisticas`, paginación, límite de puntos y parámetro `mode`. Se documentan en `specs/001-contratos-y-modelo/contracts/api.md`; confirmar con el profesor solo si hay duda sobre alguna.
12. **Spec Kit**: los comandos y flags cambian entre versiones; la fuente de verdad es `specify --help` (03 §2). Anotar la versión usada en el README.
13. **Calendario**: quedan ~18 días desde el 1-nov hasta el 19-nov; ver calendario orientativo en el roadmap §5 y la opción de fusionar features (03 §4).

---

## 6. Antes de entregar (lista final combinada de guía + FAQ)

- [ ] El profesor accede al repo y el README arranca desde un entorno limpio.
- [ ] Los 5 servicios definidos y sanos; datos persisten tras reiniciar.
- [ ] Datos reales con procedencia y originales conservados.
- [ ] Repetir mensaje no duplica; revisión antigua no sustituye a la nueva.
- [ ] Hay registros sin país y nulos tratados con justificación.
- [ ] API consulta PG; el panel React consulta la API; filtros coherentes mapa/tabla/gráficos.
- [ ] Comparación histórica con mismos filtros y periodos comparables.
- [ ] Panel abre desde otro dispositivo con túnel activo; si falla, lo indica.
- [ ] Replay aislado y etiquetado.
- [ ] Memoria con calidad, modelo, análisis, mediciones y costes; 11 pruebas ejecutadas con evidencia.
- [ ] Sin credenciales ni `node_modules` en Git; historial sin trailers de coautoría (`git log`).
- [ ] Material reutilizado (catálogo, librerías) distinguido del desarrollado por mí.
- [ ] `CODEMAP.md` al día y `docs/enunciado/` sin modificar.
- [ ] Puedo explicar un evento de principio a fin y una decisión propia.

---

## 7. Trazabilidad: IDs → features de Spec Kit

Fuente de verdad de las features: `03-procedimiento-ejecucion.md` §4. Se usa el **nombre** de la feature, no el número (la numeración la asigna Spec Kit por orden de creación).

| IDs | Feature |
|---|---|
| E1–E5, E7; contrato Kafka, esquema BD y `api.md` | `contratos-y-modelo` |
| A1–A12; M7–M9 (configuración de Git y estructura) | `infra-compose` (y F0 a mano) |
| B1–B12 | `productor-live` |
| C1–C8, C13 | `consumidor-idempotente` |
| C9–C12 | `geografia-pais` |
| B13–B18 | `historico-2025` |
| F1–F11 (F12 con `replay`) | `api` |
| G0, G1, G2, G3, G4, G5, G5b, G6, G7, G8, G9, G11, G14, G15, G17; G12 (`magType`, `country_id`, `country_name`, `truncated`, `last_ingestion`) | `panel-base-mock` (enmendada el 10-nov-2026: absorbe las cuatro features siguientes) |
| G6, G8, G16; G12 (`country_id`, `country_name`, `truncated`) | `panel-filtros-tabla` — **absorbida por `panel-base-mock`** (G16 no cubierta, decisión propia) |
| G3, G4, G5, G5b | `panel-graficos-comparacion` — **absorbida por `panel-base-mock`** |
| G7, G9; G12 (`last_ingestion`) | `panel-estado-fallos` — **absorbida por `panel-base-mock`** |
| G1 | `panel-conexion-api` — **absorbida por `panel-base-mock`** |
| G18 | `panel-mapa-2d` — **aplazada** |
| J1–J8, G10, F12; G12 (`metadata.mode`) | `replay` |
| Tabla I (las 11 pruebas) | `pruebas-aceptacion` (se prueban antes en `productor-live`, `consumidor-idempotente`, `geografia-pais`, `replay` y `despliegue-tunel`) |
| G13, H1–H4; pruebas 9 y 10 | `despliegue-tunel` |
| K1–K8, E6 | `mediciones-costes` |
| Bloque L, D y C14 (calidad), B2/B11/B12/B18 (texto), H5, M1–M6 | `memoria-defensa` (el contenido se prepara en `notebooks/` y `docs/memoria.md` desde las features anteriores) |
| M1, M3 (README), M8 | Todas las features (cada una deja README y `CODEMAP.md` al cerrarse) |
