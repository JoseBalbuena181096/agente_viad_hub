from pydantic import BaseModel
from typing import Optional, Literal


class VectorizeRequest(BaseModel):
    prompt_id: Optional[str] = None
    video_id: Optional[str] = None


class BatchVectorizeRequest(BaseModel):
    type: Literal["prompt", "video", "all"]
