"""
FastAPI Application - VZ WhatsApp Gateway
Recebe webhooks do provedor de WhatsApp e repassa para o backend Django
"""

import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Any

from app.api import router
from app.services.provider_client import WhatsAppProviderClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="VZ WhatsApp Gateway",
    description="Gateway intermediário para integração WhatsApp com Évora/VitrineZap",
    version="1.0.0"
)

# CORS - Permitir requisições do provedor e do Django
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(router)

# Variáveis de ambiente
DJANGO_BACKEND_URL = os.getenv("DJANGO_BACKEND_URL", "http://localhost:8000")
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")

# Inicializar cliente do provedor
provider_client = WhatsAppProviderClient(
    base_url=PROVIDER_BASE_URL,
    api_key=PROVIDER_API_KEY
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "VZ WhatsApp Gateway",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check detalhado"""
    return {
        "status": "ok",
        "django_backend": DJANGO_BACKEND_URL,
        "provider_configured": bool(PROVIDER_BASE_URL and PROVIDER_API_KEY)
    }


@app.on_event("startup")
async def startup_event():
    """Evento de inicialização"""
    logger.info("🚀 VZ WhatsApp Gateway iniciado")
    logger.info(f"📡 Django Backend: {DJANGO_BACKEND_URL}")
    logger.info(f"📱 Provider Base URL: {PROVIDER_BASE_URL or 'Não configurado'}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de encerramento"""
    logger.info("🛑 VZ WhatsApp Gateway encerrado")

