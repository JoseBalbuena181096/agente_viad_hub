from fastapi import APIRouter, HTTPException
from app.schemas.vectorize import VectorizeRequest, BatchVectorizeRequest
from app.services.vectorize import (
    vectorize_prompt,
    vectorize_video,
    vectorize_all_prompts,
    vectorize_all_videos,
)

router = APIRouter(prefix="/vectorize", tags=["vectorize"])


@router.post("/prompt")
async def vectorize_prompt_endpoint(data: VectorizeRequest):
    """Vectorize a single prompt."""
    if not data.prompt_id:
        raise HTTPException(status_code=400, detail="prompt_id is required")

    try:
        result = await vectorize_prompt(data.prompt_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video")
async def vectorize_video_endpoint(data: VectorizeRequest):
    """Vectorize a single video."""
    if not data.video_id:
        raise HTTPException(status_code=400, detail="video_id is required")

    try:
        result = await vectorize_video(data.video_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_vectorize(data: BatchVectorizeRequest):
    """Batch vectorize all prompts, videos, or both."""
    results = {}

    if data.type in ("prompt", "all"):
        results["prompts"] = await vectorize_all_prompts()

    if data.type in ("video", "all"):
        results["videos"] = await vectorize_all_videos()

    return {"success": True, **results}
