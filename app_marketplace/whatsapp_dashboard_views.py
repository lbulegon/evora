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
    Cliente, Produto, Categoria, Agente, ClienteRelacao,
    RelacionamentoClienteShopper, TrustlineKeeper,
    ParticipantPermissionRequest, CarteiraCliente,
    PostScreenshot, WhatsappConversation, ConversationNote
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
def get_available_clients(request, group_id):
    """Buscar clientes disponíveis para adicionar ao grupo"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        
        # Buscar agente do shopper
        agente = None
        if request.user.is_shopper and hasattr(request.user, 'agente'):
            agente = request.user.agente
        elif request.user.is_shopper and hasattr(request.user, 'personalshopper'):
            # Criar agente se não existir
            try:
                agente = Agente.objects.get(user=request.user)
            except Agente.DoesNotExist:
                agente = None
        
        clientes_proprios = []
        clientes_trustline = []
        
        if agente:
            # 1. Clientes próprios do agente
            # Via ClienteRelacao
            relacoes_proprias = ClienteRelacao.objects.filter(
                agente=agente,
                status='ativa'
            ).select_related('cliente', 'cliente__user')
            
            for relacao in relacoes_proprias:
                cliente = relacao.cliente
                telefone = cliente.telefone or (cliente.user.username if cliente.user else '')
                if telefone:
                    clientes_proprios.append({
                        'id': cliente.id,
                        'name': cliente.user.get_full_name() or cliente.user.username,
                        'phone': telefone,
                        'owner': 'proprio',
                        'owner_name': request.user.get_full_name() or request.user.username
                    })
            
            # Via RelacionamentoClienteShopper (compatibilidade)
            if agente.personal_shopper:
                relacionamentos = RelacionamentoClienteShopper.objects.filter(
                    personal_shopper=agente.personal_shopper,
                    status='seguindo'
                ).select_related('cliente', 'cliente__user')
                
                for rel in relacionamentos:
                    cliente = rel.cliente
                    telefone = cliente.telefone or (cliente.user.username if cliente.user else '')
                    if telefone and not any(c['id'] == cliente.id for c in clientes_proprios):
                        clientes_proprios.append({
                            'id': cliente.id,
                            'name': cliente.user.get_full_name() or cliente.user.username,
                            'phone': telefone,
                            'owner': 'proprio',
                            'owner_name': request.user.get_full_name() or request.user.username
                        })
            
            # 2. Clientes via trustlines
            trustlines_ativas = TrustlineKeeper.objects.filter(
                Q(agente_a=agente) | Q(agente_b=agente),
                status=TrustlineKeeper.StatusTrustline.ATIVA
            ).defer('tipo_compartilhamento').select_related('agente_a__user', 'agente_b__user')
            
            for trustline in trustlines_ativas:
                parceiro = trustline.agente_b if trustline.agente_a == agente else trustline.agente_a
                
                # Buscar clientes do parceiro
                relacoes_parceiro = ClienteRelacao.objects.filter(
                    agente=parceiro,
                    status='ativa'
                ).select_related('cliente', 'cliente__user')
                
                for relacao in relacoes_parceiro:
                    cliente = relacao.cliente
                    telefone = cliente.telefone or (cliente.user.username if cliente.user else '')
                    if telefone:
                        # Verificar se já existe permissão
                        permission = ParticipantPermissionRequest.objects.filter(
                            group=group,
                            cliente=cliente,
                            status__in=['pendente', 'aprovado']
                        ).first()
                        
                        has_permission = False
                        permission_pending = False
                        permission_id = None
                        
                        if permission:
                            has_permission = permission.status == 'aprovado'
                            permission_pending = permission.status == 'pendente'
                            permission_id = permission.id
                        
                        clientes_trustline.append({
                            'id': cliente.id,
                            'name': cliente.user.get_full_name() or cliente.user.username,
                            'phone': telefone,
                            'owner': 'trustline',
                            'owner_name': parceiro.user.get_full_name() or parceiro.user.username,
                            'owner_id': parceiro.user.id,
                            'trustline_id': trustline.id,
                            'has_permission': has_permission,
                            'permission_pending': permission_pending,
                            'permission_id': permission_id
                        })
        
        return JsonResponse({
            'success': True,
            'clientes_proprios': clientes_proprios,
            'clientes_trustline': clientes_trustline
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def request_participant_permission(request, group_id):
    """Solicitar permissão para adicionar cliente de outro shopper"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        data = json.loads(request.body)
        
        cliente_id = data.get('cliente_id')
        carteira_owner_id = data.get('carteira_owner_id')
        message = data.get('message', '')
        
        if not cliente_id or not carteira_owner_id:
            return JsonResponse({'error': 'Cliente e dono da carteira são obrigatórios'}, status=400)
        
        cliente = get_object_or_404(Cliente, id=cliente_id)
        carteira_owner = get_object_or_404(User, id=carteira_owner_id)
        
        # Verificar se já existe solicitação pendente ou aprovada
        existing = ParticipantPermissionRequest.objects.filter(
            group=group,
            cliente=cliente,
            status__in=['pendente', 'aprovado']
        ).first()
        
        if existing:
            if existing.status == 'aprovado':
                return JsonResponse({
                    'error': 'Permissão já foi aprovada para este cliente',
                    'permission_id': existing.id,
                    'already_approved': True
                }, status=400)
            else:
                return JsonResponse({
                    'error': 'Já existe uma solicitação pendente para este cliente',
                    'permission_id': existing.id
                }, status=400)
        
        # Criar solicitação
        from django.utils import timezone
        from datetime import timedelta
        
        permission_request = ParticipantPermissionRequest.objects.create(
            group=group,
            cliente=cliente,
            requested_by=request.user,
            carteira_owner=carteira_owner,
            message=message,
            expires_at=timezone.now() + timedelta(days=7)  # Expira em 7 dias
        )
        
        # TODO: Enviar notificação para o dono da carteira
        
        return JsonResponse({
            'success': True,
            'permission_request': {
                'id': permission_request.id,
                'status': permission_request.status,
                'requested_at': permission_request.requested_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_participant(request, group_id):
    """Adicionar participante ao grupo (agora com verificação de permissões)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        data = json.loads(request.body)
        
        cliente_id = data.get('cliente_id')
        phone = data.get('phone')
        name = data.get('name', '')
        
        cliente = None
        needs_permission = False
        carteira_owner = None
        
        # Se cliente_id foi fornecido, buscar o cliente
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                name = name or (cliente.user.get_full_name() or cliente.user.username)
                phone = phone or cliente.telefone
                
                # Verificar se o cliente pertence à carteira de outro shopper
                if cliente.wallet and cliente.wallet.owner != request.user:
                    carteira_owner = cliente.wallet.owner
                    needs_permission = True
                else:
                    # Verificar via ClienteRelacao
                    relacao = ClienteRelacao.objects.filter(
                        cliente=cliente,
                        status='ativa'
                    ).select_related('agente__user').first()
                    
                    if relacao and relacao.agente.user != request.user:
                        carteira_owner = relacao.agente.user
                        needs_permission = True
            except Cliente.DoesNotExist:
                pass
        
        # Se precisa de permissão e não foi fornecida, retornar erro
        if needs_permission and carteira_owner:
            # Verificar se já existe permissão aprovada
            permission = ParticipantPermissionRequest.objects.filter(
                group=group,
                cliente=cliente,
                carteira_owner=carteira_owner,
                status='aprovado'
            ).first()
            
            if not permission:
                # Verificar se existe solicitação pendente
                pending = ParticipantPermissionRequest.objects.filter(
                    group=group,
                    cliente=cliente,
                    carteira_owner=carteira_owner,
                    status='pendente'
                ).first()
                
                if pending:
                    return JsonResponse({
                        'error': 'Aguardando aprovação do dono da carteira',
                        'needs_permission': True,
                        'permission_id': pending.id,
                        'carteira_owner_name': carteira_owner.get_full_name() or carteira_owner.username
                    }, status=403)
                else:
                    return JsonResponse({
                        'error': 'É necessário solicitar permissão ao dono da carteira',
                        'needs_permission': True,
                        'cliente_id': cliente.id,
                        'carteira_owner_id': carteira_owner.id,
                        'carteira_owner_name': carteira_owner.get_full_name() or carteira_owner.username
                    }, status=403)
        
        if not phone:
            return JsonResponse({'error': 'Telefone é obrigatório'}, status=400)
        
        # Limpar e formatar telefone
        phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not phone.startswith('+'):
            if phone.startswith('55'):
                phone = '+' + phone
            elif phone.startswith('0'):
                phone = '+55' + phone[1:]
            else:
                phone = '+55' + phone
        
        # Verificar se já existe
        if WhatsappParticipant.objects.filter(group=group, phone=phone).exists():
            return JsonResponse({'error': 'Participante já cadastrado neste grupo'}, status=400)
        
        # Se não foi fornecido cliente_id, tentar buscar pelo telefone
        if not cliente:
            try:
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


@login_required
@require_http_methods(["POST"])
def respond_permission_request(request, permission_id):
    """Aprovar ou rejeitar solicitação de permissão"""
    try:
        permission = get_object_or_404(ParticipantPermissionRequest, id=permission_id)
        
        # Verificar se o usuário é o dono da carteira
        if permission.carteira_owner != request.user:
            return JsonResponse({'error': 'Você não tem permissão para responder esta solicitação'}, status=403)
        
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' ou 'reject'
        response_message = data.get('message', '')
        
        if action == 'approve':
            permission.approve(response_message)
            # Criar participante automaticamente após aprovação
            try:
                cliente = permission.cliente
                phone = cliente.telefone or (cliente.user.username if cliente.user else '')
                if phone:
                    # Formatar telefone
                    phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                    if not phone.startswith('+'):
                        if phone.startswith('55'):
                            phone = '+' + phone
                        elif phone.startswith('0'):
                            phone = '+55' + phone[1:]
                        else:
                            phone = '+55' + phone
                    
                    # Verificar se já existe
                    if not WhatsappParticipant.objects.filter(group=permission.group, phone=phone).exists():
                        WhatsappParticipant.objects.create(
                            group=permission.group,
                            phone=phone,
                            name=cliente.user.get_full_name() or cliente.user.username,
                            cliente=cliente
                        )
            except Exception as e:
                pass  # Logar erro mas não falhar a aprovação
            
            return JsonResponse({
                'success': True,
                'message': 'Permissão aprovada e participante adicionado ao grupo'
            })
        elif action == 'reject':
            permission.reject(response_message)
            return JsonResponse({
                'success': True,
                'message': 'Permissão rejeitada'
            })
        else:
            return JsonResponse({'error': 'Ação inválida'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# GERENCIAMENTO DE PRODUTOS
# ============================================================================

@login_required
def products_list(request, group_id):
    """Lista posts/produtos de um grupo (MVP)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito.")
        return redirect('home')
    
    group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
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
    """Criar post/produto no grupo (MVP)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        
        # Se for FormData (upload de imagem)
        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            price = request.POST.get('price')
            currency = request.POST.get('currency', 'USD')
            brand = request.POST.get('brand', '')
            category = request.POST.get('category', '')
            is_available = request.POST.get('is_available', 'true') == 'true'
            is_featured = request.POST.get('is_featured', 'false') == 'true'
            
            # Processar imagens
            image_urls = []
            if 'images' in request.FILES:
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                import os
                from datetime import datetime
                
                for image_file in request.FILES.getlist('images'):
                    # Salvar imagem
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"posts/{group.id}/{timestamp}_{image_file.name}"
                    path = default_storage.save(filename, ContentFile(image_file.read()))
                    image_urls.append(default_storage.url(path))
        else:
            # JSON
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description', '')
            price = data.get('price')
            currency = data.get('currency', 'USD')
            brand = data.get('brand', '')
            category = data.get('category', '')
            image_urls = data.get('image_urls', [])
            is_available = data.get('is_available', True)
            is_featured = data.get('is_featured', False)
        
        if not name:
            return JsonResponse({'error': 'Nome do post é obrigatório'}, status=400)
        
        # Buscar ou criar participante para o owner
        participant, _ = WhatsappParticipant.objects.get_or_create(
            group=group,
            phone=request.user.username if not hasattr(request.user, 'cliente') else (request.user.cliente.telefone or request.user.username),
            defaults={
                'name': request.user.get_full_name() or request.user.username,
                'is_admin': True
            }
        )
        
        # Criar produto/post
        product = WhatsappProduct.objects.create(
            group=group,
            name=name,
            description=description,
            price=Decimal(price) if price else None,
            currency=currency,
            brand=brand,
            category=category,
            image_urls=image_urls,
            is_available=is_available,
            is_featured=is_featured,
            posted_by=participant
        )
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': str(product.price) if product.price else None,
                'currency': product.currency,
                'brand': product.brand,
                'category': product.category,
                'image_urls': product.image_urls,
                'is_available': product.is_available,
                'is_featured': product.is_featured,
                'created_at': product.created_at.isoformat(),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_product(request, group_id, product_id):
    """Buscar produto específico (para edição)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        product = get_object_or_404(WhatsappProduct, id=product_id, group=group)
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': str(product.price) if product.price else None,
                'currency': product.currency,
                'brand': product.brand,
                'category': product.category,
                'image_urls': product.image_urls,
                'is_available': product.is_available,
                'is_featured': product.is_featured,
                'created_at': product.created_at.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT", "PATCH"])
def update_product(request, group_id, product_id):
    """Atualizar post/produto (MVP)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        product = get_object_or_404(WhatsappProduct, id=product_id, group=group)
        
        data = json.loads(request.body)
        
        # Atualizar campos
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data.get('description', '')
        if 'price' in data:
            product.price = Decimal(data['price']) if data['price'] else None
        if 'currency' in data:
            product.currency = data['currency']
        if 'brand' in data:
            product.brand = data.get('brand', '')
        if 'category' in data:
            product.category = data.get('category', '')
        if 'image_urls' in data:
            product.image_urls = data['image_urls']
        if 'is_available' in data:
            product.is_available = data['is_available']
        if 'is_featured' in data:
            product.is_featured = data['is_featured']
        
        product.save()
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': str(product.price) if product.price else None,
                'currency': product.currency,
                'image_urls': product.image_urls,
                'is_available': product.is_available,
                'is_featured': product.is_featured,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_product(request, group_id, product_id):
    """Deletar post/produto (MVP)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        product = get_object_or_404(WhatsappProduct, id=product_id, group=group)
        
        product.delete()
        
        return JsonResponse({'success': True, 'message': 'Post deletado com sucesso'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# CAPTURA DE IMAGENS (MVP)
# ============================================================================

@login_required
@require_http_methods(["POST"])
def capture_post_screenshot(request, group_id, product_id):
    """Capturar screenshot de um post (MVP)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        product = get_object_or_404(WhatsappProduct, id=product_id, group=group)
        
        # Se for upload de imagem
        if 'screenshot' in request.FILES:
            screenshot_file = request.FILES['screenshot']
            
            # Criar screenshot
            screenshot = PostScreenshot.objects.create(
                post=product,
                group=group,
                screenshot_file=screenshot_file,
                captured_by=request.user,
                notes=request.POST.get('notes', '')
            )
            
            # Obter dimensões se possível
            try:
                from PIL import Image
                img = Image.open(screenshot.screenshot_file)
                screenshot.width = img.width
                screenshot.height = img.height
                screenshot.file_size = screenshot.screenshot_file.size
                screenshot.save()
            except:
                pass
            
            return JsonResponse({
                'success': True,
                'screenshot': {
                    'id': screenshot.id,
                    'url': screenshot.screenshot_file.url,
                    'captured_at': screenshot.captured_at.isoformat(),
                    'width': screenshot.width,
                    'height': screenshot.height,
                }
            })
        else:
            return JsonResponse({'error': 'Arquivo de screenshot é obrigatório'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_post_screenshots(request, group_id, product_id):
    """Listar screenshots de um post (MVP)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        product = get_object_or_404(WhatsappProduct, id=product_id, group=group)
        
        screenshots = PostScreenshot.objects.filter(post=product).order_by('-captured_at')
        
        screenshots_data = [{
            'id': s.id,
            'url': s.screenshot_file.url,
            'captured_at': s.captured_at.isoformat(),
            'captured_by': s.captured_by.get_full_name() or s.captured_by.username if s.captured_by else None,
            'width': s.width,
            'height': s.height,
            'file_size': s.file_size,
            'notes': s.notes,
        } for s in screenshots]
        
        return JsonResponse({
            'success': True,
            'screenshots': screenshots_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_screenshot(request, group_id, product_id, screenshot_id):
    """Deletar screenshot (MVP)"""
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        product = get_object_or_404(WhatsappProduct, id=product_id, group=group)
        screenshot = get_object_or_404(PostScreenshot, id=screenshot_id, post=product)
        
        screenshot.delete()
        
        return JsonResponse({'success': True, 'message': 'Screenshot deletado com sucesso'})
        
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
