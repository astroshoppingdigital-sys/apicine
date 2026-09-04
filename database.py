from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import httpx

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
    site_name: str = "CinePayload Oficial"
    logo_url: str = "https://i.postimg.cc/nrMbmhcQ/Gemini-Generated-Image-jeh7xqjeh7xqjeh7.jpg"
    display_mode: str = "active_break_screen"
    alt_text: str = "Aguardando próxima transmissão - Intervalo CinePayload"

DATABASE: List[MediaItem] = []

def fetch_free_public_movies():
    try:
        # Puxa automaticamente os fluxos e logotipos da lista pública de animações
        response = httpx.get("https://iptv-org.github.io/iptv/categories/animation.m3u", timeout=10.0)
        if response.status_code == 200:
            lines = response.text.split("\n")
            idx = 1
            current_title = "Desenho Animado"
            current_logo = "https://via.placeholder.com/300x450?text=CinePayload"
            
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    if 'tvg-logo="' in line:
                        try:
                            current_logo = line.split('tvg-logo="')[1].split('"')[0]
                        except:
                            pass
                    if "," in line:
                        current_title = line.split(",")[-1].strip()
                elif line and not line.startswith("#"):
                    stream_url = line
                    item = MediaItem(
                        id=idx,
                        title=current_title,
                        type="movie",
                        genre=["Animação", "Família"],
                        release_year=2024,
                        rating=8.0,
                        synopsis="Transmissão contínua CinePayload - Programação automática.",
                        cast=["Elenco Animado"],
                        episodes=None,
                        stream_url=stream_url,
                        logo_url=current_logo
                    )
                    DATABASE.append(item)
                    idx += 1
                    if idx > 40:
                        break
    except Exception:
        pass
        
    # Fallback se a lista externa falhar
    if not DATABASE:
        DATABASE.append(
            MediaItem(
                id=1, 
                title="Clássico Animado 1", 
                type="movie", 
                genre=["Animation"], 
                release_year=2020, 
                rating=8.0, 
                synopsis="Desenho clássico em transmissão contínua.", 
                cast=["Personagem Principal"],
                stream_url="https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
                logo_url=""
            )
        )

fetch_free_public_movies()

CACHE_STORE: Dict[str, dict] = {}
SCHEDULE_STORE: List[dict] = []
SITE_LOGO_CONFIG = SiteLogo()
