"""
vz_whatsapp_gateway - Microserviço de Gateway WhatsApp
======================================================

Este microserviço atua como intermediário entre o provedor de WhatsApp
(Z-API, Evolution API, UltraMsg, etc.) e o backend Django (Évora/VitrineZap).

Fluxo:
1. Recebe webhook do provedor de WhatsApp
2. Repassa para o backend Django
3. Recebe resposta do Django
4. Envia resposta via provedor de WhatsApp

Autor: Évora Connect
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .api import router
from .services.provider_client import WhatsAppProviderClient

# Carregar variáveis de ambiente
load_dotenv()


class Settings(BaseSettings):
    """Configurações do gateway"""
    PROVIDER_BASE_URL: str = os.getenv("PROVIDER_BASE_URL", "")
    PROVIDER_API_KEY: str = os.getenv("PROVIDER_API_KEY", "")
    DJANGO_BACKEND_URL: str = os.getenv("DJANGO_BACKEND_URL", "http://localhost:8000")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    class Config:
        env_file = ".env"


settings = Settings()

# Inicializar FastAPI
app = FastAPI(
    title="Évora WhatsApp Gateway",
    description="Gateway de integração WhatsApp para Évora/VitrineZap",
    version="1.0.0"
)

# CORS - Permitir requisições do frontend e do provedor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar cliente do provedor
provider_client = WhatsAppProviderClient(
    base_url=settings.PROVIDER_BASE_URL,
    api_key=settings.PROVIDER_API_KEY
)

# Incluir rotas
app.include_router(router, prefix="/webhook")

# Variável global para acesso nas rotas
app.state.provider_client = provider_client
app.state.django_backend_url = settings.DJANGO_BACKEND_URL


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Évora WhatsApp Gateway",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check detalhado"""
    return {
        "status": "healthy",
        "provider_configured": bool(settings.PROVIDER_BASE_URL and settings.PROVIDER_API_KEY),
        "django_backend": settings.DJANGO_BACKEND_URL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True
    )
