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
        print(f"Connecting to DB pooler...")
        _pool = AsyncConnectionPool(
            conninfo=settings.SUPABASE_DB_URL,
            min_size=1,
            max_size=5,
            open=False,
        )
        await _pool.open()
        print("DB pool connected successfully")
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()

    return _checkpointer


async def close_checkpointer():
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
