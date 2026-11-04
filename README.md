# seismic-activity-observatory

Observatorio de actividad sísmica: un sistema que consulta el feed de terremotos de USGS, lo publica en Kafka, lo guarda en PostgreSQL sin duplicados ni pérdida de versiones y lo expone mediante una API a un panel con mapa. También permite reproducir un histórico, aislado de los datos en vivo. Proyecto de curso.

## Estado actual

Se trabaja con Spec Kit, una feature cada vez y con revisión antes de avanzar.

| Feature | Estado |
|---|---|
| `contratos-y-modelo` | Cerrada (2026-11-02): contratos, DDL, modelo de datos y evidencias |
| `infra-compose` | Implementada y verificada (2026-11-04), pendiente de la revisión del alumno: Compose con cinco servicios, "hola mundo" de punta a punta con un evento sintético, roles de base de datos y evidencias en `docs/evidencias/infra-compose/` |
| Resto de features | No empezadas |

El productor, el consumidor y la API son por ahora **mínimos**: el productor publica eventos sintéticos, el consumidor los muestra en su registro y la API solo responde `GET /api/salud`. La lógica real llega en las siguientes features.

El orden de las fases está en [`docs/planificacion/02-roadmap-implementacion.md`](docs/planificacion/02-roadmap-implementacion.md).

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| [`compose.yaml`](compose.yaml) | Los cinco servicios: Kafka, PostgreSQL, productor, consumidor y API |
| [`Dockerfile`](Dockerfile) | Imagen Python compartida por productor, consumidor y API |
| [`.env.example`](.env.example) | Variables de ejemplo, sin credenciales reales (se copia a `.env`) |
| `pyproject.toml`, `uv.lock`, `.python-version` | Python 3.12.16 y dependencias con versiones exactas y bloqueo |
| [`common/`](common/) | Código compartido por todos los servicios Python (configuración, reintentos, latido, conexión a PostgreSQL, temas de Kafka, evento sintético) |
| [`producer/`](producer/) | Productor mínimo: publica un evento sintético cada intervalo configurable |
| [`consumer/`](consumer/) | Consumidor mínimo: lee el tema y registra cada evento |
| [`api/`](api/) | API FastAPI mínima: solo `GET /api/salud` |
| [`sql/`](sql/) | `001_schema.sql` (esquema) y `002_roles.sql` (roles y permisos) |
| [`scripts/`](scripts/) | `postgres_init.sh` (inicialización de la base), `verify_stack.py` y `check_env_example.py` (verificación) y `explore_usgs.py` (exploración del feed) |
| [`tests/`](tests/) | Pruebas unitarias de `common/`, `producer/` y `consumer/` (pytest) |
| [`docs/planificacion/`](docs/planificacion/) | Checklist de requisitos ([01](docs/planificacion/01-checklist-requisitos.md)), roadmap ([02](docs/planificacion/02-roadmap-implementacion.md)), procedimiento de ejecución ([03](docs/planificacion/03-procedimiento-ejecucion.md)), glosario ([04](docs/planificacion/04-glosario-nomenclatura.md)) y [decisiones abiertas del contrato](docs/planificacion/decisiones-abiertas-contrato.md) |
| `docs/enunciado/` | Material del profesor (solo lectura) |
| `docs/evidencias/` | Salidas de pruebas y de revisiones; las de esta feature, en [`docs/evidencias/infra-compose/`](docs/evidencias/infra-compose/) |
| `docs/memoria.md` | Memoria del proyecto (en redacción) |
| [`specs/001-contratos-y-modelo/`](specs/001-contratos-y-modelo/) | Spec, plan, tareas y los tres contratos (`contracts/`) |
| [`specs/002-infra-compose/`](specs/002-infra-compose/) | Spec, plan, tareas, investigación, modelo de infraestructura, contrato de variables de entorno y [quickstart](specs/002-infra-compose/quickstart.md) |
| `data/catalogo/` | Catálogo de países (`paises.geojson`) |
| `CODEMAP.md` | Mapa de dónde está cada cosa |
| `.specify/`, `.claude/` | Configuración y plantillas de Spec Kit; agentes, habilidades y `settings.json` de Claude Code |

## Contratos y esquema

Los contratos viven solo en `specs/001-contratos-y-modelo/contracts/`:

- [`kafka-message.md`](specs/001-contratos-y-modelo/contracts/kafka-message.md): mensaje productor → consumidor, versiones y cuarentena.
- [`db-schema.md`](specs/001-contratos-y-modelo/contracts/db-schema.md): tablas, claves e índices.
- [`api.md`](specs/001-contratos-y-modelo/contracts/api.md): API → panel.

El DDL es [`sql/001_schema.sql`](sql/001_schema.sql); los roles de base de datos y sus permisos (exactamente los de la tabla «Quién escribe y quién lee» de `db-schema.md`) están en [`sql/002_roles.sql`](sql/002_roles.sql). Las variables de entorno y su correspondencia con el código están en [`specs/002-infra-compose/contracts/config.md`](specs/002-infra-compose/contracts/config.md).

## Herramientas

- Spec Kit CLI (`specify`): versión 1.2.4, obtenida con `specify --version`.
- Python 3.12.16 (imagen `python:3.12.16-slim-bookworm`, `.python-version`), dependencias bloqueadas con `uv` 0.12.13 (`uv.lock`).
- Docker con Compose v2 (probado con Docker 29.1.5 y Compose v5.0.1).
- Imágenes: `apache/kafka:4.1.2` (modo KRaft, un nodo) y `postgres:16.15-bookworm`.

## Ejecución con Docker Compose

Guía completa, con resolución de problemas: [`specs/002-infra-compose/quickstart.md`](specs/002-infra-compose/quickstart.md).

### Levantar

```bash
cp .env.example .env          # en PowerShell: Copy-Item .env.example .env
# Edita .env y cambia las contraseñas de ejemplo; .env está ignorado por Git.
docker compose up --build -d
docker compose ps             # los cinco servicios deben figurar como healthy
```

Solo la API se publica en el equipo, y solo en `127.0.0.1:8000`. Kafka y PostgreSQL no publican ningún puerto; entre contenedores se usan los nombres de servicio (`kafka`, `postgres`), nunca `localhost`.

### Comprobar

```bash
curl http://127.0.0.1:8000/api/salud                  # {"status":"ok","last_ingestion":null,"generated":...}
docker compose logs consumer --no-log-prefix --tail 5 # líneas «Evento recibido [SINTÉTICO] …»
python scripts/verify_stack.py                        # verificación completa de punta a punta (reinicia los contenedores)
python scripts/verify_stack.py --skip-restart         # sin detener nada
python scripts/check_env_example.py                   # .env.example ↔ compose.yaml ↔ código
uv run pytest                                         # pruebas unitarias (no necesitan Docker)
```

### Reiniciar y parar

| Quiero… | Comando | Datos |
|---|---|---|
| Parar y volver a arrancar | `docker compose down` y `docker compose up -d` | Se conservan (volúmenes) |
| Reconstruir tras cambiar código | `docker compose up --build -d` | Se conservan |
| **Empezar de cero** | `docker compose down -v` | **Se borran** PostgreSQL y Kafka |

**Cambiar las contraseñas de la base de datos sobre un volumen ya inicializado exige `docker compose down -v`.** El esquema y los roles (con sus contraseñas) se aplican solo la primera vez, cuando el volumen de PostgreSQL está vacío; si cambias el `.env` después, los servicios usarán la contraseña nueva y no podrán conectar con las del volumen.

### Retención de Kafka

Los dos temas del contrato, `earthquakes.live` y `earthquakes.replay`, se crean con 1 partición, factor de replicación 1 y **retención de 7 días** (`retention.ms=604800000`); el broker además tiene `KAFKA_LOG_RETENTION_HOURS=168` como valor por defecto. **Motivo:** 7 días cubren una caída del consumidor de varios días sin perder mensajes, y el límite evita que el broker crezca sin control; el estado definitivo vive en PostgreSQL, no en Kafka. El valor está en `common/kafka_topics.py` y en `compose.yaml`.

### Listeners de Kafka y acceso desde el equipo anfitrión

Hoy el broker tiene **un solo listener de clientes**, interno: `kafka:9092`, anunciado por nombre de servicio y sin puerto publicado en el equipo (más el listener del controlador, `9093`, también interno). Dentro de un contenedor `localhost` apunta al propio contenedor, no al equipo, por eso los servicios usan `kafka:9092`.

Si en algún momento quieres leer Kafka desde el equipo anfitrión, el cambio es **añadir un segundo listener** en el servicio `kafka` de `compose.yaml`, sin tocar el interno:

```yaml
KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093,EXTERNAL://:9094
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:9094
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT
ports:
  - "127.0.0.1:9094:9094"
```

Los contenedores siguen usando `kafka:9092`; los programas del equipo usan `localhost:9094`. **Advertencias:** (1) esta configuración **no se ha probado** en esta feature; (2) publica un puerto de Kafka, lo que contradice la regla «solo la API se expone» (constitución §10, requisito A8): úsala solo de forma temporal y en local, ligada a `127.0.0.1`, **nunca a través de un túnel**, y revierte el cambio antes de entregar.

### ngrok

ngrok **se ejecuta en el equipo anfitrión** (`ngrok http 8000`) y **queda fuera de Compose y de esta feature**. Publica la API, que ya está en `127.0.0.1:8000`. Su authtoken nunca va al repositorio ni a Angular.

## Configuración de Git: el hook `commit-msg`

`.claude/settings.json` está versionado y desactiva la atribución en commits y PRs. **El hook `commit-msg` no se versiona** (vive en `.git/hooks/`, que Git no sube): **debe instalarse en cada clon**. Es un archivo `.git/hooks/commit-msg`, ejecutable, que rechaza los mensajes con trailers de coautoría o con «generated with»:

```sh
#!/bin/sh
if grep -qiE "co-authored-by|generated with" "$1"; then
  echo "Commit rechazado: sin trailers de coautoria ni lineas de herramienta." >&2
  exit 1
fi
```

Instálalo con `chmod +x .git/hooks/commit-msg`; en Windows, guárdalo con saltos de línea LF. Limitación conocida: no detecta «generado por» en español.
