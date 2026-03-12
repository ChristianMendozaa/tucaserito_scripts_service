from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno antes de importar core o services
load_dotenv()

from app.api.endpoints import router as api_router

app = FastAPI(title="Script Generator Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://www.tucaserito.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1/scripts")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
