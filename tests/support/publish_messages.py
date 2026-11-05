"""Publicador de casos de prueba en `earthquakes.live` para `scripts/verify_consumer.py` (T072).

Se ejecuta dentro del servicio `tests` (alcanza Kafka por el nombre de servicio):
    docker compose --profile test run --rm tests python -m tests.support.publish_messages <caso>

Todos los datos son SINTÉTICOS (`is_synthetic = true`, ids `synthetic-...`). La clave Kafka es el
`event.id` cuando el valor es un mensaje bien formado; los casos hostiles publican bytes exactos.
`print` está permitido: es un script de línea de comandos.
"""
import argparse
import asyncio
import copy
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass

from tests.support.messages import (
    E1_TIME_MS,
    E1_UPDATED_1005,
    FAQ12_E1,
    build_message,
    build_synthetic_message,
    faq12_sequence,
    geo_cases,
    late_old_version_message,
    to_bytes,
)

BOOTSTRAP_VARIABLE = "KAFKA_BOOTSTRAP_SERVERS"
REPLAY_REPEATS = 100
DEFAULT_NUMBERED_COUNT = 20
INVALID_LATITUDE = 145
LONG_ID_CHARS = 600
LATITUDE_INDEX = 1
NOT_UTF8 = b"\xff\xfe{"
REPLAY_AT = "2026-11-04T10:30:00Z"
VALID_AFTER_INVALID_ID = "synthetic-quarantine-valid"
NUL_ID = "synthetic-quarantine-nul"
REPLAY_MODE_ID = "synthetic-quarantine-replay"
TOMBSTONE_KEY = b"synthetic-quarantine-tombstone"


@dataclass(frozen=True)
class Outgoing:
    """Un mensaje a publicar: clave y valor en bytes exactos (`value=None` es un tombstone)."""

    key: bytes | None
    value: bytes | None


def _from_message(message: dict) -> Outgoing:
    """Mensaje bien formado: clave = `event.id`, valor = JSON UTF-8."""
    return Outgoing(message["event"]["id"].encode("utf-8"), to_bytes(message))


def _message(event_id: str = FAQ12_E1, mag: float | None = 4.2) -> dict:
    """Mensaje sintético válido con el tiempo y la actualización de la FAQ 12."""
    return build_synthetic_message(event_id, E1_TIME_MS, E1_UPDATED_1005, mag)


def _with_latitude(event_id: str, latitude: float) -> dict:
    """Mensaje sintético con la latitud cambiada (145 queda fuera de rango)."""
    message = copy.deepcopy(_message(event_id))
    message["event"]["geometry"]["coordinates"][LATITUDE_INDEX] = latitude
    return message


def case_faq12() -> list[Outgoing]:
    """Los 5 mensajes de la FAQ 12 (data-model.md §4)."""
    return [_from_message(message) for message in faq12_sequence()]


def case_late_old() -> list[Outgoing]:
    """E1 con `updated` 10:07 y mag 4.4: versión antigua tardía no vista (prueba 4)."""
    return [_from_message(late_old_version_message())]


def case_replay_100() -> list[Outgoing]:
    """El primer mensaje de la FAQ 12 repetido 100 veces (prueba 2)."""
    return [case_faq12()[0]] * REPLAY_REPEATS


def case_invalid_twice() -> list[Outgoing]:
    """El mismo mensaje con latitud 145, dos veces (cuarentena y duplicado de cuarentena)."""
    return [_from_message(_with_latitude("synthetic-invalid-lat", INVALID_LATITUDE))] * 2


def case_constraint_twice() -> list[Outgoing]:
    """Un mensaje con `dmin = NaN` dos veces (`db_constraint_violation`, FR-036)."""
    message = _message("synthetic-constraint-nan")
    message["event"]["properties"]["dmin"] = float("nan")
    return [_from_message(message)] * 2


def case_quarantine_set() -> list[Outgoing]:
    """Prueba 6: seis mensajes inválidos de motivos distintos y uno válido (el 2.º)."""
    nul = _message(NUL_ID)
    nul["event"]["properties"]["place"] = "a\u0000b"
    replay = build_message(_message(REPLAY_MODE_ID)["event"], mode="replay", replay_at=REPLAY_AT)
    return [
        _from_message(_with_latitude("synthetic-quarantine-lat145", INVALID_LATITUDE)),
        _from_message(_message(VALID_AFTER_INVALID_ID)),
        _from_message(nul),
        Outgoing(None, NOT_UTF8),
        Outgoing(TOMBSTONE_KEY, None),
        _from_message(replay),
        _from_message(_message("synthetic-" + "y" * (LONG_ID_CHARS - len("synthetic-")))),
    ]


def case_numbered(count: int = DEFAULT_NUMBERED_COUNT) -> list[Outgoing]:
    """`count` eventos distintos `synthetic-numbered-0001...` (para las caídas de servicios)."""
    return [_from_message(_message(f"synthetic-numbered-{number:04d}")) for number in range(1, count + 1)]


def _geo_case(name: str) -> Callable[[], list[Outgoing]]:
    """Fabrica el caso `geo-<name>`: un único mensaje de `geo_cases()` (F5, sintético)."""
    def build() -> list[Outgoing]:
        return [_from_message(geo_cases()[name])]
    build.__doc__ = f"Caso geográfico `{name}` (un mensaje sintético de F5)."
    return build


GEO_CASE_NAMES = ("madrid", "atlantico", "mag-nula", "lat-145")

CASES: dict[str, Callable[[], list[Outgoing]]] = {
    "faq12": case_faq12,
    "late-old": case_late_old,
    "replay-100": case_replay_100,
    "invalid-twice": case_invalid_twice,
    "constraint-twice": case_constraint_twice,
    "quarantine-set": case_quarantine_set,
    "numbered": case_numbered,
    **{f"geo-{name}": _geo_case(name) for name in GEO_CASE_NAMES},
}


def build_case(name: str, count: int = DEFAULT_NUMBERED_COUNT) -> list[Outgoing]:
    """Devuelve los mensajes de un caso; `count` solo afecta a `numbered`."""
    if name == "numbered":
        return case_numbered(count)
    return CASES[name]()


async def publish(outgoing: list[Outgoing], bootstrap_servers: str) -> None:
    """Crea los temas si faltan y publica los mensajes en orden en `earthquakes.live`."""
    from aiokafka import AIOKafkaProducer

    from common.kafka_topics import TOPIC_LIVE, ensure_topics

    await ensure_topics(bootstrap_servers)
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await producer.start()
    try:
        for item in outgoing:
            await producer.send_and_wait(TOPIC_LIVE, value=item.value, key=item.key)
    finally:
        await producer.stop()


def build_parser() -> argparse.ArgumentParser:
    """Parser de línea de comandos: `--help` lista los casos."""
    descriptions = "\n".join(f"  {name:<17}{(func.__doc__ or '').splitlines()[0]}" for name, func in CASES.items())
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], epilog=f"Casos:\n{descriptions}",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case", choices=sorted(CASES), help="caso a publicar")
    parser.add_argument("--count", type=int, default=DEFAULT_NUMBERED_COUNT, help="solo para `numbered`")
    return parser


def main() -> int:
    """Publica el caso pedido y devuelve el código de salida."""
    from common.config import read_str

    args = build_parser().parse_args()
    outgoing = build_case(args.case, args.count)
    asyncio.run(publish(outgoing, read_str(BOOTSTRAP_VARIABLE)))
    print(f"published case={args.case} messages={len(outgoing)} topic=earthquakes.live")
    return 0


if __name__ == "__main__":
    sys.exit(main())
