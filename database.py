import httpx
from typing import Dict, List, Optional, Set
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

class SiteLogo(BaseModel):
    site_name: str = "CineVerse Oficial"
    logo_url: str = "https://i.postimg.cc/nrMbmhcQ/Gemini-Generated-Image-jeh7xqjeh7xqjeh7.jpg"
    display_mode: str = "active_break_screen"
    alt_text: str = "Aguardando próxima transmissão - Intervalo"

DATABASE: List[MediaItem] = []

def fetch_free_public_movies():
    try:
        response = httpx.get("https://api.tvmaze.com/shows", timeout=10.0)
        if response.status_code == 200:
            shows = response.json()
            for idx, show in enumerate(shows[:50], start=1):
                premiered = show.get("premiered")
                year = int(premiered[:4]) if premiered and len(premiered) >= 4 else 2020
                rating_data = show.get("rating", {})
                rating = float(rating_data.get("average", 7.5)) if rating_data and rating_data.get("average") else 7.5
                
                summary = show.get("summary", "Sem sinopse disponível.")
                if summary:
                    summary = summary.replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "")
                
                item = MediaItem(
                    id=idx,
                    title=show.get("name", "Desconhecido"),
                    type="series",
                    genre=show.get("genres", ["Drama"]),
                    release_year=year,
                    rating=rating,
                    synopsis=summary,
                    cast=["Elenco padrão TVmaze"],
                    episodes=show.get("averageRuntime", 45)
                )
                DATABASE.append(item)
    except Exception:
        DATABASE.append(
            MediaItem(id=1, title="Inception", type="movie", genre=["Sci-Fi"], release_year=2010, rating=8.8, synopsis="A thief who steals corporate secrets.", cast=["Leonardo DiCaprio"])
        )

fetch_free_public_movies()

CACHE_STORE: Dict[str, dict] = {}

SCHEDULE_STORE: List[dict] = [
    {"slot_id": 1, "start_time": "18:00", "end_time": "20:30", "media_id": 1, "title": "Under the Dome (Exemplo)", "status": "Scheduled"},
    {"slot_id": 2, "start_time": "21:15", "end_time": "23:30", "media_id": 2, "title": "Person of Interest (Exemplo)", "status": "Scheduled"}
]

SITE_LOGO_CONFIG = SiteLogo()
ACTIVE_WEBSOCKETS: Set = set()