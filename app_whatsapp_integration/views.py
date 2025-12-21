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
from typing import Optional
import json
import logging

from .models import (
    WhatsAppContact, 
    WhatsAppMessageLog,
    EvolutionInstance,
    EvolutionMessage
)
from .evolution_service import EvolutionAPIService
from app_marketplace.models import (
    Cliente, PersonalShopper, AddressKeeper,
    WhatsappGroup, WhatsappParticipant, WhatsappConversation
)
from app_marketplace.whatsapp_flow_engine import WhatsAppFlowEngine

logger = logging.getLogger(__name__)

# Inicializar serviços
evolution_service = EvolutionAPIService()
flow_engine = WhatsAppFlowEngine()


@csrf_exempt
@csrf_exempt
@require_http_methods(["POST", "GET"])  # Evolution API pode usar GET ou POST
def webhook_evolution_api(request):
    """
    Endpoint que recebe webhooks da Evolution API
    
    Formato Evolution API:
    {
        "event": "messages.upsert",
        "instance": "default",
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "id": "msg_123"
            },
            "message": {
                "conversation": "Texto da mensagem"
            },
            "messageTimestamp": 1234567890
        }
    }
    """
    try:
        data = json.loads(request.body)
        event = data.get('event')
        instance = data.get('instance')
        event_data = data.get('data', {})
        
        logger.info(f"Webhook Evolution API recebido: {event} da instância {instance}")
        
        # Processar apenas eventos de mensagens
        if event == 'messages.upsert':
            key = event_data.get('key', {})
            remote_jid = key.get('remoteJid', '')
            message_id = key.get('id', '')
            
            # Extrair número do JID (formato: 5511999999999@s.whatsapp.net)
            phone = remote_jid.split('@')[0] if '@' in remote_jid else remote_jid
            
            # Extrair mensagem
            message_obj = event_data.get('message', {})
            message_text = None
            message_type = 'text'
            
            if 'conversation' in message_obj:
                message_text = message_obj['conversation']
            elif 'extendedTextMessage' in message_obj:
                message_text = message_obj['extendedTextMessage'].get('text', '')
            elif 'imageMessage' in message_obj:
                message_type = 'image'
                message_text = message_obj['imageMessage'].get('caption', '')
            elif 'videoMessage' in message_obj:
                message_type = 'video'
                message_text = message_obj['videoMessage'].get('caption', '')
            
            if not message_text:
                return JsonResponse({'status': 'ok'})
            
            # Timestamp
            timestamp_ms = event_data.get('messageTimestamp', 0)
            from datetime import datetime
            timestamp = datetime.fromtimestamp(timestamp_ms) if timestamp_ms else timezone.now()
            
            # Processar mensagem
            with transaction.atomic():
                # Buscar instância no banco
                try:
                    instance = EvolutionInstance.objects.get(name=instance)
                except EvolutionInstance.DoesNotExist:
                    # Criar instância se não existir
                    instance = EvolutionInstance.objects.create(
                        name=instance,
                        status=EvolutionInstance.InstanceStatus.UNKNOWN
                    )
                
                # Buscar ou criar contato
                contact, created = WhatsAppContact.objects.get_or_create(
                    phone=f"+{phone}",
                    defaults={'name': ''}
                )
                
                # Tentar identificar usuário
                if not contact.user and not contact.cliente:
                    cliente = Cliente.objects.filter(telefone__icontains=phone).first()
                    if cliente:
                        contact.cliente = cliente
                        if cliente.user:
                            contact.user = cliente.user
                        contact.save()
                
                # Mapear tipo de mensagem
                message_type_map = {
                    'text': EvolutionMessage.MessageType.TEXT,
                    'image': EvolutionMessage.MessageType.IMAGE,
                    'video': EvolutionMessage.MessageType.VIDEO,
                    'audio': EvolutionMessage.MessageType.AUDIO,
                    'document': EvolutionMessage.MessageType.DOCUMENT,
                }
                evolution_message_type = message_type_map.get(message_type, EvolutionMessage.MessageType.UNKNOWN)
                
                # Salvar mensagem no banco Django (EvolutionMessage)
                evolution_message = EvolutionMessage.objects.create(
                    instance=instance,
                    contact=contact,
                    evolution_message_id=message_id or f"ev_{timezone.now().timestamp()}",
                    phone=f"+{phone}",
                    direction=EvolutionMessage.MessageDirection.INBOUND,
                    message_type=evolution_message_type,
                    content=message_text,
                    status=EvolutionMessage.MessageStatus.DELIVERED,
                    timestamp=timestamp,
                    raw_payload=data
                )
                
                # Também salvar no log antigo (compatibilidade)
                message_log = WhatsAppMessageLog.objects.create(
                    message_id=message_id or f"ev_{timezone.now().timestamp()}",
                    contact=contact,
                    phone=f"+{phone}",
                    direction=WhatsAppMessageLog.MessageDirection.INBOUND,
                    message_type=message_type,
                    content=message_text,
                    timestamp=timestamp,
                    raw_payload=data
                )
                
                # Atualizar último contato
                contact.last_message_at = timestamp
                contact.save()
                
                # ============================================================
                # FLUXO CONVERSACIONAL ÉVORA/VITRINEZAP
                # ============================================================
                # Verificar se é mensagem de grupo ou privada
                is_group = '@g.us' in remote_jid
                
                if is_group:
                    # FLUXO GRUPO: Intenção Social Assistida
                    grupo = _obter_grupo_por_jid(remote_jid)
                    if grupo:
                        participante = _obter_ou_criar_participante(grupo, phone, contact)
                        resultado = flow_engine.processar_mensagem_grupo(
                            grupo=grupo,
                            participante=participante,
                            mensagem=message_text,
                            mensagem_id=message_id,
                            tipo_mensagem=message_type
                        )
                        
                        # Enviar resposta no grupo se houver
                        if resultado.get('resposta_grupo'):
                            reply_message = resultado.get('resposta_grupo')
                            result = evolution_service.send_text_message(
                                number=remote_jid,
                                text=reply_message,
                                instance_name=instance.name
                            )
                            if result.get('success'):
                                message_log.reply_sent = True
                                message_log.reply_content = reply_message
                                evolution_message.processed = True
                else:
                    # FLUXO PRIVADO: Negociação e Carrinho Invisível
                    conversa = _obter_ou_criar_conversa(contact, phone)
                    if conversa:
                        participante = _obter_participante_da_conversa(conversa, phone, contact)
                        if participante:
                            resultado = flow_engine.processar_mensagem_privada(
                                conversa=conversa,
                                participante=participante,
                                mensagem=message_text,
                                mensagem_id=message_id
                            )
                            
                            # Enviar resposta do IA-Vendedor
                            if resultado.get('resposta'):
                                reply_message = resultado.get('resposta')
                                result = evolution_service.send_text_message(
                                    number=contact.phone,
                                    text=reply_message,
                                    instance_name=instance.name
                                )
                                if result.get('success'):
                                    message_log.reply_sent = True
                                    message_log.reply_content = reply_message
                                    evolution_message.processed = True
                    else:
                        # Fallback: processar mensagem padrão
                        reply_message = process_message(contact, message_text, message_log)
                        if reply_message:
                            result = evolution_service.send_text_message(contact.phone, reply_message, instance_name=instance.name)
                            if result.get('success'):
                                message_log.reply_sent = True
                                message_log.reply_content = reply_message
                                evolution_message.processed = True
                
                message_log.processed = True
                message_log.save()
                evolution_message.save()
        
        return JsonResponse({'status': 'ok'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar webhook Evolution API: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# FUNÇÕES AUXILIARES PARA FLUXO CONVERSACIONAL
# ============================================================================

def _obter_grupo_por_jid(jid: str) -> Optional[WhatsappGroup]:
    """Obtém grupo WhatsApp por JID"""
    # Extrair chat_id do JID (formato: 5511999999999@g.us)
    chat_id = jid.split('@')[0] if '@' in jid else jid
    try:
        return WhatsappGroup.objects.get(chat_id=chat_id)
    except WhatsappGroup.DoesNotExist:
        return None


def _obter_ou_criar_participante(
    grupo: WhatsappGroup,
    phone: str,
    contact: WhatsAppContact
) -> WhatsappParticipant:
    """Obtém ou cria participante do grupo"""
    participante, created = WhatsappParticipant.objects.get_or_create(
        group=grupo,
        phone=phone,
        defaults={
            'name': contact.name or 'Participante'
        }
    )
    return participante


def _obter_ou_criar_conversa(
    contact: WhatsAppContact,
    phone: str
) -> Optional[WhatsappConversation]:
    """Obtém ou cria conversa privada"""
    try:
        # Buscar participante por telefone
        participante = WhatsappParticipant.objects.filter(phone=phone).first()
        if not participante:
            return None
        
        conversa = WhatsappConversation.objects.filter(
            participant=participante
        ).order_by('-last_message_at').first()
        
        if not conversa:
            # Criar nova conversa
            conversa = WhatsappConversation.objects.create(
                conversation_id=f"PRIV-{phone}-{timezone.now().timestamp()}",
                participant=participante,
                status='open'
            )
        
        return conversa
    except Exception as e:
        logger.error(f"Erro ao obter/criar conversa: {e}")
        return None


def _obter_participante_da_conversa(
    conversa: Optional[WhatsappConversation],
    phone: str,
    contact: WhatsAppContact
) -> Optional[WhatsappParticipant]:
    """Obtém participante de uma conversa"""
    if conversa and conversa.participant:
        return conversa.participant
    
    # Buscar participante por telefone em qualquer grupo
    participante = WhatsappParticipant.objects.filter(phone=phone).first()
    if not participante:
        # Criar participante genérico (sem grupo específico)
        # Nota: Isso pode precisar de ajuste dependendo da estrutura
        pass
    
    return participante


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
        return """📱 *Comandos disponíveis:*
        
🛍️ */produtos* - Ver produtos disponíveis
📦 */pedidos* - Ver meus pedidos
📊 */status* - Ver status do sistema
🔍 */buscar [nome]* - Buscar produto
📞 */contato* - Informações de contato
ℹ️ */sobre* - Sobre o Évora Connect"""
    
    if message_lower.startswith('/produtos'):
        return "🛍️ Acesse seus produtos em: https://evora-product.up.railway.app/client/products/"
    
    if message_lower.startswith('/pedidos'):
        return "📦 Acesse seus pedidos em: https://evora-product.up.railway.app/client/orders/"
    
    if message_lower.startswith('/buscar'):
        # Extrair termo de busca
        search_term = message_lower.replace('/buscar', '').strip()
        if search_term:
            # Buscar produtos
            from app_marketplace.models import Produto
            produtos = Produto.objects.filter(
                nome__icontains=search_term
            )[:5]  # Limitar a 5 resultados
            
            if produtos.exists():
                response = f"🔍 *Encontrei {produtos.count()} produto(s):*\n\n"
                for produto in produtos:
                    response += f"• *{produto.nome}*\n"
                    if produto.marca:
                        response += f"  Marca: {produto.marca}\n"
                    response += f"  Ver: https://evora-product.up.railway.app/client/products/\n\n"
                return response
            else:
                return f"❌ Nenhum produto encontrado para '{search_term}'"
        else:
            return "🔍 Digite: /buscar [nome do produto]"
    
    if message_lower.startswith('/contato'):
        return """📞 *Contato Évora Connect:*
        
🌐 Site: https://evora-product.up.railway.app
📧 Email: contato@evora.com
💬 WhatsApp: Este número"""
    
    if message_lower.startswith('/sobre'):
        return """ℹ️ *Sobre o Évora Connect:*
        
Plataforma de marketplace e personal shopping.
Conectamos clientes, shoppers e keepers em uma experiência única de compras."""
    
    if message_lower.startswith('/status'):
        # Verificar status da instância
        try:
            result = evolution_service.get_instance_status()
            if result.get('success'):
                instance = result.get('instance', {})
                status_icon = "✅" if instance.get('status') == 'open' else "❌"
                return f"""{status_icon} *Status do Sistema:*
                
Status: {instance.get('status', 'unknown')}
Instância: {instance.get('name', 'N/A')}
Telefone: {instance.get('phone_number', 'N/A')}"""
            else:
                return f"❌ Erro ao verificar status: {result.get('error', 'Desconhecido')}"
        except Exception as e:
            return f"❌ Erro ao verificar status: {str(e)}"
    
    # Identificar tipo de usuário e responder adequadamente
    user_type = contact.user_type
    
    if user_type == 'cliente':
        return """👋 Olá! Você é um cliente.
        
Digite:
• /produtos - Ver produtos
• /pedidos - Ver seus pedidos
• /ajuda - Ver todos os comandos"""
    
    elif user_type == 'shopper':
        return """👋 Olá Shopper!
        
Acesse seu dashboard:
https://evora-product.up.railway.app/shopper/dashboard/"""
    
    elif user_type == 'keeper':
        return """👋 Olá Keeper!
        
Acesse seu dashboard:
https://evora-product.up.railway.app/"""
    
    # Resposta padrão para contatos não identificados
    return """👋 Olá! Bem-vindo ao Évora Connect.
    
Para começar, digite /ajuda para ver os comandos disponíveis.
Ou acesse: https://evora-product.up.railway.app/"""


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    Endpoint para enviar mensagem via WhatsApp
    
    Payload:
    {
        "phone": "+5511999999999",
        "message": "Texto da mensagem"
    }
    """
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        message = data.get('message')
        
        if not phone or not message:
            return JsonResponse({'error': 'phone e message são obrigatórios'}, status=400)
        
        result = evolution_service.send_text_message(phone, message)
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': 'Mensagem enviada com sucesso'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def instance_status(request):
    """
    Verifica status da instância Evolution API
    """
    try:
        result = evolution_service.get_instance_status()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_product(request):
    """
    Endpoint para enviar produto via WhatsApp
    
    Payload:
    {
        "phone": "+5511999999999",
        "product_id": 123,  // ID do produto no banco
        "product_data": {   // Ou dados do produto diretamente
            "produto": {
                "nome": "Produto",
                "marca": "Marca",
                "categoria": "Categoria",
                "preco": "R$ 100,00",
                "descricao": "Descrição"
            }
        },
        "image_url": "https://..."  // Opcional
    }
    """
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        product_id = data.get('product_id')
        product_data = data.get('product_data')
        image_url = data.get('image_url')
        
        if not phone:
            return JsonResponse({'error': 'phone é obrigatório'}, status=400)
        
        # Se forneceu product_id, buscar do banco
        if product_id and not product_data:
            from app_marketplace.models import ProdutoJSON, Produto
            produto = None
            
            # Tentar buscar primeiro no ProdutoJSON (formato completo)
            try:
                produto_json = ProdutoJSON.objects.get(id=product_id)
                dados_json = produto_json.dados_json
                produto_data_json = dados_json.get('produto', {})
                
                # Construir product_data no formato esperado
                product_data = {
                    'produto': {
                        'nome': produto_data_json.get('nome') or produto_json.nome_produto or 'Produto',
                        'marca': produto_data_json.get('marca') or produto_json.marca or '',
                        'categoria': produto_data_json.get('categoria') or produto_json.categoria or '',
                        'subcategoria': produto_data_json.get('subcategoria', ''),
                        'preco': produto_data_json.get('preco', ''),
                        'descricao': produto_data_json.get('descricao', '')
                    }
                }
                
                # Buscar primeira imagem se houver
                imagens = produto_data_json.get('imagens', [])
                if imagens and isinstance(imagens, list) and len(imagens) > 0:
                    image_path = imagens[0]
                    # Construir URL completa
                    from django.conf import settings
                    if not image_url:
                        if hasattr(settings, 'RAILWAY_URL'):
                            image_url = f"{settings.RAILWAY_URL}/api/images/proxy/{image_path}"
                        else:
                            image_url = f"http://localhost:8000/api/images/proxy/{image_path}"
                elif produto_json.imagem_original:
                    image_path = produto_json.imagem_original
                    from django.conf import settings
                    if not image_url:
                        if hasattr(settings, 'RAILWAY_URL'):
                            image_url = f"{settings.RAILWAY_URL}/api/images/proxy/{image_path}"
                        else:
                            image_url = f"http://localhost:8000/api/images/proxy/{image_path}"
                
                produto = produto_json
                
            except ProdutoJSON.DoesNotExist:
                # Tentar buscar no modelo Produto tradicional
                try:
                    produto_tradicional = Produto.objects.get(id=product_id)
                    # Construir product_data no formato esperado
                    product_data = {
                        'produto': {
                            'nome': produto_tradicional.nome or 'Produto',
                            'marca': '',  # Produto tradicional não tem marca
                            'categoria': produto_tradicional.categoria.nome if produto_tradicional.categoria else '',
                            'subcategoria': '',
                            'preco': str(produto_tradicional.preco) if produto_tradicional.preco else '',
                            'descricao': produto_tradicional.descricao or ''
                        }
                    }
                    # Buscar imagem se houver
                    if produto_tradicional.imagem:
                        from django.conf import settings
                        if not image_url:
                            if hasattr(settings, 'RAILWAY_URL'):
                                image_url = f"{settings.RAILWAY_URL}{produto_tradicional.imagem.url}"
                            else:
                                image_url = f"http://localhost:8000{produto_tradicional.imagem.url}"
                    produto = produto_tradicional
                except Produto.DoesNotExist:
                    return JsonResponse({'error': f'Produto {product_id} não encontrado'}, status=404)
        
        if not product_data:
            return JsonResponse({'error': 'product_id ou product_data é obrigatório'}, status=400)
        
        result = evolution_service.send_product_message(phone, product_data, image_url)
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': 'Produto enviado com sucesso'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao enviar produto: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)