"""
Dashboard de Administração - ÉVORA Connect
Interface completa para administradores visualizarem estatísticas do sistema
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Cliente, PersonalShopper, AddressKeeper, Pedido, Pacote,
    WhatsappGroup, WhatsappOrder, WhatsappProduct, WhatsappParticipant,
    PagamentoIntent, Evento, Produto, Categoria, Empresa
)


def is_admin(user):
    """Verifica se o usuário é administrador (superuser)"""
    return user.is_authenticated and user.is_superuser


# ============================================================================
# DASHBOARD PRINCIPAL DE ADMINISTRAÇÃO
# ============================================================================

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard principal do administrador"""
    
    # Período para análise (últimos 30 dias)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # ========== ESTATÍSTICAS DE USUÁRIOS ==========
    total_clientes = Cliente.objects.count()
    total_shoppers = PersonalShopper.objects.count()
    total_keepers = AddressKeeper.objects.count()
    total_usuarios = total_clientes + total_shoppers + total_keepers
    
    # Novos usuários no período
    novos_clientes = Cliente.objects.filter(criado_em__gte=start_date).count()
    novos_shoppers = PersonalShopper.objects.filter(criado_em__gte=start_date).count()
    novos_keepers = AddressKeeper.objects.filter(criado_em__gte=start_date).count()
    
    # ========== ESTATÍSTICAS DE PEDIDOS ==========
    pedidos = Pedido.objects.all()
    total_pedidos = pedidos.count()
    
    # Pedidos por status
    pedidos_pendentes = pedidos.filter(status='pendente').count()
    pedidos_pagos = pedidos.filter(status='pago').count()
    pedidos_enviados = pedidos.filter(status='enviado').count()
    pedidos_entregues = pedidos.filter(status='entregue').count()
    pedidos_cancelados = pedidos.filter(status='cancelado').count()
    
    # Receita de pedidos
    receita_total = pedidos.filter(
        status__in=['pago', 'enviado', 'entregue']
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
    
    receita_mensal = pedidos.filter(
        status__in=['pago', 'enviado', 'entregue'],
        criado_em__gte=start_date
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
    
    # ========== ESTATÍSTICAS DE PEDIDOS WHATSAPP ==========
    whatsapp_orders = WhatsappOrder.objects.all()
    total_whatsapp_orders = whatsapp_orders.count()
    
    whatsapp_receita = whatsapp_orders.filter(
        status__in=['paid', 'purchased', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    whatsapp_receita_mensal = whatsapp_orders.filter(
        status__in=['paid', 'purchased', 'shipped', 'delivered'],
        created_at__gte=start_date
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # ========== ESTATÍSTICAS DE PACOTES ==========
    pacotes = Pacote.objects.all()
    total_pacotes = pacotes.count()
    
    pacotes_em_guarda = pacotes.filter(status='em_guarda').count()
    pacotes_enviados = pacotes.filter(status='enviado').count()
    pacotes_entregues = pacotes.filter(status='entregue').count()
    
    # ========== ESTATÍSTICAS DE GRUPOS WHATSAPP ==========
    grupos = WhatsappGroup.objects.all()
    total_grupos = grupos.count()
    grupos_ativos = grupos.filter(active=True).count()
    total_participantes = WhatsappParticipant.objects.count()
    total_produtos_whatsapp = WhatsappProduct.objects.count()
    
    # ========== ESTATÍSTICAS DE PRODUTOS ==========
    produtos = Produto.objects.all()
    total_produtos = produtos.count()
    produtos_ativos = produtos.filter(ativo=True).count()
    total_categorias = Categoria.objects.count()
    total_empresas = Empresa.objects.count()
    
    # ========== ESTATÍSTICAS DE EVENTOS ==========
    eventos = Evento.objects.all()
    total_eventos = eventos.count()
    eventos_ativos = eventos.filter(status=Evento.Status.ATIVO).count()
    
    # ========== ATIVIDADES RECENTES ==========
    pedidos_recentes = pedidos.order_by('-criado_em')[:10]
    whatsapp_orders_recentes = whatsapp_orders.order_by('-created_at')[:10]
    pacotes_recentes = pacotes.order_by('-criado_em')[:10]
    
    # ========== CRESCIMENTO MENSAL ==========
    monthly_growth = []
    for i in range(6):  # Últimos 6 meses
        month_start = end_date - timedelta(days=30*(i+1))
        month_end = end_date - timedelta(days=30*i)
        
        month_pedidos = pedidos.filter(
            criado_em__gte=month_start,
            criado_em__lt=month_end
        ).count()
        
        month_receita = pedidos.filter(
            criado_em__gte=month_start,
            criado_em__lt=month_end,
            status__in=['pago', 'enviado', 'entregue']
        ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
        
        month_whatsapp_receita = whatsapp_orders.filter(
            created_at__gte=month_start,
            created_at__lt=month_end,
            status__in=['paid', 'purchased', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        monthly_growth.append({
            'month': month_start.strftime('%b/%Y'),
            'pedidos': month_pedidos,
            'receita': float(month_receita),
            'whatsapp_receita': float(month_whatsapp_receita),
            'total_receita': float(month_receita + month_whatsapp_receita)
        })
    
    monthly_growth.reverse()  # Ordem cronológica
    
    # ========== TOP PERFORMERS ==========
    # Top shoppers por receita
    top_shoppers = PersonalShopper.objects.annotate(
        total_receita=Sum('pacotes__pedidos_relacionados__pedido__valor_total',
                         filter=Q(pacotes__pedidos_relacionados__pedido__status__in=['pago', 'enviado', 'entregue']))
    ).order_by('-total_receita')[:5]
    
    # Top keepers por pacotes
    top_keepers = AddressKeeper.objects.annotate(
        total_pacotes=Count('pacotes')
    ).order_by('-total_pacotes')[:5]
    
    # Top clientes por pedidos
    top_clientes = Cliente.objects.annotate(
        total_pedidos=Count('pedidos'),
        total_gasto=Sum('pedidos__valor_total',
                       filter=Q(pedidos__status__in=['pago', 'enviado', 'entregue']))
    ).order_by('-total_gasto')[:5]
    
    context = {
        # Usuários
        'total_clientes': total_clientes,
        'total_shoppers': total_shoppers,
        'total_keepers': total_keepers,
        'total_usuarios': total_usuarios,
        'novos_clientes': novos_clientes,
        'novos_shoppers': novos_shoppers,
        'novos_keepers': novos_keepers,
        
        # Pedidos
        'total_pedidos': total_pedidos,
        'pedidos_pendentes': pedidos_pendentes,
        'pedidos_pagos': pedidos_pagos,
        'pedidos_enviados': pedidos_enviados,
        'pedidos_entregues': pedidos_entregues,
        'pedidos_cancelados': pedidos_cancelados,
        'receita_total': receita_total,
        'receita_mensal': receita_mensal,
        
        # WhatsApp
        'total_whatsapp_orders': total_whatsapp_orders,
        'whatsapp_receita': whatsapp_receita,
        'whatsapp_receita_mensal': whatsapp_receita_mensal,
        
        # Pacotes
        'total_pacotes': total_pacotes,
        'pacotes_em_guarda': pacotes_em_guarda,
        'pacotes_enviados': pacotes_enviados,
        'pacotes_entregues': pacotes_entregues,
        
        # Grupos WhatsApp
        'total_grupos': total_grupos,
        'grupos_ativos': grupos_ativos,
        'total_participantes': total_participantes,
        'total_produtos_whatsapp': total_produtos_whatsapp,
        
        # Produtos
        'total_produtos': total_produtos,
        'produtos_ativos': produtos_ativos,
        'total_categorias': total_categorias,
        'total_empresas': total_empresas,
        
        # Eventos
        'total_eventos': total_eventos,
        'eventos_ativos': eventos_ativos,
        
        # Atividades recentes
        'pedidos_recentes': pedidos_recentes,
        'whatsapp_orders_recentes': whatsapp_orders_recentes,
        'pacotes_recentes': pacotes_recentes,
        
        # Crescimento
        'monthly_growth': monthly_growth,
        
        # Top performers
        'top_shoppers': top_shoppers,
        'top_keepers': top_keepers,
        'top_clientes': top_clientes,
        
        # Período
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'app_marketplace/admin_dashboard.html', context)


