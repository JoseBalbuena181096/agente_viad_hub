import socket
from urllib.parse import urlparse, urlunparse

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import get_settings

_checkpointer: AsyncPostgresSaver | None = None
_pool: AsyncConnectionPool | None = None


def _force_ipv4(db_url: str) -> str:
    """Resolve hostname to IPv4 to avoid IPv6 issues on Railway."""
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    if not hostname:
        return db_url
    try:
        ipv4 = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        # Replace hostname with IPv4 but keep original hostname for SSL SNI
        new_netloc = parsed.netloc.replace(hostname, ipv4)
        return urlunparse(parsed._replace(netloc=new_netloc))
    except (socket.gaierror, IndexError):
        return db_url


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the PostgresSaver checkpointer.
    Uses the same Supabase PostgreSQL database.
    """
    global _checkpointer, _pool

    if _checkpointer is None:
        settings = get_settings()
        conninfo = _force_ipv4(settings.SUPABASE_DB_URL)
        _pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=1,
            max_size=5,
        )
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()

    return _checkpointer


async def close_checkpointer():
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
