from typing import List, Dict, Optional
import httpx
from schemas import MediaItem, SiteLogo

DATABASE: List[MediaItem] = []

def fetch_animation_streams():
    global DATABASE
    DATABASE.clear()
    try:
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
                    
                    if not current_title or current_title.startswith("http"):
                        current_title = f"Canal Animação {idx}"

                    item = MediaItem(
                        id=idx,
                        title=current_title,
                        type="movie",
                        genre=["Animação", "Infantil"],
                        release_year=2024,
                        rating=8.5,
                        synopsis="Transmissão contínua de desenhos animados e programação infantil 24h.",
                        cast=["Turma Animada"],
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
        
    if not DATABASE:
        DATABASE.append(
            MediaItem(
                id=1, 
                title="Canal Desenho Animado 24h", 
                type="movie", 
                genre=["Animation", "Kids"], 
                release_year=2024, 
                rating=8.5, 
                synopsis="Desenhos clássicos e modernos em transmissão contínua.", 
                cast=["Personagens Animados"],
                stream_url="https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
                logo_url=""
            )
        )

fetch_animation_streams()

CACHE_STORE: Dict[str, dict] = {}
SCHEDULE_STORE: List[dict] = []
SITE_LOGO_CONFIG = SiteLogo()