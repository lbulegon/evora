"""
Dashboard Específico para Personal Shopper - ÉVORA Connect
Interface completa para gerenciar grupos, produtos e vendas
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
import requests
from decimal import Decimal

from .models import (
    PersonalShopper, WhatsappGroup, WhatsappParticipant, 
    WhatsappMessage, WhatsappProduct, WhatsappOrder,
    Cliente, Produto, Categoria, Estabelecimento
)
from .whatsapp_views import send_message, send_reaction


# ============================================================================
# DASHBOARD PRINCIPAL DO SHOPPER
# ============================================================================

@login_required
def shopper_dashboard(request):
    """Dashboard principal do Personal Shopper"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    shopper = request.user.personalshopper
    
    # Período para análise (últimos 30 dias)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Estatísticas gerais
    groups = WhatsappGroup.objects.filter(owner=request.user)
    total_groups = groups.count()
    active_groups = groups.filter(active=True).count()
    
    # Participantes
    total_participants = WhatsappParticipant.objects.filter(group__owner=request.user).count()
    new_participants = WhatsappParticipant.objects.filter(
        group__owner=request.user,
        joined_at__gte=start_date
    ).count()
    
    # Produtos
    total_products = WhatsappProduct.objects.filter(group__owner=request.user).count()
    available_products = WhatsappProduct.objects.filter(
        group__owner=request.user,
        is_available=True
    ).count()
    featured_products = WhatsappProduct.objects.filter(
        group__owner=request.user,
        is_featured=True
    ).count()
    
    # Pedidos e vendas
    orders = WhatsappOrder.objects.filter(group__owner=request.user)
    total_orders = orders.count()
    
    # Vendas por status
    pending_orders = orders.filter(status='pending').count()
    paid_orders = orders.filter(status='paid').count()
    delivered_orders = orders.filter(status='delivered').count()
    
    # Receita
    total_revenue = orders.filter(
        status__in=['paid', 'purchased', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    monthly_revenue = orders.filter(
        status__in=['paid', 'purchased', 'shipped', 'delivered'],
        created_at__gte=start_date
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Grupos com mais atividade
    active_groups_data = groups.annotate(
        message_count=Count('messages'),
        order_count=Count('orders')
    ).order_by('-message_count')[:5]
    
    # Produtos mais vendidos
    popular_products = WhatsappProduct.objects.filter(
        group__owner=request.user
    ).annotate(
        order_count=Count('group__orders')
    ).order_by('-order_count')[:5]
    
    # Pedidos recentes
    recent_orders = orders.order_by('-created_at')[:10]
    
    # Mensagens recentes
    recent_messages = WhatsappMessage.objects.filter(
        group__owner=request.user
    ).order_by('-timestamp')[:10]
    
    # Crescimento mensal
    monthly_growth = []
    for i in range(6):  # Últimos 6 meses
        month_start = end_date - timedelta(days=30*(i+1))
        month_end = end_date - timedelta(days=30*i)
        
        month_orders = orders.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        month_revenue = orders.filter(
            created_at__gte=month_start,
            created_at__lt=month_end,
            status__in=['paid', 'purchased', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        monthly_growth.append({
            'month': month_start.strftime('%b'),
            'orders': month_orders,
            'revenue': float(month_revenue)
        })
    
    monthly_growth.reverse()  # Ordem cronológica
    
    context = {
        'shopper': shopper,
        'total_groups': total_groups,
        'active_groups': active_groups,
        'total_participants': total_participants,
        'new_participants': new_participants,
        'total_products': total_products,
        'available_products': available_products,
        'featured_products': featured_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'paid_orders': paid_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'active_groups_data': active_groups_data,
        'popular_products': popular_products,
        'recent_orders': recent_orders,
        'recent_messages': recent_messages,
        'monthly_growth': monthly_growth,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'app_marketplace/shopper_dashboard.html', context)


# ============================================================================
# GERENCIAMENTO DE GRUPOS
# ============================================================================

@login_required
def shopper_groups(request):
    """Lista e gerencia grupos do shopper"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    groups = WhatsappGroup.objects.filter(owner=request.user).order_by('-last_activity')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'activity')
    
    if search:
        groups = groups.filter(
            Q(name__icontains=search) | 
            Q(chat_id__icontains=search)
        )
    
    if status == 'active':
        groups = groups.filter(active=True)
    elif status == 'inactive':
        groups = groups.filter(active=False)
    
    # Ordenação
    if sort_by == 'name':
        groups = groups.order_by('name')
    elif sort_by == 'participants':
        # Ordenar por número de participantes usando a propriedade
        groups = list(groups)
        groups.sort(key=lambda g: g.participant_count, reverse=True)
    elif sort_by == 'orders':
        groups = groups.annotate(order_count=Count('orders')).order_by('-order_count')
    elif sort_by == 'revenue':
        groups = groups.annotate(
            revenue=Sum('orders__total_amount', filter=Q(orders__status__in=['paid', 'purchased', 'shipped', 'delivered']))
        ).order_by('-revenue')
    else:  # activity
        groups = groups.order_by('-last_activity')
    
    # Paginação
    paginator = Paginator(groups, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'sort_by': sort_by,
    }
    
    return render(request, 'app_marketplace/shopper_groups.html', context)


@login_required
def shopper_group_detail(request, group_id):
    """Detalhes completos de um grupo"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
    
    # Estatísticas do grupo
    participants = group.participants.all().order_by('-joined_at')
    messages = group.messages.all().order_by('-timestamp')
    products = group.products.all().order_by('-created_at')
    orders = group.orders.all().order_by('-created_at')
    
    # Métricas do grupo
    group_stats = {
        'participant_count': participants.count(),
        'message_count': messages.count(),
        'product_count': products.count(),
        'order_count': orders.count(),
        'total_revenue': orders.filter(
            status__in=['paid', 'purchased', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
        'avg_order_value': orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0'),
        'conversion_rate': (orders.count() / max(participants.count(), 1)) * 100,
    }
    
    # Participantes recentes
    recent_participants = participants[:5]
    
    # Mensagens recentes
    recent_messages = messages[:10]
    
    # Produtos em destaque
    featured_products = products.filter(is_featured=True)[:5]
    
    # Pedidos por status
    orders_by_status = {}
    for status, label in WhatsappOrder.STATUS_CHOICES:
        orders_by_status[status] = {
            'label': label,
            'count': orders.filter(status=status).count()
        }
    
    # Atividade por dia (últimos 7 dias)
    daily_activity = []
    for i in range(7):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_messages = messages.filter(timestamp__gte=day_start, timestamp__lte=day_end).count()
        day_orders = orders.filter(created_at__gte=day_start, created_at__lte=day_end).count()
        
        daily_activity.append({
            'date': day.strftime('%d/%m'),
            'messages': day_messages,
            'orders': day_orders
        })
    
    daily_activity.reverse()
    
    context = {
        'group': group,
        'participants': participants,
        'messages': messages,
        'products': products,
        'orders': orders,
        'group_stats': group_stats,
        'recent_participants': recent_participants,
        'recent_messages': recent_messages,
        'featured_products': featured_products,
        'orders_by_status': orders_by_status,
        'daily_activity': daily_activity,
    }
    
    return render(request, 'app_marketplace/shopper_group_detail.html', context)


# ============================================================================
# GERENCIAMENTO DE PRODUTOS
# ============================================================================

@login_required
def shopper_products(request):
    """Catálogo de produtos do shopper"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    products = WhatsappProduct.objects.filter(group__owner=request.user).order_by('-created_at')
    
    # Estabelecimentos disponíveis (base geral)
    estabelecimentos = Estabelecimento.objects.filter(ativo=True).order_by('nome')
    
    # Filtros
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    brand = request.GET.get('brand', '')
    availability = request.GET.get('availability', '')
    featured = request.GET.get('featured', '')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(brand__icontains=search)
        )
    
    if category:
        products = products.filter(category=category)
    
    if brand:
        products = products.filter(brand=brand)
    
    if availability == 'available':
        products = products.filter(is_available=True)
    elif availability == 'unavailable':
        products = products.filter(is_available=False)
    
    if featured == 'yes':
        products = products.filter(is_featured=True)
    elif featured == 'no':
        products = products.filter(is_featured=False)
    
    # Estatísticas
    total_products = products.count()
    available_products = products.filter(is_available=True).count()
    featured_products = products.filter(is_featured=True).count()
    
    # Categorias e marcas disponíveis
    categories = products.values_list('category', flat=True).distinct().exclude(category='')
    brands = products.values_list('brand', flat=True).distinct().exclude(brand='')
    
    # Paginação
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'brand': brand,
        'availability': availability,
        'featured': featured,
        'categories': categories,
        'brands': brands,
        'total_products': total_products,
        'available_products': available_products,
        'featured_products': featured_products,
        'estabelecimentos': estabelecimentos,
    }
    
    return render(request, 'app_marketplace/shopper_products.html', context)


# ============================================================================
# GERENCIAMENTO DE PEDIDOS
# ============================================================================

@login_required
def shopper_orders(request):
    """Lista de pedidos do shopper"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    orders = WhatsappOrder.objects.filter(group__owner=request.user).order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    payment_status = request.GET.get('payment_status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(customer__phone__icontains=search)
        )
    
    if status:
        orders = orders.filter(status=status)
    
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    
    if date_from:
        orders = orders.filter(created_at__gte=date_from)
    
    if date_to:
        orders = orders.filter(created_at__lte=date_to)
    
    # Estatísticas
    total_orders = orders.count()
    total_revenue = orders.filter(
        status__in=['paid', 'purchased', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Pedidos por status
    orders_by_status = {}
    for status_code, status_label in WhatsappOrder.STATUS_CHOICES:
        orders_by_status[status_code] = {
            'label': status_label,
            'count': orders.filter(status=status_code).count()
        }
    
    # Paginação
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'payment_status': payment_status,
        'date_from': date_from,
        'date_to': date_to,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'orders_by_status': orders_by_status,
        'status_choices': WhatsappOrder.STATUS_CHOICES,
    }
    
    return render(request, 'app_marketplace/shopper_orders.html', context)


# ============================================================================
# ANALYTICS E RELATÓRIOS
# ============================================================================

@login_required
def shopper_analytics(request):
    """Analytics detalhados do shopper"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    # Período (padrão: últimos 90 dias)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)
    
    # Ajustar período se especificado
    if request.GET.get('period'):
        days = int(request.GET.get('period', 90))
        start_date = end_date - timedelta(days=days)
    
    # Dados do período
    orders = WhatsappOrder.objects.filter(
        group__owner=request.user,
        created_at__gte=start_date
    )
    
    # Métricas principais
    total_orders = orders.count()
    total_revenue = orders.filter(
        status__in=['paid', 'purchased', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    avg_order_value = orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0')
    
    # Participantes
    total_participants = WhatsappParticipant.objects.filter(
        group__owner=request.user,
        joined_at__gte=start_date
    ).count()
    
    # Produtos
    total_products = WhatsappProduct.objects.filter(
        group__owner=request.user,
        created_at__gte=start_date
    ).count()
    
    # Vendas por status
    sales_by_status = {}
    for status, label in WhatsappOrder.STATUS_CHOICES:
        count = orders.filter(status=status).count()
        revenue = orders.filter(
            status=status,
            status__in=['paid', 'purchased', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        sales_by_status[status] = {
            'label': label,
            'count': count,
            'revenue': float(revenue)
        }
    
    # Vendas por grupo
    sales_by_group = WhatsappGroup.objects.filter(owner=request.user).annotate(
        order_count=Count('orders', filter=Q(orders__created_at__gte=start_date)),
        revenue=Sum('orders__total_amount', filter=Q(
            orders__created_at__gte=start_date,
            orders__status__in=['paid', 'purchased', 'shipped', 'delivered']
        ))
    ).order_by('-revenue')
    
    # Produtos mais vendidos
    popular_products = WhatsappProduct.objects.filter(
        group__owner=request.user
    ).annotate(
        order_count=Count('group__orders', filter=Q(group__orders__created_at__gte=start_date))
    ).order_by('-order_count')[:10]
    
    # Crescimento diário
    daily_sales = []
    for i in range(30):  # Últimos 30 dias
        day = end_date - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_orders = orders.filter(created_at__gte=day_start, created_at__lte=day_end).count()
        day_revenue = orders.filter(
            created_at__gte=day_start,
            created_at__lte=day_end,
            status__in=['paid', 'purchased', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'orders': day_orders,
            'revenue': float(day_revenue)
        })
    
    daily_sales.reverse()
    
    # Horários de maior atividade
    hourly_activity = []
    for hour in range(24):
        hour_orders = orders.filter(created_at__hour=hour).count()
        hourly_activity.append({
            'hour': f"{hour:02d}:00",
            'orders': hour_orders
        })
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'total_participants': total_participants,
        'total_products': total_products,
        'sales_by_status': sales_by_status,
        'sales_by_group': sales_by_group,
        'popular_products': popular_products,
        'daily_sales': daily_sales,
        'hourly_activity': hourly_activity,
    }
    
    return render(request, 'app_marketplace/shopper_analytics.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_product(request):
    """Criar novo produto para o shopper"""
    if not request.user.is_shopper:
        return JsonResponse({'error': 'Acesso restrito a Personal Shoppers'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validar dados obrigatórios
        name = data.get('name')
        if not name:
            return JsonResponse({'error': 'Nome do produto é obrigatório'}, status=400)
        
        # Buscar grupo (opcional)
        group_id = data.get('group_id')
        group = None
        if group_id:
            group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        
        # Buscar estabelecimento
        estabelecimento_id = data.get('estabelecimento_id')
        estabelecimento = None
        if estabelecimento_id:
            estabelecimento = get_object_or_404(Estabelecimento, id=estabelecimento_id)
        
        # Criar produto
        product = WhatsappProduct.objects.create(
            name=name,
            description=data.get('description', ''),
            price=Decimal(data.get('price', 0)) if data.get('price') else None,
            currency=data.get('currency', 'USD'),
            brand=data.get('brand', ''),
            category=data.get('category', ''),
            group=group,
            estabelecimento=estabelecimento,
            localizacao_especifica=data.get('localizacao_especifica', ''),
            codigo_barras=data.get('codigo_barras', ''),
            sku_loja=data.get('sku_loja', ''),
            is_featured=data.get('is_featured', False),
            is_available=True
        )
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': str(product.price) if product.price else None,
                'brand': product.brand,
                'estabelecimento': product.estabelecimento.nome if product.estabelecimento else None,
                'localizacao': product.localizacao_especifica
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erro ao criar produto: {str(e)}'}, status=500)
