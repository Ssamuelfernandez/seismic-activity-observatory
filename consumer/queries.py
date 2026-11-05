"""Sentencias SQL del consumidor (constitución §14: el SQL vive solo aquí).

El nombre del esquema se compone únicamente desde una lista cerrada (`schema_for_mode`):
ningún texto del mensaje llega a un identificador de SQL.
"""
SCHEMAS_BY_MODE = {"live": "live", "replay": "replay"}

DATE_COLUMNS = ("date_id", "year", "month", "day", "dow")
CURRENT_COLUMNS = (
    "event_id", "event_time", "event_time_ms", "updated_at", "updated_ms", "mag", "mag_type",
    "depth_km", "lon", "lat", "place", "status", "url", "sig", "date_id", "country_id", "source",
    "is_synthetic", "ingested_at", "replay_at",
)
VERSION_COLUMNS = (
    "event_id", "updated_ms", "updated_at", "event_time", "mag", "depth_km", "original", "source",
    "is_synthetic", "received_at", "kafka_topic", "kafka_partition", "kafka_offset",
)
QUARANTINE_COLUMNS = (
    "event_id", "reason", "original", "raw_text", "original_sha256", "source", "kafka_topic",
    "kafka_partition", "kafka_offset", "received_at", "is_synthetic",
)
COUNTRY_COLUMNS = ("country_id", "name_es", "admin", "continent", "subregion")
JSONB_COLUMNS = frozenset({"original"})
# Columnas que el DO UPDATE de current_event nunca toca (solo la clave; el país se actualiza con la versión).
UPSERT_FIXED_COLUMNS = frozenset({"event_id"})


def fingerprint_query(table: str, columns: tuple[str, ...], order: str) -> str:
    """Recuento y md5 agregado de una tabla fija (huella para comprobar «0 diferencias»).

    `table`, `columns` y `order` son constantes de este módulo; nunca texto externo.
    """
    values = ", ".join(f"{name}::text" for name in columns)
    return (f"SELECT count(*), coalesce(md5(string_agg(concat_ws('|', {values}), '#' ORDER BY {order})), '') "
            f"FROM {table}")


# Verificación de la carga histórica (data-model §6): solo el esquema `live`.
HISTORICAL_LOADED_COUNT = "SELECT count(*) FROM live.current_event WHERE event_id = ANY($1)"
# Q (cuarentena) no se consulta: el rol del consumidor solo puede INSERTAR en `live.quarantine`.
HISTORICAL_SOURCE_COUNT = "SELECT count(*) FROM live.current_event WHERE source = 'usgs_historical'"
FINGERPRINT_CURRENT = fingerprint_query("live.current_event", CURRENT_COLUMNS, "event_id")
FINGERPRINT_VERSION = fingerprint_query("live.event_version", VERSION_COLUMNS, "event_id, updated_ms")
# Sin la columna `id` de la cuarentena (identidad): la clave natural es (hash, motivo).
FINGERPRINT_QUARANTINE = fingerprint_query("live.quarantine", QUARANTINE_COLUMNS, "original_sha256, reason")


def schema_for_mode(mode: str) -> str:
    """Devuelve el esquema destino de un modo (`live` o `replay`); otro texto lanza ValueError."""
    try:
        return SCHEMAS_BY_MODE[mode]
    except KeyError:
        raise ValueError(f"Modo desconocido para elegir esquema: {mode!r}") from None


def _placeholders(columns: tuple[str, ...]) -> str:
    """Lista `$1, $2::jsonb, ...` con la conversión a jsonb en las columnas que la necesitan."""
    parts = [f"${i}::jsonb" if name in JSONB_COLUMNS else f"${i}" for i, name in enumerate(columns, 1)]
    return ", ".join(parts)


def _insert(table: str, columns: tuple[str, ...], tail: str) -> str:
    """Compone un `INSERT INTO tabla (columnas) VALUES (...)` con la cola indicada."""
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({_placeholders(columns)}) {tail}"


DATE_DIM_INSERT = _insert("public.date_dim", DATE_COLUMNS, "ON CONFLICT (date_id) DO NOTHING")

COUNTRY_UPSERT = (
    _insert("public.country", COUNTRY_COLUMNS, "ON CONFLICT (country_id) DO UPDATE SET "
            "name_es = EXCLUDED.name_es, admin = EXCLUDED.admin, continent = EXCLUDED.continent, "
            "subregion = EXCLUDED.subregion WHERE (public.country.name_es, public.country.admin, "
            "public.country.continent, public.country.subregion) IS DISTINCT FROM "
            "(EXCLUDED.name_es, EXCLUDED.admin, EXCLUDED.continent, EXCLUDED.subregion)")
)

COUNTRY_COUNT = "SELECT count(*) FROM public.country"
# `::text` evita depender del decodificador de `regclass`; NULL = la tabla no existe.
REGCLASS_CHECK = "SELECT to_regclass($1)::text"


def select_stored_updated(mode: str) -> str:
    """Estado previo: `updated_ms` actual del evento, bloqueando su fila."""
    return f"SELECT updated_ms FROM {schema_for_mode(mode)}.current_event WHERE event_id = $1 FOR UPDATE"


def event_version_insert(mode: str) -> str:
    """Inserta la versión; un duplicado (evento, updated) no hace nada."""
    return _insert(f"{schema_for_mode(mode)}.event_version", VERSION_COLUMNS,
                   "ON CONFLICT (event_id, updated_ms) DO NOTHING")


def version_content_differs(mode: str) -> str:
    """Compara (jsonb) el `original` guardado con el recibido ($1) para (evento $2, updated $3)."""
    return (f"SELECT original IS DISTINCT FROM $1::jsonb FROM {schema_for_mode(mode)}.event_version "
            "WHERE event_id = $2 AND updated_ms = $3")


def current_event_upsert(mode: str) -> str:
    """Upsert condicional del estado actual: solo gana un `updated` estrictamente mayor."""
    table = f"{schema_for_mode(mode)}.current_event"
    assignments = ", ".join(f"{c} = EXCLUDED.{c}" for c in CURRENT_COLUMNS if c not in UPSERT_FIXED_COLUMNS)
    tail = (f"ON CONFLICT (event_id) DO UPDATE SET {assignments} "
            f"WHERE EXCLUDED.updated_ms > {table}.updated_ms")
    return _insert(table, CURRENT_COLUMNS, tail)


def quarantine_insert(mode: str) -> str:
    """Cuarentena sin SELECT: `ON CONFLICT DO NOTHING` sin destino, sin RETURNING (research §8)."""
    return _insert(f"{schema_for_mode(mode)}.quarantine", QUARANTINE_COLUMNS, "ON CONFLICT DO NOTHING")
