from langgraph.checkpoint.memory import MemorySaver

_checkpointer: MemorySaver | None = None


async def get_checkpointer() -> MemorySaver:
    """
    Get or create the checkpointer.
    Uses in-memory storage. Conversation messages are persisted
    to Supabase via REST API in the save_message node.
    """
    global _checkpointer

    if _checkpointer is None:
        _checkpointer = MemorySaver()
        print("MemorySaver checkpointer initialized")

    return _checkpointer


async def close_checkpointer():
    """No-op for MemorySaver."""
    pass
