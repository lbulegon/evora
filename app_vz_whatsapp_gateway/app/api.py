"""
API Routes - Endpoints do Gateway WhatsApp
===========================================

Este módulo define os endpoints que recebem webhooks do provedor
e fazem a comunicação com o backend Django.
"""

from fastapi import APIRouter, Request, HTTPException, Body
from fastapi.responses import JSONResponse
import httpx
import logging
from typing import Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class WhatsAppWebhookPayload(BaseModel):
    """Payload recebido do provedor de WhatsApp"""
    from_number: str = None
    from_: str = None  # Alguns provedores usam "from"
    message: str = None
    message_id: str = None
    timestamp: str = None
    type: str = "text"
    # Campos adicionais que podem vir do provedor
    data: Dict[str, Any] = {}


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, payload: Dict[str, Any] = Body(...)):
    """
    Endpoint que recebe webhooks do provedor de WhatsApp
    
    Fluxo:
    1. Recebe mensagem do provedor
    2. Envia para o backend Django
    3. Recebe resposta do Django
    4. Envia resposta via provedor
    """
    try:
        # Normalizar payload (diferentes provedores podem ter formatos diferentes)
        from_number = payload.get("from") or payload.get("from_number") or payload.get("phone")
        message = payload.get("message") or payload.get("text") or payload.get("body")
        message_id = payload.get("message_id") or payload.get("id")
        
        if not from_number or not message:
            logger.warning(f"Payload incompleto recebido: {payload}")
            return JSONResponse(
                status_code=200,
                content={"status": "ignored", "reason": "missing_fields"}
            )
        
        logger.info(f"Mensagem recebida de {from_number}: {message[:50]}...")
        
        # Preparar payload para enviar ao Django
        django_payload = {
            "from": from_number,
            "message": message,
            "message_id": message_id,
            "timestamp": payload.get("timestamp"),
            "type": payload.get("type", "text"),
            "raw_payload": payload  # Enviar payload completo para análise
        }
        
        # Enviar para o backend Django
        provider_client = request.app.state.provider_client
        django_backend_url = request.app.state.django_backend_url
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{django_backend_url}/api/whatsapp/webhook-from-gateway/",
                    json=django_payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                django_response = response.json()
                
                # Verificar se o Django retornou uma resposta para enviar
                reply_message = django_response.get("reply")
                
                if reply_message:
                    logger.info(f"Enviando resposta para {from_number}: {reply_message[:50]}...")
                    
                    # Enviar resposta via provedor
                    send_result = await provider_client.send_text(
                        phone=from_number,
                        message=reply_message
                    )
                    
                    if send_result.get("success"):
                        logger.info(f"Resposta enviada com sucesso para {from_number}")
                    else:
                        logger.error(f"Erro ao enviar resposta: {send_result.get('error')}")
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "processed",
                        "reply_sent": bool(reply_message)
                    }
                )
                
            except httpx.HTTPError as e:
                logger.error(f"Erro ao comunicar com Django: {str(e)}")
                return JSONResponse(
                    status_code=200,  # Retornar 200 para o provedor não reenviar
                    content={"status": "error", "error": "django_communication_failed"}
                )
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,  # Sempre retornar 200 para o provedor
            content={"status": "error", "error": str(e)}
        )


@router.get("/whatsapp")
async def whatsapp_webhook_get():
    """Endpoint GET para verificação do webhook (alguns provedores requerem)"""
    return {"status": "ok", "message": "Webhook endpoint is active"}
