"""
Dashboard do Cliente - ÉVORA Connect
Interface completa para clientes acompanharem pedidos, pacotes e compras
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from decimal import Decimal

from .models import (
    Cliente, Pedido, Pacote, PedidoPacote, EnderecoEntrega,
    WhatsappOrder, PagamentoIntent, MovimentoPacote, FotoPacote,
    WhatsappGroup, WhatsappProduct, WhatsappParticipant
)
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal


# ============================================================================
# DASHBOARD PRINCIPAL DO CLIENTE
# ============================================================================

@login_required
def client_dashboard(request):
    """Dashboard principal do cliente"""
    if not request.user.is_cliente:
        messages.error(request, "Acesso restrito a clientes.")
        return redirect('home')
    
    try:
        cliente = request.user.cliente
    except (Cliente.DoesNotExist, AttributeError):
        messages.error(request, "Perfil de cliente não encontrado.")
        return redirect('home')
    
    # ========== PEDIDOS ==========
    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-criado_em')
    total_pedidos = pedidos.count()
    
    # Pedidos por status
    pedidos_pendentes = pedidos.filter(status='pendente').count()
    pedidos_pagos = pedidos.filter(status='pago').count()
    pedidos_enviados = pedidos.filter(status='enviado').count()
    pedidos_entregues = pedidos.filter(status='entregue').count()
    
    # Total gasto
    total_gasto = pedidos.filter(
        status__in=['pago', 'enviado', 'entregue']
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
    
    # ========== PEDIDOS WHATSAPP ==========
    whatsapp_orders = WhatsappOrder.objects.filter(cliente=cliente).order_by('-created_at')
    total_whatsapp_orders = whatsapp_orders.count()
    
    whatsapp_gasto = whatsapp_orders.filter(
        status__in=['paid', 'purchased', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Total gasto geral (pedidos + whatsapp)
    total_gasto_geral = total_gasto + whatsapp_gasto
    
    # ========== PACOTES ==========
    # Pacotes relacionados aos pedidos do cliente
    pedido_ids = pedidos.values_list('id', flat=True)
    pacotes_ids = PedidoPacote.objects.filter(
        pedido_id__in=pedido_ids
    ).values_list('pacote_id', flat=True)
    
    pacotes = Pacote.objects.filter(id__in=pacotes_ids).order_by('-criado_em')
    total_pacotes = pacotes.count()
    
    pacotes_em_guarda = pacotes.filter(status='em_guarda').count()
    pacotes_enviados = pacotes.filter(status='enviado').count()
    pacotes_entregues = pacotes.filter(status='entregue').count()
    
    # ========== ENDEREÇOS ==========
    enderecos = EnderecoEntrega.objects.filter(cliente=cliente).order_by('-padrao', 'apelido')
    total_enderecos = enderecos.count()
    
    # ========== PAGAMENTOS PENDENTES ==========
    pagamentos_pendentes = PagamentoIntent.objects.filter(
        pedido__cliente=cliente,
        status__in=['criado', 'pendente']
    ).order_by('-criado_em')
    
    # ========== PEDIDOS RECENTES ==========
    pedidos_recentes = pedidos[:5]
    whatsapp_orders_recentes = whatsapp_orders[:5]
    pacotes_recentes = pacotes[:5]
    
    # ========== TIMELINE DE ATIVIDADES ==========
    # Combinar pedidos e pacotes recentes para timeline
    atividades = []
    
    for pedido in pedidos[:10]:
        atividades.append({
            'tipo': 'pedido',
            'objeto': pedido,
            'data': pedido.criado_em,
            'titulo': f"Pedido #{pedido.id}",
            'status': pedido.get_status_display(),
            'valor': pedido.valor_total
        })
    
    for pacote in pacotes[:10]:
        atividades.append({
            'tipo': 'pacote',
            'objeto': pacote,
            'data': pacote.criado_em,
            'titulo': f"Pacote {pacote.codigo_publico}",
            'status': pacote.get_status_display()
        })
    
    # Ordenar por data
    atividades.sort(key=lambda x: x['data'], reverse=True)
    atividades = atividades[:10]
    
    context = {
        'cliente': cliente,
        
        # Pedidos
        'total_pedidos': total_pedidos,
        'pedidos_pendentes': pedidos_pendentes,
        'pedidos_pagos': pedidos_pagos,
        'pedidos_enviados': pedidos_enviados,
        'pedidos_entregues': pedidos_entregues,
        'total_gasto': total_gasto,
        'total_gasto_geral': total_gasto_geral,
        'pedidos_recentes': pedidos_recentes,
        
        # WhatsApp Orders
        'total_whatsapp_orders': total_whatsapp_orders,
        'whatsapp_gasto': whatsapp_gasto,
        'whatsapp_orders_recentes': whatsapp_orders_recentes,
        
        # Pacotes
        'total_pacotes': total_pacotes,
        'pacotes_em_guarda': pacotes_em_guarda,
        'pacotes_enviados': pacotes_enviados,
        'pacotes_entregues': pacotes_entregues,
        'pacotes_recentes': pacotes_recentes,
        
        # Endereços
        'enderecos': enderecos,
        'total_enderecos': total_enderecos,
        
        # Pagamentos
        'pagamentos_pendentes': pagamentos_pendentes,
        
        # Timeline
        'atividades': atividades,
    }
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro no client_dashboard: {str(e)}", exc_info=True)
        messages.error(request, f"Erro ao carregar dashboard: {str(e)}")
        # Retornar contexto mínimo em caso de erro
        context = {
            'cliente': cliente,
            'total_pedidos': 0,
            'pedidos_pendentes': 0,
            'pedidos_pagos': 0,
            'pedidos_enviados': 0,
            'pedidos_entregues': 0,
            'total_gasto': Decimal('0'),
            'total_gasto_geral': Decimal('0'),
            'pedidos_recentes': [],
            'total_whatsapp_orders': 0,
            'whatsapp_gasto': Decimal('0'),
            'whatsapp_orders_recentes': [],
            'total_pacotes': 0,
            'pacotes_em_guarda': 0,
            'pacotes_enviados': 0,
            'pacotes_entregues': 0,
            'pacotes_recentes': [],
            'enderecos': [],
            'total_enderecos': 0,
            'pagamentos_pendentes': [],
            'atividades': [],
        }
    
    return render(request, 'app_marketplace/client_dashboard.html', context)


# ============================================================================
# DETALHES DE PEDIDO
# ============================================================================

@login_required
def client_order_detail(request, pedido_id):
    """Detalhes de um pedido específico"""
    if not request.user.is_cliente:
        messages.error(request, "Acesso restrito a clientes.")
        return redirect('home')
    
    cliente = request.user.cliente
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    
    # Itens do pedido
    itens = pedido.itens.all()
    
    # Pagamentos
    pagamentos = pedido.pagamentos.all().order_by('-criado_em')
    
    # Pacotes relacionados
    pacotes_relacionados = PedidoPacote.objects.filter(pedido=pedido)
    
    context = {
        'pedido': pedido,
        'itens': itens,
        'pagamentos': pagamentos,
        'pacotes_relacionados': pacotes_relacionados,
    }
    
    return render(request, 'app_marketplace/client_order_detail.html', context)


# ============================================================================
# DETALHES DE PACOTE
# ============================================================================

@login_required
def client_package_detail(request, pacote_id):
    """Detalhes de um pacote específico"""
    if not request.user.is_cliente:
        messages.error(request, "Acesso restrito a clientes.")
        return redirect('home')
    
    cliente = request.user.cliente
    
    # Verificar se o pacote está relacionado a algum pedido do cliente
    pedido_ids = Pedido.objects.filter(cliente=cliente).values_list('id', flat=True)
    pacote_ids = PedidoPacote.objects.filter(
        pedido_id__in=pedido_ids
    ).values_list('pacote_id', flat=True)
    
    if pacote_id not in pacote_ids:
        messages.error(request, "Pacote não encontrado ou não pertence a você.")
        return redirect('client_dashboard')
    
    pacote = get_object_or_404(Pacote, id=pacote_id)
    
    # Movimentos do pacote
    movimentos = MovimentoPacote.objects.filter(pacote=pacote).order_by('-criado_em')
    
    # Fotos do pacote
    fotos = FotoPacote.objects.filter(pacote=pacote).order_by('-criado_em')
    
    # Pedidos relacionados
    pedidos_relacionados = PedidoPacote.objects.filter(pacote=pacote)
    
    context = {
        'pacote': pacote,
        'movimentos': movimentos,
        'fotos': fotos,
        'pedidos_relacionados': pedidos_relacionados,
    }
    
    return render(request, 'app_marketplace/client_package_detail.html', context)


# ============================================================================
# LISTA DE PEDIDOS
# ============================================================================

@login_required
def client_orders(request):
    """Lista completa de pedidos do cliente"""
    if not request.user.is_cliente:
        messages.error(request, "Acesso restrito a clientes.")
        return redirect('home')
    
    cliente = request.user.cliente
    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-criado_em')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    if search:
        pedidos = pedidos.filter(
            Q(id__icontains=search) |
            Q(codigo_rastreamento__icontains=search)
        )
    
    if status:
        pedidos = pedidos.filter(status=status)
    
    # Paginação
    paginator = Paginator(pedidos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'status_choices': Pedido.Status.choices,
    }
    
    return render(request, 'app_marketplace/client_orders.html', context)


# ============================================================================
# LISTA DE PACOTES
# ============================================================================

@login_required
def client_products(request):
    """Lista de produtos disponíveis para o cliente (MVP)"""
    if not request.user.is_cliente:
        messages.error(request, "Acesso restrito a clientes.")
        return redirect('home')
    
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "Perfil de cliente não encontrado.")
        return redirect('home')
    
    # Buscar grupos onde o cliente é participante
    participant_groups = WhatsappParticipant.objects.filter(
        cliente=cliente
    ).values_list('group_id', flat=True)
    
    # Buscar produtos dos grupos
    products = WhatsappProduct.objects.filter(
        group_id__in=participant_groups,
        is_available=True
    ).order_by('-is_featured', '-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    group_id = request.GET.get('group', '')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(brand__icontains=search)
        )
    
    if category:
        products = products.filter(category=category)
    
    if group_id:
        products = products.filter(group_id=group_id)
    
    # Grupos disponíveis
    groups = WhatsappGroup.objects.filter(id__in=participant_groups).order_by('name')
    
    # Paginação
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorias disponíveis
    categories = products.values_list('category', flat=True).distinct().exclude(category='')
    
    context = {
        'page_obj': page_obj,
        'groups': groups,
        'search': search,
        'category': category,
        'group_id': group_id,
        'categories': categories,
    }
    
    return render(request, 'app_marketplace/client_products.html', context)


@login_required
@require_http_methods(["POST"])
def create_whatsapp_order(request):
    """Criar pedido via WhatsApp (MVP)"""
    if not request.user.is_cliente:
        return JsonResponse({'error': 'Acesso restrito a clientes'}, status=403)
    
    try:
        cliente = request.user.cliente
        data = json.loads(request.body)
        
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return JsonResponse({'error': 'Produto é obrigatório'}, status=400)
        
        product = get_object_or_404(WhatsappProduct, id=product_id, is_available=True)
        
        # Buscar participante do cliente no grupo
        participant = WhatsappParticipant.objects.filter(
            group=product.group,
            cliente=cliente
        ).first()
        
        if not participant:
            return JsonResponse({'error': 'Cliente não é participante deste grupo'}, status=403)
        
        # Calcular total
        total = (product.price or Decimal('0')) * quantity
        
        # Criar pedido
        order = WhatsappOrder.objects.create(
            group=product.group,
            customer=participant,
            cliente=cliente,
            order_number=f"WH{timezone.now().strftime('%Y%m%d%H%M%S')}",
            status='pending',
            total_amount=total,
            currency=product.currency,
            products=[{
                'product_id': product.id,
                'name': product.name,
                'price': str(product.price) if product.price else '0',
                'quantity': quantity
            }],
            payment_status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'total_amount': str(order.total_amount),
                'currency': order.currency,
                'status': order.status,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def client_packages(request):
    """Lista completa de pacotes do cliente"""
    if not request.user.is_cliente:
        messages.error(request, "Acesso restrito a clientes.")
        return redirect('home')
    
    cliente = request.user.cliente
    
    # Buscar pacotes relacionados aos pedidos do cliente
    pedido_ids = Pedido.objects.filter(cliente=cliente).values_list('id', flat=True)
    pacote_ids = PedidoPacote.objects.filter(
        pedido_id__in=pedido_ids
    ).values_list('pacote_id', flat=True)
    
    pacotes = Pacote.objects.filter(id__in=pacote_ids).order_by('-criado_em')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    if search:
        pacotes = pacotes.filter(
            Q(codigo_publico__icontains=search) |
            Q(descricao__icontains=search)
        )
    
    if status:
        pacotes = pacotes.filter(status=status)
    
    # Paginação
    paginator = Paginator(pacotes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'status_choices': Pacote.Status.choices,
    }
    
    return render(request, 'app_marketplace/client_packages.html', context)

