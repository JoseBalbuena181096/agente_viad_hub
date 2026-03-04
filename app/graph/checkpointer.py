from langgraph.checkpoint.memory import MemorySaver

_checkpointer: MemorySaver | None = None


async def get_checkpointer() -> MemorySaver:
    """
    Get or create the checkpointer.
    Uses MemorySaver for fast in-memory state.
    Conversation messages are persisted to Supabase via REST API
    in the save_message node, so history survives restarts.
    """
    global _checkpointer

    if _checkpointer is None:
        _checkpointer = MemorySaver()
        print("✓ MemorySaver initialized")

    return _checkpointer


async def close_checkpointer():
    """No-op for MemorySaver."""
    pass
