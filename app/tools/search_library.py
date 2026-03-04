import json
from langchain_core.tools import tool
from app.services.rag import search_by_similarity


@tool
async def search_library(query: str) -> str:
    """Busca prompts relevantes en la biblioteca del CEO IA Hub.
    Usa esta herramienta cuando el usuario busca un prompt, plantilla o ejemplo
    para una tarea específica. Retorna los prompts más similares con título,
    categoría y contenido completo."""
    results = await search_by_similarity(query, content_type="prompt", limit=3)

    if not results:
        return "No se encontraron prompts relevantes en la biblioteca."

    output_parts = []
    for r in results:
        meta = r.get("metadata", {})
        if isinstance(meta, str):
            meta = json.loads(meta)
        output_parts.append(
            f"**{meta.get('title', 'Sin título')}** | Categoría: {meta.get('category', 'N/A')}\n"
            f"Tags: {', '.join(meta.get('tags', []))}\n"
            f"Contenido:\n{r.get('content_chunk', '')}\n"
            f"Similitud: {r.get('similarity', 0):.2f}"
        )

    return "\n---\n".join(output_parts)
