"""
Views - WhatsApp Integration
============================

Views para receber e processar mensagens do gateway WhatsApp.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
import json
import logging

from .models import WhatsAppContact, WhatsAppMessageLog
from app_marketplace.models import Cliente, PersonalShopper, AddressKeeper

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_from_gateway(request):
    """
    Endpoint que recebe mensagens do gateway WhatsApp
    
    Fluxo:
    1. Recebe mensagem do gateway
    2. Identifica o contato (cria se não existir)
    3. Salva log da mensagem
    4. Identifica tipo de usuário (Cliente, Shopper, Keeper)
    5. Retorna resposta (se houver)
    
    Payload esperado:
    {
        "from": "5511999999999",
        "message": "Texto da mensagem",
        "message_id": "msg_123",
        "timestamp": "2025-11-29T20:00:00Z",
        "type": "text"
    }
    
    Retorna:
    {
        "reply": "Resposta automática"  // Opcional
    }
    """
    try:
        # Parse do payload
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            return JsonResponse(
                {'error': 'Content-Type deve ser application/json'},
                status=400
            )
        
        from_number = data.get('from') or data.get('from_number')
        message = data.get('message') or data.get('text') or data.get('body')
        message_id = data.get('message_id') or data.get('id')
        message_type = data.get('type', 'text')
        timestamp_str = data.get('timestamp')
        raw_payload = data.get('raw_payload', data)
        
        if not from_number or not message:
            logger.warning(f"Payload incompleto: {data}")
            return JsonResponse({'error': 'Campos obrigatórios faltando'}, status=400)
        
        # Normalizar número de telefone
        phone = from_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not phone.startswith("+"):
            phone = f"+{phone}"
        
        # Parse timestamp
        try:
            if timestamp_str:
                from django.utils.dateparse import parse_datetime
                timestamp = parse_datetime(timestamp_str) or timezone.now()
            else:
                timestamp = timezone.now()
        except Exception:
            timestamp = timezone.now()
        
        # Processar em transação
        with transaction.atomic():
            # Buscar ou criar contato
            contact, created = WhatsAppContact.objects.get_or_create(
                phone=phone,
                defaults={'name': data.get('name', '')}
            )
            
            # Tentar identificar o usuário vinculado
            if not contact.user and not contact.cliente and not contact.shopper and not contact.keeper:
                # Tentar encontrar por telefone
                # Cliente
                cliente = Cliente.objects.filter(telefone__icontains=phone.replace('+', '')).first()
                if cliente:
                    contact.cliente = cliente
                    if cliente.user:
                        contact.user = cliente.user
                    contact.save()
                else:
                    # Shopper (via user)
                    # Keeper (via user)
                    # Por enquanto, deixar sem vinculação
                    pass
            
            # Criar log da mensagem
            message_log = WhatsAppMessageLog.objects.create(
                message_id=message_id or f"msg_{timezone.now().timestamp()}",
                contact=contact,
                phone=phone,
                direction=WhatsAppMessageLog.MessageDirection.INBOUND,
                message_type=message_type,
                content=message,
                timestamp=timestamp,
                raw_payload=raw_payload
            )
            
            # Atualizar último contato do contato
            contact.last_message_at = timestamp
            contact.save()
            
            # Processar mensagem e gerar resposta
            reply_message = process_message(contact, message, message_log)
            
            # Marcar como processada
            message_log.processed = True
            if reply_message:
                message_log.reply_sent = True
                message_log.reply_content = reply_message
            message_log.save()
        
        # Retornar resposta
        response_data = {}
        if reply_message:
            response_data['reply'] = reply_message
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def process_message(contact: WhatsAppContact, message: str, message_log: WhatsAppMessageLog) -> str:
    """
    Processa mensagem recebida e gera resposta automática
    
    Args:
        contact: Contato que enviou a mensagem
        message: Texto da mensagem
        message_log: Log da mensagem
        
    Returns:
        Resposta automática (ou None se não houver)
    """
    message_lower = message.lower().strip()
    
    # Respostas automáticas básicas
    if message_lower in ['oi', 'olá', 'ola', 'hi', 'hello']:
        return "Olá! Bem-vindo ao Évora Connect. Como posso ajudar?"
    
    if message_lower in ['ajuda', 'help', 'comandos']:
        return "Comandos disponíveis:\n- /produtos: Ver produtos disponíveis\n- /pedidos: Ver meus pedidos\n- /status: Ver status do sistema"
    
    if message_lower.startswith('/produtos'):
        return "Acesse seus produtos em: https://evora-product.up.railway.app/client/products/"
    
    if message_lower.startswith('/pedidos'):
        return "Acesse seus pedidos em: https://evora-product.up.railway.app/client/orders/"
    
    # Identificar tipo de usuário e responder adequadamente
    user_type = contact.user_type
    
    if user_type == 'cliente':
        return f"Olá! Você é um cliente. Digite /produtos para ver produtos ou /pedidos para ver seus pedidos."
    
    elif user_type == 'shopper':
        return f"Olá Shopper! Acesse seu dashboard: https://evora-product.up.railway.app/shopper/dashboard/"
    
    elif user_type == 'keeper':
        return f"Olá Keeper! Acesse seu dashboard: https://evora-product.up.railway.app/"
    
    # Resposta padrão para contatos não identificados
    return "Olá! Bem-vindo ao Évora Connect. Para começar, acesse: https://evora-product.up.railway.app/"
