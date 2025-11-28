"""
API Routes - Endpoints do Gateway
"""

import os
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx

from app.services.provider_client import WhatsAppProviderClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Variáveis de ambiente
DJANGO_BACKEND_URL = os.getenv("DJANGO_BACKEND_URL", "http://localhost:8000")
DJANGO_WEBHOOK_ENDPOINT = f"{DJANGO_BACKEND_URL}/api/whatsapp/webhook-from-gateway/"

# Inicializar cliente do provedor
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")
provider_client = WhatsAppProviderClient(
    base_url=PROVIDER_BASE_URL,
    api_key=PROVIDER_API_KEY
)


class WhatsAppWebhookPayload(BaseModel):
    """Modelo para payload do webhook do provedor"""
    from: Optional[str] = None
    to: Optional[str] = None
    message: Optional[str] = None
    messageId: Optional[str] = None
    timestamp: Optional[int] = None
    type: Optional[str] = None
    # Campos adicionais podem variar por provedor
    data: Optional[Dict[str, Any]] = None


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint que recebe webhooks do provedor de WhatsApp
    
    Fluxo:
    1. Recebe evento do provedor (Z-API, Evolution API, etc.)
    2. Extrai dados da mensagem
    3. Envia para o backend Django
    4. Recebe resposta do Django (pode conter campo 'reply')
    5. Se houver 'reply', envia de volta via provedor
    """
    try:
        # Receber payload do provedor
        payload = await request.json()
        logger.info(f"📥 Webhook recebido: {payload}")
        
        # Normalizar payload (diferentes provedores têm formatos diferentes)
        normalized = _normalize_payload(payload)
        
        if not normalized.get("from") or not normalized.get("message"):
            logger.warning("⚠️ Payload incompleto, ignorando")
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "message": "Payload incompleto ignorado"}
            )
        
        # Enviar para o backend Django
        django_payload = {
            "from": normalized["from"],
            "message": normalized["message"],
            "message_id": normalized.get("message_id"),
            "timestamp": normalized.get("timestamp"),
            "type": normalized.get("type", "text")
        }
        
        logger.info(f"📤 Enviando para Django: {django_payload}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    DJANGO_WEBHOOK_ENDPOINT,
                    json=django_payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                django_response = response.json()
                logger.info(f"📥 Resposta do Django: {django_response}")
                
                # Verificar se há resposta para enviar
                if django_response.get("reply"):
                    reply_message = django_response["reply"]
                    phone_number = normalized["from"]
                    
                    logger.info(f"📱 Enviando resposta para {phone_number}: {reply_message}")
                    
                    # Enviar resposta via provedor
                    send_result = await provider_client.send_text(
                        phone=phone_number,
                        message=reply_message
                    )
                    
                    logger.info(f"✅ Mensagem enviada: {send_result}")
                    
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "ok",
                            "message": "Processado com sucesso",
                            "reply_sent": True
                        }
                    )
                else:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "ok",
                            "message": "Processado, sem resposta automática",
                            "reply_sent": False
                        }
                    )
                    
            except httpx.HTTPError as e:
                logger.error(f"❌ Erro ao comunicar com Django: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Erro ao comunicar com backend"}
                )
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza payload de diferentes provedores para formato padrão
    
    Suporta formatos de:
    - Z-API
    - Evolution API
    - UltraMsg
    - Outros formatos comuns
    """
    normalized = {
        "from": None,
        "message": None,
        "message_id": None,
        "timestamp": None,
        "type": "text"
    }
    
    # Tentar diferentes formatos de campos
    # Campo "from" pode vir como: from, phone, phoneNumber, sender, etc.
    normalized["from"] = (
        payload.get("from") or
        payload.get("phone") or
        payload.get("phoneNumber") or
        payload.get("sender") or
        payload.get("data", {}).get("from")
    )
    
    # Campo "message" pode vir como: message, text, body, content, etc.
    normalized["message"] = (
        payload.get("message") or
        payload.get("text") or
        payload.get("body") or
        payload.get("content") or
        payload.get("data", {}).get("message") or
        payload.get("data", {}).get("text")
    )
    
    # Message ID
    normalized["message_id"] = (
        payload.get("messageId") or
        payload.get("message_id") or
        payload.get("id") or
        payload.get("data", {}).get("messageId")
    )
    
    # Timestamp
    normalized["timestamp"] = (
        payload.get("timestamp") or
        payload.get("time") or
        payload.get("data", {}).get("timestamp")
    )
    
    # Tipo de mensagem
    normalized["type"] = (
        payload.get("type") or
        payload.get("messageType") or
        payload.get("data", {}).get("type") or
        "text"
    )
    
    return normalized

