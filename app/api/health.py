from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "VIAD Bot",
        "model": "gemini-2.5-flash-preview-04-17",
    }
