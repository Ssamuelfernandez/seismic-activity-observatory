-- =============================================================================
-- 002_roles.sql — Roles de base de datos y permisos de cada servicio (infra-compose)
--
-- Fuente de los permisos: db-schema.md §1.1 «Quién escribe y quién lee». 001_schema.sql
-- no crea roles; este archivo se ejecuta después de él, con el administrador, en la
-- primera inicialización (scripts/postgres_init.sh).
--
-- Las contraseñas NO están aquí: llegan como variables de psql (-v) leídas de variables de
-- entorno. Es idempotente: crea los roles solo si no existen y actualiza la contraseña.
--
-- Variables de psql: api_password, producer_password, consumer_password.
-- Mínimo privilegio: la API solo lee; productor y consumidor escriben solo lo que fija el contrato.
-- =============================================================================

\set ON_ERROR_STOP on

-- Roles (LOGIN, sin superusuario, sin crear bases ni roles).
SELECT format('CREATE ROLE %I LOGIN', role_name)
FROM (VALUES ('observatory_api'), ('observatory_producer'), ('observatory_consumer')) AS roles(role_name)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name)
\gexec

ALTER ROLE observatory_api      PASSWORD :'api_password';
ALTER ROLE observatory_producer PASSWORD :'producer_password';
ALTER ROLE observatory_consumer PASSWORD :'consumer_password';

-- Acceso a los esquemas (sin USAGE no se ve ninguna tabla).
GRANT USAGE ON SCHEMA public TO observatory_api, observatory_producer, observatory_consumer;
GRANT USAGE ON SCHEMA live    TO observatory_api, observatory_producer, observatory_consumer;
GRANT USAGE ON SCHEMA replay  TO observatory_api, observatory_producer, observatory_consumer;
GRANT USAGE ON SCHEMA ingest  TO observatory_api, observatory_producer, observatory_consumer;

-- -----------------------------------------------------------------------------
-- API: solo lectura (current_event de live y replay, country e ingest_run).
-- -----------------------------------------------------------------------------
GRANT SELECT ON live.current_event, replay.current_event, public.country, ingest.ingest_run
    TO observatory_api;

-- -----------------------------------------------------------------------------
-- Productor (db-schema.md §1.1):
--   escribe exclusion (live y replay), ingest_state, ingest_run y raw_response;
--   lee ingest_state e ingest_run (Q12).
-- productor-live añade SELECT y DELETE sobre raw_response: la purga por retención (§3.9)
-- necesita DELETE y SELECT (para el WHERE y la subconsulta). No es un cambio de contrato.
-- -----------------------------------------------------------------------------
GRANT INSERT ON live.exclusion, replay.exclusion TO observatory_producer;
GRANT SELECT, INSERT, UPDATE ON ingest.ingest_state TO observatory_producer;
GRANT SELECT, INSERT ON ingest.ingest_run TO observatory_producer;
GRANT SELECT, INSERT, DELETE ON ingest.raw_response TO observatory_producer;
GRANT USAGE ON SEQUENCE live.exclusion_id_seq, replay.exclusion_id_seq,
                        ingest.ingest_run_id_seq, ingest.raw_response_id_seq
    TO observatory_producer;

-- -----------------------------------------------------------------------------
-- Consumidor (db-schema.md §1.1):
--   escribe country, date_dim, current_event, event_version y quarantine (live y replay);
--   lee country, date_dim, current_event y event_version (clave foránea y comparar updated).
-- -----------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE ON public.country TO observatory_consumer;
GRANT SELECT, INSERT ON public.date_dim TO observatory_consumer;
GRANT SELECT, INSERT, UPDATE ON live.current_event, replay.current_event TO observatory_consumer;
GRANT SELECT, INSERT ON live.event_version, replay.event_version TO observatory_consumer;
GRANT INSERT ON live.quarantine, replay.quarantine TO observatory_consumer;
GRANT USAGE ON SEQUENCE live.quarantine_id_seq, replay.quarantine_id_seq TO observatory_consumer;
