from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import httpx
import database
import schemas

# Inicializa o banco de dados
database.init_db()

app = FastAPI(
    title="CinePayload Animation API",
    description="API dedicada de streaming 24/7 para animações e conteúdo infantil.",
    version="1.0.0"
)

# Configuração de CORS para permitir requisições do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dados de fallback padrão caso a fonte externa não responda ou venha vazia
DEFAULT_ANIMATIONS = [
    {
        "title": "3ABN Kids Network",
        "type": "movie",
        "genre": ["Animação", "Infantil"],
        "release_year": 2024,
        "rating": 8.5,
        "synopsis": "Transmissão contínua de desenhos animados e programação infantil 24h.",
        "cast": ["Turma Animada"],
        "stream_url": "https://3abn.bozztv.com/3abn2/Kids_Live/smil:Kids_live.smil/playlist.m3u8",
        "logo_url": "https://i.imgur.com/z3apq01.png"
    }
]

@app.get("/")
def read_root():
    return {"message": "CinePayload Animation API está no ar!", "docs": "/docs"}

@app.get("/api/v1/media")
def get_media(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    items = db.query(database.MediaModel).offset(skip).limit(limit).all()
    
    # Se o banco estiver vazio, injeta automaticamente o fallback para nunca retornar vazio
    if not items:
        for item_data in DEFAULT_ANIMATIONS:
            db_item = database.MediaModel(**item_data)
            db.add(db_item)
        db.commit()
        items = db.query(database.MediaModel).offset(skip).limit(limit).all()

    total = db.query(database.MediaModel).count()
    return {
        "success": True,
        "message": "Mídias de animação recuperadas com sucesso.",
        "data": {
            "total": total,
            "results": items
        }
    }

@app.post("/api/v1/refresh")
def refresh_catalog(db: Session = Depends(database.get_db)):
    try:
        # Insere os dados padrão garantindo o catálogo atualizado
        db.query(database.MediaModel).delete()
        db.commit()

        for item_data in DEFAULT_ANIMATIONS:
            db_item = database.MediaModel(**item_data)
            db.add(db_item)
        db.commit()

        return {
            "success": True,
            "message": "Catálogo de animações atualizado com sucesso.",
            "total_added": len(DEFAULT_ANIMATIONS)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar o catálogo: {str(e)}"
        )
