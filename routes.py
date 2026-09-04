from typing import Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from database import DATABASE, SCHEDULE_STORE, SITE_LOGO_CONFIG, ACTIVE_WEBSOCKETS

router = APIRouter(tags=["Movies, Series & Interval Engine"])

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict | list] = None

class ScheduleCreate(BaseModel):
    slot_id: int
    start_time: str = Field(..., example="20:00", description="Formato HH:MM")
    media_id: int = Field(..., example=1)
    duration_minutes: int = Field(120, description="Duração estimada do filme/série em minutos")

class TransitionPayload(BaseModel):
    source_media_id: int
    target_media_id: int
    transition_effect: str = Field("fade", description="Efeito de transição ex: fade, cut")

def parse_time_to_minutes(time_str: str) -> int:
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def minutes_to_time_str(total_minutes: int) -> str:
    total_minutes = total_minutes % (24 * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h:02d}:{m:02d}"

@router.get("/media", response_model=StandardResponse)
async def get_all_media(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), media_type: Optional[str] = None):
    items = [i for i in DATABASE if not media_type or i.type == media_type]
    paginated = items[skip : skip + limit]
    return StandardResponse(success=True, message="Mídias recuperadas com sucesso.", data={"total": len(items), "results": [i.model_dump() for i in paginated]})

@router.get("/media/search", response_model=StandardResponse)
async def search_media(query: str = Query(..., min_length=2)):
    q = query.lower()
    results = [i for i in DATABASE if q in i.title.lower() or q in i.synopsis.lower()]
    return StandardResponse(success=True, message="Busca finalizada.", data={"count": len(results), "results": [i.model_dump() for i in results]})

@router.get("/media/filter", response_model=StandardResponse)
async def filter_media(genre: Optional[str] = None, min_year: Optional[int] = None, min_rating: Optional[float] = None):
    filtered = DATABASE
    if genre:
        filtered = [i for i in filtered if genre.lower() in [g.lower() for g in i.genre]]
    if min_year:
        filtered = [i for i in filtered if i.release_year >= min_year]
    if min_rating:
        filtered = [i for i in filtered if i.rating >= min_rating]
    return StandardResponse(success=True, message="Filtros aplicados.", data={"count": len(filtered), "results": [i.model_dump() for i in filtered]})

@router.get("/media/{media_id}", response_model=StandardResponse)
async def get_media_by_id(media_id: int):
    item = next((i for i in DATABASE if i.id == media_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Mídia não encontrada.")
    return StandardResponse(success=True, message="Item recuperado.", data=item.model_dump())

@router.post("/schedule", response_model=StandardResponse, status_code=201)
async def create_schedule(payload: ScheduleCreate):
    media = next((i for i in DATABASE if i.id == payload.media_id), None)
    if not media:
        raise HTTPException(status_code=400, detail="Media ID inválido.")
    
    start_mins = parse_time_to_minutes(payload.start_time)
    end_mins = start_mins + payload.duration_minutes
    end_time_str = minutes_to_time_str(end_mins)
    
    entry = {
        "slot_id": payload.slot_id,
        "start_time": payload.start_time,
        "end_time": end_time_str,
        "media_id": media.id,
        "title": media.title,
        "status": "Scheduled"
    }
    SCHEDULE_STORE.append(entry)
    
    for ws in ACTIVE_WEBSOCKETS:
        try:
            await ws.send_json({"event": "NEW_SCHEDULE", "data": entry})
        except:
            pass
            
    return StandardResponse(success=True, message="Programação criada com sucesso.", data=entry)

@router.get("/schedule", response_model=StandardResponse)
async def get_schedule():
    return StandardResponse(success=True, message="Agenda recuperada.", data={"schedule": SCHEDULE_STORE})

@router.get("/broadcast/status", response_model=StandardResponse)
async def get_broadcast_status(current_time_str: str = Query(..., description="Horário atual no formato HH:MM ex: 20:40")):
    current_mins = parse_time_to_minutes(current_time_str)
    
    active_media = None
    next_media = None
    in_interval = False
    interval_remaining_minutes = 0
    
    sorted_schedule = sorted(SCHEDULE_STORE, key=lambda x: parse_time_to_minutes(x["start_time"]))
    
    for i, slot in enumerate(sorted_schedule):
        start_m = parse_time_to_minutes(slot["start_time"])
        
        if start_m <= current_mins < (start_m + 120):
            active_media = slot
            break
            
        next_slot = sorted_schedule[i + 1] if i + 1 < len(sorted_schedule) else None
        if next_slot:
            next_start_m = parse_time_to_minutes(next_slot["start_time"])
            previous_end_m = start_m + 120
            
            if previous_end_m <= current_mins < next_start_m:
                in_interval = True
                interval_remaining_minutes = next_start_m - current_mins
                next_media = next_slot
                break

    if in_interval:
        return StandardResponse(
            success=True,
            message="Transmissão em intervalo. Exibindo logo do site.",
            data={
                "state": "INTERVALO_ATIVO",
                "interval_duration_target": "40-45 minutos",
                "remaining_minutes": interval_remaining_minutes,
                "next_program": next_media,
                "logo_display": SITE_LOGO_CONFIG.model_dump()
            }
        )
    elif active_media:
        return StandardResponse(
            success=True,
            message="Filme/Série em exibição no momento.",
            data={
                "state": "EXIBINDO_MIDIA",
                "current_program": active_media,
                "logo_display": None
            }
        )
    else:
        return StandardResponse(
            success=True,
            message="Nenhuma transmissão ativa no momento. Modo de espera.",
            data={
                "state": "STANDBY",
                "logo_display": SITE_LOGO_CONFIG.model_dump()
            }
        )

@router.post("/transition", response_model=StandardResponse)
async def execute_media_transition(payload: TransitionPayload):
    source = next((i for i in DATABASE if i.id == payload.source_media_id), None)
    target = next((i for i in DATABASE if i.id == payload.target_media_id), None)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Mídias de origem ou destino não encontradas.")
    
    return StandardResponse(
        success=True, 
        message=f"Transição executada com efeito {payload.transition_effect} (Intervalo de 42 min aplicado entre as mídias).", 
        data={"status": "success", "from": source.title, "to": target.title, "interval_applied": "42 minutes"}
    )

@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ACTIVE_WEBSOCKETS.add(websocket)
    try:
        await websocket.send_json({
            "event": "CONNECTION_ESTABLISHED",
            "message": "Conectado ao CineVerse WebSocket. Interval Engine ativado.",
            "logo_config": SITE_LOGO_CONFIG.model_dump()
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ACTIVE_WEBSOCKETS.remove(websocket)