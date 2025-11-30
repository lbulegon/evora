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
    WhatsappGroup, WhatsappProduct, WhatsappParticipant,
    RelacionamentoClienteShopper, PersonalShopper, LigacaoMesh, TrustlineKeeper
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
    # Usar query raw para evitar problemas com campos que não existem no banco
    from django.db import connection
    
    try:
        # Verificar quais campos existem na tabela
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='app_marketplace_pedido'
            """)
            columns = [row[0] for row in cursor.fetchall()]
        
        # Campos básicos que sempre devem existir
        campos_base = ['id', 'cliente_id', 'status', 'valor_total', 'criado_em', 'atualizado_em']
        campos_existentes = [campo for campo in campos_base if campo in columns]
        
        # Adicionar campos opcionais se existirem
        campos_opcionais = ['metodo_pagamento', 'observacoes', 'codigo_rastreamento']
        for campo in campos_opcionais:
            if campo in columns:
                campos_existentes.append(campo)
        
        # Usar .only() apenas com campos que existem
        pedidos = Pedido.objects.filter(cliente=cliente).only(*campos_existentes).order_by('-criado_em')
            
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg.lower() or 'ProgrammingError' in str(type(e).__name__):
            messages.warning(
                request,
                "Algumas migrations podem não ter sido aplicadas. "
                "O dashboard funcionará com funcionalidades limitadas."
            )
            # Tenta apenas com campos mínimos essenciais
            try:
                pedidos = Pedido.objects.filter(cliente=cliente).only(
                    'id', 'cliente_id', 'status', 'valor_total', 'criado_em'
                ).order_by('-criado_em')
            except:
                pedidos = Pedido.objects.none()
        else:
            raise
    
    total_pedidos = pedidos.count()
    
    # Pedidos por status (usando status corretos do modelo)
    pedidos_pendentes = pedidos.filter(status__in=['criado', 'aguardando_pagamento']).count()
    pedidos_pagos = pedidos.filter(status='pago').count()
    pedidos_enviados = pedidos.filter(status='em_transporte').count()
    pedidos_entregues = pedidos.filter(status='concluido').count()
    
    # Total gasto (pedidos pagos ou concluídos)
    total_gasto = pedidos.filter(
        status__in=['pago', 'em_preparacao', 'em_transporte', 'concluido']
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
    pacotes_enviados = pacotes.filter(status='despachado').count()
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
    try:
        pedidos_recentes = list(pedidos[:5])
    except Exception as e:
        # Se houver erro ao carregar pedidos (campos faltantes), usa lista vazia
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Erro ao carregar pedidos recentes: {str(e)}")
        pedidos_recentes = []
    
    whatsapp_orders_recentes = whatsapp_orders[:5]
    pacotes_recentes = pacotes[:5]
    
    # ========== TIMELINE DE ATIVIDADES ==========
    # Combinar pedidos e pacotes recentes para timeline
    atividades = []
    
    try:
        for pedido in pedidos[:10]:
            try:
                atividades.append({
                    'tipo': 'pedido',
                    'objeto': pedido,
                    'data': pedido.criado_em,
                    'titulo': f"Pedido #{pedido.id}",
                    'status': pedido.get_status_display(),
                    'valor': pedido.valor_total
                })
            except Exception as e:
                # Se houver erro ao acessar campos específicos, ignora este pedido
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erro ao processar pedido {pedido.id}: {str(e)}")
                continue
    except Exception as e:
        # Se houver erro ao iterar, ignora timeline de pedidos
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Erro ao processar pedidos na timeline: {str(e)}")
        pass
    
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
    """
    Lista de produtos disponíveis para o cliente.
    
    REGRA DE NEGÓCIO:
    1. Produtos aparecem se o cliente segue o shopper que criou o produto
    2. OU se o shopper seguido tem KMN/TrustLine com outro shopper/keeper,
       os produtos desse outro também aparecem (mas cliente só precisa seguir o shopper de origem)
    """
    if not request.user.is_cliente:
        messages.error(request, "Acesso restrito a clientes.")
        return redirect('home')
    
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "Perfil de cliente não encontrado.")
        return redirect('home')
    
    # 1. Buscar shoppers que o cliente está seguindo
    relacionamentos = RelacionamentoClienteShopper.objects.filter(
        cliente=cliente,
        status=RelacionamentoClienteShopper.Status.SEGUINDO
    ).select_related('personal_shopper', 'personal_shopper__user', 'personal_shopper__agente_profile', 'personal_shopper__agente_profile__user')
    
    # IDs dos usuários (owners) dos shoppers seguidos e conectados via KMN
    users_com_mesh = set()
    
    # Adicionar os próprios shoppers seguidos e buscar conexões KMN
    for relacao in relacionamentos:
        if relacao.personal_shopper and relacao.personal_shopper.user:
            shopper_user = relacao.personal_shopper.user
            users_com_mesh.add(shopper_user.id)
            
            # Buscar LigacaoMesh onde este shopper está envolvido (se existir)
            try:
                mesh_ligacoes = LigacaoMesh.objects.filter(
                    (Q(agente_a=shopper_user) | Q(agente_b=shopper_user)),
                    ativo=True
                ).select_related('agente_a', 'agente_b')
                
                # Adicionar os outros agentes das ligações Mesh
                for mesh in mesh_ligacoes:
                    if mesh.agente_a_id == shopper_user.id:
                        users_com_mesh.add(mesh.agente_b_id)
                    elif mesh.agente_b_id == shopper_user.id:
                        users_com_mesh.add(mesh.agente_a_id)
            except Exception:
                # LigacaoMesh pode não estar disponível, continuar
                pass
            
            # Buscar TrustlineKeeper (KMN) via Agente
            try:
                # Verificar se o PersonalShopper tem um Agente vinculado
                if hasattr(relacao.personal_shopper, 'agente_profile') and relacao.personal_shopper.agente_profile:
                    agente_shopper = relacao.personal_shopper.agente_profile
                    
                    # Buscar TrustlineKeeper ativas onde este agente está envolvido
                    trustlines = TrustlineKeeper.objects.filter(
                        (Q(agente_a=agente_shopper) | Q(agente_b=agente_shopper)),
                        status=TrustlineKeeper.StatusTrustline.ATIVA
                    ).select_related('agente_a__user', 'agente_b__user', 'agente_a__personal_shopper', 'agente_b__personal_shopper')
                    
                    # Para cada trustline, pegar o outro agente e seu PersonalShopper (se existir)
                    for trustline in trustlines:
                        outro_agente = None
                        if trustline.agente_a == agente_shopper:
                            outro_agente = trustline.agente_b
                        else:
                            outro_agente = trustline.agente_a
                        
                        # Se o outro agente tem um PersonalShopper vinculado, adicionar o User dele
                        if outro_agente and hasattr(outro_agente, 'personal_shopper') and outro_agente.personal_shopper:
                            outro_shopper_user = outro_agente.personal_shopper.user
                            if outro_shopper_user:
                                users_com_mesh.add(outro_shopper_user.id)
            except Exception as e:
                # TrustlineKeeper ou Agente podem não estar disponíveis, continuar
                import traceback
                print(f"Erro ao buscar TrustlineKeeper: {e}")
                traceback.print_exc()
                pass
    
    # 2. Buscar grupos dos agentes conectados via Mesh (incluindo os seguidos diretamente)
    grupos_validos = WhatsappGroup.objects.filter(
        owner_id__in=list(users_com_mesh),
        active=True
    )
    
    group_ids_validos = grupos_validos.values_list('id', flat=True)
    
    # 5. Buscar produtos dos grupos válidos
    products = WhatsappProduct.objects.filter(
        group_id__in=group_ids_validos,
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
    
    # Grupos disponíveis (apenas os válidos pela regra de negócio)
    groups = grupos_validos.order_by('name')
    
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

