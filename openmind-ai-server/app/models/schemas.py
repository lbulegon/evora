"""
Schemas Pydantic para validação
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class AnalyzeResponse(BaseModel):
    """Resposta da análise de imagem"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = None


class HealthResponse(BaseModel):
    """Resposta do health check"""
    status: str
    version: str
    service: str
