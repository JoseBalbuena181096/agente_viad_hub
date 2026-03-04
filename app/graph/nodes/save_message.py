from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from app.services.supabase import get_supabase
from app.services.llm import get_llm
from app.core.prompts import TITLE_GENERATOR_PROMPT


async def save_message(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save conversation messages to Supabase tables.
    - Save the last user message and the last AI response to the messages table
    - Auto-generate conversation title on first message
    """
    conversation_id = state.get("conversation_id")
    if not conversation_id:
        return {}

    supabase = get_supabase()
    messages = state.get("messages", [])

    # Find the last user message and last AI message
    last_user = None
    last_ai = None

    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and last_ai is None:
            # Skip tool call messages (they have tool_calls but no text content)
            if msg.content and not msg.tool_calls:
                last_ai = msg
        elif isinstance(msg, HumanMessage) and last_user is None:
            last_user = msg

        if last_user and last_ai:
            break

    # Save messages
    try:
        if last_user:
            content = last_user.content
            if isinstance(content, list):
                # Extract text from multimodal content
                content = next(
                    (item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"),
                    str(content)
                )
            supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "role": "user",
                "content": content,
            }).execute()

        if last_ai:
            supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": last_ai.content,
            }).execute()

        # Auto-generate title on first message
        if state.get("is_first_message") and last_user:
            try:
                user_text = last_user.content
                if isinstance(user_text, list):
                    user_text = next(
                        (item.get("text", "") for item in user_text if isinstance(item, dict) and item.get("type") == "text"),
                        ""
                    )

                llm = get_llm()
                prompt = TITLE_GENERATOR_PROMPT.format(message=user_text[:200])
                title_response = await llm.ainvoke(prompt)
                title = title_response.content.strip()[:50]

                supabase.table("conversations").update({
                    "title": title,
                }).eq("id", conversation_id).execute()
            except Exception:
                pass

        # Update conversation timestamp
        supabase.table("conversations").update({
            "updated_at": "now()",
        }).eq("id", conversation_id).execute()

    except Exception as e:
        print(f"Error saving messages: {e}")

    return {}
