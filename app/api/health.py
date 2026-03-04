from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "VIAD Bot",
        "model": "gemini-3-flash-preview",
    }
