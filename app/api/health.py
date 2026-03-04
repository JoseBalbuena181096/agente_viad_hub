from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "VIAD Bot",
        "model": "gemini-2.0-flash",
    }
