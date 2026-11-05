"""Datos de conexión a la base temporal de las pruebas de integración (T036)."""
from dataclasses import dataclass

import asyncpg

CONNECT_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class TempDatabase:
    """Datos de conexión a la base temporal para el administrador y el rol del consumidor."""

    name: str
    host: str
    port: int
    admin_user: str
    admin_password: str
    consumer_user: str
    consumer_password: str
    producer_user: str = "observatory_producer"
    producer_password: str = ""
    api_user: str = "observatory_api"
    api_password: str = ""

    async def api_pool(self) -> asyncpg.Pool:
        """Pool con el rol real `observatory_api` (solo lectura), el que usa la API de consulta."""
        return await asyncpg.create_pool(host=self.host, port=self.port, database=self.name,
                                         user=self.api_user, password=self.api_password,
                                         min_size=1, max_size=2, timeout=CONNECT_TIMEOUT_SECONDS)

    async def producer(self) -> asyncpg.Connection:
        """Conexión con el rol real `observatory_producer` (productor-live)."""
        return await self._connect(self.producer_user, self.producer_password)

    async def producer_pool(self) -> asyncpg.Pool:
        """Pool con el rol real `observatory_producer` (lo que usa el almacén de ingesta)."""
        return await asyncpg.create_pool(host=self.host, port=self.port, database=self.name,
                                         user=self.producer_user, password=self.producer_password,
                                         min_size=1, max_size=2, timeout=CONNECT_TIMEOUT_SECONDS)

    async def admin(self) -> asyncpg.Connection:
        """Conexión del administrador a la base temporal (lectura de cuarentena y comprobaciones)."""
        return await self._connect(self.admin_user, self.admin_password)

    async def consumer(self) -> asyncpg.Connection:
        """Conexión con el rol real `observatory_consumer`."""
        return await self._connect(self.consumer_user, self.consumer_password)

    async def _connect(self, user: str, password: str) -> asyncpg.Connection:
        return await asyncpg.connect(host=self.host, port=self.port, database=self.name,
                                     user=user, password=password, timeout=CONNECT_TIMEOUT_SECONDS)
