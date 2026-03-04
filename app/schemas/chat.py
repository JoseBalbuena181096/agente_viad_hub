from pydantic import BaseModel
from typing import Optional, List


class FileAttachment(BaseModel):
    filename: str
    mime_type: str
    data: str  # base64 encoded


class ChatRequest(BaseModel):
    query: str
    user_id: str
    conversation_id: Optional[str] = None
    files: Optional[List[FileAttachment]] = None
