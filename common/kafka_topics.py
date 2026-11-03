"""Creación idempotente de los temas del contrato (kafka-message.md §1)."""
import logging

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

logger = logging.getLogger(__name__)

TOPIC_LIVE = "earthquakes.live"
TOPIC_REPLAY = "earthquakes.replay"
CONTRACT_TOPICS = (TOPIC_LIVE, TOPIC_REPLAY)
TOPIC_PARTITIONS = 1
TOPIC_REPLICATION_FACTOR = 1
# 7 días: cubre una caída del consumidor de varios días (kafka-message.md §1, A6).
TOPIC_RETENTION_MS = 7 * 24 * 60 * 60 * 1000


def build_topic(name: str) -> NewTopic:
    """Construye la definición de un tema con las propiedades del contrato.

    Qué hace:
        Fija 1 partición, factor de replicación 1 y retención de 7 días.
    Recibe:
        name: nombre del tema.
    Devuelve:
        La definición lista para crear.
    Por qué existe:
        Los valores del contrato viven en un solo sitio (constitución §15, A6).
    """
    return NewTopic(
        name=name,
        num_partitions=TOPIC_PARTITIONS,
        replication_factor=TOPIC_REPLICATION_FACTOR,
        topic_configs={"retention.ms": str(TOPIC_RETENTION_MS)},
    )


async def ensure_topics(bootstrap_servers: str) -> None:
    """Crea los temas del contrato si no existen.

    Qué hace:
        Crea cada tema por separado e ignora los que ya existen.
    Recibe:
        bootstrap_servers: dirección del broker (nombre de servicio).
    Devuelve:
        Nada.
    Por qué existe:
        Con la creación automática desactivada, productor y consumidor garantizan los temas al
        arrancar, sin importar cuál lo haga primero (FR-016).
    """
    admin = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    await admin.start()
    try:
        for name in CONTRACT_TOPICS:
            try:
                await admin.create_topics([build_topic(name)])
                logger.info("Tema creado: %s", name)
            except TopicAlreadyExistsError:
                logger.info("El tema ya existe: %s", name)
    finally:
        await admin.close()
