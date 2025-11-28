"""
Views para WhatsApp Integration
Endpoint que recebe webhooks do gateway FastAPI
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
import json

from .models import WhatsAppContact, WhatsAppMessageLog

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_from_gateway(request):
    """
    Endpoint que recebe mensagens do gateway FastAPI
    
    Este endpoint é chamado pelo vz_whatsapp_gateway quando uma mensagem
    é recebida do provedor de WhatsApp.
    
    Payload esperado:
    {
        "from": "5511999999999",
        "message": "texto da mensagem",
        "message_id": "123",
        "timestamp": 1234567890,
        "type": "text"
    }
    
    Resposta:
    {
        "reply": "mensagem de resposta automática"  # opcional
    }
    
    Se o campo "reply" estiver presente, o gateway enviará essa mensagem
    de volta ao WhatsApp via provedor.
    """
    try:
        # Parse do JSON
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar JSON: {e}")
            return JsonResponse(
                {"error": "Invalid JSON"},
                status=400
            )
        
        # Validar campos obrigatórios
        phone_number = payload.get("from")
        message_text = payload.get("message")
        
        if not phone_number or not message_text:
            logger.warning("⚠️ Payload incompleto: faltando 'from' ou 'message'")
            return JsonResponse(
                {"error": "Missing required fields: 'from' and 'message'"},
                status=400
            )
        
        logger.info(f"📥 Mensagem recebida de {phone_number}: {message_text[:50]}")
        
        # Normalizar número de telefone
        phone_number = _normalize_phone(phone_number)
        
        # Processar em transação
        with transaction.atomic():
            # Buscar ou criar contato
            contact, created = WhatsAppContact.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'name': payload.get('name', ''),
                    'contact_type': 'unknown'
                }
            )
            
            if created:
                logger.info(f"✅ Novo contato criado: {phone_number}")
            
            # Identificar tipo de contato (Keeper, Shopper, Cliente)
            contact_type = _identify_contact_type(contact, phone_number)
            if contact_type != contact.contact_type:
                contact.contact_type = contact_type
                contact.save(update_fields=['contact_type'])
            
            # Criar log da mensagem
            message_log = WhatsAppMessageLog.objects.create(
                contact=contact,
                direction='incoming',
                message_text=message_text,
                provider_message_id=payload.get('message_id'),
                message_type=payload.get('type', 'text'),
                message_timestamp=_parse_timestamp(payload.get('timestamp')),
                metadata={
                    'raw_payload': payload,
                    'gateway_received_at': timezone.now().isoformat()
                }
            )
            
            logger.info(f"📝 Log criado: {message_log.id}")
            
            # Processar mensagem e gerar resposta (se necessário)
            reply_message = _process_message(contact, message_text, message_log)
            
            # Marcar como processada
            if reply_message:
                message_log.auto_reply_sent = True
            message_log.processing_status = 'processed'
            message_log.save(update_fields=['processing_status', 'auto_reply_sent'])
        
        # Retornar resposta
        response_data = {}
        if reply_message:
            response_data['reply'] = reply_message
            logger.info(f"📤 Resposta gerada: {reply_message[:50]}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}", exc_info=True)
        return JsonResponse(
            {"error": "Internal server error"},
            status=500
        )


def _normalize_phone(phone: str) -> str:
    """Normaliza número de telefone para formato padrão"""
    # Remove caracteres não numéricos
    phone = ''.join(filter(str.isdigit, phone))
    
    # Se não começar com código do país, assumir Brasil (55)
    if not phone.startswith('55') and len(phone) <= 11:
        phone = '55' + phone
    
    return phone


def _parse_timestamp(timestamp):
    """Converte timestamp Unix para datetime"""
    if timestamp:
        try:
            return timezone.datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, TypeError):
            pass
    return timezone.now()


def _identify_contact_type(contact: WhatsAppContact, phone_number: str) -> str:
    """
    Identifica o tipo de contato (Keeper, Shopper, Cliente)
    
    Por enquanto, implementação simples. Futuramente, será integrado
    com o sistema KMN para identificar baseado em:
    - Trustlines
    - Relacionamentos
    - Registros no sistema
    """
    # Se já tem user associado, tentar identificar pelo user
    if contact.user:
        # TODO: Verificar se user é Keeper, Shopper ou Cliente
        # Por enquanto, retornar 'unknown'
        pass
    
    # TODO: Integrar com app_marketplace para verificar:
    # - Se é um Agente (Keeper)
    # - Se é um PersonalShopper
    # - Se é um Cliente
    
    # Por enquanto, retornar 'unknown'
    return 'unknown'


def _process_message(
    contact: WhatsAppContact,
    message_text: str,
    message_log: WhatsAppMessageLog
) -> str:
    """
    Processa a mensagem e gera resposta automática
    
    Por enquanto, implementação simples. Futuramente, será integrado
    com DropKeeping e KMN para:
    - Processar comandos (/comprar, /status, etc.)
    - Consultar catálogo
    - Verificar ofertas
    - Gerenciar pedidos
    """
    message_lower = message_text.lower().strip()
    
    # Respostas automáticas simples
    if message_lower in ['oi', 'olá', 'ola', 'hello', 'hi']:
        return "Olá! Bem-vindo ao VitrineZap. Como posso ajudar?"
    
    if message_lower in ['ajuda', 'help', 'comandos']:
        return (
            "Comandos disponíveis:\n"
            "/comprar - Ver produtos disponíveis\n"
            "/status - Ver status do pedido\n"
            "/ajuda - Ver esta mensagem"
        )
    
    if message_lower.startswith('/comprar'):
        return "Funcionalidade de compra será implementada em breve. Aguarde!"
    
    if message_lower.startswith('/status'):
        return "Funcionalidade de status será implementada em breve. Aguarde!"
    
    # Resposta padrão
    return (
        "Obrigado pela mensagem! "
        "Nossa equipe irá responder em breve. "
        "Envie /ajuda para ver os comandos disponíveis."
    )

