"""SQL del productor: constantes con las sentencias de ingesta (data-model.md §1). Sin E/S."""

# Hash de la última consulta correcta (contrato db-schema.md §3.8; índice ix_ingest_run_last_ok).
LAST_OK_HASH = (
    "SELECT sha256 FROM ingest.ingest_run "
    "WHERE error IS NULL AND status = 200 ORDER BY run_at DESC, id DESC LIMIT 1"
)

RAW_RESPONSE_INSERT = (
    "INSERT INTO ingest.raw_response (fetched_at, sha256, body) VALUES ($1, $2, $3::jsonb)"
)

INGEST_RUN_INSERT = (
    "INSERT INTO ingest.ingest_run (run_at, url, status, latency_ms, event_count, sha256, error) "
    "VALUES ($1, $2, $3, $4, $5, $6, $7)"
)

# Sin objetivo de conflicto y sin RETURNING: el rol del productor solo tiene INSERT en la tabla.
EXCLUSION_INSERT = (
    "INSERT INTO live.exclusion (event_id, updated_ms, kind, reason, observed_type, fetched_at, is_synthetic) "
    "VALUES ($1, $2, $3, $4, $5, $6, $7) ON CONFLICT DO NOTHING"
)

STATE_SELECT = (
    "SELECT event_id, last_updated_ms FROM ingest.ingest_state WHERE event_id = ANY($1::text[])"
)

# Solo avanza: una marca tardía nunca retrocede el estado.
STATE_UPSERT = (
    "INSERT INTO ingest.ingest_state (event_id, last_updated_ms, published_at) VALUES ($1, $2, $3) "
    "ON CONFLICT (event_id) DO UPDATE "
    "SET last_updated_ms = EXCLUDED.last_updated_ms, published_at = EXCLUDED.published_at "
    "WHERE EXCLUDED.last_updated_ms > ingest.ingest_state.last_updated_ms"
)

# Q9: purga por antigüedad; conserva siempre la fila más reciente (research §5).
RAW_RESPONSE_PURGE = (
    "DELETE FROM ingest.raw_response "
    "WHERE fetched_at < now() - make_interval(days => $1) "
    "AND id <> (SELECT max(id) FROM ingest.raw_response)"
)
