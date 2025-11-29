"""
Views do Dashboard WhatsApp - ÉVORA Connect
Gerenciamento de grupos, produtos e pedidos via dashboard web
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator
import json
import requests
from decimal import Decimal

from .models import (
    PersonalShopper, WhatsappGroup, WhatsappParticipant, 
    WhatsappMessage, WhatsappProduct, WhatsappOrder,
    Cliente, Produto, Categoria
)
from .whatsapp_views import send_message, send_reaction


# ============================================================================
# DASHBOARD PRINCIPAL - GRUPOS WHATSAPP
# ============================================================================

@login_required
def whatsapp_dashboard(request):
    """Dashboard principal para gerenciar grupos WhatsApp"""
    # Verificar se é shopper ou keeper
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito a Personal Shoppers ou Keepers.")
        return redirect('home')
    
    # Determinar o tipo de usuário e pegar o perfil
    user_profile = None
    if request.user.is_shopper:
        user_profile = request.user.personalshopper
    elif request.user.is_address_keeper:
        user_profile = request.user.address_keeper
    
    # Estatísticas gerais - FILTRAR POR USUÁRIO MASTER
    groups = WhatsappGroup.objects.filter(owner=request.user)
    total_groups = groups.count()
    active_groups = groups.filter(active=True).count()
    total_participants = WhatsappParticipant.objects.filter(group__owner=request.user).count()
    total_orders = WhatsappOrder.objects.filter(group__owner=request.user).count()
    total_revenue = WhatsappOrder.objects.filter(
        group__owner=request.user, 
        status__in=['paid', 'purchased', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Grupos recentes
    recent_groups = groups.order_by('-last_activity')[:5]
    
    # Pedidos recentes
    recent_orders = WhatsappOrder.objects.filter(
        group__owner=request.user
    ).order_by('-created_at')[:10]
    
    # Produtos mais vendidos
    popular_products = WhatsappProduct.objects.filter(
        group__owner=request.user,
        is_available=True
    ).annotate(
        order_count=Count('group__orders')
    ).order_by('-order_count')[:5]
    
    context = {
        'user_profile': user_profile,
        'user_type': 'shopper' if request.user.is_shopper else 'keeper',
        'total_groups': total_groups,
        'active_groups': active_groups,
        'total_participants': total_participants,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_groups': recent_groups,
        'recent_orders': recent_orders,
        'popular_products': popular_products,
    }
    
    return render(request, 'app_marketplace/whatsapp_dashboard.html', context)


@login_required
def groups_list(request):
    """Lista todos os grupos WhatsApp do usuário master"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito a Personal Shoppers ou Keepers.")
        return redirect('home')
    
    # FILTRAR APENAS GRUPOS DO USUÁRIO MASTER
    groups = WhatsappGroup.objects.filter(owner=request.user).order_by('-last_activity')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    if search:
        groups = groups.filter(
            Q(name__icontains=search) | 
            Q(chat_id__icontains=search)
        )
    
    if status == 'active':
        groups = groups.filter(active=True)
    elif status == 'inactive':
        groups = groups.filter(active=False)
    
    # Paginação
    paginator = Paginator(groups, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'app_marketplace/groups_list.html', context)


@login_required
def group_detail(request, group_id):
    """Detalhes de um grupo WhatsApp específico"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito a Personal Shoppers ou Keepers.")
        return redirect('home')
    
    # VERIFICAR SE O GRUPO PERTENCE AO USUÁRIO MASTER
    group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
    
    # Participantes
    participants = group.participants.all().order_by('-joined_at')
    
    # Mensagens recentes
    recent_messages = group.messages.all().order_by('-timestamp')[:20]
    
    # Produtos do grupo
    products = group.products.all().order_by('-created_at')
    
    # Pedidos do grupo
    orders = group.orders.all().order_by('-created_at')
    
    # Estatísticas do grupo
    stats = {
        'participant_count': participants.count(),
        'message_count': group.messages.count(),
        'product_count': products.count(),
        'order_count': orders.count(),
        'total_revenue': orders.filter(
            status__in=['paid', 'purchased', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
    }
    
    context = {
        'group': group,
        'participants': participants,
        'recent_messages': recent_messages,
        'products': products[:10],  # Últimos 10 produtos
        'orders': orders[:10],      # Últimos 10 pedidos
        'stats': stats,
    }
    
    return render(request, 'app_marketplace/group_detail.html', context)


# ============================================================================
# GERENCIAMENTO DE GRUPOS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def create_group(request):
    """Criar novo grupo WhatsApp"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        data = json.loads(request.body)
        chat_id = data.get('chat_id')
        name = data.get('name')
        
        if not chat_id or not name:
            return JsonResponse({'error': 'Chat ID e nome são obrigatórios'}, status=400)
        
        # Verificar se já existe
        if WhatsappGroup.objects.filter(chat_id=chat_id).exists():
            return JsonResponse({'error': 'Grupo já cadastrado'}, status=400)
        
        # Criar grupo - VINCULAR AO USUÁRIO MASTER
        group = WhatsappGroup.objects.create(
            chat_id=chat_id,
            name=name,
            owner=request.user,  # Usuário master
            shopper=request.user.personalshopper if request.user.is_shopper else None,
            address_keeper=request.user.address_keeper if request.user.is_address_keeper else None
        )
        
        return JsonResponse({
            'success': True,
            'group': {
                'id': group.id,
                'name': group.name,
                'chat_id': group.chat_id,
                'created_at': group.created_at.isoformat(),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_group(request, group_id):
    """Atualizar configurações do grupo"""
    if not request.user.is_shopper:
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, shopper=request.user.personalshopper)
        data = json.loads(request.body)
        
        # Atualizar campos
        if 'name' in data:
            group.name = data['name']
        if 'active' in data:
            group.active = data['active']
        if 'auto_approve_orders' in data:
            group.auto_approve_orders = data['auto_approve_orders']
        if 'send_notifications' in data:
            group.send_notifications = data['send_notifications']
        if 'max_participants' in data:
            group.max_participants = data['max_participants']
        
        group.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_participant(request, group_id):
    """Adicionar participante ao grupo"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        # Verificar se o grupo pertence ao usuário (owner)
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        data = json.loads(request.body)
        
        phone = data.get('phone')
        name = data.get('name', '')
        
        if not phone:
            return JsonResponse({'error': 'Telefone é obrigatório'}, status=400)
        
        # Limpar e formatar telefone
        phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not phone.startswith('+'):
            # Se não começar com +, assumir que é brasileiro
            if phone.startswith('55'):
                phone = '+' + phone
            elif phone.startswith('0'):
                phone = '+55' + phone[1:]
            else:
                phone = '+55' + phone
        
        # Verificar se já existe
        if WhatsappParticipant.objects.filter(group=group, phone=phone).exists():
            return JsonResponse({'error': 'Participante já cadastrado neste grupo'}, status=400)
        
        # Tentar vincular com cliente existente pelo telefone
        cliente = None
        try:
            # Buscar cliente pelo telefone
            cliente = Cliente.objects.filter(
                telefone__icontains=phone.replace('+', '')
            ).first()
        except:
            pass
        
        # Criar participante
        participant = WhatsappParticipant.objects.create(
            group=group,
            phone=phone,
            name=name or phone,
            cliente=cliente
        )
        
        return JsonResponse({
            'success': True,
            'participant': {
                'id': participant.id,
                'name': participant.name,
                'phone': participant.phone,
                'joined_at': participant.joined_at.isoformat(),
                'is_cliente': participant.cliente is not None
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# GERENCIAMENTO DE PRODUTOS
# ============================================================================

@login_required
def products_list(request, group_id):
    """Lista produtos de um grupo"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    group = get_object_or_404(WhatsappGroup, id=group_id, shopper=request.user.personalshopper)
    products = group.products.all().order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    available = request.GET.get('available', '')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(brand__icontains=search)
        )
    
    if category:
        products = products.filter(category=category)
    
    if available == 'true':
        products = products.filter(is_available=True)
    elif available == 'false':
        products = products.filter(is_available=False)
    
    # Paginação
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorias disponíveis
    categories = products.values_list('category', flat=True).distinct().exclude(category='')
    
    context = {
        'group': group,
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'available': available,
        'categories': categories,
    }
    
    return render(request, 'app_marketplace/products_list.html', context)


@login_required
@require_http_methods(["POST"])
def create_product(request, group_id):
    """Criar produto no grupo"""
    if not request.user.is_shopper:
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, shopper=request.user.personalshopper)
        data = json.loads(request.body)
        
        # Dados obrigatórios
        name = data.get('name')
        if not name:
            return JsonResponse({'error': 'Nome do produto é obrigatório'}, status=400)
        
        # Criar produto
        product = WhatsappProduct.objects.create(
            group=group,
            name=name,
            description=data.get('description', ''),
            price=Decimal(data.get('price', 0)) if data.get('price') else None,
            currency=data.get('currency', 'USD'),
            brand=data.get('brand', ''),
            category=data.get('category', ''),
            image_urls=data.get('image_urls', []),
            is_available=data.get('is_available', True),
            is_featured=data.get('is_featured', False),
            posted_by=group.participants.first()  # Usar primeiro participante como exemplo
        )
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': str(product.price) if product.price else None,
                'currency': product.currency,
                'brand': product.brand,
                'category': product.category,
                'is_available': product.is_available,
                'created_at': product.created_at.isoformat(),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# GERENCIAMENTO DE PEDIDOS
# ============================================================================

@login_required
def orders_list(request, group_id):
    """Lista pedidos de um grupo"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    group = get_object_or_404(WhatsappGroup, id=group_id, shopper=request.user.personalshopper)
    orders = group.orders.all().order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if status:
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(customer__phone__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'group': group,
        'page_obj': page_obj,
        'status': status,
        'search': search,
        'status_choices': WhatsappOrder.STATUS_CHOICES,
    }
    
    return render(request, 'app_marketplace/orders_list.html', context)


@login_required
@require_http_methods(["POST"])
def update_order_status(request, order_id):
    """Atualizar status do pedido"""
    if not request.user.is_shopper:
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        order = get_object_or_404(
            WhatsappOrder, 
            id=order_id, 
            group__shopper=request.user.personalshopper
        )
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if not new_status:
            return JsonResponse({'error': 'Status é obrigatório'}, status=400)
        
        if new_status not in [choice[0] for choice in WhatsappOrder.STATUS_CHOICES]:
            return JsonResponse({'error': 'Status inválido'}, status=400)
        
        # Atualizar status
        old_status = order.status
        order.status = new_status
        
        # Atualizar timestamps específicos
        if new_status == 'confirmed' and old_status == 'pending':
            order.confirmed_at = timezone.now()
        elif new_status == 'paid' and old_status in ['pending', 'confirmed']:
            order.paid_at = timezone.now()
        
        order.save()
        
        # Enviar notificação para o grupo (se habilitado)
        if order.group.send_notifications:
            status_text = dict(WhatsappOrder.STATUS_CHOICES)[new_status]
            message = f"📦 *Pedido {order.order_number}*\n\nStatus atualizado: *{status_text}*"
            send_message(order.group.chat_id, message)
        
        return JsonResponse({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'updated_at': order.updated_at.isoformat(),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# ENVIO DE MENSAGENS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def send_group_message(request, group_id):
    """Enviar mensagem para o grupo"""
    if not request.user.is_shopper:
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, shopper=request.user.personalshopper)
        data = json.loads(request.body)
        
        message = data.get('message')
        if not message:
            return JsonResponse({'error': 'Mensagem é obrigatória'}, status=400)
        
        # Enviar mensagem
        result = send_message(group.chat_id, message)
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=500)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# ESTATÍSTICAS E RELATÓRIOS
# ============================================================================

@login_required
def whatsapp_analytics(request):
    """Analytics dos grupos WhatsApp"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    shopper = request.user.personalshopper
    
    # Período (padrão: últimos 30 dias)
    from datetime import datetime, timedelta
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Grupos ativos
    groups = WhatsappGroup.objects.filter(shopper=shopper, active=True)
    
    # Estatísticas gerais
    total_participants = WhatsappParticipant.objects.filter(group__shopper=shopper).count()
    total_messages = WhatsappMessage.objects.filter(
        group__shopper=shopper,
        timestamp__gte=start_date
    ).count()
    total_orders = WhatsappOrder.objects.filter(
        group__shopper=shopper,
        created_at__gte=start_date
    ).count()
    
    # Receita
    revenue = WhatsappOrder.objects.filter(
        group__shopper=shopper,
        status__in=['paid', 'purchased', 'shipped', 'delivered'],
        created_at__gte=start_date
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Produtos mais vendidos
    popular_products = WhatsappProduct.objects.filter(
        group__shopper=shopper
    ).annotate(
        order_count=Count('group__orders')
    ).order_by('-order_count')[:10]
    
    # Grupos com mais atividade
    active_groups = groups.annotate(
        message_count=Count('messages'),
        order_count=Count('orders')
    ).order_by('-message_count')[:5]
    
    context = {
        'shopper': shopper,
        'start_date': start_date,
        'end_date': end_date,
        'total_participants': total_participants,
        'total_messages': total_messages,
        'total_orders': total_orders,
        'revenue': revenue,
        'popular_products': popular_products,
        'active_groups': active_groups,
    }
    
    return render(request, 'app_marketplace/whatsapp_analytics.html', context)
