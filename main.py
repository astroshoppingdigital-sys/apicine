from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from schemas import MediaItem
from database import DATABASE, SCHEDULE_STORE, SITE_LOGO_CONFIG, fetch_animation_streams

app = FastAPI(
    title="CinePayload Animation API",
    version="2.0.0",
    description="API dedicada de streaming 24/7 para animações e conteúdo infantil."
)

@app.get("/api/v1/media", response_model=dict)
def get_all_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    media_type: Optional[str] = None
):
    results = DATABASE
    if media_type:
        results = [m for m in results if m.type == media_type]
    
    paginated = results[skip : skip + limit]
    return {
        "success": True,
        "message": "Mídias de animação recuperadas com sucesso.",
        "data": {
            "total": len(results),
            "results": paginated
        }
    }

@app.post("/api/v1/refresh")
def refresh_catalog():
    fetch_animation_streams()
    return {"success": True, "total_loaded": len(DATABASE)}