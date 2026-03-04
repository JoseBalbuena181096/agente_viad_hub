from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.core.config import get_settings

_llm = None
_embeddings = None


def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        settings = get_settings()
        _llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=1.0,  # Gemini 3 preview requires temperature=1.0
            streaming=True,
            convert_system_message_to_human=True,
        )
    return _llm


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        settings = get_settings()
        _embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GOOGLE_API_KEY,
        )
    return _embeddings


def safe_text(content) -> str:
    """Safely extract text from AIMessage.content (str or list of content blocks).

    Gemini 3 Flash Preview returns content as a list of content blocks:
        [{"type": "text", "text": "Hello"}]
    instead of a plain string. This helper handles both formats.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts) if parts else ""
    return str(content)
