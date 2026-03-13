import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Cargar variables de entorno antes de importar core o services
load_dotenv()

from app.api.endpoints import router as api_router

from app.core.rate_limit import limiter

app = FastAPI(title="Script Generator Microservice", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000", "https://www.tucaserito.com"]')
try:
    origins = json.loads(allowed_origins_env)
except Exception:
    origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

app.include_router(api_router, prefix="/api/v1/scripts")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
