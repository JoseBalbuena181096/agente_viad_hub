from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import get_settings

_checkpointer: AsyncPostgresSaver | None = None
_pool: AsyncConnectionPool | None = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the PostgresSaver checkpointer.
    Uses Supabase Session Pooler (IPv4 compatible).
    """
    global _checkpointer, _pool

    if _checkpointer is None:
        settings = get_settings()
        db_url = settings.SUPABASE_DB_URL
        print(f"Connecting to DB pooler...")
        _pool = AsyncConnectionPool(
            conninfo=db_url,
            min_size=0,
            max_size=3,
            open=False,
            timeout=10,
        )
        await _pool.open(wait=True, timeout=15)
        print("DB pool connected successfully")
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()
        print("Checkpointer setup complete")

    return _checkpointer


async def close_checkpointer():
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
