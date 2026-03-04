import os
from langgraph.checkpoint.memory import MemorySaver

_checkpointer = None
_checkpointer_type: str = "none"


async def get_checkpointer():
    """
    Get or create the checkpointer.
    Tries AsyncPostgresSaver (shared across workers/restarts) first,
    falls back to MemorySaver if DB connection fails.
    """
    global _checkpointer, _checkpointer_type

    if _checkpointer is not None:
        return _checkpointer

    db_url = os.getenv("SUPABASE_DB_URL")

    if db_url:
        try:
            from psycopg_pool import AsyncConnectionPool
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            pool = AsyncConnectionPool(
                conninfo=db_url,
                min_size=1,
                max_size=5,
                open=False,
            )
            await pool.open()
            # Test the connection
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")

            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()

            _checkpointer = checkpointer
            _checkpointer_type = "postgres"
            print(f"✓ AsyncPostgresSaver initialized (pool 1-5)")
            return _checkpointer

        except Exception as e:
            print(f"✗ PostgresSaver failed: {e}")
            print("  Falling back to MemorySaver")

    _checkpointer = MemorySaver()
    _checkpointer_type = "memory"
    print("✓ MemorySaver initialized (in-memory, no persistence across restarts)")
    return _checkpointer


async def close_checkpointer():
    """Close the checkpointer if it has a pool."""
    global _checkpointer, _checkpointer_type
    if _checkpointer_type == "postgres" and _checkpointer is not None:
        try:
            await _checkpointer.conn.close()
            print("PostgresSaver pool closed")
        except Exception:
            pass
    _checkpointer = None
    _checkpointer_type = "none"
