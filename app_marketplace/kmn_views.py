"""
Views KMN integradas ao frontend ÉVORA
Dashboard e interfaces para o sistema Keeper Mesh Network
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from .models import (
    Agente, Cliente, ClienteRelacao, Produto, EstoqueItem,
    Oferta, TrustlineKeeper, RoleStats, Pedido
)
from .services import KMNRoleEngine, KMNStatsService, CatalogoService


# ============================================================================
# DASHBOARD KMN PRINCIPAL
# ============================================================================

@login_required
def kmn_dashboard(request):
    """Dashboard principal KMN - adaptado ao perfil do usuário"""
    
    # Verificar se o usuário tem perfil de agente
    try:
        agente = request.user.agente
    except:
        # Se não tem agente, criar um baseado no perfil existente
        agente = criar_agente_automatico(request.user)
        if not agente:
            messages.error(request, "Você precisa ser um Personal Shopper ou Keeper para acessar o KMN.")
            return redirect('home')
    
    # Período para análise (últimos 30 dias)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Estatísticas gerais
    stats = {
        'total_clientes': ClienteRelacao.objects.filter(agente=agente, status='ativa').count(),
        'total_ofertas': Oferta.objects.filter(agente_ofertante=agente, ativo=True).count(),
        'total_estoque': EstoqueItem.objects.filter(agente=agente, ativo=True).count(),
        'total_trustlines': TrustlineKeeper.objects.filter(
            Q(agente_a=agente) | Q(agente_b=agente),
            status='ativa'
        ).count(),
    }
    
    # Scores do agente
    scores = KMNStatsService.calcular_score_agente(agente)
    
    # Clientes principais (top 5 por força de relação)
    clientes_principais = ClienteRelacao.objects.filter(
        agente=agente,
        status='ativa'
    ).order_by('-forca_relacao')[:5]
    
    # Ofertas recentes
    ofertas_recentes = Oferta.objects.filter(
        agente_ofertante=agente,
        ativo=True
    ).order_by('-criado_em')[:5]
    
    # Trustlines ativas
    trustlines_ativas = TrustlineKeeper.objects.filter(
        Q(agente_a=agente) | Q(agente_b=agente),
        status='ativa'
    ).order_by('-aceito_em')[:5]
    
    # Produtos mais ofertados
    produtos_populares = Produto.objects.filter(
        ofertas__agente_ofertante=agente,
        ofertas__ativo=True
    ).annotate(
        total_ofertas=Count('ofertas')
    ).order_by('-total_ofertas')[:5]
    
    context = {
        'agente': agente,
        'stats': stats,
        'scores': scores,
        'clientes_principais': clientes_principais,
        'ofertas_recentes': ofertas_recentes,
        'trustlines_ativas': trustlines_ativas,
        'produtos_populares': produtos_populares,
        'is_dual_role': agente.is_dual_role,
    }
    
    return render(request, 'app_marketplace/kmn_dashboard.html', context)


@login_required
def kmn_clientes(request):
    """Gestão de clientes KMN"""
    try:
        agente = request.user.agente
    except:
        messages.error(request, "Acesso restrito a agentes KMN.")
        return redirect('home')
    
    # Filtros
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Query base
    relacoes = ClienteRelacao.objects.filter(agente=agente)
    
    # Aplicar filtros
    if search:
        relacoes = relacoes.filter(
            Q(cliente__user__first_name__icontains=search) |
            Q(cliente__user__last_name__icontains=search) |
            Q(cliente__user__username__icontains=search)
        )
    
    if status_filter:
        relacoes = relacoes.filter(status=status_filter)
    
    # Ordenação
    relacoes = relacoes.order_by('-forca_relacao', '-ultimo_pedido')
    
    # Paginação
    paginator = Paginator(relacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'agente': agente,
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'status_choices': ClienteRelacao.StatusRelacao.choices,
    }
    
    return render(request, 'app_marketplace/kmn_clientes.html', context)


@login_required
def kmn_ofertas(request):
    """Gestão de ofertas KMN"""
    try:
        agente = request.user.agente
    except:
        messages.error(request, "Acesso restrito a agentes KMN.")
        return redirect('home')
    
    # Filtros
    search = request.GET.get('search', '')
    ativo_filter = request.GET.get('ativo', '')
    
    # Query base
    ofertas = Oferta.objects.filter(agente_ofertante=agente)
    
    # Aplicar filtros
    if search:
        ofertas = ofertas.filter(produto__nome__icontains=search)
    
    if ativo_filter:
        ofertas = ofertas.filter(ativo=ativo_filter.lower() == 'true')
    
    # Ordenação
    ofertas = ofertas.order_by('-criado_em')
    
    # Paginação
    paginator = Paginator(ofertas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Produtos disponíveis para criar ofertas
    produtos_disponiveis = Produto.objects.filter(ativo=True)
    
    context = {
        'agente': agente,
        'page_obj': page_obj,
        'search': search,
        'ativo_filter': ativo_filter,
        'produtos_disponiveis': produtos_disponiveis,
    }
    
    return render(request, 'app_marketplace/kmn_ofertas.html', context)


@login_required
def kmn_estoque(request):
    """Gestão de estoque KMN"""
    try:
        agente = request.user.agente
    except:
        messages.error(request, "Acesso restrito a agentes KMN.")
        return redirect('home')
    
    # Filtros
    search = request.GET.get('search', '')
    disponivel_filter = request.GET.get('disponivel', '')
    
    # Query base
    estoque = EstoqueItem.objects.filter(agente=agente)
    
    # Aplicar filtros
    if search:
        estoque = estoque.filter(produto__nome__icontains=search)
    
    if disponivel_filter == 'true':
        estoque = estoque.filter(quantidade_disponivel__gt=0)
    elif disponivel_filter == 'false':
        estoque = estoque.filter(quantidade_disponivel=0)
    
    # Ordenação
    estoque = estoque.order_by('-atualizado_em')
    
    # Paginação
    paginator = Paginator(estoque, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Produtos disponíveis para adicionar ao estoque
    produtos_disponiveis = Produto.objects.filter(ativo=True)
    
    context = {
        'agente': agente,
        'page_obj': page_obj,
        'search': search,
        'disponivel_filter': disponivel_filter,
        'produtos_disponiveis': produtos_disponiveis,
    }
    
    return render(request, 'app_marketplace/kmn_estoque.html', context)


@login_required
def kmn_trustlines(request):
    """Gestão de trustlines KMN"""
    try:
        agente = request.user.agente
    except:
        messages.error(request, "Acesso restrito a agentes KMN.")
        return redirect('home')
    
    # Trustlines do agente
    trustlines = TrustlineKeeper.objects.filter(
        Q(agente_a=agente) | Q(agente_b=agente)
    ).order_by('-aceito_em', '-criado_em')
    
    # Agentes disponíveis para criar trustlines
    agentes_disponiveis = Agente.objects.filter(
        verificado_kmn=True
    ).exclude(id=agente.id)
    
    # Excluir agentes que já têm trustline
    trustline_agente_ids = []
    for tl in trustlines:
        if tl.agente_a == agente:
            trustline_agente_ids.append(tl.agente_b.id)
        else:
            trustline_agente_ids.append(tl.agente_a.id)
    
    agentes_disponiveis = agentes_disponiveis.exclude(id__in=trustline_agente_ids)
    
    context = {
        'agente': agente,
        'trustlines': trustlines,
        'agentes_disponiveis': agentes_disponiveis,
    }
    
    return render(request, 'app_marketplace/kmn_trustlines.html', context)


@login_required
def kmn_catalogo_cliente(request, cliente_id):
    """Visualizar catálogo personalizado de um cliente"""
    try:
        agente = request.user.agente
    except:
        messages.error(request, "Acesso restrito a agentes KMN.")
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Verificar se o agente tem relação com o cliente
    relacao = ClienteRelacao.objects.filter(
        cliente=cliente,
        agente=agente,
        status='ativa'
    ).first()
    
    if not relacao:
        messages.error(request, "Você não tem relação ativa com este cliente.")
        return redirect('kmn_clientes')
    
    # Gerar catálogo personalizado
    catalogo = CatalogoService.gerar_catalogo_cliente(cliente)
    
    context = {
        'agente': agente,
        'cliente': cliente,
        'relacao': relacao,
        'catalogo': catalogo,
    }
    
    return render(request, 'app_marketplace/kmn_catalogo_cliente.html', context)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def criar_agente_automatico(user):
    """Cria agente automaticamente baseado no perfil existente"""
    try:
        # Verificar se já existe
        if hasattr(user, 'agente'):
            return user.agente
        
        # Criar baseado no perfil existente
        agente_data = {
            'user': user,
            'verificado_kmn': True,
        }
        
        if hasattr(user, 'personalshopper'):
            shopper = user.personalshopper
            agente_data.update({
                'personal_shopper': shopper,
                'nome_comercial': shopper.nome or f"{user.get_full_name()} - Shopper",
                'bio_agente': shopper.bio,
                'ativo_como_shopper': shopper.ativo,
                'ativo_como_keeper': False,
            })
        
        if hasattr(user, 'keeper'):
            keeper = user.keeper
            agente_data.update({
                'keeper': keeper,
                'nome_comercial': f"{user.get_full_name()} - Keeper",
                'ativo_como_keeper': keeper.ativo,
                'ativo_como_shopper': agente_data.get('ativo_como_shopper', False),
            })
        
        if 'nome_comercial' in agente_data:
            agente = Agente.objects.create(**agente_data)
            
            # Criar stats iniciais
            RoleStats.objects.create(agente=agente)
            
            return agente
        
        return None
        
    except Exception as e:
        print(f"Erro ao criar agente automático: {e}")
        return None


# ============================================================================
# AJAX ENDPOINTS
# ============================================================================

@login_required
def ajax_criar_oferta(request):
    """Criar oferta via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        agente = request.user.agente
        data = json.loads(request.body)
        
        produto = get_object_or_404(Produto, id=data['produto_id'])
        
        # Buscar estoque do produto
        estoque = EstoqueItem.objects.filter(
            produto=produto,
            agente=agente,
            ativo=True
        ).first()
        
        if not estoque:
            return JsonResponse({'error': 'Produto não encontrado no seu estoque'}, status=400)
        
        # Criar oferta
        oferta = Oferta.objects.create(
            produto=produto,
            agente_origem=agente,
            agente_ofertante=agente,
            preco_base=estoque.preco_base,
            preco_oferta=Decimal(data['preco_oferta']),
            quantidade_disponivel=min(int(data['quantidade']), estoque.quantidade_disponivel),
            exclusiva_para_clientes=data.get('exclusiva', False)
        )
        
        return JsonResponse({
            'success': True,
            'oferta_id': oferta.id,
            'markup': float(oferta.markup_local),
            'percentual_markup': float(oferta.percentual_markup)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ajax_atualizar_estoque(request):
    """Atualizar quantidade de estoque via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        agente = request.user.agente
        data = json.loads(request.body)
        
        estoque = get_object_or_404(
            EstoqueItem,
            id=data['estoque_id'],
            agente=agente
        )
        
        estoque.quantidade_disponivel = int(data['quantidade'])
        estoque.save()
        
        return JsonResponse({
            'success': True,
            'nova_quantidade': estoque.quantidade_disponivel,
            'quantidade_total': estoque.quantidade_total
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ajax_aceitar_trustline(request):
    """Aceitar trustline via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        agente = request.user.agente
        data = json.loads(request.body)
        
        trustline = get_object_or_404(
            TrustlineKeeper,
            id=data['trustline_id']
        )
        
        # Verificar se o usuário é um dos agentes
        if agente not in [trustline.agente_a, trustline.agente_b]:
            return JsonResponse({'error': 'Não autorizado'}, status=403)
        
        if trustline.status == TrustlineKeeper.StatusTrustline.PENDENTE:
            trustline.status = TrustlineKeeper.StatusTrustline.ATIVA
            trustline.aceito_em = timezone.now()
            trustline.save()
            
            return JsonResponse({
                'success': True,
                'status': trustline.get_status_display(),
                'aceito_em': trustline.aceito_em.strftime('%d/%m/%Y %H:%M')
            })
        else:
            return JsonResponse({'error': 'Trustline não está pendente'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
