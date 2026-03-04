from urllib.parse import urlparse

import httpx
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import get_settings

_checkpointer: AsyncPostgresSaver | None = None
_pool: AsyncConnectionPool | None = None


def _resolve_ipv4(hostname: str) -> str | None:
    """Resolve hostname to IPv4 via Cloudflare DNS-over-HTTPS."""
    try:
        resp = httpx.get(
            "https://1.1.1.1/dns-query",
            params={"name": hostname, "type": "A"},
            headers={"Accept": "application/dns-json"},
            timeout=5,
        )
        for answer in resp.json().get("Answer", []):
            if answer.get("type") == 1:  # A record
                return answer["data"]
    except Exception as e:
        print(f"DoH resolution failed: {e}")
    return None


def _build_conninfo(db_url: str) -> str:
    """Build psycopg conninfo forcing IPv4 via DNS-over-HTTPS."""
    parsed = urlparse(db_url)
    hostname = parsed.hostname or ""
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/") or "postgres"
    user = parsed.username or "postgres"
    password = parsed.password or ""

    ipv4 = _resolve_ipv4(hostname)
    if ipv4:
        print(f"Resolved {hostname} -> {ipv4} (via DoH)")
        return (
            f"host={hostname} hostaddr={ipv4} port={port} "
            f"dbname={dbname} user={user} password={password}"
        )

    print(f"WARNING: Could not resolve {hostname} to IPv4")
    return db_url


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the PostgresSaver checkpointer.
    Uses the same Supabase PostgreSQL database.
    """
    global _checkpointer, _pool

    if _checkpointer is None:
        settings = get_settings()
        conninfo = _build_conninfo(settings.SUPABASE_DB_URL)
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
