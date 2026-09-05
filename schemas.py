from typing import List, Optional
from pydantic import BaseModel, Field

class MediaItem(BaseModel):
    id: int
    title: str
    type: str = Field(..., description="'movie' ou 'series'")
    genre: List[str]
    release_year: int
    rating: float
    synopsis: str
    cast: List[str]
    episodes: Optional[int] = None
    stream_url: Optional[str] = None
    logo_url: Optional[str] = None

class SiteLogo(BaseModel):
    site_name: str = "CinePayload Animation"
    logo_url: str = "https://i.postimg.cc/nrMbmhcQ/Gemini-Generated-Image-jeh7xqjeh7xqjeh7.jpg"
    display_mode: str = "active_break_screen"
    alt_text: str = "Aguardando próxima transmissão - Animação 24h"