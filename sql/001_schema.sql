-- =============================================================================
-- 001_schema.sql — Esquema de base de datos del observatorio sísmico
--
-- Fuente de verdad documental: specs/001-contratos-y-modelo/contracts/db-schema.md
-- (mismas tablas, columnas, claves e índices; si cambia uno, cambia el otro).
--
-- Idempotente: puede ejecutarse más de una vez (IF NOT EXISTS). No carga datos:
-- el catálogo de países y la tabla de fechas se cargan en la feature
-- consumidor-idempotente.
--
-- Esquemas:
--   public  catálogo compartido (country, date_dim)
--   live    datos en vivo e histórico 2025 (current_event, event_version, quarantine, exclusion)
--   replay  reproducción histórica: mismas tablas que live, aislada de ella (J3)
--   ingest  estado del productor (ingest_state, ingest_run, raw_response)
--
-- Quién escribe y quién lee cada tabla: db-schema.md §1.1 (la API es solo lectura;
-- los roles y permisos se definen en la feature infra-compose, no aquí).
--
-- Convención: los esquemas live y replay se escriben a mano, uno tras otro, con
-- idéntico contenido. Los comentarios "Qn" remiten a la consulta que justifica
-- cada índice (tabla de consultas en db-schema.md §4).
-- =============================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS live;
CREATE SCHEMA IF NOT EXISTS replay;
CREATE SCHEMA IF NOT EXISTS ingest;

-- -----------------------------------------------------------------------------
-- public.country — catálogo de países (data/catalogo/paises.geojson)
-- Grano: una fila por entidad del catálogo. Clave: country_id (= ADM0_A3).
-- Origen de columnas: ADM0_A3, NAME_ES, ADMIN, CONTINENT, SUBREGION.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.country (
    country_id  text PRIMARY KEY CHECK (country_id ~ '^[A-Z]{3}$'),
    name_es     text NOT NULL,
    admin       text NOT NULL,
    continent   text NOT NULL,
    subregion   text NOT NULL
);

-- -----------------------------------------------------------------------------
-- public.date_dim — dimensión de fechas
-- Grano: una fila por día UTC. Clave: date_id. dow sigue ISO (1 = lunes ... 7 = domingo).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.date_dim (
    date_id  date PRIMARY KEY,
    year     smallint NOT NULL,
    month    smallint NOT NULL CHECK (month BETWEEN 1 AND 12),
    day      smallint NOT NULL CHECK (day BETWEEN 1 AND 31),
    dow      smallint NOT NULL CHECK (dow BETWEEN 1 AND 7)
);

-- =============================================================================
-- Esquema live
-- =============================================================================

-- live.current_event — estado actual. Grano: una fila por evento (versión más reciente).
CREATE TABLE IF NOT EXISTS live.current_event (
    event_id       text PRIMARY KEY,
    event_time     timestamptz NOT NULL,
    event_time_ms  bigint NOT NULL,
    updated_at     timestamptz NOT NULL,
    updated_ms     bigint NOT NULL,
    mag            numeric,
    mag_type       text,
    depth_km       numeric,
    lon            double precision NOT NULL,
    lat            double precision NOT NULL,
    place          text,
    status         text,
    url            text,
    sig            integer,
    country_id     text REFERENCES public.country (country_id),
    date_id        date NOT NULL REFERENCES public.date_dim (date_id),
    source         text NOT NULL,
    is_synthetic   boolean NOT NULL DEFAULT false,
    ingested_at    timestamptz NOT NULL,
    replay_at      timestamptz,
    -- Rangos de cordura (DECIDIDOS, db-schema.md §2): descartan NaN/Infinity y valores
    -- imposibles, no los negativos.
    CONSTRAINT current_event_mag_range   CHECK (mag BETWEEN -10 AND 15),
    CONSTRAINT current_event_depth_range CHECK (depth_km BETWEEN -100 AND 1000),
    CONSTRAINT current_event_lon_range   CHECK (lon BETWEEN -180 AND 180),
    CONSTRAINT current_event_lat_range   CHECK (lat BETWEEN -90 AND 90),
    CONSTRAINT current_event_source_values
        CHECK (source IN ('usgs_feed', 'usgs_historical', 'replay_demo')),
    -- El instante convertido debe coincidir con el valor original en ms Unix.
    CONSTRAINT current_event_time_matches_ms
        CHECK (event_time = timestamptz 'epoch' + event_time_ms * interval '1 millisecond'),
    CONSTRAINT current_event_updated_matches_ms
        CHECK (updated_at = timestamptz 'epoch' + updated_ms * interval '1 millisecond'),
    CONSTRAINT current_event_date_matches_time
        CHECK (date_id = (event_time AT TIME ZONE 'UTC')::date)
);

-- Q1: listado por intervalo con orden estable y paginación por cursor (event_time DESC, event_id DESC);
-- también sirve a Q4 (conteo por hora) y a la comparación con 2025 (rango de un año).
CREATE INDEX IF NOT EXISTS ix_current_event_time
    ON live.current_event (event_time DESC, event_id DESC);
-- Q2: filtro por país dentro de un intervalo y recuentos por país.
CREATE INDEX IF NOT EXISTS ix_current_event_country_time
    ON live.current_event (country_id, event_time DESC);
-- Q3: filtro por magnitud mínima (candidato; se conserva solo si EXPLAIN ANALYZE lo justifica, E6).
CREATE INDEX IF NOT EXISTS ix_current_event_mag
    ON live.current_event (mag);

-- live.event_version — historial. Grano: una fila por (evento, valor de updated) recibido.
CREATE TABLE IF NOT EXISTS live.event_version (
    event_id        text NOT NULL,
    updated_ms      bigint NOT NULL,
    updated_at      timestamptz NOT NULL,
    event_time      timestamptz NOT NULL,
    mag             numeric,
    depth_km        numeric,
    original        jsonb NOT NULL,
    source          text NOT NULL,
    is_synthetic    boolean NOT NULL DEFAULT false,
    received_at     timestamptz NOT NULL,
    kafka_topic     text,
    kafka_partition integer,
    kafka_offset    bigint,
    PRIMARY KEY (event_id, updated_ms),
    -- Diferida: la versión y el estado actual se escriben en la misma transacción, en cualquier orden.
    CONSTRAINT event_version_event_fk FOREIGN KEY (event_id)
        REFERENCES live.current_event (event_id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT event_version_mag_range   CHECK (mag BETWEEN -10 AND 15),
    CONSTRAINT event_version_depth_range CHECK (depth_km BETWEEN -100 AND 1000),
    CONSTRAINT event_version_source_values
        CHECK (source IN ('usgs_feed', 'usgs_historical', 'replay_demo')),
    CONSTRAINT event_version_updated_matches_ms
        CHECK (updated_at = timestamptz 'epoch' + updated_ms * interval '1 millisecond')
);
-- Q5/Q6: la clave primaria (event_id, updated_ms) cubre la comprobación de duplicados
-- (ON CONFLICT DO NOTHING) y la consulta del historial de un evento; no necesita índice extra.

-- live.quarantine — datos inválidos. Grano: un original rechazado por un motivo.
CREATE TABLE IF NOT EXISTS live.quarantine (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id         text,
    reason           text NOT NULL,
    original         jsonb,
    raw_text         text,
    original_sha256  text NOT NULL CHECK (original_sha256 ~ '^[0-9a-f]{64}$'),
    source           text,
    kafka_topic      text,
    kafka_partition  integer,
    kafka_offset     bigint,
    received_at      timestamptz NOT NULL,
    is_synthetic     boolean NOT NULL DEFAULT false,
    CONSTRAINT quarantine_has_original CHECK (original IS NOT NULL OR raw_text IS NOT NULL),
    CONSTRAINT quarantine_source_values
        CHECK (source IS NULL OR source IN ('usgs_feed', 'usgs_historical', 'replay_demo')),
    -- Q10: reprocesar el mismo original por el mismo motivo no duplica la fila (idempotencia).
    CONSTRAINT quarantine_original_reason_key UNIQUE (original_sha256, reason)
);
-- Q7: consultar por qué se rechazó un evento concreto.
CREATE INDEX IF NOT EXISTS ix_quarantine_event_id
    ON live.quarantine (event_id) WHERE event_id IS NOT NULL;

-- live.exclusion — descartes controlados (p. ej. type distinto de earthquake, B3).
-- Grano: una fila por (evento, updated, tipo de exclusión).
CREATE TABLE IF NOT EXISTS live.exclusion (
    id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id       text NOT NULL,
    updated_ms     bigint NOT NULL,
    kind           text NOT NULL,
    reason         text NOT NULL,
    observed_type  text,
    fetched_at     timestamptz NOT NULL,
    is_synthetic   boolean NOT NULL DEFAULT false,
    -- Q11: el feed repite el mismo evento en cada consulta; no se registra dos veces.
    CONSTRAINT exclusion_event_kind_key UNIQUE (event_id, updated_ms, kind)
);

-- =============================================================================
-- Esquema replay (mismas tablas que live)
-- =============================================================================

CREATE TABLE IF NOT EXISTS replay.current_event (
    event_id       text PRIMARY KEY,
    event_time     timestamptz NOT NULL,
    event_time_ms  bigint NOT NULL,
    updated_at     timestamptz NOT NULL,
    updated_ms     bigint NOT NULL,
    mag            numeric,
    mag_type       text,
    depth_km       numeric,
    lon            double precision NOT NULL,
    lat            double precision NOT NULL,
    place          text,
    status         text,
    url            text,
    sig            integer,
    country_id     text REFERENCES public.country (country_id),
    date_id        date NOT NULL REFERENCES public.date_dim (date_id),
    source         text NOT NULL,
    is_synthetic   boolean NOT NULL DEFAULT false,
    ingested_at    timestamptz NOT NULL,
    replay_at      timestamptz,
    CONSTRAINT current_event_mag_range   CHECK (mag BETWEEN -10 AND 15),
    CONSTRAINT current_event_depth_range CHECK (depth_km BETWEEN -100 AND 1000),
    CONSTRAINT current_event_lon_range   CHECK (lon BETWEEN -180 AND 180),
    CONSTRAINT current_event_lat_range   CHECK (lat BETWEEN -90 AND 90),
    CONSTRAINT current_event_source_values
        CHECK (source IN ('usgs_feed', 'usgs_historical', 'replay_demo')),
    CONSTRAINT current_event_time_matches_ms
        CHECK (event_time = timestamptz 'epoch' + event_time_ms * interval '1 millisecond'),
    CONSTRAINT current_event_updated_matches_ms
        CHECK (updated_at = timestamptz 'epoch' + updated_ms * interval '1 millisecond'),
    CONSTRAINT current_event_date_matches_time
        CHECK (date_id = (event_time AT TIME ZONE 'UTC')::date)
);

CREATE INDEX IF NOT EXISTS ix_current_event_time
    ON replay.current_event (event_time DESC, event_id DESC);
CREATE INDEX IF NOT EXISTS ix_current_event_country_time
    ON replay.current_event (country_id, event_time DESC);
CREATE INDEX IF NOT EXISTS ix_current_event_mag
    ON replay.current_event (mag);

CREATE TABLE IF NOT EXISTS replay.event_version (
    event_id        text NOT NULL,
    updated_ms      bigint NOT NULL,
    updated_at      timestamptz NOT NULL,
    event_time      timestamptz NOT NULL,
    mag             numeric,
    depth_km        numeric,
    original        jsonb NOT NULL,
    source          text NOT NULL,
    is_synthetic    boolean NOT NULL DEFAULT false,
    received_at     timestamptz NOT NULL,
    kafka_topic     text,
    kafka_partition integer,
    kafka_offset    bigint,
    PRIMARY KEY (event_id, updated_ms),
    CONSTRAINT event_version_event_fk FOREIGN KEY (event_id)
        REFERENCES replay.current_event (event_id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT event_version_mag_range   CHECK (mag BETWEEN -10 AND 15),
    CONSTRAINT event_version_depth_range CHECK (depth_km BETWEEN -100 AND 1000),
    CONSTRAINT event_version_source_values
        CHECK (source IN ('usgs_feed', 'usgs_historical', 'replay_demo')),
    CONSTRAINT event_version_updated_matches_ms
        CHECK (updated_at = timestamptz 'epoch' + updated_ms * interval '1 millisecond')
);

CREATE TABLE IF NOT EXISTS replay.quarantine (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id         text,
    reason           text NOT NULL,
    original         jsonb,
    raw_text         text,
    original_sha256  text NOT NULL CHECK (original_sha256 ~ '^[0-9a-f]{64}$'),
    source           text,
    kafka_topic      text,
    kafka_partition  integer,
    kafka_offset     bigint,
    received_at      timestamptz NOT NULL,
    is_synthetic     boolean NOT NULL DEFAULT false,
    CONSTRAINT quarantine_has_original CHECK (original IS NOT NULL OR raw_text IS NOT NULL),
    CONSTRAINT quarantine_source_values
        CHECK (source IS NULL OR source IN ('usgs_feed', 'usgs_historical', 'replay_demo')),
    CONSTRAINT quarantine_original_reason_key UNIQUE (original_sha256, reason)
);
CREATE INDEX IF NOT EXISTS ix_quarantine_event_id
    ON replay.quarantine (event_id) WHERE event_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS replay.exclusion (
    id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id       text NOT NULL,
    updated_ms     bigint NOT NULL,
    kind           text NOT NULL,
    reason         text NOT NULL,
    observed_type  text,
    fetched_at     timestamptz NOT NULL,
    is_synthetic   boolean NOT NULL DEFAULT false,
    CONSTRAINT exclusion_event_kind_key UNIQUE (event_id, updated_ms, kind)
);

-- =============================================================================
-- Esquema ingest (estado del productor)
-- =============================================================================

-- ingest.ingest_state — último updated publicado. Grano: una fila por evento publicado.
-- Clave primaria event_id: Q12 (el productor decide si publica comparando con esta fila).
CREATE TABLE IF NOT EXISTS ingest.ingest_state (
    event_id         text PRIMARY KEY,
    last_updated_ms  bigint NOT NULL,
    published_at     timestamptz NOT NULL
);

-- ingest.ingest_run — consultas al feed. Grano: una fila por consulta (correcta o fallida).
CREATE TABLE IF NOT EXISTS ingest.ingest_run (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_at        timestamptz NOT NULL,
    url           text NOT NULL,
    status        integer,
    latency_ms    integer CHECK (latency_ms >= 0),
    event_count   integer CHECK (event_count >= 0),
    sha256        text,
    error         text
);
-- Q8: última consulta correcta (last_ingestion de /api/salud y de metadata). Índice parcial.
CREATE INDEX IF NOT EXISTS ix_ingest_run_last_ok
    ON ingest.ingest_run (run_at DESC) WHERE error IS NULL AND status = 200;

-- ingest.raw_response — respuestas originales. Grano: una fila por cuerpo distinto
-- (se inserta solo si el hash difiere del anterior).
CREATE TABLE IF NOT EXISTS ingest.raw_response (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fetched_at  timestamptz NOT NULL,
    sha256      text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    body        jsonb NOT NULL
);
-- Q9: purga por antigüedad (retención definida en la feature productor-live).
CREATE INDEX IF NOT EXISTS ix_raw_response_fetched_at ON ingest.raw_response (fetched_at);
-- Q13: recuperar el cuerpo original de una consulta a partir del hash de ingest_run.
CREATE INDEX IF NOT EXISTS ix_raw_response_sha256 ON ingest.raw_response (sha256);

-- =============================================================================
-- Comentarios de tabla (grano)
-- =============================================================================

COMMENT ON TABLE public.country IS 'Una fila por entidad del catálogo de países (ADM0_A3).';
COMMENT ON TABLE public.date_dim IS 'Una fila por día UTC.';
COMMENT ON TABLE live.current_event IS 'Una fila por evento: su versión más reciente (en vivo e histórico).';
COMMENT ON TABLE live.event_version IS 'Una fila por (evento, updated) recibido; conserva el original.';
COMMENT ON TABLE live.quarantine IS 'Un original inválido rechazado por un motivo.';
COMMENT ON TABLE live.exclusion IS 'Un evento descartado de forma controlada (p. ej. type distinto de earthquake).';
COMMENT ON TABLE replay.current_event IS 'Una fila por evento reproducido: su versión más reciente.';
COMMENT ON TABLE replay.event_version IS 'Una fila por (evento, updated) reproducido; conserva el original.';
COMMENT ON TABLE replay.quarantine IS 'Un original inválido de la reproducción, rechazado por un motivo.';
COMMENT ON TABLE replay.exclusion IS 'Un evento de la reproducción descartado de forma controlada.';
COMMENT ON TABLE ingest.ingest_state IS 'Último updated publicado por evento.';
COMMENT ON TABLE ingest.ingest_run IS 'Una consulta al feed de USGS (correcta o fallida).';
COMMENT ON TABLE ingest.raw_response IS 'Una respuesta original distinta de la anterior (por hash).';

COMMIT;
