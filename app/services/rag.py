from typing import List, Dict, Any, Optional
from app.services.supabase import get_supabase
from app.services.embeddings import embed_text


async def search_by_similarity(
    query: str,
    content_type: Optional[str] = None,
    threshold: float = 0.5,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Search content_vectors by cosine similarity."""
    query_embedding = await embed_text(query)
    supabase = get_supabase()

    response = supabase.rpc(
        "match_content_vectors",
        {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": limit,
            "filter_content_type": content_type,
        }
    ).execute()

    return response.data if response.data else []
