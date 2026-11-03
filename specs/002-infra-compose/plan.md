# Implementation Plan: Infraestructura Compose y verificación de punta a punta

**Branch**: `002-infra-compose` | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-infra-compose/spec.md`

## Summary

Un único `docker compose up --build -d` levanta cinco servicios (Kafka en modo KRaft, PostgreSQL 16, productor, consumidor y API) en una red interna de Compose. Solo la API se publica, en `127.0.0.1:8000`. El productor mínimo publica un evento sintético cada intervalo configurable en `earthquakes.live`; el consumidor mínimo lo escribe en su registro; la API responde `GET /api/salud` leyendo la base con un rol de solo lectura. PostgreSQL y Kafka usan volúmenes con nombre. El esquema (`sql/001_schema.sql`, sin cambios) y los roles (`sql/002_roles.sql`, nuevo) se aplican en la primera inicialización con contraseñas de variables de entorno. Productor, consumidor y API comparten una imagen Python con versión exacta y dependencias bloqueadas con `uv.lock`. El detalle de las decisiones está en [research.md](research.md); las variables, en [contracts/config.md](contracts/config.md); el procedimiento de verificación, en [quickstart.md](quickstart.md).

**Estado**: las seis propuestas están aprobadas (DECIDIDO). Los archivos de la feature ya están escritos y se ejecutaron contra Docker (ver «Verificación realizada»). `tasks.md` ya existe (33 tareas, 14 hechas). Quedan las verificaciones pendientes de `tasks.md` (arranque adverso, clon limpio con descarga en frío, checkout con LF, reaplicar el esquema, 503 de `/api/salud`, caducidad del latido y otras), la revisión del alumno y el cierre (README, CODEMAP).

## Technical Context

**Language/Version**: Python 3.12.16 (exacto: `Dockerfile` y `.python-version`; `pyproject.toml` admite `>=3.12,<3.13` para que `uv` pueda bloquear sin tener 3.12.16 instalado en el equipo de desarrollo)

**Primary Dependencies**: aiokafka 0.15.0, asyncpg 0.32.0, FastAPI 0.162.0, Uvicorn 0.54.0 (exactas en `pyproject.toml`; todo el árbol, en `uv.lock`). Desarrollo: pytest 9.2.0. Imágenes: `apache/kafka:4.1.2`, `postgres:16.15-bookworm`, `ghcr.io/astral-sh/uv:0.12.13`

**Storage**: PostgreSQL 16 (volumen `postgres-data`); Kafka (volumen `kafka-data`)

**Testing**: pytest para la lógica sin red (configuración, reintentos, latido, mensaje sintético); `scripts/verify_stack.py` para la verificación de punta a punta contra Docker; `scripts/check_env_example.py` para `.env.example`

**Target Platform**: Docker Compose v2 en el equipo del alumno (probado en Windows 11 con Docker 29.1.5, Compose v5.0.1)

**Project Type**: sistema de servicios (productor, consumidor y API) con infraestructura Compose

**Performance Goals**: sistema sano en menos de 5 minutos desde un clon limpio (SC-001); evento sintético visible en el consumidor en menos de 60 s (SC-003). Medido: ~15 s con imágenes ya descargadas

**Constraints**: solo la API expuesta (`127.0.0.1:8000`); nombres de servicio entre contenedores; sin secretos en Git; versiones fijadas; sin ampliar el alcance (constitución §12)

**Scale/Scope**: 5 contenedores, 1 broker de un nodo, 1 partición por tema, un evento sintético cada 30 s por defecto

## Constitution Check

*GATE: pasa antes de la investigación y se vuelve a evaluar tras el diseño.*

| § | Principio | Cumplimiento |
|---|---|---|
| 1 | Al menos una vez, offset tras commit en PG | No aplica todavía: el consumidor mínimo no escribe. No confirma offsets (`enable_auto_commit=False`) y lo deja documentado en el código; la regla se implementa en `consumidor-idempotente`. |
| 7 | Datos sintéticos etiquetados y separados | `is_synthetic = true`, `event.id` con prefijo `synthetic` y `source = replay_demo`. No se escribe ninguna fila de eventos. |
| 9 | Nombres de servicio | `kafka:9092` y `postgres:5432`. `127.0.0.1` solo aparece en la comprobación de salud de la propia API (su propio contenedor) y en la publicación del puerto. |
| 10 | Solo la API expuesta; sin secretos; `.env.example` al día | Un solo puerto publicado; contraseñas de ejemplo con prefijo `cambia-esta-clave`; `scripts/check_env_example.py` comprueba la coincidencia. |
| 11 | Versiones fijadas | Python exacto, dependencias `==` más `uv.lock`, imágenes con etiqueta concreta. |
| 12 | Alcance cerrado | Sin USGS, validación, país, histórico, endpoints de datos, frontend ni ngrok. |
| 13 | Idioma | Identificadores en inglés; docstrings y comentarios en español. |
| 14 | Una responsabilidad por función; lógica pura separada del I/O | `main.py` solo arranca; `common/health.py::is_heartbeat_fresh`, `common/retry.py::next_delay` y `common/synthetic_event.py` son puros. |
| 15 | Contratos únicos | No se duplica ni se modifica ningún contrato. Constantes de temas en `common/kafka_topics.py` (valores de `kafka-message.md` §1). |
| 16 | Cierre de feature | **Pendiente**: hay pruebas y evidencia parciales (borrador); faltan las verificaciones pendientes de `tasks.md` y el cierre con `README.md` y `CODEMAP.md` (T028 y T030). |
| 19 | Una feature cada vez; sin implementar sin spec, plan y tareas revisados | **Desviación de la constitución §19, validada por el alumno**: el código se escribió antes de `tasks.md` y de la revisión de las tareas (borrador adelantado, commit `33e1fc7`), porque el alumno pidió escribir los archivos reales junto con el plan. El alumno ha validado esa desviación. Las tareas (`tasks.md`) se limitan a completar y verificar; no hay merge. |
| 20 | Commits | Ninguno hecho. |

**Resultado**: sin violaciones sin justificar. Reevaluado tras el diseño: igual.

## Project Structure

### Documentation (this feature)

```text
specs/002-infra-compose/
├── plan.md              # Este archivo
├── research.md          # Decisiones y alternativas
├── data-model.md        # Roles, permisos, volúmenes y red
├── quickstart.md        # Levantar, verificar y reiniciar
├── contracts/
│   └── config.md        # Variables de entorno ↔ .env.example ↔ código
├── checklists/
│   └── requirements.md
└── tasks.md             # Lo genera /speckit-tasks (aún no existe)
```

### Source Code (repository root)

```text
compose.yaml                  # 5 servicios, red, volúmenes, healthchecks
Dockerfile                    # imagen Python compartida (contexto de build: raíz)
.dockerignore
.env.example                  # variables de ejemplo, sin secretos
.gitattributes                # LF en .sh, .sql, .py, .yaml y Dockerfile (se montan en Linux)
.python-version               # 3.12.16
pyproject.toml  uv.lock       # dependencias exactas y bloqueo

common/                       # importable por cualquier servicio (PYTHONPATH=/app)
├── config.py                 # variables de entorno
├── logging_setup.py
├── retry.py                  # espera exponencial
├── health.py                 # latido + healthcheck (python -m common.health)
├── db.py                     # conexión y pool con reintentos
├── kafka_topics.py           # creación idempotente de los temas del contrato
└── synthetic_event.py        # mensaje sintético (lógica pura)

producer/   main.py  loop.py  publisher.py
consumer/   main.py  loop.py
api/        main.py  queries.py  routers/health.py

sql/
├── 001_schema.sql            # sin cambios
└── 002_roles.sql             # roles y permisos (nuevo)

scripts/
├── postgres_init.sh          # aplica 001 y 002 en la primera inicialización
├── verify_stack.py           # verificación de punta a punta
└── check_env_example.py      # .env.example ↔ compose ↔ código

tests/  common/  producer/    # espejo de la estructura del código

docs/evidencias/infra-compose/
```

**Structure Decision**: se respeta la estructura de `03-procedimiento-ejecucion.md` §3 y §7.1. No se crea `docker/`: la imagen compartida vive en la raíz porque su contexto de build es la raíz (para que `common/` entre en la imagen) y la inicialización de PostgreSQL usa las carpetas `sql/` y `scripts/` existentes. `producer/loop.py` y `consumer/loop.py` son nuevos respecto al esqueleto de §7.1: separan el bucle del arranque (`main.py`, regla 5) y se reutilizarán en `productor-live` y `consumidor-idempotente`.

## Decisiones — todas DECIDIDO (aprobadas por el alumno el 2026-11-03)

| # | Tema | DECIDIDO | Detalle |
|---|---|---|---|
| 1 | Bloqueo de dependencias | `uv` 0.12.13 con `pyproject.toml` (versiones `==`) y `uv.lock`; `uv sync --frozen` en el `Dockerfile` | research.md §1 |
| 2 | Imágenes | `python:3.12.16-slim-bookworm`, `apache/kafka:4.1.2`, `postgres:16.15-bookworm` | research.md §2 |
| 3 | Creación de temas | `common/kafka_topics.py::ensure_topics()` desde productor y consumidor al arrancar; auto-creación desactivada; retención a nivel de tema y a nivel de broker | research.md §3 |
| 4 | Esquema y roles | `scripts/postgres_init.sh` en `docker-entrypoint-initdb.d`: aplica `001_schema.sql` y `002_roles.sql`, contraseñas por `psql -v` desde el entorno | research.md §4 |
| 5 | Dato de la prueba de persistencia | Tabla `public.zz_infra_check` con un token aleatorio, creada y eliminada por `verify_stack.py` | research.md §5 |
| 6 | Salud de productor y consumidor | Archivo de latido renovado tras cada vuelta correcta del bucle; el healthcheck comprueba su antigüedad | research.md §6 |

Las decisiones constan en la sección Clarifications de [spec.md](spec.md). Los permisos de los roles siguen exactamente la tabla §1.1 de `db-schema.md` (ver [data-model.md](data-model.md)).

## Trazabilidad A1–A12

Cada requisito del checklist con su criterio de la spec, la tarea de `tasks.md` que lo verifica y la evidencia en `docs/evidencias/infra-compose/`. «(pendiente)» = evidencia aún por generar; el resto ya existe.

| ID | Requisito (resumen) | Criterio de la spec | Tarea que lo verifica | Evidencia |
|---|---|---|---|---|
| A1 | 5 servicios separados, `docker compose ps` los muestra healthy | FR-001, FR-006; US1 escenario 1; SC-001 | T007 (hecha); T013 (pendiente, en clon limpio) | `arranque_desde_cero.txt`, `verificacion_completa.txt`; `clon_limpio_verify.txt` (pendiente) |
| A2 | `docker compose up --build -d` lo levanta todo desde un clon limpio | FR-002; SC-001; SC-002; SC-010 | T010, T011, T012 (pendientes) | `clon_limpio.txt`, `checkout_lf.txt` (pendientes) |
| A3 | Imagen reproducible por servicio Python, dependencias fijadas | FR-003, FR-004, FR-034, FR-035; SC-008 | T001 (hecha); T012 (construcción en frío, pendiente) | `uv.lock`, `Dockerfile`; `clon_limpio.txt` (pendiente) |
| A4 | Healthchecks y reintentos en el código | FR-006, FR-007, FR-008, FR-009; SC-002 | T008 (hecha); T009, T014, T015 (pendientes) | `reintentos_y_configuracion.txt`; `arranque_sin_postgres.txt`, `latido_caduca.txt`, `salud_503.txt` (pendientes) |
| A5 | Volúmenes persistentes: reiniciar no pierde datos | FR-018, FR-019, FR-020; SC-004 | T018 (hecha); T019 (pendiente) | `verificacion_completa.txt`; `reaplicar_esquema.txt` (pendiente) |
| A6 | Retención limitada de Kafka, configurada y documentada | FR-016, FR-021; SC-009 | T025 (hecha); T028 (documentación en README, pendiente) | `verificacion_completa.txt`; `README.md` (pendiente) |
| A7 | Nombres de servicio en vez de `localhost`; listeners documentados | FR-022, FR-026, FR-031 | T022 (hecha) | `check_env_example.txt`, `reintentos_y_configuracion.txt` (`DB_HOST=postgres`, `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`); listeners en `research.md` §3 |
| A8 | Solo la API se expone (`127.0.0.1:8000`) | FR-023; SC-005 | T020 (hecha); T013 (repite en el clon, pendiente) | `verificacion_completa.txt`; `clon_limpio_verify.txt` (pendiente) |
| A9 | Uvicorn en `0.0.0.0:8000` dentro del contenedor | FR-024; US1 escenario 3 | T020 (hecha, indirecta: si escuchara solo en `127.0.0.1` el puerto publicado no respondería) | `verificacion_completa.txt` (`GET /api/salud` desde el equipo); comando en `compose.yaml` |
| A10 | `.env.example` sin credenciales; variables coinciden con el código; productor configurable por entorno | FR-012, FR-031, FR-032, FR-033, FR-036; SC-007 | T022 (hecha); T023, T033 (pendientes) | `check_env_example.txt`; `busqueda_secretos.txt`, `config_por_entorno.txt` (pendientes) |
| A11 | Dependencias fijadas (`requirements`/lock) | FR-034, FR-035; SC-008 | T001 (hecha); T012 (pendiente) | `pyproject.toml`, `uv.lock`; `clon_limpio.txt` (pendiente) |
| A12 | Sin contenedor Angular; ngrok en el equipo | FR-005 | T029 (pendiente) | `a12.txt` (pendiente) |

M7–M9 solo se verifican (FR-037): T024, evidencia `m7_m9.txt` (pendiente).

## Pendientes trasladados a otras features

| Pendiente | Feature | Dónde se anota |
|---|---|---|
| Los 404 (`not_found`) y 405 (`method_not_allowed`) deben devolver el cuerpo de error común `{"error": {"code", "message"}}` de `contracts/api.md` §6; hoy FastAPI usa su cuerpo por defecto (`{"detail": …}`). Añadir manejadores globales en `api/main.py`. | `007-api` | T027 → `docs/planificacion/02-roadmap-implementacion.md`, sección F7 |
| Permisos de lectura de `raw_response`, purga (`DELETE`) y lecturas de `exclusion` y `quarantine`: se añaden al rol que corresponda actualizando la tabla §1.1 de `db-schema.md`. | `productor-live`, `consumidor-idempotente` | `data-model.md` |
| Aplicar migraciones sobre un volumen ya inicializado (`postgres_init.sh` solo corre con el volumen vacío). | primera feature que añada una migración | `research.md` §4 |
| Rol de la carga histórica (¿reutiliza `observatory_consumer` o uno propio?). | `historico-2025` | `data-model.md` |

## Verificación realizada (2026-11-03)

Evidencia en [docs/evidencias/infra-compose/](../../docs/evidencias/infra-compose/):

- `arranque_desde_cero.txt`: `docker compose down -v` + `up --build -d`; los cinco servicios `healthy` en 15 s (imágenes ya descargadas).
- `verificacion_completa.txt`: `scripts/verify_stack.py`, 16/16 comprobaciones (salud, evento sintético en el log del consumidor, `/api/salud`, un único puerto publicado, temas con 1 partición, factor 1 y 7 días, permisos por rol, escritura de la API rechazada, persistencia tras `down` + `up`).
- `reintentos_y_configuracion.txt`: con Kafka detenido, productor y consumidor registran los reintentos y quedan en `starting`; al volver Kafka, los cinco `healthy`. Variable ausente: el error nombra la variable.
- `permisos_lectura_y_secuencias.txt`: comprobación manual de lecturas y secuencias tras ajustar los roles a `db-schema.md` §1.1 (el productor no lee `exclusion` ni `raw_response` y no borra; el consumidor no lee `quarantine`). `verificacion_completa.txt` se regeneró tras ese ajuste: 16/16.
- `check_env_example.txt` y `pytest.txt`: `.env.example` coincide; 22 pruebas superadas.

## Hallazgos para la revisión

1. **M7 incompleto**: el historial no tiene trailers de coautoría ni líneas de «generado por» (0 coincidencias), pero **no existen** `.claude/settings.json` ni el hook `commit-msg` que el checklist M7 menciona. Solo se verifica, no se rehace (spec FR-037): **el alumno lo resuelve a mano** y la tarea T024 solo comprueba que ambos existen y registra el resultado. El hook `commit-msg` no se versiona (vive en `.git/hooks/`), así que debe instalarse en cada clon; el README lo avisará (T028).
2. **M9 correcto en el repositorio**: el SHA-256 de `paises.geojson` en Git coincide con `FUENTES-Y-LICENCIAS.md`. La copia de trabajo en Windows tiene saltos CRLF (por `autocrlf`) y su hash local difiere. `.gitattributes` fija ahora `data/catalogo/paises.geojson -text` para que Git no convierta sus saltos de línea en futuras descargas; la copia de trabajo actual no se ha tocado.
3. **PostgreSQL local en el 5432 del equipo**: la sonda TCP desde el anfitrión responde, pero lo atiende un servicio local, no Compose. La comprobación de aislamiento se basa en que Docker no enlaza ningún puerto de Kafka ni de PostgreSQL.
4. **Dos fallos encontrados y corregidos durante la verificación**: construir la imagen en tres servicios con la misma etiqueta provoca un conflicto (se construye solo en `producer`); un contenedor reiniciado conservaba su latido anterior y parecía sano (se borra al arrancar).
5. **Supuestos de la spec que el plan afina**: el consumidor mínimo también crea los temas y comprueba su rol de base de datos al arrancar (necesario para FR-016 y FR-030); no escribe en ninguna tabla.

## Complexity Tracking

Sin violaciones de la constitución que justificar; la única desviación (§19) está declarada arriba.
