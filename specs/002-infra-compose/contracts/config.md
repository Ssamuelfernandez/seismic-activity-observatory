# Contrato de configuración: variables de entorno

Lista todas las variables de entorno del sistema y su correspondencia entre `.env.example`, `compose.yaml` y el código. `scripts/check_env_example.py` comprueba tres reglas: (1) las variables que `compose.yaml` interpola con `${…}` son exactamente las de `.env.example`; (2) toda variable que el código lee (`read_str`/`read_int`) la define algún servicio en `compose.yaml`; (3) las contraseñas de `.env.example` son de ejemplo (`cambia-esta-clave…`).

Los valores de `.env.example` son **ejemplos no sensibles**. El archivo real es `.env`, ignorado por Git. Si falta una variable obligatoria, `docker compose` falla nombrándola (`${VAR:?mensaje}`) y el código lanza `ConfigError` con su nombre.

## A. Variables de `.env.example` (las que el usuario edita)

| Variable | Ejemplo | Quién la usa | Cómo llega al código | Descripción |
|---|---|---|---|---|
| `POSTGRES_USER` | `observatory_admin` | `postgres` | tal cual | Administrador de la base; solo inicializa (esquema y roles). Ningún servicio Python lo usa |
| `POSTGRES_PASSWORD` | `cambia-esta-clave-admin` | `postgres` | tal cual | Contraseña del administrador |
| `POSTGRES_DB` | `observatory` | `postgres`, `producer`, `consumer`, `api` | `DB_NAME` en los servicios Python | Nombre de la base |
| `DB_API_PASSWORD` | `cambia-esta-clave-api` | `postgres` (crea el rol), `api` | `DB_PASSWORD` en `api` | Contraseña del rol `observatory_api` (solo lectura) |
| `DB_PRODUCER_PASSWORD` | `cambia-esta-clave-productor` | `postgres`, `producer` | `DB_PASSWORD` en `producer` | Contraseña del rol `observatory_producer` |
| `DB_CONSUMER_PASSWORD` | `cambia-esta-clave-consumidor` | `postgres`, `consumer` | `DB_PASSWORD` en `consumer` | Contraseña del rol `observatory_consumer` |
| `DB_HOST` | `postgres` | `producer`, `consumer`, `api` | tal cual | Nombre de servicio de la base, nunca `localhost` (A7) |
| `DB_PORT` | `5432` | `producer`, `consumer`, `api` | tal cual | Puerto interno de PostgreSQL (1–65535) |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | `producer`, `consumer` | tal cual | Dirección del broker por nombre de servicio (A7) |
| `KAFKA_TOPIC` | `earthquakes.live` | `producer`, `consumer` | tal cual | Tema donde publica el productor y del que lee el consumidor |
| `KAFKA_GROUP_ID` | `consumer-minimal` | `consumer` | tal cual | Grupo del consumidor |
| `PRODUCER_INTERVAL_SECONDS` | `30` | `producer` | tal cual | Segundos entre eventos sintéticos; entre 1 y 60 (FR-012) |
| `RETRY_INITIAL_SECONDS` | `1` | `producer`, `consumer`, `api` | tal cual | Primera espera entre reintentos de conexión (≥ 1) |
| `RETRY_MAX_SECONDS` | `30` | `producer`, `consumer`, `api` | tal cual | Espera máxima entre reintentos (≥ `RETRY_INITIAL_SECONDS`) |
| `LOG_LEVEL` | `INFO` | `producer`, `consumer`, `api` | tal cual | Nivel de registro |

Total: **15** variables.

## B. Variables que `compose.yaml` fija (no están en `.env.example`)

Son constantes de diseño, no configuración del usuario. Las lee el código; el valor lo decide el plan.

| Variable | Valor | Servicio | Motivo |
|---|---|---|---|
| `DB_USER` | `observatory_producer` / `observatory_consumer` / `observatory_api` | cada uno | Cada servicio usa su propio rol (FR-030); el nombre del rol es parte del diseño de permisos |
| `HEALTH_FILE` | `/tmp/producer.alive` / `/tmp/consumer.alive` | `producer`, `consumer` | Ruta interna del latido |
| `HEALTH_MAX_AGE_SECONDS` | `120` (productor) / `60` (consumidor) | `producer`, `consumer` | Antigüedad máxima del latido. Debe cumplirse `PRODUCER_INTERVAL_SECONDS` ≤ `HEALTH_MAX_AGE_SECONDS` / 2 |

## C. Variables de las imágenes oficiales (las pone `compose.yaml`; el código Python no las lee)

| Imagen | Variables | Notas |
|---|---|---|
| `apache/kafka` | `KAFKA_NODE_ID`, `KAFKA_PROCESS_ROLES`, `KAFKA_LISTENERS`, `KAFKA_ADVERTISED_LISTENERS`, `KAFKA_LISTENER_SECURITY_PROTOCOL_MAP`, `KAFKA_INTER_BROKER_LISTENER_NAME`, `KAFKA_CONTROLLER_LISTENER_NAMES`, `KAFKA_CONTROLLER_QUORUM_VOTERS`, factores de replicación de los temas internos (1), `KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS`, `KAFKA_AUTO_CREATE_TOPICS_ENABLE=false`, `KAFKA_LOG_RETENTION_HOURS=168`, `KAFKA_LOG_DIRS` | Un solo nodo (broker y controlador), listener interno `kafka:9092`. Sin listener para el equipo anfitrión (ver research.md §3) |
| `postgres` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (de la sección A), más `DB_*_PASSWORD` que lee `scripts/postgres_init.sh` | El script falla si falta alguna |

## D. Lectura en el código

| Función (`common/config.py`) | Variables |
|---|---|
| `load_kafka_settings` | `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_TOPIC` |
| `load_database_settings` | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` |
| `load_retry_settings` | `RETRY_INITIAL_SECONDS`, `RETRY_MAX_SECONDS` (con valores por defecto en el código: 1 y 30) |
| `load_health_settings` | `HEALTH_FILE`, `HEALTH_MAX_AGE_SECONDS` |
| `load_log_level` | `LOG_LEVEL` (por defecto `INFO`) |
| `producer.loop.read_interval_seconds` | `PRODUCER_INTERVAL_SECONDS` |
| `consumer.main` | `KAFKA_GROUP_ID` |

El código lee 14 nombres distintos; los 14 están definidos en `compose.yaml` (A: 11 con `${…}`; B: `DB_USER`, `HEALTH_FILE`, `HEALTH_MAX_AGE_SECONDS`).


## E. Umbrales de salud (latido y healthchecks)

Valores fijados en `compose.yaml`; los verifican las tareas T014 (latido) y T015 (API) de `tasks.md`. El razonamiento está en `research.md` §6.

| Servicio | Sano cuando… | Antigüedad máxima del latido (`HEALTH_MAX_AGE_SECONDS`) | `interval` | `timeout` | `retries` | `start_period` |
|---|---|---|---|---|---|---|
| `producer` | el archivo de latido se renovó hace menos del máximo | **120 s** | 15 s | 5 s | 3 | 90 s |
| `consumer` | ídem | **60 s** | 15 s | 5 s | 3 | 90 s |
| `api` | `GET /api/salud` responde 2xx | — | 10 s | 5 s | 5 | 20 s |
| `postgres` | `pg_isready` por TCP (tras aplicar esquema y roles) | — | 5 s | 5 s | 20 | 20 s |
| `kafka` | `kafka-broker-api-versions.sh` responde | — | 15 s | 10 s | 10 | 40 s |

Reglas y tiempos esperados:

- **Coherencia**: `PRODUCER_INTERVAL_SECONDS` ≤ `HEALTH_MAX_AGE_SECONDS` / 2 del productor (hoy ≤ 60 s). El productor lo valida al arrancar.
- **Latido**: el servicio lo borra al arrancar y lo renueva solo tras una vuelta correcta del bucle (productor: evento publicado y confirmado; consumidor: consulta al broker, cada segundo).
- **Detección tras parar Kafka**: el latido caduca a los 60 s (consumidor) o 120 s (productor); `unhealthy` llega tras 3 comprobaciones fallidas consecutivas, cada 15 s. Esperado: consumidor `unhealthy` a los 90–120 s y productor a los 150–180 s de haber parado el broker. Un valor fuera de estos rangos se trata como fallo en T014 (o se corrige esta tabla si el cálculo era erróneo).
