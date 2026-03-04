from langchain_core.tools import tool


@tool
async def generate_prompt(task_description: str, target_tool: str, department: str) -> str:
    """Genera un prompt profesional personalizado cuando no se encontró uno en la biblioteca.
    Usa esta herramienta SOLO después de haber buscado en la biblioteca sin resultados relevantes.

    Args:
        task_description: Qué quiere lograr el usuario (ej: "crear imágenes para campaña de inscripciones")
        target_tool: Para qué herramienta de IA es el prompt (ej: "ChatGPT", "Gemini", "Midjourney", "DALL-E")
        department: Área del usuario para contextualizar (ej: "Marketing", "Docencia", "RH")
    """
    from app.services.llm import get_llm

    llm = get_llm()

    generation_prompt = f"""Eres un experto en ingeniería de prompts para herramientas de IA Generativa.
Genera un prompt profesional, detallado y listo para usar.

TAREA DEL USUARIO: {task_description}
HERRAMIENTA DESTINO: {target_tool}
ÁREA/DEPARTAMENTO: {department}
CONTEXTO: Consorcio Educativo de Oriente (institución educativa mexicana)

REGLAS:
1. El prompt debe ser específico, no genérico
2. Incluir placeholders claros con {{llaves}} para que el usuario personalice
3. Adaptar el lenguaje al área del usuario
4. Si es para generación de imágenes: incluir estilo, composición, formato
5. Si es para texto: incluir tono, audiencia, estructura esperada
6. Escribir el prompt en español

Responde SOLO con el prompt generado, sin explicación previa."""

    response = await llm.ainvoke(generation_prompt)
    return response.content
