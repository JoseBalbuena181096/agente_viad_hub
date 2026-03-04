from fastapi import APIRouter, HTTPException
from app.services.supabase import get_supabase
from app.schemas.conversation import ConversationCreate, ConversationUpdate

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(user_id: str):
    """List all conversations for a user, most recent first."""
    supabase = get_supabase()

    response = supabase.table("conversations").select(
        "id, title, created_at, updated_at"
    ).eq("user_id", user_id).order(
        "updated_at", desc=True
    ).execute()

    conversations = response.data or []

    # Get last message preview for each conversation
    for conv in conversations:
        msg_response = supabase.table("messages").select(
            "content"
        ).eq("conversation_id", conv["id"]).order(
            "created_at", desc=True
        ).limit(1).execute()

        if msg_response.data:
            preview = msg_response.data[0]["content"][:100]
            conv["last_message"] = preview
        else:
            conv["last_message"] = None

    return conversations


@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    """Get all messages for a conversation."""
    supabase = get_supabase()

    response = supabase.table("messages").select(
        "id, role, content, created_at"
    ).eq("conversation_id", conversation_id).order(
        "created_at", desc=False
    ).execute()

    return response.data or []


@router.post("")
async def create_conversation(data: ConversationCreate):
    """Create a new conversation."""
    supabase = get_supabase()

    response = supabase.table("conversations").insert({
        "user_id": data.user_id,
        "title": data.title or "Nueva conversación",
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    return response.data[0]


@router.patch("/{conversation_id}")
async def update_conversation(conversation_id: str, data: ConversationUpdate):
    """Update conversation title."""
    supabase = get_supabase()

    response = supabase.table("conversations").update({
        "title": data.title,
    }).eq("id", conversation_id).execute()

    return response.data[0] if response.data else {}


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages (cascade)."""
    supabase = get_supabase()

    supabase.table("conversations").delete().eq(
        "id", conversation_id
    ).execute()

    return {"status": "deleted"}
