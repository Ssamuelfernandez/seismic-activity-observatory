# Observatorio de actividad sísmica — Roadmap de implementación (para dirigir a un agente)

Complementa `01-checklist-requisitos.md` (los IDs A1, B6, C4… remiten a él) y `03-procedimiento-ejecucion.md` (cómo se trabaja, features de Spec Kit, constitución, reglas de código). Cada fase termina con una **evidencia visible** y una **verificación**; no se pasa a la siguiente sin cumplirlas. Es la versión ampliada del itinerario de 11 pasos de la FAQ (pregunta 6).

**Registro de cambios**
- 31-oct-2026 (rev. 2): el frontend se construye desde cero; F1 pasa a ser exploración de USGS; F8 se divide en F8a–F8e; mock del contrato.
- 1-nov-2026 (rev. 3): **reconciliación con `03-procedimiento-ejecucion.md`.** Cada fase indica su feature de Spec Kit (la tabla única vive en 03 §4; las "semillas de spec" se movieron allí). Se añade **F1b** (feature `contratos-y-modelo`, antes de la infraestructura). Identificadores de BD, topics, scripts y módulos en inglés. Estructura del repo alineada con 03 §3. Panel: la parte de replay pasa a F9; F8d queda en estado y fallos. Calendario orientativo hasta el 19-nov (§5).
- 2-nov-2026 (rev. 4): la librería del mapa es libre (el profesor confirmó por correo el 2-nov-2026 que Leaflet era una guía, no una obligación). Candidata: Globe.gl; alternativas: MapLibre o Leaflet; se decide en el plan de `panel-base-mock` tras un prototipo corto. Afecta a §0, §1 (Frontend: mapa), F8a y riesgos (§4).

---

## 0. Contexto fijo para el agente

*(Claude Code ya lee `CLAUDE.md` y la constitución; este resumen sirve para sesiones fuera de Claude Code o para recordar el contexto.)*

**Objetivo.** Sistema que ingiere terremotos de USGS (feed reciente + histórico 2025 M≥4) y los integra con un catálogo de países, y responde: *¿dónde hay actividad sísmica y cómo se compara con un periodo histórico equivalente?*

**Arquitectura obligatoria (Docker Compose, 5 servicios):** `producer` (Python+aiokafka) · `kafka` · `consumer` (Python+aiokafka) · `postgres` · `api` (FastAPI). Fuera de Compose: ngrok (HTTPS a la API) y el panel **Angular + librería de mapa a decidir, construido desde cero**, en Netlify. El `paises.geojson` y el `CONTRATO-API.md` (contrato mínimo) del profesor son la única base entregada; el frontend de ejemplo del paquete es solo referencia.

**Reglas no negociables:** la fuente de verdad es la **constitución** (borrador en 03 §5; si difiere de esta lista, manda la constitución). Las más críticas:
1. Procesamiento *al menos una vez* + escritura **idempotente**; offset de Kafka confirmado **después** del commit en PostgreSQL.
2. Una versión con `updated` menor o igual **nunca** sustituye a una mayor. Un evento = una fila actual.
3. `updated`/`time` en **milisegundos Unix**; convertir a UTC conservando el original.
4. País por **punto dentro de polígono** (EPSG:4326, `ADM0_A3`), nunca desde `place`; sin polígono → `NULL`.
5. Nunca rellenar nulos con 0; magnitud o profundidad negativas no se rechazan solo por serlo.
6. Datos inválidos → **cuarentena** con motivo y referencia al original.
7. Entre contenedores, nombres de servicio; solo la API se expone; sin secretos en Git ni en Angular.
8. Datos sintéticos / de prueba / mock **etiquetados** y separados de los reales.
9. Identificadores en inglés; docstrings y comentarios en español.
10. El frontend no calcula estadísticas: consume `/api/estadisticas`.
11. `docs/enunciado/` es solo lectura.
12. Una feature cada vez, con spec/plan/tareas revisados antes de implementar; sin commits ni merges sin aprobación; **sin trailers de coautoría ni líneas de "generado por" herramientas de IA**.
13. No ampliar alcance: nada de Spark/Flink/K8s/ML, ni informes de calidad automáticos, ni panel de calidad. Sin lenguaje de predicción ni riesgo.

**Definición de "hecho" de una fase:** código + prueba ejecutada + evidencia guardada en `docs/evidencias/<feature>/` + README y `CODEMAP.md` actualizados + borrador de memoria al día + checklist marcado.

---

## 1. Decisiones de diseño propuestas (se confirman en la feature `001-contratos-y-modelo`)

| Tema | Propuesta | Por qué / alternativa |
|---|---|---|
| Topics | `earthquakes.live` y `earthquakes.replay`, 1 partición (orden por clave garantizado), retención 7 días (`log.retention.hours=168`) | Simple y justificable; el orden por clave no sustituye la comparación de `updated` |
| Aislamiento replay | Esquemas PostgreSQL `live` y `replay` con las **mismas tablas**; el consumidor enruta por `mode` del mensaje | Cumple "topic y esquema separados"; `country` y `date_dim` compartidas en `public` |
| Histórico 2025 | Se carga en el esquema `live` con columna `source ∈ {feed, historical}`; datos sintéticos con `is_synthetic = true` | Necesario para comparar con las últimas 24 h; el replay lo toma de los **archivos** descargados y va a `replay` |
| Carga del histórico | Proceso batch que importa `common.processing.process_event()` (misma lógica del consumidor) | Más rápido que Kafka para ~miles de eventos; **documentar la elección** (FAQ 21) |
| Lógica compartida | Paquete `common/` (validación, conversión de tiempos, asignación de país, SQL de upsert) usado por consumidor, carga histórica y tests (estructura en 03 §7.1) | Garantiza "mismas reglas" (B16) y "replay reutiliza el procesamiento" (J5) |
| País | Cargar `paises.geojson` en GeoPandas al arrancar, índice espacial (`STRtree`); `covers` para fronteras; si hay varias coincidencias, elegir `ADM0_A3` menor y contarlo en log | Regla documentada (C11) |
| Estado productor | Esquema `ingest`: tabla `ingest_state(event_id PK, last_updated_ms, published_at)` + `ingest_run` (ts, url, status, latency_ms, event_count, sha256, error) | Sobrevive a reinicios (B6, B15) |
| Originales | Tabla `ingest.raw_response(id, fetched_at, sha256, body jsonb)` insertando solo si el hash difiere del anterior; purga por antigüedad | Cumple B4–B5 (retención definida) |
| Estadísticas | Todas calculadas en SQL sobre `current_event` | Reflejan revisiones sin contadores incrementales (FAQ 22) |
| Frontend: base | Proyecto Angular nuevo (`ng new`, standalone components, versión estable vigente fijada en el plan de `panel-base-mock`) en `frontend/`, build de producción para Netlify | Se construye desde cero; el ejemplo del paquete solo se consulta |
| Frontend: mapa | Librería libre (el profesor confirmó por correo el 2-nov-2026 que Leaflet era una guía, no una obligación). Candidata: Globe.gl; prototipo corto con unos 5.000 eventos del mock antes de fijarla (clic, leyenda, nulos como ND). Mapa en un componente aislado que recibe eventos y emite el seleccionado. Ocultar la Antártida (`ADM0_A3 = ATA`) en el globo. Plan B: Leaflet o MapLibre. Fronteras desde `paises.geojson` copiado a los assets (material reutilizado, G14). Se decide en el plan de `panel-base-mock` | Menos dependencias = menos riesgo de incompatibilidad con la versión de Angular; el componente aislado permite cambiar de librería |
| Frontend: estado | Un servicio único de filtros (signals o RxJS) del que leen mapa, tabla, gráficos y panel lateral | Garantiza coherencia entre vistas (G6) |
| Frontend: datos | `ApiService` con timeout, refresco ~60 s sin solapar peticiones, conservación de la última lectura y fuente seleccionable por `config.json` (`mock` \| `api`) | Permite desarrollar sin backend (G15) y probar fallos (G9) |
| Gráficos Angular | Chart.js (versión fijada); empezar por el gráfico de dos barras del panel lateral y reutilizar el componente para el resto | Primer gráfico simple para calibrar; el resto reutiliza el componente |
| Forma de `/salud`, `/estadisticas`, paginación, límite de puntos, `mode` | Decisión propia, documentada en `specs/001-contratos-y-modelo/contracts/api.md` (el contrato mínimo del profesor no los define) | Ver 03 §4.1 |
| Modalidad / fecha | Individual · entrega 19-nov-2026 (quedan ~18 días desde el 1-nov) | Priorizar núcleo en la primera semana y empezar el panel contra mock en paralelo; calendario en §5 |
| ngrok | En el host (`ngrok http 8000`) con puerto `127.0.0.1:8000:8000` | Más simple; el token queda fuera del repo |

### Estructura objetivo del repositorio (las carpetas nacen con su feature)

La estructura completa está en **03 §3**. Resumen: `docs/{enunciado,planificacion,evidencias}/` + `docs/memoria.md` · `data/catalogo/paises.geojson` (versionado) y `data/raw/` (ignorado) · `common/ producer/ consumer/ api/ frontend/ sql/ scripts/ notebooks/ tests/` · `compose.yaml .env.example .gitignore README.md CLAUDE.md CODEMAP.md` · `.specify/ .claude/ specs/`.

### Esquema SQL orientativo (esquemas `live` y `replay` idénticos)

```sql
-- public
CREATE TABLE country (country_id text PRIMARY KEY, name_es text, admin text, continent text, subregion text);
CREATE TABLE date_dim (date_id date PRIMARY KEY, year int, month int, day int, dow int);

-- por esquema (live | replay)
CREATE TABLE current_event (
  event_id text PRIMARY KEY,
  event_time timestamptz NOT NULL,
  updated_ms bigint NOT NULL,
  updated_at timestamptz NOT NULL,
  mag numeric, mag_type text, depth_km numeric,
  lon double precision NOT NULL, lat double precision NOT NULL,
  place text, country_id text REFERENCES public.country, date_id date REFERENCES public.date_dim,
  source text NOT NULL,            -- feed | historical | replay
  is_synthetic boolean NOT NULL DEFAULT false,
  ingested_at timestamptz NOT NULL, replay_at timestamptz
);
CREATE TABLE event_version (
  event_id text NOT NULL, updated_ms bigint NOT NULL,
  mag numeric, depth_km numeric, event_time timestamptz, original jsonb NOT NULL,
  received_at timestamptz NOT NULL, kafka_partition int, kafka_offset bigint,
  PRIMARY KEY (event_id, updated_ms)
);
CREATE TABLE quarantine (id bigserial PRIMARY KEY, event_id text, reason text NOT NULL,
  original jsonb NOT NULL, received_at timestamptz NOT NULL, is_synthetic boolean DEFAULT false);
CREATE TABLE exclusion (id bigserial PRIMARY KEY, event_id text, reason text NOT NULL, kind text, fetched_at timestamptz);

-- esquema ingest (productor)
CREATE TABLE ingest.ingest_state (event_id text PRIMARY KEY, last_updated_ms bigint NOT NULL, published_at timestamptz NOT NULL);
CREATE TABLE ingest.ingest_run (id bigserial PRIMARY KEY, run_at timestamptz NOT NULL, url text, status int, latency_ms int, event_count int, sha256 text, error text);
CREATE TABLE ingest.raw_response (id bigserial PRIMARY KEY, fetched_at timestamptz NOT NULL, sha256 text NOT NULL, body jsonb NOT NULL);
-- índices (justificar con EXPLAIN ANALYZE): event_time, country_id, mag
```

Equivalencia con la estructura orientativa del enunciado (E3), a documentar en la memoria: `evento_actual` = `current_event`; `evento_version` = `event_version`; `pais` = `country`; `fecha` = `date_dim`; cuarentena = `quarantine`.

Upsert de estado actual (núcleo de idempotencia):

```sql
INSERT INTO event_version (...) VALUES (...) ON CONFLICT (event_id, updated_ms) DO NOTHING;
INSERT INTO current_event (...) VALUES (...)
ON CONFLICT (event_id) DO UPDATE SET ... WHERE EXCLUDED.updated_ms > current_event.updated_ms;
```

### Contrato de mensaje Kafka

```json
{ "source": "usgs_feed | usgs_historical | replay_demo", "mode": "live | replay",
  "ingested_at": "2026-11-01T12:00:00Z", "replay_at": null, "event": { /* Feature GeoJSON original */ } }
```
Clave = `event.id`.

---

## 2. Fases

Cada fase indica la **feature de Spec Kit** que la ejecuta (tabla única en 03 §4; usar el nombre, no el número).

Dependencias de backend: `F0 → F1 → F1b → F2 → F3 → F4 → F5 → F7`. `F6` (histórico) puede empezar tras F1 y debe estar listo antes de F8c. `F9` (replay) tras F5. `F12` (mediciones) tras F7 con datos cargados.
Dependencias de frontend: `F8a` (esqueleto + mapa contra mock) solo necesita el `CONTRATO-API.md` y `002-infra-compose`; `F8b–F8d` siguen contra el mock; `F8e` **reconecta a la API real** al terminar F7. La memoria se redacta **a medida que avanzas**, no al final.

### F0 — Repositorio, documentación y Spec Kit (sin feature, a mano)
- Seguir 03 §2 (paso 0 y arranque): repo privado con acceso al profesor; `docs/enunciado/` (paquete completo, solo lectura), `docs/planificacion/` (01, 02 y 03), `data/catalogo/paises.geojson` (sin modificar), `.gitignore` (node_modules, `.env`, `data/raw/`, `.venv/`, `__pycache__/`, volúmenes, token ngrok), `README.md` mínimo. **No** crear aún carpetas de servicio ni copiar el frontend de ejemplo.
- Comprobar herramientas: git, Python ≥3.11, uv, Node LTS, Docker Desktop. Primer commit manual, sin trailers de coautoría.
- Instalar la CLI de Spec Kit, `specify init . --integration claude` (o `--ai claude` en versiones antiguas; ver `specify init --help`), revisar lo generado y commit.
- `/speckit.constitution` con el borrador de 03 §5; crear `CLAUDE.md` (03 §9) y `CODEMAP.md` vacío (03 §7.6); configurar la no-atribución en `.claude/settings.json` y el hook `commit-msg` (03 §2); commit de prueba y `git log -1`.
- Esqueleto de `docs/memoria.md` con el índice de la checklist §L.
- **Verificación:** `git status` limpio de secretos; el commit de prueba no lleva trailers. **Cubre:** M1 (parcial), M5–M9.

### F1 — Explorar USGS y leer el contrato (sin feature: script suelto)
- `scripts/explore_usgs.py`: descargar una respuesta de `all_day.geojson` y explorarla (campos, nulos, `type` distintos de `earthquake`, tipos, unidades, latencia).
- Leer `CONTRATO-API.md` completo y anotar las decisiones que el contrato mínimo deja abiertas (03 §4.1); opcional (≤30 min): abrir el frontend de ejemplo solo para ver qué muestra, sin copiarlo.
- Empezar la tabla de **tipos/unidades** y el **diccionario de datos** (borrador).
- **Evidencia:** salida del script + borrador del diccionario. **Cubre:** B2, parte de Extracción.

### F1b — Contratos y modelo (feature `001-contratos-y-modelo`)
- Produce `specs/001-contratos-y-modelo/contracts/` (`kafka-message.md`, `db-schema.md`, `api.md`) a partir de las propuestas de §1, y `sql/001_schema.sql` (DDL de §1 con índices candidatos).
- `api.md` parte del `CONTRATO-API.md` y decide: forma de `/api/salud` y `/api/estadisticas`, paginación y límite de puntos, parámetro `mode`, `country_name`.
- Borrador de los modelos conceptual, lógico y físico para `docs/memoria.md` §5.
- **Verificación:** `/speckit.analyze` (o revisión manual) sin incoherencias entre contratos; el DDL se valida formalmente al aplicarlo en F3. **Cubre:** E1–E5, E7, regla C4 en diseño.

### F2 — Compose base y "hola mundo" end-to-end (feature `002-infra-compose`)
- `compose.yaml` con `kafka` (KRaft, listeners interno `kafka:9092` y opcional externo), `postgres` (volumen), healthchecks; imagen Python compartida para `producer`/`consumer`/`api` con comandos distintos; `depends_on: condition: service_healthy` + reintentos en código.
- Productor mínimo que publica un evento ficticio **marcado como sintético**; consumidor mínimo que lo imprime.
- **Verificación:** `docker compose up --build -d` desde cero; el log del consumidor muestra el mensaje; reiniciar contenedores y comprobar que PG conserva datos (volumen). **Cubre:** A1–A12.

### F3 — Base de datos y consumidor idempotente (feature `004-consumidor-idempotente`)
- Aplicar `sql/001_schema.sql` al iniciar (idempotente), carga del catálogo `country`/`date_dim`.
- Consumidor: `enable_auto_commit=False`; por mensaje: validar → transformar (ms→UTC) → transacción (insert versión `DO NOTHING` + upsert condicional) → commit PG → commit offset. Mensaje inválido → `quarantine` + commit offset. Reintentos de conexión PG/Kafka.
- Reproducir **la secuencia de la FAQ 12** con mensajes sintéticos (E1 10:05 mag 4.2 → repetición → E1 10:09 mag 4.6 → E1 10:05 repetida → E2).
- **Verificación esperada:** 2 eventos actuales, E1 mag 4.6, 3 versiones. Test automático (pytest) + consulta SQL como evidencia. **Cubre:** C1–C5, C8, C13 (pruebas 2, 3, 4, 6, 8).

### F4 — Productor real (feature `003-productor-live`)
- Bucle cada `POLL_SECONDS` (env): GET con timeout → guardar `ingest_run` y `raw_response` (por hash) → filtrar `type=="earthquake"` y registrar `exclusion` → comparar con `ingest_state` → publicar `send_and_wait` (acks=all, idempotencia, clave=id) → marcar publicado **tras** el ack.
- Errores: timeout, 429/5xx con backoff exponencial y jitter, JSON inválido; sin tocar `ingest_state` previo.
- Arranque robusto: reintentos hasta que Kafka esté listo.
- **Verificación:** el segundo ciclo publica ≈0 eventos nuevos; matar y reiniciar el productor no republica; simular 500/429/timeout (mock) y comprobar logs y estado. **Cubre:** B1–B12, A10 (pruebas 1 real y 2).
- *Nota de orden:* en Spec Kit `003` se ejecuta antes que `004`; esta fase F4 puede probarse con un consumidor mínimo hasta que F3 esté lista.

### F5 — Catálogo de países y calidad en el consumidor (feature `005-geografia-pais`)
- `common/geo.py`: carga, `STRtree`, `covers`, regla de empates, test de unicidad `ADM0_A3`.
- Reglas de validez: tipo `Point`, lon/lat finitos en rango, `time` y `updated` presentes y parseables, `mag` nula permitida; profundidad/magnitud negativas permitidas.
- Casos sintéticos etiquetados: mag nula, coordenadas inválidas (lat 145), punto marítimo, tipo no-earthquake.
- **Verificación:** evento en Madrid → `ESP`; punto en el Atlántico → `NULL`; lat 145 → cuarentena con motivo. **Cubre:** C9–C12 (pruebas 5, 7).

### F6 — Histórico 2025 (feature `006-historico-2025`; puede ir en paralelo desde F1)
- Script `scripts/download_historical.py`: 12 meses, `minmagnitude=4`, `eventtype=earthquake`, `orderby=time-asc`; si `count>20000`, dividir; guardar cada archivo con nombre `usgs_2025-MM.geojson`, `manifest.json` (URL, fecha de extracción, nº registros, sha256).
- Deduplicar por `id` entre intervalos; contrastar el total contra la consulta `count` de USGS si procede.
- Cargador `scripts/load_historical.py` que usa `common.processing.process_event()` y escribe en `live` con `source='historical'`. Documentar la elección (batch vs Kafka).
- Documentar el procedimiento para recuperar un hueco de >24 h con este mismo mecanismo (B12).
- **Verificación:** nº de eventos en BD = nº únicos de archivos − cuarentena; recarga repetida no duplica. **Cubre:** B13–B18.

### F7 — API FastAPI (feature `007-api`)
- `/api/eventos` (filtros `start`, `end`, `min_mag`, `country_id`, `mode`, `limit`, `cursor`; default últimas 24 h; `metadata` completo; `truncated` con total y paginación; `properties` con `mag`, `magType`, `place`, `time`, `updated`, `country_id`, `country_name`), `/api/salud`, `/api/estadisticas` (mismos filtros). Forma de respuesta según `api.md` (F1b).
- `/api/estadisticas` devuelve: conteos por hora UTC (ventana `[h, h+1)`, tiempo del evento), por país (incluyendo `null`), histogramas de magnitud y profundidad con `sin_valor`, comparación histórica (`n_reciente`, `media_diaria_2025 = n_2025/365`, `variacion_pct` o `null`), periodo, filtros, unidades.
- CORS exacto + `localhost:4200` + cabecera ngrok; BD caída → 503 con mensaje (no `[]`).
- **Verificación:** tests con `httpx`; `curl` de cada endpoint; parar PG y comprobar el 503; evento con mag nula excluido por `min_mag` pero contado aparte. **Cubre:** F1–F11.

### F8 — Frontend Angular desde cero (cinco features)

El panel se construye en cinco bloques. Primero se trabaja contra el **mock del contrato** (G15) y al final se reconecta a la API real. Estructura de carpetas en 03 §7.5.

**F8a — Esqueleto + mapa contra mock (feature `008-panel-base-mock`)**
- Crear el proyecto Angular en `frontend/` (versión estable fijada en el plan, lock, `npm ci && npm start` y `npm run build` funcionando). Estructura: `core/` (api.service, config.service, filters.service), `features/` (map, events-table, charts, filters, system-status, historical-panel), `shared/`.
- `public/config.json` con `mode: mock|api`, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`; se lee en tiempo de ejecución.
- Mock en `frontend/mock/` conforme a `CONTRATO-API.md` (casos: mag nula, sin país, truncado, modo replay, intervalo vacío), **marcado como sintético**.
- Mapa o globo con la librería elegida: fondo con atribución de su fuente, capa de fronteras (`paises.geojson` desde `data/catalogo/`), círculos (tamaño ∝ magnitud, color ∝ profundidad, ND para nulos), popup con ficha (incluye `magType`), leyenda.
- **Verificación:** ver el mapa con los casos del mock en el navegador; captura. **Cubre:** G0, G2, G11, G14, G15, G12 (`magType`).

**F8b — Filtros, tabla y estado único (feature `009-panel-filtros-tabla`)**
- `filters.service` único (fechas, magnitud mínima, país/región) compartido por todas las vistas; tabla de eventos ordenable y accesible; uso de `country_id`, `country_name` y `truncated` (aviso, sin estadísticas sobre muestra truncada).
- **Verificación:** al cambiar un filtro, mapa y tabla cambian a la vez; truncado visible. **Cubre:** G6, G8, G16, G12 (`country_id`, `country_name`, `truncated`).

**F8c — Gráficos y panel lateral de comparación histórica (feature `010-panel-graficos-comparacion`)**
- Chart.js (versión fijada). Primer componente: gráfico de dos barras (reciente vs media 2025) dentro del **panel lateral de comparación histórica** (decisión del alumno): columna fija a la derecha del mapa (debajo en pantallas estrechas) con nº de eventos M≥4 en las últimas 24 h para la zona/país y filtros activos, media diaria 2025 (`n_2025 / 365`, incluyendo días con cero), diferencia absoluta, variación % (ND si la media es 0) y aviso "el periodo reciente puede estar incompleto". Se actualiza al cambiar los filtros; es un panel anclado (no ventana flotante) porque no tapa el mapa y es accesible con teclado. Los datos salen de `/api/estadisticas`; el frontend no calcula nada.
- Reutilizar el componente de gráfico para: recuento por hora UTC, recuento por país (con "Sin país asignado"), distribuciones de magnitud y profundidad con registros sin valor.
- **Verificación:** gráficos coherentes con la tabla al cambiar filtros; capturas con filtros visibles. **Cubre:** G3, G4, G5, G5b.

**F8d — Estado del sistema y fallos (feature `011-panel-estado-fallos`)**
- Barra de **estado del sistema**: última lectura correcta de la API, `generated`, `last_ingestion`, periodo consultado, aviso de desactualización por umbral y error de backend; refresco ~60 s sin solapar peticiones, timeout, conservación e identificación de la última lectura (no presentarla como reciente).
- **Verificación:** simular API caída en el mock (y luego con ngrok real en F11) y comprobar aviso + recuperación. **Cubre:** G7, G9, G12 (`last_ingestion`).

**F8e — Conexión con la API real (feature `012-panel-conexion-api`)**
- Cambiar `config.json` a `mode: api` (dev: `http://localhost:8000`); contrastar respuestas reales con el mock y corregir diferencias (si el contrato y la API divergen, se arregla la API o el mock, nunca el contrato sin avisar).
- **Verificación:** con datos reales ver mapa + tabla + gráficos coherentes al cambiar filtros; capturas con filtros visibles. **Cubre:** G1.

### F9 — Replay histórico (feature `013-replay`)
- `producer/replay.py`: lee una selección ordenada por fecha desde los archivos de F6 (p. ej. 20 eventos de una zona), publica en `earthquakes.replay` con `mode="replay"`, `replay_at`, velocidad configurable (p. ej. 1 evento / 2 s), incluyendo **duplicados y revisiones controlados** (se pueden fabricar y etiquetar como sintéticos o forzar con dos versiones reales).
- Consumidor enruta a esquema `replay` reutilizando `common`.
- API y panel: selector de modo, intervalo 2025, banner **REPRODUCCIÓN** (`metadata.mode`).
- **Verificación:** durante el replay `live` no cambia; la secuencia de duplicados/revisiones da los recuentos esperados. **Cubre:** J1–J8, G10, F12, G12 (`metadata.mode`) (prueba 11).

### F10 — Pruebas de aceptación con evidencias (feature `014-pruebas-aceptacion`)
- Una prueba por caso de la tabla I del checklist. Cada una: procedimiento repetible (script o comandos), resultado esperado, observado, evidencia (SQL, log, captura). Automatizar con `pytest` lo que sea posible (1–8) y documentar a mano las del túnel (9–10).
- **Evidencia:** `docs/evidencias/pruebas/NN-*.md` + tabla resumen en la memoria §8.

### F11 — ngrok y Netlify (feature `015-despliegue-tunel`)
- Reservar dominio ngrok si la cuenta lo permite; `ngrok http 8000`; actualizar `config.json` con la URL HTTPS; build de producción; deploy en Netlify (Base directory `frontend`, publish `dist/<nombre-del-proyecto>/browser`; confirmar el `outputPath` en `angular.json`); poner el dominio de Netlify en CORS.
- Añadir `netlify.toml` y la regla de redirección para SPA (`/* /index.html 200`).
- Probar desde otro dispositivo; probar cierre/reapertura del túnel (pruebas 9–10) y apagado de ngrok mientras el panel sigue abierto.
- Escribir el **procedimiento de activación** para la defensa (H2).
- **Cubre:** G13, H1–H4, pruebas 9–10.

### F12 — Mediciones, complejidad y costes (feature `016-mediciones-costes`)
- **Búsqueda por identificador:** lista secuencial vs `dict` vs consulta PG sin/con índice (`EXPLAIN ANALYZE`), tamaños p. ej. 1.000 / 10.000 / 100.000 (datos sintéticos marcados).
- **Integración geográfica:** bucle ingenuo sobre todos los polígonos vs `STRtree`, mismos tres tamaños.
- **Agregación por ventanas:** SQL `GROUP BY date_trunc('hour', event_time)` con y sin índice en `event_time`.
- Medir tiempo (`time.perf_counter`) y memoria (`tracemalloc` / `psutil`); repetir N veces; anotar equipo (CPU, RAM, SO) y procedimiento.
- Costes: hardware (amortización), electricidad (potencia medida o supuesta × horas × €/kWh, indicando que es supuesto), almacenamiento (tamaño real de BD y archivos), transferencia, mantenimiento, horas de desarrollo; escalado y razonamiento a 100 M de registros (particionado por fecha, índices, batch, varios consumidores por partición).
- **Cubre:** K1–K8, E6.

### F13 — Memoria final, README y ensayo de defensa (feature `017-memoria-defensa`; el contenido se redacta a mano)
- Completar `docs/memoria.md` (índice de checklist §L), con diccionario, procedencia, calidad con consultas y resultados reales (`notebooks/`), modelo (diagrama y equivalencias de nombres con el enunciado), análisis y **≥3 conclusiones** con cifras/filtros/denominador y capturas, pruebas, replay, limitaciones y mejoras. Indicar el material reutilizado (M2).
- README reproducible desde un clon limpio (probarlo realmente en otra carpeta o equipo).
- Preparar la explicación oral: recorrido de un evento de USGS al panel (usar `event_id` real y seguirlo por `ingest.raw_response` → Kafka offset → `event_version` → `current_event` → API → mapa; apoyarse en `CODEMAP.md`) + una decisión propia (p. ej. commit de offset tras PG; esquema separado para replay; agregaciones en SQL sobre `current_event`).
- Recorrer la checklist final del §6 del documento 01.

---

## 3. Spec Kit: cómo se aplica a este proyecto

**Fuente de verdad: `03-procedimiento-ejecucion.md`** (§4 features y semillas de spec, §5 constitución, §6 ciclo de trabajo, §2 instalación y notas de versión de los comandos). Este roadmap no duplica esa información: solo indica la feature de cada fase.

Reparto de la documentación entre herramientas: la **constitución** recoge los principios (no el roadmap entero); la **spec** recoge el qué y los criterios de aceptación (IDs del checklist y pruebas de la tabla I); el **plan** recoge las decisiones de §1 (stack, esquema, topics, mensaje Kafka); el roadmap y el checklist se citan desde las specs, no se pegan enteros.

---

## 4. Riesgos y cómo evitarlos

| Riesgo | Mitigación |
|---|---|
| Kafka conecta pero falla después | Revisar `advertised.listeners`; usar nombres de servicio |
| Recuentos suben sin eventos nuevos | Contar desde `current_event`, no por mensaje; comprobar clave de upsert |
| Replay "no muestra nada" | Consultar el intervalo 2025 y el esquema `replay`, no "últimas 24 h" |
| CORS falla aunque la URL abre | Origen exacto de Netlify, preflight OPTIONS, cabecera ngrok |
| Angular recibe HTML | Página de aviso de ngrok o URL con `/api` duplicado |
| Puntos en sitios raros | Orden lon/lat en GeoJSON vs el orden que exija la librería de mapa elegida; comprobarlo con un evento conocido |
| Mes >20.000 resultados | Detectar `count` y subdividir; nunca truncar en silencio |
| Sobrecarga de alcance | Prioridad: pipeline correcto → pruebas → memoria; ignorar "opcionales" |
| URL ngrok cambia | Dominio estático o recompilar Netlify; documentarlo en H2 |
| Frontend desde cero consume demasiado tiempo | Empezar por el mock del contrato (F8a) en paralelo al backend; priorizar solo los G marcados [OBL]; no pulir estilos hasta tener F8e |
| Mock y API real divergen | El contrato manda; contrastar en F8e y corregir mock o API, no el contrato |
| Versiones de Angular y de la librería de mapa incompatibles | Fijar versiones en el plan de `008`; si hay problemas con un envoltorio de Angular, usar la librería directamente o el plan B (Leaflet o MapLibre) |
| Globo 3D: rendimiento con miles de puntos y la Antártida | Prototipo corto con ~5.000 eventos antes de fijar la librería; límite de anillos animados; ocultar ATA |
| Spec Kit cambia comandos entre versiones | Confirmar con `specify --help`; fijar la versión de la CLI usada en el README (03 §2) |
| Atribución de IA en commits por defecto | Constitución + `.claude/settings.json` + hook `commit-msg`; revisar cada commit antes de `git push` |
| Documentos que se contradicen | Aplicar la tabla de fuente de verdad (03 §0) y corregir el derivado el mismo día |
| Demasiadas features para el tiempo disponible | Fusionar features pequeñas (03 §4, notas) y respetar la prioridad de §5 |

---

## 5. Orden de trabajo sugerido por prioridad de nota

1. F1b y F2→F5 (contratos, infraestructura y núcleo: idempotencia, revisiones, calidad, país) — sostiene Modelado, Calidad y Extracción.
2. F6 y F7 — datos reales y API. En paralelo, **F8a** (panel contra mock) en cuanto F2 esté hecha.
3. F8b–F8e — resto del frontend, análisis y conclusiones.
4. F9–F11 — replay, pruebas, despliegue.
5. F12–F13 — Reflexión y memoria; documentar desde F2 para no acumular al final.

### Calendario orientativo (1-nov → entrega 19-nov; ajustar según avance real)

| Días | Trabajo |
|---|---|
| 1–3 nov | F0, F1, F1b (`001`), F2 (`002`) |
| 4–7 nov | F4 (`003`), F3 (`004`), F5 (`005`); F6 (`006`) en paralelo |
| 8–11 nov | F7 (`007`), F8a (`008`), F8b (`009`) |
| 12–15 nov | F8c (`010`), F8d (`011`), F8e (`012`), F9 (`013`) |
| 16–18 nov | F10 (`014`), F11 (`015`), F12 (`016`); memoria (`017`) en continuo |
| 19 nov | Entrega: revisión final con la lista del checklist §6 y ensayo de la defensa |

Si el calendario se retrasa, fusionar features y recortar primero lo no obligatorio (pulido visual, extras de gráficos); nunca recortar las pruebas de aceptación ni la memoria.
