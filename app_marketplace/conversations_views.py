"""
Views para Sistema de Conversas Individuais WhatsApp - Estilo Umbler Talk
Paradigma: Grupo para vendas → Atendimento individual após compra
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from django.core.paginator import Paginator
import json
from datetime import timedelta

from .models import (
    WhatsappConversation, WhatsappMessage, WhatsappParticipant,
    WhatsappGroup, WhatsappOrder, Cliente, PersonalShopper,
    ConversationNote
)
from .whatsapp_views import send_message


# ============================================================================
# CAIXA DE ENTRADA UNIFICADA - ESTILO UMBLER TALK
# ============================================================================

@login_required
def conversations_inbox(request):
    """
    Caixa de entrada unificada de conversas WhatsApp
    Inspirado no Umbler Talk - https://www.umbler.com/br
    """
    # Verificar se é shopper ou keeper
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito a Personal Shoppers ou Keepers.")
        return redirect('home')
    
    # Base queryset - conversas dos grupos do usuário
    conversations = WhatsappConversation.objects.filter(
        Q(group__owner=request.user) | Q(assigned_to=request.user)
    ).select_related(
        'participant', 'cliente', 'group', 'assigned_to'
    ).prefetch_related('related_orders')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    assigned_filter = request.GET.get('assigned', '')
    tag_filter = request.GET.get('tag', '')
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', '')
    
    # Aplicar filtros
    if status_filter:
        conversations = conversations.filter(status=status_filter)
    else:
        # Padrão: mostrar novas e abertas
        conversations = conversations.filter(status__in=['new', 'open', 'waiting'])
    
    if assigned_filter == 'me':
        conversations = conversations.filter(assigned_to=request.user)
    elif assigned_filter == 'unassigned':
        conversations = conversations.filter(assigned_to__isnull=True)
    
    if tag_filter:
        conversations = conversations.filter(tags__contains=[tag_filter])
    
    if priority_filter:
        conversations = conversations.filter(priority__gte=int(priority_filter))
    
    if search_query:
        conversations = conversations.filter(
            Q(participant__name__icontains=search_query) |
            Q(participant__phone__icontains=search_query) |
            Q(conversation_id__icontains=search_query) |
            Q(messages__content__icontains=search_query)
        ).distinct()
    
    # Estatísticas para sidebar
    all_conversations = WhatsappConversation.objects.filter(
        Q(group__owner=request.user) | Q(assigned_to=request.user)
    )
    
    stats = {
        'total': all_conversations.count(),
        'new': all_conversations.filter(status='new').count(),
        'open': all_conversations.filter(status='open').count(),
        'waiting': all_conversations.filter(status='waiting').count(),
        'pending': all_conversations.filter(status='pending').count(),
        'resolved': all_conversations.filter(status='resolved').count(),
        'closed': all_conversations.filter(status='closed').count(),
        'unread': all_conversations.filter(unread_count__gt=0).count(),
        'assigned_to_me': all_conversations.filter(assigned_to=request.user, status__in=['new', 'open', 'waiting']).count(),
    }
    
    # Ordenar por não lidas primeiro, depois por prioridade e última mensagem
    conversations = conversations.order_by(
        '-unread_count',
        '-priority',
        '-last_message_at'
    )
    
    # Paginação
    paginator = Paginator(conversations, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Tags disponíveis para filtro
    all_tags = set()
    for conv in all_conversations:
        all_tags.update(conv.tags or [])
    
    context = {
        'page_obj': page_obj,
        'conversations': page_obj,
        'stats': stats,
        'all_tags': sorted(all_tags),
        'filters': {
            'status': status_filter,
            'assigned': assigned_filter,
            'tag': tag_filter,
            'search': search_query,
            'priority': priority_filter,
        },
        'user_type': 'shopper' if request.user.is_shopper else 'keeper',
    }
    
    return render(request, 'app_marketplace/conversations_inbox.html', context)


# ============================================================================
# DETALHES DA CONVERSA - CHAT INDIVIDUAL
# ============================================================================

@login_required
def conversation_detail(request, conversation_id):
    """
    Visualização detalhada de uma conversa individual
    Estilo chat WhatsApp
    """
    # Verificar se é shopper ou keeper
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito a Personal Shoppers ou Keepers.")
        return redirect('home')
    
    # Buscar conversa (verificar permissão)
    conversation = get_object_or_404(
        WhatsappConversation.objects.select_related(
            'participant', 'cliente', 'group', 'assigned_to'
        ).prefetch_related('related_orders', 'messages'),
        conversation_id=conversation_id
    )
    
    # Verificar se tem permissão (dono do grupo ou atribuído a ele)
    if conversation.group and conversation.group.owner != request.user:
        if conversation.assigned_to != request.user:
            messages.error(request, "Você não tem permissão para acessar esta conversa.")
            return redirect('conversations_inbox')
    
    # Mensagens da conversa
    messages_list = conversation.messages.all().order_by('timestamp')[:100]
    
    # Marcar mensagens como lidas
    if conversation.unread_count > 0:
        conversation.mark_as_read(request.user)
    
    # Informações do cliente
    cliente_info = {
        'name': conversation.participant.name or conversation.participant.phone,
        'phone': conversation.participant.phone,
        'cliente': conversation.cliente,
        'pedidos': conversation.related_orders.all() if conversation.related_orders.exists() else [],
        'total_pedidos': conversation.related_orders.count(),
        'total_gasto': conversation.related_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
    }
    
    # Notas internas
    internal_notes = conversation.internal_notes.all().order_by('-created_at')[:10]
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'cliente_info': cliente_info,
        'internal_notes': internal_notes,
        'user_type': 'shopper' if request.user.is_shopper else 'keeper',
    }
    
    return render(request, 'app_marketplace/conversation_detail.html', context)


# ============================================================================
# APIS - ENVIAR MENSAGEM, ATRIBUIR, TAGS, etc.
# ============================================================================

@login_required
@require_http_methods(["POST"])
def send_conversation_message(request, conversation_id):
    """
    API para enviar mensagem em uma conversa individual
    POST /api/conversations/{conversation_id}/send-message/
    """
    conversation = get_object_or_404(
        WhatsappConversation,
        conversation_id=conversation_id
    )
    
    # Verificar permissão
    if conversation.group and conversation.group.owner != request.user:
        if conversation.assigned_to != request.user:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)
        
        # Obter chat_id (do participante ou grupo)
        chat_id = None
        if conversation.participant:
            # Se tem grupo, usar grupo; senão, mensagem direta
            if conversation.group:
                chat_id = conversation.group.chat_id
            else:
                # Mensagem direta ao participante
                chat_id = f"{conversation.participant.phone}@c.us"
        
        if not chat_id:
            return JsonResponse({'error': 'Chat ID não encontrado'}, status=400)
        
        # Enviar mensagem via WhatsApp
        result = send_message(chat_id, message_text)
        
        if result.get('error'):
            return JsonResponse({'error': result['error']}, status=500)
        
        # Criar registro da mensagem
        message = WhatsappMessage.objects.create(
            message_id=f"web_{timezone.now().timestamp()}",
            group=conversation.group,
            sender=conversation.participant,  # Ou criar um sender do sistema
            message_type='text',
            content=message_text,
            timestamp=timezone.now(),
            conversation=conversation,
            is_from_customer=False,
            read=True,
            read_at=timezone.now(),
        )
        
        # Atualizar conversa
        conversation.last_message_at = timezone.now()
        conversation.message_count += 1
        conversation.status = 'open' if conversation.status == 'new' else conversation.status
        
        # Se é primeira resposta, registrar
        if not conversation.first_response_at:
            conversation.first_response_at = timezone.now()
        
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def assign_conversation(request, conversation_id):
    """
    Atribuir conversa para um agente
    POST /api/conversations/{conversation_id}/assign/
    """
    conversation = get_object_or_404(
        WhatsappConversation,
        conversation_id=conversation_id
    )
    
    # Verificar permissão (dono do grupo)
    if conversation.group and conversation.group.owner != request.user:
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        data = json.loads(request.body)
        agent_id = data.get('agent_id')
        
        if agent_id:
            from django.contrib.auth.models import User
            agent = get_object_or_404(User, id=agent_id)
        else:
            # Atribuir para si mesmo
            agent = request.user
        
        conversation.assign(agent)
        
        return JsonResponse({
            'success': True,
            'conversation': {
                'id': conversation.conversation_id,
                'assigned_to': agent.username,
                'status': conversation.status,
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_conversation_status(request, conversation_id):
    """
    Atualizar status da conversa
    POST /api/conversations/{conversation_id}/status/
    """
    conversation = get_object_or_404(
        WhatsappConversation,
        conversation_id=conversation_id
    )
    
    # Verificar permissão
    if conversation.group and conversation.group.owner != request.user:
        if conversation.assigned_to != request.user:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status', '').strip()
        
        valid_statuses = ['new', 'open', 'waiting', 'pending', 'resolved', 'closed']
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Status inválido'}, status=400)
        
        conversation.status = new_status
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'conversation': {
                'id': conversation.conversation_id,
                'status': conversation.status,
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_conversation_tag(request, conversation_id):
    """
    Adicionar tag à conversa
    POST /api/conversations/{conversation_id}/tags/
    """
    conversation = get_object_or_404(
        WhatsappConversation,
        conversation_id=conversation_id
    )
    
    # Verificar permissão
    if conversation.group and conversation.group.owner != request.user:
        if conversation.assigned_to != request.user:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        data = json.loads(request.body)
        tag = data.get('tag', '').strip()
        
        if not tag:
            return JsonResponse({'error': 'Tag vazia'}, status=400)
        
        conversation.add_tag(tag)
        
        # Recalcular prioridade
        conversation.auto_calculate_priority()
        
        return JsonResponse({
            'success': True,
            'tags': conversation.tags,
            'priority': conversation.priority,
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_conversation_note(request, conversation_id):
    """
    Criar nota interna sobre a conversa
    POST /api/conversations/{conversation_id}/notes/
    """
    conversation = get_object_or_404(
        WhatsappConversation,
        conversation_id=conversation_id
    )
    
    # Verificar permissão
    if conversation.group and conversation.group.owner != request.user:
        if conversation.assigned_to != request.user:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        data = json.loads(request.body)
        note_content = data.get('content', '').strip()
        
        if not note_content:
            return JsonResponse({'error': 'Nota vazia'}, status=400)
        
        note = ConversationNote.objects.create(
            conversation=conversation,
            author=request.user,
            content=note_content
        )
        
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'author': note.author.username,
                'created_at': note.created_at.isoformat(),
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# SISTEMA DE TRANSIÇÃO GRUPO → INDIVIDUAL (APÓS PEDIDO)
# ============================================================================

def create_conversation_after_order(order):
    """
    Cria conversa individual automaticamente após pedido
    Chamado quando um pedido é criado
    """
    try:
        # Verificar se já existe conversa para este participante e pedido
        existing = WhatsappConversation.objects.filter(
            participant=order.customer,
            related_orders=order,
            source='after_purchase'
        ).first()
        
        if existing:
            return existing
        
        # Criar nova conversa
        conversation = WhatsappConversation.objects.create(
            group=order.group,
            participant=order.customer,
            cliente=order.cliente,
            status='new',
            source='after_purchase',
            priority=5,  # Prioridade média para pedidos
        )
        
        # Vincular pedido
        conversation.related_orders.add(order)
        
        # Adicionar tags
        conversation.add_tag('pedido')
        conversation.add_tag('pós-compra')
        
        # Recalcular prioridade
        conversation.auto_calculate_priority()
        
        # Enviar mensagem de boas-vindas (opcional)
        welcome_message = (
            f"✅ *Pedido criado com sucesso!*\n\n"
            f"📋 Número: {order.order_number}\n"
            f"💰 Total: {order.total_amount} {order.currency}\n\n"
            f"A partir de agora, você terá atendimento individualizado. "
            f"Estamos aqui para ajudar com qualquer dúvida sobre seu pedido!\n\n"
            f"_ÉVORA Connect_ ✨"
        )
        
        chat_id = order.group.chat_id if order.group else f"{order.customer.phone}@c.us"
        send_message(chat_id, welcome_message)
        
        return conversation
    
    except Exception as e:
        print(f"Erro ao criar conversa após pedido: {e}")
        return None

