from typing import Dict, Any
from app.services.supabase import get_supabase
from app.services.embeddings import embed_text
import json


async def vectorize_prompt(prompt_id: str) -> Dict[str, Any]:
    """Vectorize a prompt from the prompts table."""
    supabase = get_supabase()

    # Fetch the prompt
    response = supabase.table("prompts").select("*").eq("id", prompt_id).single().execute()
    prompt = response.data
    if not prompt:
        raise ValueError(f"Prompt {prompt_id} not found")

    # Build text for embedding
    parts = [prompt["title"]]
    if prompt.get("description"):
        parts.append(prompt["description"])
    parts.append(prompt["content"])
    if prompt.get("category"):
        parts.append(f"Categoría: {prompt['category']}")
    if prompt.get("tags"):
        parts.append(f"Tags: {', '.join(prompt['tags'])}")

    text = "\n".join(parts)
    embedding = await embed_text(text)

    # Metadata for retrieval display
    metadata = {
        "title": prompt["title"],
        "category": prompt.get("category", ""),
        "tags": prompt.get("tags", []),
        "description": prompt.get("description", ""),
    }

    # Upsert into content_vectors
    supabase.table("content_vectors").upsert(
        {
            "content_type": "prompt",
            "content_id": prompt_id,
            "content_chunk": text,
            "embedding": embedding,
            "metadata": json.dumps(metadata),
        },
        on_conflict="content_type,content_id"
    ).execute()

    return {"id": prompt_id, "title": prompt["title"], "status": "vectorized"}


async def vectorize_video(video_id: str) -> Dict[str, Any]:
    """Vectorize a video from the videos table."""
    supabase = get_supabase()

    # Fetch the video
    response = supabase.table("videos").select("*").eq("id", video_id).single().execute()
    video = response.data
    if not video:
        raise ValueError(f"Video {video_id} not found")

    # Build text for embedding (title + category + duration)
    parts = [video["title"]]
    if video.get("category"):
        parts.append(f"Categoría: {video['category']}")
    if video.get("duration"):
        parts.append(f"Duración: {video['duration']}")

    text = "\n".join(parts)
    embedding = await embed_text(text)

    metadata = {
        "title": video["title"],
        "url": video.get("url", ""),
        "category": video.get("category", ""),
        "duration": video.get("duration", ""),
    }

    supabase.table("content_vectors").upsert(
        {
            "content_type": "video",
            "content_id": video_id,
            "content_chunk": text,
            "embedding": embedding,
            "metadata": json.dumps(metadata),
        },
        on_conflict="content_type,content_id"
    ).execute()

    return {"id": video_id, "title": video["title"], "status": "vectorized"}


async def vectorize_all_prompts() -> Dict[str, Any]:
    """Vectorize all prompts."""
    supabase = get_supabase()
    response = supabase.table("prompts").select("id").execute()
    results = []
    errors = []

    for row in response.data or []:
        try:
            result = await vectorize_prompt(row["id"])
            results.append(result)
        except Exception as e:
            errors.append({"id": row["id"], "error": str(e)})

    return {"vectorized": len(results), "errors": len(errors), "error_details": errors}


async def vectorize_all_videos() -> Dict[str, Any]:
    """Vectorize all videos."""
    supabase = get_supabase()
    response = supabase.table("videos").select("id").execute()
    results = []
    errors = []

    for row in response.data or []:
        try:
            result = await vectorize_video(row["id"])
            results.append(result)
        except Exception as e:
            errors.append({"id": row["id"], "error": str(e)})

    return {"vectorized": len(results), "errors": len(errors), "error_details": errors}
