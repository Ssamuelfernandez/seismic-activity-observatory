-- =============================================================================
-- 003_jupyter_role.sql — Rol de solo lectura para los cuadernos Jupyter
--
-- No forma parte de la inicialización de PostgreSQL: se aplica a mano sobre la base
-- ya creada con `python scripts/apply_jupyter_role.py` (ver docs/jupyter.md).
--
-- La contraseña NO está aquí: psql la lee de la variable de entorno
-- DB_JUPYTER_PASSWORD. Es idempotente: crea el rol solo si no existe y actualiza
-- la contraseña.
-- =============================================================================

\set ON_ERROR_STOP on
\getenv jupyter_password DB_JUPYTER_PASSWORD

BEGIN;

SELECT 'CREATE ROLE observatory_jupyter LOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'observatory_jupyter')
\gexec

ALTER ROLE observatory_jupyter LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'jupyter_password';
-- Segunda barrera: la protección real es que solo se conceden SELECT.
ALTER ROLE observatory_jupyter SET default_transaction_read_only = on;

GRANT USAGE ON SCHEMA public, live, replay, ingest TO observatory_jupyter;

-- Quedan fuera ingest.ingest_state e ingest.raw_response (estado interno del productor).
GRANT SELECT ON
    public.country, public.date_dim,
    live.current_event, live.event_version, live.quarantine, live.exclusion,
    replay.current_event, replay.event_version, replay.quarantine, replay.exclusion,
    ingest.ingest_run
    TO observatory_jupyter;

COMMIT;
