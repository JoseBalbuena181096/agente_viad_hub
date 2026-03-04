import json
from langchain_core.tools import tool
from app.services.rag import search_by_similarity


@tool
async def search_videos(query: str) -> str:
    """Busca videos de microaprendizaje en la biblioteca del CEO IA Hub.
    Usa esta herramienta cuando el usuario busca tutoriales, videos o guías
    sobre herramientas de IA. Retorna los videos más similares con título,
    URL y categoría."""
    results = await search_by_similarity(query, content_type="video", limit=3)

    if not results:
        return "No se encontraron videos relevantes en la biblioteca."

    output_parts = []
    for r in results:
        meta = r.get("metadata", {})
        if isinstance(meta, str):
            meta = json.loads(meta)
        output_parts.append(
            f"**{meta.get('title', 'Sin título')}** | Categoría: {meta.get('category', 'N/A')}\n"
            f"URL: {meta.get('url', 'N/A')}\n"
            f"Duración: {meta.get('duration', 'N/A')}\n"
            f"Similitud: {r.get('similarity', 0):.2f}"
        )

    return "\n---\n".join(output_parts)
