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

    async def admin(self) -> asyncpg.Connection:
        """Conexión del administrador a la base temporal (lectura de cuarentena y comprobaciones)."""
        return await self._connect(self.admin_user, self.admin_password)

    async def consumer(self) -> asyncpg.Connection:
        """Conexión con el rol real `observatory_consumer`."""
        return await self._connect(self.consumer_user, self.consumer_password)

    async def _connect(self, user: str, password: str) -> asyncpg.Connection:
        return await asyncpg.connect(host=self.host, port=self.port, database=self.name,
                                     user=user, password=password, timeout=CONNECT_TIMEOUT_SECONDS)
