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
    Oferta, TrustlineKeeper, RoleStats, Pedido, RelacionamentoClienteShopper
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
    """
    Gestão de clientes KMN.
    
    Mostra:
    1. Clientes diretos do agente (via ClienteRelacao ou RelacionamentoClienteShopper)
    2. Clientes de parceiros via trustlines ATIVAS (emprestimo de carteira)
    """
    try:
        agente = request.user.agente
    except:
        messages.error(request, "Acesso restrito a agentes KMN.")
        return redirect('home')
    
    # Filtros
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # 1. IDs de clientes diretos do agente
    cliente_ids_diretos = set()
    
    # Via ClienteRelacao
    cliente_ids_diretos.update(
        ClienteRelacao.objects.filter(agente=agente).values_list('cliente_id', flat=True)
    )
    
    # Via RelacionamentoClienteShopper (se o agente tem personal_shopper)
    if agente.personal_shopper:
        cliente_ids_diretos.update(
            Cliente.objects.filter(
                relacionamentoclienteshopper__personal_shopper=agente.personal_shopper,
                relacionamentoclienteshopper__status=RelacionamentoClienteShopper.Status.SEGUINDO
            ).values_list('id', flat=True)
        )
    
    # 2. IDs de clientes via trustlines ATIVAS (emprestimo de carteira)
    cliente_ids_via_trustline = set()
    
    # Buscar trustlines onde o agente é agente_a ou agente_b
    trustlines_ativas = TrustlineKeeper.objects.filter(
        Q(agente_a=agente) | Q(agente_b=agente),
        status=TrustlineKeeper.StatusTrustline.ATIVA
    ).select_related('agente_a', 'agente_b')
    
    # Para cada trustline, buscar clientes do parceiro respeitando a direcionalidade
    for trustline in trustlines_ativas:
        parceiro = None
        pode_ver_clientes_parceiro = False
        
        # Verificar direcionalidade (com fallback para trustlines antigas sem o campo)
        tipo_compartilhamento = getattr(
            trustline, 
            'tipo_compartilhamento', 
            TrustlineKeeper.TipoCompartilhamento.BIDIRECIONAL
        )
        
        if tipo_compartilhamento == TrustlineKeeper.TipoCompartilhamento.BIDIRECIONAL:
            # Bidirecional: ambos compartilham
            parceiro = trustline.agente_b if trustline.agente_a == agente else trustline.agente_a
            pode_ver_clientes_parceiro = True
        elif tipo_compartilhamento == TrustlineKeeper.TipoCompartilhamento.UNIDIRECIONAL_A_PARA_B:
            # Unidirecional A → B: apenas A empresta para B
            if trustline.agente_a == agente:
                # Agente logado é A: não vê clientes de B (direção é A → B)
                pode_ver_clientes_parceiro = False
            else:
                # Agente logado é B: vê clientes de A (A empresta para B)
                parceiro = trustline.agente_a
                pode_ver_clientes_parceiro = True
        elif tipo_compartilhamento == TrustlineKeeper.TipoCompartilhamento.UNIDIRECIONAL_B_PARA_A:
            # Unidirecional B → A: apenas B empresta para A
            if trustline.agente_b == agente:
                # Agente logado é B: não vê clientes de A (direção é B → A)
                pode_ver_clientes_parceiro = False
            else:
                # Agente logado é A: vê clientes de B (B empresta para A)
                parceiro = trustline.agente_b
                pode_ver_clientes_parceiro = True
        else:
            # Fallback: tratar como bidirecional se o valor não for reconhecido
            parceiro = trustline.agente_b if trustline.agente_a == agente else trustline.agente_a
            pode_ver_clientes_parceiro = True
        
        # Se pode ver clientes do parceiro, buscar
        if pode_ver_clientes_parceiro and parceiro:
            # Via ClienteRelacao do parceiro
            cliente_ids_via_trustline.update(
                ClienteRelacao.objects.filter(agente=parceiro).values_list('cliente_id', flat=True)
            )
            
            # Via RelacionamentoClienteShopper do parceiro
            if parceiro.personal_shopper:
                cliente_ids_via_trustline.update(
                    Cliente.objects.filter(
                        relacionamentoclienteshopper__personal_shopper=parceiro.personal_shopper,
                        relacionamentoclienteshopper__status=RelacionamentoClienteShopper.Status.SEGUINDO
                    ).values_list('id', flat=True)
                )
    
    # Unir todos os IDs de clientes
    todos_cliente_ids = cliente_ids_diretos | cliente_ids_via_trustline
    
    # Se não houver clientes, retornar query vazia
    if not todos_cliente_ids:
        relacoes_finais = ClienteRelacao.objects.none()
    else:
        # Buscar ClienteRelacao para esses clientes
        # Primeiro, buscar relações diretas do agente
        relacoes_diretas_qs = ClienteRelacao.objects.filter(
            agente=agente,
            cliente_id__in=todos_cliente_ids
        )
        
        # Buscar relações dos parceiros (via trustline) para os mesmos clientes
        # Filtrar apenas parceiros que realmente compartilham clientes (respeitando direcionalidade)
        agentes_parceiros_compartilhando = []
        for tl in trustlines_ativas:
            tipo_compartilhamento = getattr(
                tl, 
                'tipo_compartilhamento', 
                TrustlineKeeper.TipoCompartilhamento.BIDIRECIONAL
            )
            
            if tipo_compartilhamento == TrustlineKeeper.TipoCompartilhamento.BIDIRECIONAL:
                # Bidirecional: ambos compartilham
                parceiro = tl.agente_b if tl.agente_a == agente else tl.agente_a
                if parceiro not in agentes_parceiros_compartilhando:
                    agentes_parceiros_compartilhando.append(parceiro)
            elif tipo_compartilhamento == TrustlineKeeper.TipoCompartilhamento.UNIDIRECIONAL_A_PARA_B:
                # Unidirecional A → B: apenas B vê clientes de A
                if tl.agente_b == agente:
                    # Agente logado é B: pode ver clientes de A
                    if tl.agente_a not in agentes_parceiros_compartilhando:
                        agentes_parceiros_compartilhando.append(tl.agente_a)
            elif tipo_compartilhamento == TrustlineKeeper.TipoCompartilhamento.UNIDIRECIONAL_B_PARA_A:
                # Unidirecional B → A: apenas A vê clientes de B
                if tl.agente_a == agente:
                    # Agente logado é A: pode ver clientes de B
                    if tl.agente_b not in agentes_parceiros_compartilhando:
                        agentes_parceiros_compartilhando.append(tl.agente_b)
        
        relacoes_parceiros_qs = ClienteRelacao.objects.filter(
            agente__in=agentes_parceiros_compartilhando,
            cliente_id__in=todos_cliente_ids
        ) if agentes_parceiros_compartilhando else ClienteRelacao.objects.none()
        
        # Combinar: priorizar relações diretas, mas incluir relações dos parceiros
        # Para clientes que não têm relação direta, usar a relação do parceiro
        cliente_ids_com_relacao_direta = set(relacoes_diretas_qs.values_list('cliente_id', flat=True))
        cliente_ids_sem_relacao_direta = todos_cliente_ids - cliente_ids_com_relacao_direta
        
        # Buscar relações dos parceiros apenas para clientes sem relação direta
        relacoes_parceiros_filtradas = relacoes_parceiros_qs.filter(
            cliente_id__in=cliente_ids_sem_relacao_direta
        ) if cliente_ids_sem_relacao_direta else ClienteRelacao.objects.none()
        
        # Combinar as duas queries
        relacoes_finais = relacoes_diretas_qs | relacoes_parceiros_filtradas
        
        # Se ainda houver clientes sem ClienteRelacao, criar relações virtuais
        # (para clientes que vêm apenas de RelacionamentoClienteShopper)
        cliente_ids_com_relacao = set(relacoes_finais.values_list('cliente_id', flat=True))
        clientes_sem_relacao_ids = todos_cliente_ids - cliente_ids_com_relacao
        
        if clientes_sem_relacao_ids:
            # Criar ClienteRelacao para esses clientes se não existirem
            for cliente_id in clientes_sem_relacao_ids:
                try:
                    cliente = Cliente.objects.get(id=cliente_id)
                    
                    # Verificar se já existe ClienteRelacao
                    if not ClienteRelacao.objects.filter(agente=agente, cliente=cliente).exists():
                        # Criar ClienteRelacao com valores padrão
                        ClienteRelacao.objects.get_or_create(
                            agente=agente,
                            cliente=cliente,
                            defaults={
                                'forca_relacao': 50.0,
                                'status': ClienteRelacao.StatusRelacao.ATIVA,
                            }
                        )
                except Cliente.DoesNotExist:
                    continue
            
            # Rebuscar as relações incluindo as recém-criadas
            relacoes_diretas_qs = ClienteRelacao.objects.filter(
                agente=agente,
                cliente_id__in=todos_cliente_ids
            )
            relacoes_parceiros_filtradas = relacoes_parceiros_qs.filter(
                cliente_id__in=(todos_cliente_ids - set(relacoes_diretas_qs.values_list('cliente_id', flat=True)))
            ) if relacoes_parceiros_qs.exists() else ClienteRelacao.objects.none()
            relacoes_finais = relacoes_diretas_qs | relacoes_parceiros_filtradas
    
    # Aplicar filtros de busca
    if search:
        relacoes_finais = relacoes_finais.filter(
            Q(cliente__user__first_name__icontains=search) |
            Q(cliente__user__last_name__icontains=search) |
            Q(cliente__user__username__icontains=search)
        )
    
    if status_filter:
        relacoes_finais = relacoes_finais.filter(status=status_filter)
    
    # Ordenação
    relacoes_finais = relacoes_finais.order_by('-forca_relacao', '-ultimo_pedido')
    
    # Paginação
    paginator = Paginator(relacoes_finais, 20)
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
    except AttributeError:
        messages.error(request, "Acesso restrito a agentes KMN.")
        return redirect('home')
    except Exception as e:
        messages.error(request, f"Erro ao acessar perfil de agente: {str(e)}")
        return redirect('home')
    
    # Tratar criação de trustline via GET (parâmetro ?criar=id)
    criar_agente_id = request.GET.get('criar')
    if criar_agente_id:
        try:
            agente_b = get_object_or_404(Agente, id=criar_agente_id, verificado_kmn=True)
            
            # Verificar se não está tentando criar trustline consigo mesmo
            if agente_b.id == agente.id:
                messages.error(request, "Você não pode criar uma trustline consigo mesmo.")
            else:
                # Buscar qualquer trustline existente entre os dois agentes (qualquer status)
                trustline_existente = TrustlineKeeper.objects.filter(
                    (Q(agente_a=agente) & Q(agente_b=agente_b)) |
                    (Q(agente_a=agente_b) & Q(agente_b=agente))
                ).first()

                # Se houver trustline ativa / pendente / suspensa, não deixar duplicar
                if trustline_existente and trustline_existente.status in [
                    TrustlineKeeper.StatusTrustline.ATIVA,
                    TrustlineKeeper.StatusTrustline.PENDENTE,
                    TrustlineKeeper.StatusTrustline.SUSPENSA,
                ]:
                    messages.warning(
                        request,
                        f"Já existe uma trustline com {agente_b.user.get_full_name() or agente_b.user.username}."
                    )
                else:
                    # Se já existe uma trustline ENCERRADA, reutilizar o registro
                    if trustline_existente and trustline_existente.status == TrustlineKeeper.StatusTrustline.CANCELADA:
                        trustline_existente.status = TrustlineKeeper.StatusTrustline.PENDENTE
                        trustline_existente.nivel_confianca_a_para_b = 50.0
                        trustline_existente.nivel_confianca_b_para_a = 50.0
                        trustline_existente.perc_shopper = 60.0
                        trustline_existente.perc_keeper = 40.0
                        trustline_existente.aceito_em = None
                        trustline_existente.save()
                        messages.success(
                            request,
                            f"Trustline reaberta com sucesso! Aguardando aprovação de {agente_b.user.get_full_name() or agente_b.user.username}."
                        )
                        return redirect('kmn_trustlines')

                    # Caso contrário, criar uma nova trustline
                    try:
                        nova_trustline = TrustlineKeeper.objects.create(
                            agente_a=agente,
                            agente_b=agente_b,
                            nivel_confianca_a_para_b=50.0,  # Valor padrão
                            nivel_confianca_b_para_a=50.0,  # Valor padrão
                            perc_shopper=60.0,  # Valor padrão
                            perc_keeper=40.0,   # Valor padrão
                            status=TrustlineKeeper.StatusTrustline.PENDENTE,
                            tipo_compartilhamento=TrustlineKeeper.TipoCompartilhamento.BIDIRECIONAL  # Padrão: bidirecional
                        )
                        messages.success(
                            request,
                            f"Trustline criada com sucesso! Aguardando aprovação de {agente_b.user.get_full_name() or agente_b.user.username}."
                        )
                        # Redirecionar para remover o parâmetro da URL
                        return redirect('kmn_trustlines')
                    except Exception as e:
                        messages.error(request, f"Erro ao criar trustline: {str(e)}")
        except Agente.DoesNotExist:
            messages.error(request, "Agente não encontrado ou não verificado.")
        except Exception as e:
            messages.error(request, f"Erro ao criar trustline: {str(e)}")
    
    # Trustlines do agente
    try:
        trustlines = TrustlineKeeper.objects.filter(
            Q(agente_a=agente) | Q(agente_b=agente)
        ).select_related('agente_a__user', 'agente_b__user').order_by('-aceito_em', '-criado_em')
        
        # Agentes disponíveis para criar trustlines
        # IMPORTANTE: Um agente pode ter múltiplas trustlines com diferentes agentes
        # Apenas não pode ter múltiplas trustlines com o MESMO agente
        agentes_disponiveis = Agente.objects.filter(
            verificado_kmn=True
        ).exclude(id=agente.id).select_related('user')
        
        # Excluir apenas agentes que já têm trustline ATIVA ou PENDENTE com este agente
        # Permitir múltiplas trustlines com diferentes agentes
        trustline_agente_ids = []
        for tl in trustlines:
            # Só excluir se a trustline estiver ativa ou pendente (não cancelada/suspensa)
            if tl.status in [TrustlineKeeper.StatusTrustline.ATIVA, TrustlineKeeper.StatusTrustline.PENDENTE]:
                if tl.agente_a == agente:
                    trustline_agente_ids.append(tl.agente_b.id)
                else:
                    trustline_agente_ids.append(tl.agente_a.id)
        
        # Excluir apenas os agentes que já têm trustline ativa/pendente
        agentes_disponiveis = agentes_disponiveis.exclude(id__in=trustline_agente_ids)
    except Exception as e:
        messages.error(request, f"Erro ao carregar trustlines: {str(e)}")
        trustlines = TrustlineKeeper.objects.none()
        agentes_disponiveis = Agente.objects.none()
    
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
        
        if hasattr(user, 'address_keeper'):
            address_keeper = user.address_keeper
            agente_data.update({
                'address_keeper': address_keeper,
                'nome_comercial': f"{user.get_full_name()} - Address Keeper",
                'ativo_como_address_keeper': address_keeper.ativo,
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


@login_required
def ajax_encerrar_trustline(request):
    """Encerrar/Cancelar trustline via AJAX"""
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
        
        # Verificar se a trustline pode ser encerrada (deve estar ativa ou pendente)
        if trustline.status not in [TrustlineKeeper.StatusTrustline.ATIVA, TrustlineKeeper.StatusTrustline.PENDENTE]:
            return JsonResponse({'error': 'Trustline já está encerrada'}, status=400)
        
        # Encerrar a trustline (marcar como cancelada)
        trustline.status = TrustlineKeeper.StatusTrustline.CANCELADA
        trustline.save()
        
        return JsonResponse({
            'success': True,
            'status': trustline.get_status_display(),
            'message': 'Trustline encerrada com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


