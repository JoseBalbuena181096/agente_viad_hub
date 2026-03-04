from typing import List
from app.services.llm import get_embeddings


async def embed_text(text: str) -> List[float]:
    """Generate embedding for a single text string."""
    model = get_embeddings()
    return model.embed_query(text)


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts."""
    model = get_embeddings()
    return model.embed_documents(texts)
