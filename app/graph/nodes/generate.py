from typing import Dict, Any
from langchain_core.messages import SystemMessage
from app.services.llm import get_llm
from app.core.prompts import VIAD_BOT_SYSTEM_PROMPT
from app.tools.search_library import search_library
from app.tools.search_videos import search_videos
from app.tools.generate_prompt import generate_prompt


TOOLS = [search_library, search_videos, generate_prompt]


async def generate(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main agent node. Uses VIAD Bot system prompt and decides
    whether to call tools (search, generate) or respond directly.
    """
    llm = get_llm()
    llm_with_tools = llm.bind_tools(TOOLS)

    user_name = state.get("user_name", "Usuario")
    user_department = state.get("user_department", "No especificado")

    system_prompt = VIAD_BOT_SYSTEM_PROMPT.format(
        user_name=user_name,
        user_department=user_department,
    )

    # Build messages with system prompt
    messages = state.get("messages", [])
    filtered = [m for m in messages if not isinstance(m, SystemMessage)]
    prompt_messages = [SystemMessage(content=system_prompt)] + filtered

    response = await llm_with_tools.ainvoke(prompt_messages)

    return {"messages": [response]}
