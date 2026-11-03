# Investigación y decisiones: infra-compose

Cada decisión indica qué se eligió, por qué y qué alternativas se descartaron. Las seis decisiones que la spec dejaba abiertas (§1–§6) fueron aprobadas por el alumno el 2026-11-03 y constan como DECIDIDO en Clarifications de `spec.md`. Las versiones se comprobaron el 2026-11-03 con `docker manifest inspect` (las etiquetas existen en sus registros).

## 1. Bloqueo de dependencias — DECIDIDO

- **Decisión**: `uv` 0.12.13. `pyproject.toml` declara las dependencias con `==` (aiokafka 0.15.0, asyncpg 0.32.0, FastAPI 0.162.0, Uvicorn 0.54.0; pytest 9.2.0 en el grupo `dev`) y `uv.lock` bloquea el árbol completo (23 paquetes). El `Dockerfile` ejecuta `uv sync --frozen --no-dev --no-install-project`: falla si el lock no coincide con `pyproject.toml`. El binario de `uv` se copia de `ghcr.io/astral-sh/uv:0.12.13`, también fijado.
- **Por qué**: un único archivo de bloqueo con hashes, resolución rápida y reproducible, y la misma herramienta en el equipo y en la imagen (A3, A11, constitución §11).
- **Versión exacta de Python**: `3.12.16`, en la etiqueta de imagen del `Dockerfile` y en `.python-version`. `requires-python` es `>=3.12,<3.13` y no `==3.12.16` porque en el equipo de desarrollo `uv` no tiene ese parche (`No interpreter found for Python 3.12.16`) y no puede bloquear sin un intérprete 3.12 local. La exactitud la garantizan la imagen y `.python-version`; el lock es válido para cualquier 3.12.x.
- **Alternativas**: `pip-tools` (`requirements.txt` con hashes): más piezas y sin gestión de versión de Python. Poetry: más pesado y con formato propio. `pip freeze`: no distingue dependencias directas de transitivas.
- **No se construye un paquete** (`[tool.uv] package = false`): los servicios importan `common/`, `producer/`, `consumer/` y `api/` desde `/app` con `PYTHONPATH=/app`. Así `common/` es importable por cualquier servicio sin instalarlo.

## 2. Imágenes y versiones exactas — DECIDIDO

| Imagen | Versión | Motivo |
|---|---|---|
| `python` | `3.12.16-slim-bookworm` | Última 3.12 disponible; `slim` reduce tamaño; sin `curl` (los healthchecks usan Python). |
| `apache/kafka` | `4.1.2` | Imagen oficial de Apache con KRaft nativo (sin ZooKeeper). 4.1.2 es el último parche de la serie 4.1. aiokafka 0.15.0 funciona con ella (probado: creación de temas, publicación y consumo). |
| `postgres` | `16.15-bookworm` | Versión mayor 16 exigida; parche más reciente disponible. |
| `ghcr.io/astral-sh/uv` | `0.12.13` | Solo para copiar el binario. |

- **Alternativas**: Kafka 3.9.2 (más conservadora; sigue disponible como plan B si una feature futura necesitase una API retirada en 4.x); Bitnami/Confluent (imágenes de terceros con más variables y licencias distintas). Etiquetas `latest` o `16`: descartadas por la constitución §11.

## 3. Creación de los temas — DECIDIDO

- **Decisión**: `common/kafka_topics.py::ensure_topics()` crea `earthquakes.live` y `earthquakes.replay` con 1 partición, factor de replicación 1 y `retention.ms=604800000`. La llaman el productor y el consumidor al arrancar (con reintentos); ignora «el tema ya existe», así que el orden entre ambos no importa. El broker tiene la creación automática desactivada y `KAFKA_LOG_RETENTION_HOURS=168` como valor por defecto de respaldo.
- **Por qué**: mantiene los cinco servicios (spec FR-001 y SC-001: «5 de 5 saludables»), pone los valores del contrato en un solo sitio (constitución §15), es idempotente y se prueba con el broker real. Con la creación automática desactivada, un nombre de tema mal escrito falla en vez de crear un tema con valores por defecto.
- **Alternativas**: (a) servicio `kafka-init` de un solo uso: añade un sexto contenedor que termina en `exited` y rompe «5 de 5 saludables». (b) Script envoltorio en el contenedor de Kafka o creación desde el healthcheck: frágil (señales, efectos secundarios en la comprobación). (c) Solo la creación automática: no fija 1 partición ni 7 días por tema.
- **Límite conocido**: si un tema ya existe con otra retención, `ensure_topics()` no la corrige. Se detecta con `verify_stack.py` (`kafka-topics.sh --describe`). Corregir una discrepancia queda para cuando se necesite.
- **Acceso desde el equipo anfitrión (A7, FR-026)**: no se habilita. Si se quisiera, haría falta un segundo listener (p. ej. `EXTERNAL://localhost:9094`) anunciado con `localhost`, con su puerto publicado en `127.0.0.1:9094`, mientras los contenedores siguen usando `kafka:9092`. Es lo que justifica documentar los listeners: `localhost` dentro de un contenedor no apunta al anfitrión. No forma parte de esta feature.

## 4. Esquema y roles en la primera inicialización — DECIDIDO

- **Decisión**: `scripts/postgres_init.sh` se monta en `/docker-entrypoint-initdb.d/10-init.sh`; `./sql` se monta de solo lectura en `/sql`. El script ejecuta `sql/001_schema.sql` tal cual y después `sql/002_roles.sql`, pasando las contraseñas con `psql -v` desde variables de entorno (`DB_API_PASSWORD`, `DB_PRODUCER_PASSWORD`, `DB_CONSUMER_PASSWORD`). El SQL las usa como `:'api_password'`; no hay contraseñas en ningún archivo versionado.
- **Por qué**: la imagen oficial ejecuta esos archivos solo cuando el directorio de datos está vacío. El esquema (con `IF NOT EXISTS`) y los roles (creación condicional más `ALTER ROLE … PASSWORD`) son idempotentes, así que volver a ejecutarlos manualmente no falla ni duplica (FR-020). No necesita un contenedor extra.
- **Roles** (nombres fijos; permisos exactamente los de `db-schema.md` §1.1, ver [data-model.md](data-model.md)): `observatory_api` (solo lectura), `observatory_producer`, `observatory_consumer`; el administrador (`POSTGRES_USER`) no lo usa ningún servicio Python (FR-030).
- **Salud de PostgreSQL**: `pg_isready -h 127.0.0.1`. Por TCP a propósito: el servidor temporal de la inicialización solo escucha por socket Unix, así que el servicio no se declara sano hasta que termina de aplicar esquema y roles.
- **Límite conocido**: como el script solo corre con el volumen vacío, un cambio posterior en `002_roles.sql` o una nueva migración no se aplica sobre un volumen existente. Cuando una feature añada una migración, deberá decidir cómo aplicarla (p. ej. paso explícito al arrancar el consumidor). Para rehacer la base: `docker compose down -v`.
- **Alternativas**: servicio `db-migrate` de un solo uso (sexto contenedor); aplicar el SQL desde el consumidor al arrancar (mezcla infraestructura y negocio, y el rol del consumidor no debe crear roles).

## 5. Dato de la prueba de persistencia — DECIDIDO

- **Decisión**: `scripts/verify_stack.py` crea `public.zz_infra_check (token text)`, inserta un UUID aleatorio, ejecuta `docker compose down` (sin `-v`) y `up -d`, espera a que los cinco servicios estén sanos, lee el token y elimina la tabla (incluso si la comprobación falla).
- **Por qué**: no contamina ninguna tabla del contrato; el consumidor mínimo no escribe eventos, así que no hay otro dato propio que comprobar. Usa el volumen real, no una simulación.
- **Alternativas**: insertar en `live.quarantine` o `ingest.ingest_run` (ensucia tablas con significado y los roles lo limitan); crear una base aparte (no prueba el volumen de la base real).
- `zz_infra_check` queda excluida de la comprobación de permisos por rol.

## 6. Salud del productor y del consumidor — DECIDIDO

- **Decisión**: cada servicio escribe un archivo de latido (`/tmp/producer.alive`, `/tmp/consumer.alive`) **después** de cada vuelta correcta del bucle: el productor tras confirmar la publicación del evento; el consumidor tras cada consulta al broker (cada segundo). El healthcheck (`python -m common.health file`) exige que el latido tenga menos de `HEALTH_MAX_AGE_SECONDS` (productor 120, consumidor 60). El latido se borra al arrancar, por lo que no existe hasta que el servicio terminó de conectar con la base y el broker.
- **Por qué**: «sano» significa listo y funcionando, no solo proceso vivo (FR-006). Si el broker cae, el productor deja de renovar el latido y pasa a `unhealthy`; al volver, se recupera solo. Se comprobó: con Kafka detenido ambos quedan en `starting` y, al volver Kafka, en `healthy`.
- **Regla de coherencia**: `PRODUCER_INTERVAL_SECONDS` ≤ `HEALTH_MAX_AGE_SECONDS` / 2; el productor lo valida al arrancar (por defecto 30 s frente a 120 s; máximo permitido 60 s).
- **Retraso inherente**: tras una caída del broker, el estado tarda hasta `HEALTH_MAX_AGE_SECONDS` en cambiar a `unhealthy`. Es una cota de detección, no un fallo.
- **API**: el healthcheck pide `GET /api/salud` (200 ⇒ la API alcanza la base con su rol de solo lectura).
- **Alternativas**: comprobar solo que el proceso exista (no detecta bloqueos); abrir un puerto de salud en productor y consumidor (más superficie y código); `pgrep` o `kill -0` (igual que la primera).

## 7. Reintentos en el código (A4, FR-008, FR-009)

- `common/retry.py::retry_forever`: espera exponencial (`RETRY_INITIAL_SECONDS`, doblando hasta `RETRY_MAX_SECONDS`), nunca abandona por indisponibilidad temporal y deja una línea por intento con el servicio al que no llega. Solo reintenta los tipos de error que se le indican; un error de programación se propaga.
- Se usa para: pool de la API, comprobación de la base y conexión a Kafka del productor y del consumidor, creación de temas, y cada publicación.
- `depends_on: condition: service_healthy` evita arranques inútiles, pero no sustituye a los reintentos: Kafka puede caer después de arrancar.

## 8. Red, nombres y exposición (A7, A8, A9)

- Una red `seismic-observatory-backend` compartida; no hay `ports` en Kafka ni en PostgreSQL (el `9092/tcp` y `5432/tcp` que muestra `docker compose ps` son puertos declarados por la imagen, no publicados: `HostConfig.PortBindings` está vacío, comprobado por `verify_stack.py`).
- API: `ports: ["127.0.0.1:8000:8000"]`; Uvicorn con `--host 0.0.0.0 --port 8000` dentro del contenedor.
- Los hosts (`DB_HOST=postgres`, `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`) vienen de `.env.example`, no de valores escritos en el código.
- ngrok queda en el equipo (`ngrok http 8000`) y fuera de esta feature.

## 9. Imagen compartida (A3, FR-003, FR-004)

- Contexto de build = raíz del repositorio; `.dockerignore` deja fuera `.git`, `docs`, `specs`, `data`, `tests`, `sql`, `scripts`, `.env` y la documentación.
- Un solo `Dockerfile`; la imagen se construye en el servicio `producer` y `consumer` y `api` la reutilizan por nombre (`seismic-observatory-python:0.1.0`, `pull_policy: never`). Construirla en los tres con la misma etiqueta falla (`image already exists`); se comprobó.
- Usuario sin privilegios (`observatory`, uid 10001). `PYTHONPATH=/app` hace importable `common/` desde cualquier servicio.

## 9b. API sin documentación automática

- La aplicación FastAPI se crea con `docs_url=None` y `redoc_url=None`: no sirve `/docs` ni `/redoc`. Decisión de esta feature: reduce la superficie expuesta (el túnel publicará la API) y el contrato de la API está en `api.md`, no en el esquema generado. Si una feature futura la necesita, se reactiva de forma explícita.

## 10. Consumidor mínimo y offsets

- Lee desde el principio (`auto_offset_reset=earliest`) y **no confirma offsets** (`enable_auto_commit=False`): sin escritura en PostgreSQL no hay nada que confirmar (constitución §1). Consecuencia: al reiniciarse relee y vuelve a mostrar los mensajes retenidos (hasta 7 días). Es deseable para la demostración y se corrige en `consumidor-idempotente`.

## 11. Fuera de alcance, confirmado

Sin USGS, validación, escritura de eventos, país, histórico, endpoints de datos, manejadores de error globales de la API (404/405 con el cuerpo común), CORS, frontend, ngrok ni Netlify.
