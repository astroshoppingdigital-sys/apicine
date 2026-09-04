import time
import logging
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import router as api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("uvicorn.access")

app = FastAPI(
    title="CineVerse Professional API with Auto-Interval & Logo Stream",
    description="API REST profissional para filmes e séries com dados abertos, intervalos inteligentes e exibição de logo.",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IP_REQUEST_TRACKER: dict = {}
RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW = 60

@app.middleware("http")
async def professional_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    current_time = time.time()
    if client_ip not in IP_REQUEST_TRACKER:
        IP_REQUEST_TRACKER[client_ip] = []
    
    IP_REQUEST_TRACKER[client_ip] = [t for t in IP_REQUEST_TRACKER[client_ip] if current_time - t < RATE_LIMIT_WINDOW]
    if len(IP_REQUEST_TRACKER[client_ip]) >= RATE_LIMIT_MAX:
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": "Rate limit excedido."})
    
    IP_REQUEST_TRACKER[client_ip].append(current_time)
    
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        logger.error(f"Erro crítico: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor."})
        
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "timestamp": time.time(), "version": "1.2.0", "interval_system": "active"}

app.include_router(api_router, prefix="/api/v1")