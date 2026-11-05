# Plan de implementación: API de consulta

**Rama**: `007-api` | **Spec**: [spec.md](spec.md) | **Cubre**: F1–F8, F10–F11 y F12 parcial (F9 queda en `despliegue`, P1).

Solo diseño: este plan no contiene código de aplicación, Dockerfile ni compose (constitución §19). La implementación espera a la revisión del alumno. La forma de las respuestas está en `specs/001-contratos-y-modelo/contracts/api.md`; aquí no se repite.

## 1. Resumen

Se amplía el paquete `api/` (hoy solo `/api/salud`) con tres endpoints de lectura sobre PostgreSQL con el rol `observatory_api`. La validación de parámetros, el cursor, la construcción de cada `Feature` y el armado de las estadísticas son **funciones puras** (sin base ni FastAPI); el SQL vive en dos módulos de consultas; los routers solo orquestan. Los errores salen por manejadores globales con el cuerpo común. Detalle de decisiones en [research.md](research.md), estructuras en [data-model.md](data-model.md), validación en [quickstart.md](quickstart.md).

## 2. Contexto técnico

- **Lenguaje y framework**: Python 3.12, FastAPI 0.162.0, asyncpg 0.32.0 (ya fijados). Sin ORM.
- **Dependencia nueva**: `httpx` en el grupo `dev` (cliente de las pruebas con `ASGITransport`), versión fijada y `uv.lock` actualizado (constitución §11). No entra en la imagen de producción (`uv sync --no-dev`).
- **Almacenamiento**: PostgreSQL 16 sin cambios de DDL, roles ni índices (`sql/001_schema.sql` y `sql/002_roles.sql` intactos). Lee `{live|replay}.current_event`, `public.country` e `ingest.ingest_run`.
- **Configuración nueva**: `API_MAX_EVENTS` (defecto 5000) y `API_DB_TIMEOUT_SECONDS` (defecto 5) en `common/api_config.py`; entran por `compose.yaml`, `.env.example` y README (P3).
- **Cambios fuera de `api/`**: `compose.yaml` (variables del servicio `api` y `DB_API_PASSWORD` en el servicio `tests`), `pyproject.toml`/`uv.lock` (httpx), `tests/support/temp_database.py` y `tests/integration/conftest.py` (rol de la API en la base temporal), `.env.example`, `README.md`, `CODEMAP.md`.
- **Pruebas**: unitarias sin base (parámetros, cursor, serialización, estadísticas, manejadores de error); integración con base temporal y el rol real `observatory_api` (cliente `httpx` contra la aplicación, sin `pytest-asyncio`: `asyncio.run`, como el resto). Datos `synthetic-…` con `is_synthetic=true`; los reales solo en el bloque 5.
- **Rendimiento**: sin objetivo de optimización; las consultas usan los índices existentes (Q1, Q2, Q4, Q8). Una consulta de estadísticas hace cinco lecturas en una sola transacción.
- **Restricciones**: contratos, `docs/enunciado/` y `sql/001_schema.sql` sin tocar; sin CORS, autenticación, caché ni limitación de tasa; sin secretos en el repositorio.

## 3. Revisión contra la constitución

| Principio | Cumple | Cómo |
|---|---|---|
| §1, §2, §6 Idempotencia, versionado, cuarentena | N/A | La API no escribe; lee la versión actual (`current_event`) |
| §3 Tiempos | Sí | Se sirven `event_time_ms` y `updated_ms` tal cual; los rangos se comparan con `event_time` (timestamptz) |
| §4 País por geometría | Sí | Se lee `country_id` ya asignado; `LEFT JOIN public.country`; sin país = `null` |
| §5 Nulos y negativos | Sí | `null` nunca 0/NaN/Infinity; `min_mag` rechaza `nan`/`inf`; negativos válidos y en el tramo `<1` / `<10` |
| §7 Sintéticos separados | Sí | `is_synthetic` en cada feature; `replay` aislado por esquema |
| §8 Agregaciones desde el estado actual | Sí | Todo en SQL sobre `current_event`, en una transacción de lectura única (D2) |
| §9 Nombres de servicio | Sí | Sin cambios de red |
| §10 Exposición y secretos | Sí | Solo `/api/eventos`, `/api/salud`, `/api/estadisticas`; sin rutas de administración; `/docs` desactivado; variables nuevas en `.env.example` |
| §11 Versiones fijadas | Sí | `httpx` fijado con lock; solo desarrollo |
| §12 Alcance cerrado | Sí | Sin CORS, panel, replay, caché ni auditorías |
| §13 Idioma | Sí | Identificadores en inglés (salvo rutas y campos del contrato); docstrings y mensajes en español |
| §14 Una responsabilidad; lo puro separado | Sí | Ver §5: puro (`params`, `cursor`, `serializers`, `stats_builder`) frente a E/S (`queries`, `stats_queries`) |
| §15 Contratos únicos | Sí | Se citan `api.md` y `db-schema.md`; no se copian ni modifican |
| §16 Cierre | Prevista | T021–T025 |
| §17 Frontend sin estadísticas | Sí | La API calcula todo (FR-008) |
| §19 Una feature cada vez | Sí | Este plan no contiene código |

Sin violaciones; no hay tabla de justificaciones.

## 4. Decisiones del orquestador (provisionales)

| Pregunta | Decisión | Dónde se refleja |
|---|---|---|
| P1 CORS / F9 | Fuera de esta feature; F9 lo cubre `despliegue`. `OPTIONS` responde 405 hasta entonces (límite conocido) | Sin tareas de CORS; F9 no figura en las tareas |
| P2 Rango por defecto en `replay` | La misma regla de `api.md` §3.1 en ambos modos | `params.py` no distingue el modo al calcular el rango |
| P3 Variables nuevas | `.env.example` y README; `specs/002-infra-compose/contracts/config.md` no se edita | T001, T024; `docs/evidencias/sprint/decisiones.md` |

## 5. Estructura y responsabilidades

```text
api/
├── main.py            # create_app() crea la app, registra routers y manejadores; `app = create_app()`; sin lógica
├── errors.py          # ApiError (código, estado, mensaje) y manejadores globales (400/404/405/500/503)
├── params.py          # PURO: parámetros crudos -> QueryFilters / PageRequest; validación y rango por defecto
├── cursor.py          # PURO: codificar/decodificar el cursor opaco
├── timeutil.py        # PURO: ISO 8601 <-> ms, ms -> datetime UTC exacto
├── serializers.py     # PURO: fila -> Feature, armado del metadata
├── stats_builder.py   # PURO: horas con cero, tramos de histograma, comparación (n/365, variación)
├── sql_filters.py     # PURO: arma el WHERE y sus parámetros posicionales; esquema por lista cerrada
├── queries.py         # E/S: salud (Q8), página de eventos (Q1), recuentos
├── stats_queries.py   # E/S: por hora (Q4), por país (Q2), histogramas, comparación
├── db_access.py       # E/S: transacción de lectura única con timeout -> error 503
└── routers/
    ├── health.py      # GET /api/salud
    ├── events.py      # GET /api/eventos
    └── stats.py       # GET /api/estadisticas
common/api_config.py   # ApiSettings (API_MAX_EVENTS, API_DB_TIMEOUT_SECONDS)
```

Cada archivo ≤ 250 líneas, cada función ≈ 30 líneas. Las rutas exactas pueden ajustarse al implementar si un archivo se acerca al límite; el reparto puro/E-S no cambia.

## 6. Decisiones de diseño (resumen)

Con alternativas y motivos en [research.md](research.md).

- **D1 Parámetros crudos, sin tipado de FastAPI**: los routers leen `request.query_params` y llaman a `params.py`. Así no hay 422, los repetidos se detectan y los mensajes son propios.
- **D2 Una transacción de lectura por petición**: `REPEATABLE READ`, solo lectura, en una conexión del pool. Eventos+recuentos y los cinco bloques de estadísticas ven el mismo estado, así `total` coincide con las sumas aunque el consumidor escriba entre medias (FR-010).
- **D3 Instante único «ahora»** tomado al empezar la petición; sirve para `generated`, rango por defecto y `recent_period`.
- **D4 Fechas como `datetime` UTC exactos** a partir de ms enteros; nunca coma flotante (el cursor y los rangos comparan con `event_time` e índice `ix_current_event_time`).
- **D5 Esquema por lista cerrada**: `{"live": "live", "replay": "replay"}`; el nombre se inserta en la plantilla SQL solo desde ese diccionario; todo valor del cliente va como parámetro `$n`.
- **D6 Histogramas con `width_bucket(valor, umbrales)`** en SQL y relleno de ceros en Python; los umbrales son constantes con nombre.
- **D7 Horas con cero** rellenadas en Python a partir de las horas con eventos devueltas por SQL (más simple que `generate_series` y probable sin base).
- **D8 Errores de base → 503** reutilizando `RETRIABLE_DB_ERRORS`; espera acotada por `API_DB_TIMEOUT_SECONDS` al tomar conexión. Límite: un error SQL de tipo `PostgresError` también sale como 503 (queda en el log con su tipo, sin SQL).
- **D9 `mode=replay`**: misma consulta contra `replay.current_event`; `comparison: null`; `last_ingestion` igual que en `live`.

## 7. Plan de pruebas

Por orden de coste: unitarias de lo puro → integración con `httpx` y base temporal → recorrido real con `curl` (bloque 5). Pruebas de aceptación: 25 eventos paginados (SC-002), coherencia eventos/estadísticas en cinco combinaciones (SC-003), 503 con base inalcanzable y con PostgreSQL parado (SC-004), cuerpos de error (SC-005), mag nula/negativa (SC-006), rol sin escritura (SC-008). Sin fuzz ni pruebas exhaustivas.

## 8. Límites conocidos

Rango de un año en `by_hour` ≈ 8 760 entradas; cursor reutilizado con otros filtros no se detecta; parámetros desconocidos se ignoran; `OPTIONS` devuelve 405 hasta `despliegue`; con PostgreSQL parado al arrancar la API reintenta y no atiende todavía; un error SQL no previsto sale como 503; sin CORS el panel en `localhost:4200` no consulta la API hasta `despliegue` (P1).
