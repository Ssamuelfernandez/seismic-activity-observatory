"""Estructuras inmutables del procesamiento de mensajes (data-model.md §1).

Solo datos: sin E/S ni lógica. Las comparten las funciones puras de `common/` y el consumidor.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class VersionOutcome(Enum):
    """Qué ocurrió con la versión de un evento al escribirla (data-model.md §3)."""

    NEW_EVENT = "new_event"
    NEWER_VERSION = "newer_version"
    LATE_OLD_VERSION = "late_old_version"
    REDELIVERY = "redelivery_ignored"
    SAME_UPDATED_CONFLICT = "same_updated_conflict"


class ResultKind(Enum):
    """Destino final de un mensaje: tablas de eventos o cuarentena."""

    EVENT = "event"
    QUARANTINE = "quarantine"


@dataclass(frozen=True)
class MessageRef:
    """Referencia a un mensaje de Kafka (columnas `kafka_*` de las tablas).

    `partition` y `offset` en `None` significan «carga por lote, sin referencia Kafka» (histórico);
    el `topic` se conserva porque de él se derivan el modo y el esquema.
    """

    topic: str
    partition: int | None
    offset: int | None


def kafka_columns(ref: MessageRef) -> tuple[str | None, int | None, int | None]:
    """Devuelve `(kafka_topic, kafka_partition, kafka_offset)` para las filas de la base.

    Qué hace:
        Copia la referencia tal cual si es de Kafka; si no tiene partición (carga por lote)
        devuelve tres `None`, como admite el contrato (`db-schema.md` §3.2 y §3.5).
    Recibe:
        ref: referencia del mensaje.
    Devuelve:
        Tupla con las tres columnas `kafka_*`.
    Por qué existe:
        Evita copiar `ref.*` en cada constructor de filas y permite el histórico sin Kafka.
    """
    if ref.partition is None:
        return None, None, None
    return ref.topic, ref.partition, ref.offset


@dataclass(frozen=True)
class RawRecord:
    """Registro leído de Kafka tal como llega, antes de decodificar.

    Por qué existe:
        Aísla al resto del código de los objetos de `aiokafka` (FR-030).
    """

    topic: str
    partition: int | None
    offset: int | None
    key: bytes | None
    value: bytes | None

    @property
    def ref(self) -> MessageRef:
        """Devuelve la referencia `topic/partition/offset` del registro."""
        return MessageRef(self.topic, self.partition, self.offset)


@dataclass(frozen=True)
class DecodeResult:
    """Resultado de `decode_value`.

    `raw` es siempre `bytes` (vacío si el valor Kafka era nulo); `ok = False` equivale al
    motivo `invalid_json`; `obj` es el valor JSON deserializado cuando `ok` es verdadero.
    """

    raw: bytes
    obj: Any
    ok: bool


@dataclass(frozen=True)
class ValidEvent:
    """Mensaje que superó los 14 motivos de cuarentena, con sus campos ya tipados.

    `event` es el objeto GeoJSON original (se conserva íntegro en `event_version.original`).
    """

    source: str
    mode: str
    ingested_at: datetime
    replay_at: datetime | None
    is_synthetic: bool
    event: dict
    event_id: str
    time_ms: int
    updated_ms: int
    mag: int | float | None
    depth: int | float | None
    lon: int | float
    lat: int | float
    place: str | None
    status: str | None
    url: str | None
    sig: int | None
    mag_type: str | None


@dataclass(frozen=True)
class Rejection:
    """Resultado negativo de `validate_message`: el primer motivo que falló."""

    reason: str


@dataclass(frozen=True)
class DateRow:
    """Fila de `public.date_dim` (día UTC; `dow` ISO, 1 = lunes ... 7 = domingo)."""

    date_id: date
    year: int
    month: int
    day: int
    dow: int


@dataclass(frozen=True)
class EventRows:
    """Filas listas para escribir de un evento válido (salida de `build_event_rows`).

    `current` y `version` son diccionarios columna -> valor; `country_id` va solo en `current`
    (`None` = sin país). `original` es el `event` serializado como texto JSON.
    """

    current: dict
    version: dict
    date: DateRow
    nulls: tuple[str, ...]
    original: str

    @property
    def source(self) -> str:
        """Origen copiado del sobre."""
        return self.current["source"]

    @property
    def ingested_at(self) -> datetime:
        """Instante de ingesta del productor (UTC), copiado del sobre."""
        return self.current["ingested_at"]

    @property
    def replay_at(self) -> datetime | None:
        """Instante de publicación del replay (UTC) o `None` en un mensaje live."""
        return self.current["replay_at"]

    @property
    def is_synthetic(self) -> bool:
        """Marca de dato sintético copiada del sobre."""
        return self.current["is_synthetic"]


@dataclass(frozen=True)
class CountryRow:
    """Fila de `public.country` (C10): código ADM0_A3 y nombres del catálogo."""

    country_id: str
    name_es: str
    admin: str
    continent: str
    subregion: str


@dataclass(frozen=True)
class QuarantineRow:
    """Fila de `quarantine` (todas las columnas salvo `id`)."""

    event_id: str | None
    reason: str
    original: str | None
    raw_text: str | None
    original_sha256: str
    source: str | None
    kafka_topic: str | None
    kafka_partition: int | None
    kafka_offset: int | None
    received_at: datetime
    is_synthetic: bool


@dataclass(frozen=True)
class ProcessingResult:
    """Lo que el procesamiento de un mensaje devuelve al bucle (contadores y registro).

    `outcome` solo aplica si `kind` es EVENT; `reason` e `inserted` (False = duplicado)
    solo si es QUARANTINE; `updated_ms` solo en eventos.
    """

    kind: ResultKind
    ref: MessageRef
    outcome: VersionOutcome | None = None
    reason: str | None = None
    inserted: bool = False
    converted: bool = False
    nulls: tuple[str, ...] = field(default_factory=tuple)
    event_id: str | None = None
    is_synthetic: bool = False
    updated_ms: int | None = None
