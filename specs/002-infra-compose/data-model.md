# Modelo de infraestructura: infra-compose

Esta feature no añade tablas ni cambia `sql/001_schema.sql` ni los contratos. Define los elementos de infraestructura y los permisos de base de datos. Las entidades de la spec (servicio, evento sintético, tema, volumen, rol, variable de entorno) se concretan aquí.

## Servicios

| Servicio | Imagen | Puerto publicado | Depende de (sano) | Cómo se calcula «sano» |
|---|---|---|---|---|
| `kafka` | `apache/kafka:4.1.2` | ninguno | — | `kafka-broker-api-versions.sh` responde |
| `postgres` | `postgres:16.15-bookworm` | ninguno | — | `pg_isready` por TCP (tras aplicar esquema y roles) |
| `producer` | `seismic-observatory-python:0.1.0` | ninguno | `kafka`, `postgres` | latido < 120 s |
| `consumer` | `seismic-observatory-python:0.1.0` | ninguno | `kafka`, `postgres` | latido < 60 s |
| `api` | `seismic-observatory-python:0.1.0` | `127.0.0.1:8000` | `postgres` | `GET /api/salud` → 200 |

Red: `seismic-observatory-backend` (única). Volúmenes con nombre: `postgres-data` (`/var/lib/postgresql/data`) y `kafka-data` (`/var/lib/kafka/data`). Solo `docker compose down -v` los borra.

## Temas (definidos por `kafka-message.md` §1; aquí solo se crean)

| Tema | Particiones | Replicación | Retención |
|---|---|---|---|
| `earthquakes.live` | 1 | 1 | 7 días (`retention.ms=604800000`) |
| `earthquakes.replay` | 1 | 1 | 7 días (`retention.ms=604800000`) |

## Roles de base de datos

Los permisos son **exactamente** los de la tabla «Quién escribe y quién lee» de `db-schema.md` §1.1. `001_schema.sql` no crea roles; `002_roles.sql` sí. Todos los roles son `LOGIN` y reciben `USAGE` sobre los esquemas `public`, `live`, `replay` e `ingest`. Los permisos que falten (por ejemplo, leer `raw_response` o purgarla) los añadirá la feature que los necesite, actualizando esa tabla.

| Rol | Lo usa | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|---|
| `observatory_api` | API | `live.current_event`, `replay.current_event`, `public.country`, `ingest.ingest_run` | — | — | — |
| `observatory_producer` | productor | `ingest.ingest_state`, `ingest.ingest_run` | `live.exclusion`, `replay.exclusion`, `ingest.ingest_state`, `ingest.ingest_run`, `ingest.raw_response` | `ingest.ingest_state` | — |
| `observatory_consumer` | consumidor | `public.country`, `public.date_dim`, `current_event` y `event_version` de `live` y `replay` | `public.country`, `public.date_dim`, y `current_event`, `event_version` y `quarantine` de `live` y `replay` | `public.country`, `live.current_event`, `replay.current_event` | — |

Además, `USAGE` sobre las secuencias de identidad necesarias para insertar (`*_id_seq` de `exclusion`, `ingest_run`, `raw_response` y `quarantine`).

**Qué comprueba `scripts/verify_stack.py`**: solo los permisos de **escritura** (`INSERT`, `UPDATE` y `DELETE`) de cada rol sobre las tablas existentes de `public`, `live`, `replay` e `ingest`, y que el rol de la API puede leer sus cuatro tablas. Los permisos de lectura de productor y consumidor y los de las secuencias **no** se comprueban de forma automática; se pueden verificar a mano con `has_table_privilege(rol, tabla, 'SELECT')` y `has_sequence_privilege(rol, secuencia, 'USAGE')`.

Notas de diseño:

- **Sin lecturas ni borrados extra**: el productor no lee `exclusion` ni `raw_response` y no borra de `raw_response`; el consumidor no lee `quarantine`. La tabla §1.1 los asigna a consultas de evidencia o a otra feature.
- **`UPDATE` en `country`** (consumidor): la tabla asigna al consumidor la escritura de `country` (carga del catálogo al arrancar).
- **Carga histórica**: la tabla «Quién escribe» le asigna escritura en `live` igual que al consumidor, pero es un proceso batch de otra feature. No se crea rol para ella aquí; `historico-2025` decidirá si reutiliza `observatory_consumer` o añade uno, y actualizará esta tabla.
- **Administrador** (`POSTGRES_USER`): solo inicializa. Ningún servicio Python lo usa.
- **Contraseñas**: una por rol, de variables de entorno; no existen en el repositorio.

## Evento sintético de prueba

Mensaje conforme a `kafka-message.md` §3, sin campos nuevos:

| Campo | Valor |
|---|---|
| clave del mensaje | `event.id` |
| `source` / `mode` | `replay_demo` / `live` (valores admitidos por el contrato y por los `CHECK` de `sql/001_schema.sql`) |
| `is_synthetic` | `true` |
| `replay_at` | `null` |
| `event.id` | `synthetic-<segundos Unix>` (distinto en cada ciclo; sin colisión con identificadores de USGS) |
| `event.properties` | `mag` 1.0, `place` «Evento sintético de prueba (infra-compose)», `time` = `updated` = ahora en ms, `type` `earthquake` |
| `event.geometry` | `Point` `[0.0, 0.0, 10.0]` |

Este mensaje nunca se escribe en `current_event`: el consumidor mínimo solo lo registra.

## Variables de entorno

Ver [contracts/config.md](contracts/config.md).
