"""
OpenMind AI Server - FastAPI Application
Servidor de IA para análise de imagens de produtos (ÉVORA Connect)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.endpoints import analyze
from app.models.schemas import HealthResponse
import logging

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="OpenMind AI Server",
    description="Servidor de IA para análise de imagens de produtos - ÉVORA Connect",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rotas
app.include_router(
    analyze.router,
    prefix="/api/v1",
    tags=["Análise"]
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "OpenMind AI Server",
        "version": "1.0.0",
        "description": "Servidor de IA para análise de imagens de produtos",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="OpenMind AI Server"
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções"""
    logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erro interno do servidor",
            "error_code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.OPENMIND_AI_HOST,
        port=settings.OPENMIND_AI_PORT,
        reload=True
    )
