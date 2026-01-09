"""
Aplicação FastAPI principal
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.firebase import initialize_firebase
from app.api import datasets, analyses
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="People Analytics API",
    description="API para análise de dados de RH e turnover",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Firebase
@app.on_event("startup")
async def startup_event():
    try:
        initialize_firebase()
        logger.info("Aplicação iniciada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar Firebase: {e}")
        raise

# Rotas
app.include_router(datasets.router, prefix=settings.API_V1_PREFIX)
app.include_router(analyses.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "message": "People Analytics API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
