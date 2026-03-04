from typing import Annotated, Optional, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    user_name: str
    user_department: Optional[str]
    file_context: Optional[str]
    conversation_id: str
    is_first_message: bool
