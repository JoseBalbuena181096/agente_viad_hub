import base64
import io
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from app.services.supabase import get_supabase
from app.services.llm import safe_text


async def setup(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare context before the agent generates a response.
    - Load user profile (name, department) from profiles table
    - Process file attachments (PDFs → text, images → multimodal content)
    """
    user_id = state.get("user_id", "")
    supabase = get_supabase()

    # Load user profile
    user_name = "Usuario"
    user_department = None

    if user_id:
        try:
            response = supabase.table("profiles").select(
                "full_name, department"
            ).eq("id", user_id).single().execute()

            if response.data:
                user_name = response.data.get("full_name") or "Usuario"
                user_department = response.data.get("department")
        except Exception:
            pass

    # Check if this is the first message in the conversation
    messages = state.get("messages", [])
    user_messages = [m for m in messages if isinstance(m, HumanMessage)]
    is_first_message = len(user_messages) <= 1

    # Process file context if present
    file_context = state.get("file_context")
    if file_context:
        # Append file context to the last human message
        last_msg = messages[-1]
        if isinstance(last_msg, HumanMessage):
            text_content = safe_text(last_msg.content)
            enhanced_content = (
                f"{text_content}\n\n"
                f"[Contenido del archivo adjunto]:\n{file_context}"
            )
            messages[-1] = HumanMessage(content=enhanced_content)

    return {
        "user_name": user_name,
        "user_department": user_department or "No especificado",
        "is_first_message": is_first_message,
        "messages": messages,
    }
