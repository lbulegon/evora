"""
Views para integração WhatsApp - ÉVORA Connect
Webhook, handlers de comandos e envio de mensagens
"""
import json
import os
import requests
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User

from .models import (
    WhatsappGroup, GroupLinkRequest,
    ShopperOnboardingToken, KeeperOnboardingToken,
    PersonalShopper, Keeper, Cliente,
    Pacote, Categoria, Produto
)
from .whatsapp_integration import (
    parse_intent, parse_listing, calculate_score,
    detect_brand, format_order_number
)

# Configurações WPPConnect
WPP_BASE = os.getenv("WPP_BASE", "http://localhost:21465")
WPP_SESSION = os.getenv("WPP_SESSION", "session-evora")


# ============================================================================
# FUNÇÕES DE ENVIO DE MENSAGEM
# ============================================================================

def send_message(chat_id: str, text: str) -> dict:
    """
    Envia mensagem para o WhatsApp via WPPConnect
    
    Args:
        chat_id: ID do chat (pode ser grupo ou individual)
        text: Texto da mensagem
    
    Returns:
        dict com resposta da API
    """
    try:
        # Garante formato correto do chat_id
        if not chat_id.endswith("@g.us") and not chat_id.endswith("@c.us"):
            # Tenta detectar se é grupo ou individual
            if len(chat_id) > 15:  # Grupos geralmente têm IDs mais longos
                chat_id = f"{chat_id}@g.us"
            else:
                chat_id = f"{chat_id}@c.us"
        
        url = f"{WPP_BASE}/api/{WPP_SESSION}/send-message"
        payload = {
            "phone": chat_id,
            "message": text,
            "isGroup": chat_id.endswith("@g.us")
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem WhatsApp: {e}")
        return {"error": str(e)}


def send_reaction(chat_id: str, msg_id: str, emoji: str):
    """Envia reação (emoji) a uma mensagem"""
    try:
        url = f"{WPP_BASE}/api/{WPP_SESSION}/send-reaction"
        payload = {
            "phone": chat_id,
            "messageId": msg_id,
            "reaction": emoji
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar reação: {e}")


# ============================================================================
# WEBHOOK PRINCIPAL
# ============================================================================

@csrf_exempt
def whatsapp_webhook(request):
    """
    Recebe mensagens do WPPConnect
    
    Processa comandos e mensagens do WhatsApp:
    - /vincular TOKEN - vincular grupo
    - /sou_shopper TOKEN - cadastrar shopper
    - /sou_keeper TOKEN - cadastrar keeper
    - /comprar - adicionar ao carrinho
    - /pagar - finalizar pedido
    - etc.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Apenas POST")
    
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    
    # WPPConnect pode enviar diferentes estruturas
    data = payload.get("data", payload)
    msg = data.get("message", data)
    
    # Extrair informações da mensagem
    msg_id = msg.get("id") or msg.get("key", {}).get("id", "")
    chat_id = (msg.get("chatId") or msg.get("from", "")).replace("@g.us", "").replace("@c.us", "")
    sender = msg.get("sender", {})
    sender_name = sender.get("name", sender.get("pushname", ""))
    sender_phone = sender.get("id", "").replace("@c.us", "")
    body = msg.get("body", msg.get("text", ""))
    msg_type = msg.get("type", "chat")
    
    # Ignorar mensagens do próprio bot
    if msg.get("fromMe"):
        return JsonResponse({"ok": True, "ignored": "own_message"})
    
    # Criar registro da mensagem (opcional - para auditoria)
    # WhatsappMessage.objects.create(...)
    
    # ========== PROCESSAR COMANDOS ==========
    
    # 1. Vincular grupo
    if body.strip().lower().startswith("/vincular"):
        return handle_vincular_grupo(chat_id, sender_phone, sender_name, body, msg_id)
    
    # 2. Cadastro de Shopper
    if body.strip().lower().startswith("/sou_shopper"):
        return handle_cadastro_shopper(chat_id, sender_phone, sender_name, body)
    
    # 3. Cadastro de Keeper
    if body.strip().lower().startswith("/sou_keeper"):
        return handle_cadastro_keeper(chat_id, sender_phone, sender_name, body)
    
    # 4. Outros comandos (comprar, pagar, status, etc.)
    intent = parse_intent(body)
    if intent:
        return handle_general_intent(chat_id, sender_phone, sender_name, intent, msg_id)
    
    # 5. Se não for comando, verificar se é oferta/promoção
    parsed = parse_listing(body)
    if parsed.brand or parsed.price_value:
        # É uma oferta - reagir com ❤️
        send_reaction(f"{chat_id}@g.us", msg_id, "❤️")
        # Aqui você pode salvar a oferta no banco
    
    return JsonResponse({"ok": True, "processed": True})


# ============================================================================
# HANDLERS DE COMANDOS
# ============================================================================

def handle_vincular_grupo(chat_id: str, sender_phone: str, sender_name: str, body: str, msg_id: str):
    """
    Handler para comando /vincular TOKEN
    Vincula grupo WhatsApp a um PersonalShopper
    """
    parts = body.strip().split()
    
    if len(parts) < 2:
        send_message(f"{chat_id}@g.us", 
            "❌ Uso correto: /vincular TOKEN\n\n"
            "Gere o token no app ÉVORA (painel do Shopper → Vincular Grupo)"
        )
        return JsonResponse({"ok": True, "error": "token_missing"})
    
    token = parts[1].upper().strip()
    
    try:
        link_request = GroupLinkRequest.objects.select_related('shopper').get(token=token)
    except GroupLinkRequest.DoesNotExist:
        send_message(f"{chat_id}@g.us", "❌ Token inválido ou não encontrado.")
        return JsonResponse({"ok": True, "error": "invalid_token"})
    
    if not link_request.is_valid:
        send_message(f"{chat_id}@g.us",
            "⏳ Token expirado ou já usado.\n\n"
            "Gere um novo token no app ÉVORA."
        )
        return JsonResponse({"ok": True, "error": "expired_token"})
    
    # Criar ou atualizar grupo vinculado
    chat_id_full = f"{chat_id}@g.us"
    group, created = WhatsappGroup.objects.update_or_create(
        chat_id=chat_id_full,
        defaults={
            'shopper': link_request.shopper,
            'name': f"Grupo {link_request.shopper.user.username}",  # Pode extrair nome real do grupo se disponível
            'active': True
        }
    )
    
    # Marcar token como usado
    link_request.used_at = timezone.now()
    link_request.save()
    
    # Reagir com ✅
    send_reaction(chat_id_full, msg_id, "✅")
    
    # Mensagem de confirmação
    shopper_name = link_request.shopper.user.get_full_name() or link_request.shopper.user.username
    send_message(chat_id_full,
        f"✅ *Grupo vinculado com sucesso!*\n\n"
        f"Este grupo está conectado à conta ÉVORA de *{shopper_name}*.\n\n"
        f"📱 Comandos disponíveis:\n"
        f"• /comprar - fazer pedido\n"
        f"• /status - ver status do pedido\n"
        f"• /pagar - finalizar pagamento\n\n"
        f"_Powered by ÉVORA Connect_ ✨"
    )
    
    return JsonResponse({"ok": True, "linked": True, "group_id": chat_id_full})


def handle_cadastro_shopper(chat_id: str, sender_phone: str, sender_name: str, body: str):
    """
    Handler para comando /sou_shopper TOKEN
    Cadastra novo Personal Shopper via WhatsApp
    """
    parts = body.strip().split()
    
    if len(parts) < 2:
        send_message(f"{sender_phone}@c.us",
            "❌ Uso correto: /sou_shopper TOKEN\n\n"
            "Solicite o token com o administrador do ÉVORA."
        )
        return JsonResponse({"ok": True, "error": "token_missing"})
    
    token = parts[1].upper().strip().replace("SHOP-", "")
    
    try:
        onboarding_token = ShopperOnboardingToken.objects.get(token=token)
    except ShopperOnboardingToken.DoesNotExist:
        send_message(f"{sender_phone}@c.us", "❌ Token inválido.")
        return JsonResponse({"ok": True, "error": "invalid_token"})
    
    if not onboarding_token.is_valid:
        send_message(f"{sender_phone}@c.us", "⏳ Token expirado ou já usado.")
        return JsonResponse({"ok": True, "error": "expired_token"})
    
    # Verificar se já existe usuário com esse telefone
    # Formato do telefone pode precisar normalização
    username = f"shopper_{sender_phone[-8:]}"  # últimos 8 dígitos
    
    # Criar ou pegar usuário
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': sender_name.split()[0] if sender_name else '',
            'last_name': ' '.join(sender_name.split()[1:]) if sender_name and len(sender_name.split()) > 1 else ''
        }
    )
    
    # Criar perfil de PersonalShopper
    shopper, created = PersonalShopper.objects.get_or_create(
        user=user,
        defaults={
            'nome': sender_name,
            'ativo': True
        }
    )
    
    # Marcar token como usado
    onboarding_token.used_at = timezone.now()
    onboarding_token.used_by = user
    onboarding_token.save()
    
    # Mensagem de boas-vindas
    send_message(f"{sender_phone}@c.us",
        f"🎉 *Bem-vindo ao ÉVORA, {sender_name}!*\n\n"
        f"Seu cadastro como *Personal Shopper* foi concluído.\n\n"
        f"📱 *Próximos passos:*\n"
        f"1. Crie um grupo com seus clientes\n"
        f"2. Adicione este número ao grupo\n"
        f"3. Use /vincular TOKEN para conectar\n\n"
        f"💰 *Configure seu PIX:*\n"
        f"Acesse o painel ÉVORA para cadastrar sua chave PIX e receber repasses.\n\n"
        f"_ÉVORA Connect - Minimalist, Sophisticated Style_ ✨"
    )
    
    return JsonResponse({"ok": True, "shopper_created": True, "user_id": user.id})


def handle_cadastro_keeper(chat_id: str, sender_phone: str, sender_name: str, body: str):
    """
    Handler para comando /sou_keeper TOKEN
    Cadastra novo Keeper via WhatsApp
    """
    parts = body.strip().split()
    
    if len(parts) < 2:
        send_message(f"{sender_phone}@c.us",
            "❌ Uso correto: /sou_keeper TOKEN\n\n"
            "Solicite o token com o administrador do ÉVORA."
        )
        return JsonResponse({"ok": True, "error": "token_missing"})
    
    token = parts[1].upper().strip().replace("KEEP-", "")
    
    try:
        onboarding_token = KeeperOnboardingToken.objects.get(token=token)
    except KeeperOnboardingToken.DoesNotExist:
        send_message(f"{sender_phone}@c.us", "❌ Token inválido.")
        return JsonResponse({"ok": True, "error": "invalid_token"})
    
    if not onboarding_token.is_valid:
        send_message(f"{sender_phone}@c.us", "⏳ Token expirado ou já usado.")
        return JsonResponse({"ok": True, "error": "expired_token"})
    
    # Criar usuário
    username = f"keeper_{sender_phone[-8:]}"
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': sender_name.split()[0] if sender_name else '',
            'last_name': ' '.join(sender_name.split()[1:]) if sender_name and len(sender_name.split()) > 1 else ''
        }
    )
    
    # Criar perfil de Keeper
    keeper, created = Keeper.objects.get_or_create(
        user=user,
        defaults={
            'ativo': True,
            'verificado': False,  # Admin verificará depois
            'capacidade_itens': 50  # Padrão
        }
    )
    
    # Marcar token como usado
    onboarding_token.used_at = timezone.now()
    onboarding_token.used_by = user
    onboarding_token.save()
    
    # Mensagem de boas-vindas
    send_message(f"{sender_phone}@c.us",
        f"🎉 *Bem-vindo ao ÉVORA, {sender_name}!*\n\n"
        f"Seu cadastro como *Keeper* foi concluído.\n\n"
        f"📦 *Próximos passos:*\n"
        f"1. Complete seu perfil no painel ÉVORA\n"
        f"2. Cadastre seu endereço de armazenamento\n"
        f"3. Configure suas taxas de guarda\n"
        f"4. Cadastre sua chave PIX\n\n"
        f"📱 *Comandos úteis:*\n"
        f"• /checkin PED#1234 - registrar recebimento\n"
        f"• /slot PED#1234 -> A3-14 - alocar slot\n"
        f"• /mail PED#1234 - registrar postagem\n\n"
        f"_ÉVORA Connect - Minimalist, Sophisticated Style_ ✨"
    )
    
    return JsonResponse({"ok": True, "keeper_created": True, "user_id": user.id})


def handle_general_intent(chat_id: str, sender_phone: str, sender_name: str, intent, msg_id: str):
    """
    Handler genérico para outros comandos
    """
    chat_id_full = f"{chat_id}@g.us" if not chat_id.endswith(("@g.us", "@c.us")) else chat_id
    
    # Comandos do Cliente
    if intent.name == "ADD_TO_CART":
        send_message(chat_id_full,
            f"🧺 *Adicionado ao carrinho:*\n"
            f"{intent.args['qty']}x {intent.args['query']}\n\n"
            f"Use:\n"
            f"• /entrega keeper - para retirar\n"
            f"• /entrega keeper-correio - enviar por correio\n"
            f"• /pagar pix - para finalizar"
        )
        send_reaction(chat_id_full, msg_id, "✅")
    
    elif intent.name == "SET_DELIVERY":
        mode_text = {
            "PICKUP_KEEPER": "Retirada no Keeper",
            "MAIL_KEEPER": f"Envio por correio para CEP {intent.args.get('cep', '...')}",
            "BRING_BUYER": "Shopper traz ao Brasil"
        }.get(intent.args['mode'], intent.args['mode'])
        
        send_message(chat_id_full,
            f"🚚 *Forma de entrega definida:*\n{mode_text}\n\n"
            f"Agora use /pagar para finalizar o pedido."
        )
        send_reaction(chat_id_full, msg_id, "📦")
    
    elif intent.name == "PAY":
        method_text = {
            "PIX": "PIX",
            "CARTAO_CREDITO": f"Cartão de Crédito em {intent.args['installments']}x",
            "CARTAO_DEBITO": "Cartão de Débito",
            "BOLETO": "Boleto"
        }.get(intent.args['method'], intent.args['method'])
        
        # Aqui você geraria o pedido real e o link de pagamento
        order_number = format_order_number(12345)  # Trocar por ID real
        
        send_message(chat_id_full,
            f"💳 *Pedido criado!*\n\n"
            f"📋 Número: {order_number}\n"
            f"💰 Pagamento: {method_text}\n"
            f"📊 Status: Aguardando pagamento\n\n"
            f"🔗 Link de pagamento:\n"
            f"[Link será gerado aqui]\n\n"
            f"Use /status para acompanhar seu pedido."
        )
        send_reaction(chat_id_full, msg_id, "💰")
    
    elif intent.name == "STATUS":
        pedido_id = intent.args.get('pedido')
        if pedido_id:
            send_message(chat_id_full,
                f"📦 *Status do Pedido PED#{pedido_id}*\n\n"
                f"🔹 Status: Em preparação\n"
                f"🔹 Última atualização: Hoje às 14:30\n"
                f"🔹 Próximo passo: Aguardando compra\n\n"
                f"Use /rastrear PED#{pedido_id} para detalhes de rastreamento."
            )
        else:
            send_message(chat_id_full,
                f"📦 *Seus Pedidos:*\n\n"
                f"Você não tem pedidos ativos no momento.\n\n"
                f"Use /comprar para fazer um novo pedido."
            )
    
    # Comandos do Keeper
    elif intent.name == "KEEPER_CHECKIN":
        pedido = intent.args.get('pedido', '...')
        volumes = intent.args.get('volumes', 1)
        send_message(chat_id_full,
            f"📦 *Check-in registrado!*\n\n"
            f"Pedido: PED#{pedido}\n"
            f"Volumes: {volumes}\n\n"
            f"Use /slot PED#{pedido} -> A3-14 para alocar espaço."
        )
        send_reaction(chat_id_full, msg_id, "✅")
    
    elif intent.name == "KEEPER_SLOT":
        pedido = intent.args.get('pedido', '...')
        slot = intent.args.get('slot', '...')
        send_message(chat_id_full,
            f"🗄️ *Slot alocado!*\n\n"
            f"Pedido: PED#{pedido}\n"
            f"Slot: {slot}\n\n"
            f"O cliente foi notificado."
        )
        send_reaction(chat_id_full, msg_id, "✅")
    
    elif intent.name == "KEEPER_MAIL":
        pedido = intent.args.get('pedido', '...')
        tracking = intent.args.get('tracking', '...')
        send_message(chat_id_full,
            f"✉️ *Postagem registrada!*\n\n"
            f"Pedido: PED#{pedido}\n"
            f"Rastreio: {tracking}\n\n"
            f"O cliente receberá notificação com o código de rastreamento."
        )
        send_reaction(chat_id_full, msg_id, "📮")
    
    elif intent.name == "KEEPER_DELIVERED":
        pedido = intent.args.get('pedido', '...')
        send_message(chat_id_full,
            f"🎉 *Entrega confirmada!*\n\n"
            f"Pedido: PED#{pedido}\n\n"
            f"Repasse será processado em até 24h."
        )
        send_reaction(chat_id_full, msg_id, "🎉")
    
    # Comandos do Shopper/Comprador
    elif intent.name == "BUYER_ASSIGN":
        pedido = intent.args.get('pedido', '...')
        send_message(chat_id_full,
            f"🛒 *Pedido assumido!*\n\n"
            f"Pedido: PED#{pedido}\n\n"
            f"Após comprar, use:\n"
            f"/comprado PED#{pedido} nota=IMG123 valor=$XX.XX"
        )
        send_reaction(chat_id_full, msg_id, "👍")
    
    elif intent.name == "BUYER_PURCHASED":
        pedido = intent.args.get('pedido', '...')
        valor = intent.args.get('valor', '...')
        send_message(chat_id_full,
            f"🧾 *Compra confirmada!*\n\n"
            f"Pedido: PED#{pedido}\n"
            f"Valor: ${valor}\n\n"
            f"Adiantamento será processado em até 24h.\n"
            f"Aguardando recebimento pelo Keeper..."
        )
        send_reaction(chat_id_full, msg_id, "✅")
    
    elif intent.name == "BUYER_BRING":
        pedido = intent.args.get('pedido', '...')
        voo = intent.args.get('voo', '...')
        data = intent.args.get('data', '...')
        send_message(chat_id_full,
            f"✈️ *Viagem ao Brasil registrada!*\n\n"
            f"Pedido: PED#{pedido}\n"
            f"Voo: {voo}\n"
            f"Data: {data}\n\n"
            f"Cliente será notificado sobre a previsão de entrega."
        )
        send_reaction(chat_id_full, msg_id, "✈️")
    
    else:
        send_message(chat_id_full,
            f"❓ Comando não reconhecido.\n\n"
            f"Use /ajuda para ver comandos disponíveis."
        )
    
    return JsonResponse({"ok": True, "intent": intent.name})


# ============================================================================
# API ENDPOINTS PARA PAINEL
# ============================================================================

def reply_to_group(request):
    """
    Endpoint para enviar mensagem via painel ÉVORA
    POST /api/whatsapp/reply/
    Body: {"chat_id": "...", "text": "..."}
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Apenas POST")
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    
    chat_id = data.get("chat_id")
    text = data.get("text")
    
    if not chat_id or not text:
        return HttpResponseBadRequest("Campos obrigatórios: chat_id, text")
    
    result = send_message(chat_id, text)
    
    return JsonResponse({
        "ok": True,
        "result": result
    })






