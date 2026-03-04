import socket
from urllib.parse import urlparse

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import get_settings

_checkpointer: AsyncPostgresSaver | None = None
_pool: AsyncConnectionPool | None = None


def _build_ipv4_conninfo(db_url: str) -> str:
    """Build a conninfo string forcing IPv4 to avoid IPv6 issues on Railway."""
    parsed = urlparse(db_url)
    hostname = parsed.hostname or ""
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/") or "postgres"
    user = parsed.username or "postgres"
    password = parsed.password or ""

    # Resolve hostname to IPv4
    try:
        ipv4 = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        print(f"Resolved {hostname} -> {ipv4}")
    except (socket.gaierror, IndexError):
        print(f"Could not resolve {hostname} to IPv4, using hostname directly")
        return db_url

    # Use key-value format with hostaddr to force IPv4
    return (
        f"host={hostname} hostaddr={ipv4} port={port} "
        f"dbname={dbname} user={user} password={password}"
    )


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the PostgresSaver checkpointer.
    Uses the same Supabase PostgreSQL database.
    """
    global _checkpointer, _pool

    if _checkpointer is None:
        settings = get_settings()
        conninfo = _build_ipv4_conninfo(settings.SUPABASE_DB_URL)
        _pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=1,
            max_size=5,
            open=False,
        )
        await _pool.open()
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()

    return _checkpointer


async def close_checkpointer():
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
