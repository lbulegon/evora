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
    Cliente, Produto, Categoria, Empresa, ProdutoJSON
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
    
    # Converter monthly_growth para JSON para o gráfico
    monthly_growth_json = json.dumps(monthly_growth)
    
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
        'monthly_growth_json': monthly_growth_json,
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
    """Catálogo de produtos do shopper - usando ProdutoJSON"""
    if not request.user.is_shopper:
        messages.error(request, "Acesso restrito a Personal Shoppers.")
        return redirect('home')
    
    # Base: todos os produtos do shopper (ProdutoJSON)
    base_products = ProdutoJSON.objects.filter(criado_por=request.user).order_by('-criado_em')
    
    # Categorias e marcas disponíveis - BUSCAR ANTES DOS FILTROS para mostrar todas
    categories = base_products.values_list('categoria', flat=True).distinct().exclude(categoria='').exclude(categoria__isnull=True)
    brands = base_products.values_list('marca', flat=True).distinct().exclude(marca='').exclude(marca__isnull=True)
    
    # Aplicar filtros
    products = base_products
    
    # Filtro de grupo (se vier na URL)
    group_id = request.GET.get('group', '')
    if group_id:
        try:
            products = products.filter(grupo_whatsapp_id=group_id)
        except ValueError:
            pass  # Se não for um ID válido, ignora
    
    # Outros filtros
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    brand = request.GET.get('brand', '')
    availability = request.GET.get('availability', '')
    featured = request.GET.get('featured', '')
    
    if search:
        products = products.filter(
            Q(nome_produto__icontains=search) | 
            Q(marca__icontains=search) |
            Q(categoria__icontains=search)
        )
    
    if category:
        products = products.filter(categoria=category)
    
    if brand:
        products = products.filter(marca=brand)
    
    # Estatísticas (base total do shopper)
    total_products = base_products.count()
    # Para ProdutoJSON, não temos is_available ou is_featured, então usamos total
    available_products = total_products
    featured_products = 0
    
    # Estabelecimentos disponíveis (base geral)
    estabelecimentos = Empresa.objects.filter(ativo=True).order_by('nome')
    
    # Grupos do shopper para o modal de criação (OBRIGATÓRIO para o dropdown)
    groups = WhatsappGroup.objects.filter(owner=request.user).order_by('name')
    
    # Paginação do QuerySet primeiro
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Converter ProdutoJSON para formato compatível com o template
    # O template espera campos como name, brand, image_urls, etc.
    from django.conf import settings
    
    produtos_adaptados = []
    import logging
    logger = logging.getLogger(__name__)
    
    for produto_json in page_obj:
        try:
            dados = produto_json.get_produto_data()
            produto_data = dados.get('produto', {})
            
            # Extrair imagens - verificar múltiplos locais possíveis
            image_urls = []
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            
            # DEBUG: Log para verificar dados do produto
            logger.info(f"[SHOPPER_PRODUCTS] Processando produto ID: {produto_json.id}, Nome: {produto_json.nome_produto}")
            logger.info(f"[SHOPPER_PRODUCTS] imagem_original: {produto_json.imagem_original}")
            logger.info(f"[SHOPPER_PRODUCTS] dados completos (keys): {list(dados.keys()) if dados else 'None'}")
            logger.info(f"[SHOPPER_PRODUCTS] produto_data (keys): {list(produto_data.keys()) if produto_data else 'None'}")
            logger.info(f"[SHOPPER_PRODUCTS] produto_data.imagens: {produto_data.get('imagens', [])}")
            
            # Helper para construir URL correta
            def build_image_url(img_path):
            """
            Constrói URL completa para imagem do SinapUm.
            
            Baseado na documentação do OpenMind:
            - image_path: "media/uploads/{uuid}.jpg" (caminho relativo)
            - image_url: "http://69.169.102.84:8000/media/uploads/{uuid}.jpg" (URL completa)
            
            O SinapUm serve imagens em: http://{HOST}:{PORT}/media/{path}
            
            IMPORTANTE: Tenta diferentes variações de caminho para resolver divergências.
            """
            if not img_path:
                return None
            if isinstance(img_path, str):
                # 1. Se já é URL completa (HTTP/HTTPS), corrigir se necessário e retornar
                if img_path.startswith('http://') or img_path.startswith('https://'):
                    # Corrigir URL malformada (ex: mediauploads -> media/uploads)
                    if 'mediauploads' in img_path:
                        logger.info(f"[SHOPPER_PRODUCTS] Corrigindo URL malformada: {img_path}")
                        img_path = img_path.replace('mediauploads', 'media/uploads')
                    return img_path
                
                # 2. Obter URL base do SinapUm
                openmind_url = getattr(settings, 'OPENMIND_AI_URL', 'http://69.169.102.84:8000')
                
                # Remover /api/v1 se existir para obter base URL do servidor
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                
                # 3. Normalizar o caminho - remover barras duplicadas e normalizar
                img_path_clean = img_path.strip().lstrip('/')
                
                # 4. Tentar diferentes variações de caminho
                # Variação 1: "media/uploads/{arquivo}" (formato padrão)
                if img_path_clean.startswith('media/uploads/'):
                    url = f"{sinapum_base}/{img_path_clean}"
                    logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (variação 1): {url}")
                    return url
                
                # Variação 2: "uploads/{arquivo}" (sem media/)
                if img_path_clean.startswith('uploads/'):
                    url = f"{sinapum_base}/media/{img_path_clean}"
                    logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (variação 2): {url}")
                    return url
                
                # Variação 3: Apenas nome do arquivo (ex: "uuid.jpg")
                if '/' not in img_path_clean and '.' in img_path_clean:
                    # Verificar se parece ser um UUID ou nome de arquivo
                    if any(img_path_clean.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        url = f"{sinapum_base}/media/uploads/{img_path_clean}"
                        logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (variação 3): {url}")
                        return url
                
                # Variação 4: "media/{arquivo}" (sem uploads/)
                if img_path_clean.startswith('media/'):
                    url = f"{sinapum_base}/{img_path_clean}"
                    logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (variação 4): {url}")
                    return url
                
                # Variação 5: Path completo com "/media/uploads/"
                if '/media/uploads/' in img_path or '/media/uploads/' in img_path_clean:
                    # Extrair apenas a parte após /media/uploads/
                    if '/media/uploads/' in img_path:
                        filename = img_path.split('/media/uploads/')[-1]
                    else:
                        filename = img_path_clean.split('/media/uploads/')[-1]
                    url = f"{sinapum_base}/media/uploads/{filename}"
                    logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (variação 5): {url}")
                    return url
                
                # Variação 6: Se começa com "/media/" (com barra inicial)
                if img_path.startswith('/media/'):
                    url = f"{sinapum_base}{img_path}"
                    logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (variação 6): {url}")
                    return url
                
                # Variação 7: Path absoluto local (começa com / mas não é /media/)
                if img_path.startswith('/'):
                    # Se parece ser uma imagem, tentar adicionar /media
                    if '.' in img_path and any(img_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        url = f"{sinapum_base}/media{img_path}"
                        logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (variação 7): {url}")
                        return url
                    # Caso contrário, retornar como path local
                    logger.warning(f"[SHOPPER_PRODUCTS] Path absoluto não reconhecido: {img_path}")
                    return img_path
                
                # Fallback: adicionar media/uploads/ diretamente
                url = f"{sinapum_base}/media/uploads/{img_path_clean}"
                logger.info(f"[SHOPPER_PRODUCTS] Construindo URL (fallback): {url}")
                return url
            return None
            
            # 1. Tentar campo imagens (array) - priorizar image_url completo quando disponível
            imagens = produto_data.get('imagens', [])
            logger.info(f"[SHOPPER_PRODUCTS] Campo 'imagens' encontrado: {imagens} (tipo: {type(imagens)})")
            if imagens and isinstance(imagens, list):
                for idx, img in enumerate(imagens):
                    logger.info(f"[SHOPPER_PRODUCTS]   Processando imagem {idx + 1}: {img} (tipo: {type(img)})")
                    if isinstance(img, str):
                        # Se já é URL completa, usar diretamente; senão, construir
                        if img.startswith('http://') or img.startswith('https://'):
                            logger.info(f"[SHOPPER_PRODUCTS]     URL completa detectada, adicionando: {img}")
                            image_urls.append(img)
                        else:
                            logger.info(f"[SHOPPER_PRODUCTS]     Construindo URL a partir de: {img}")
                            url = build_image_url(img)
                            logger.info(f"[SHOPPER_PRODUCTS]     URL construída: {url}")
                            if url:
                                image_urls.append(url)
                    elif isinstance(img, dict):
                        # Se for objeto, priorizar image_url, depois url, src, path
                        # Formato esperado do SinapUm: { "image_url": "...", "image_path": "..." }
                        url = img.get('image_url') or img.get('url') or img.get('src') or img.get('path')
                        if url:
                            # Se já é URL completa, usar diretamente
                            if url.startswith('http://') or url.startswith('https://'):
                                image_urls.append(url)
                            else:
                                final_url = build_image_url(url)
                                if final_url:
                                    image_urls.append(final_url)
            
            # 2. Tentar campo imagem_original do modelo ProdutoJSON
            if not image_urls and produto_json.imagem_original:
                url = build_image_url(produto_json.imagem_original)
                if url:
                    image_urls.append(url)
            
            # 3. Tentar campo imagem (singular) no dados_json
            if not image_urls:
                imagem = produto_data.get('imagem') or produto_data.get('image')
                if imagem:
                    url = build_image_url(imagem)
                    if url:
                        image_urls.append(url)
            
            # 4. Verificar também em produto_viagem
            if not image_urls:
                produto_viagem = dados.get('produto_viagem', {})
                imagem_viagem = produto_viagem.get('imagem') or produto_viagem.get('image')
                if imagem_viagem:
                    url = build_image_url(imagem_viagem)
                    if url:
                        image_urls.append(url)
            
            # DEBUG: Log das URLs extraídas
            logger.info(f"[SHOPPER_PRODUCTS] image_urls extraídas: {image_urls}")
            logger.info(f"[SHOPPER_PRODUCTS] Total de URLs: {len(image_urls)}")
            
            # Extrair preço do produto_viagem se disponível
            produto_viagem = dados.get('produto_viagem', {})
            price = produto_viagem.get('preco_venda_brl') or produto_viagem.get('preco_venda_usd')
            currency = 'BRL' if produto_viagem.get('preco_venda_brl') else 'USD'
            
            # Criar objeto adaptado
            produto_adaptado = type('ProdutoAdaptado', (), {
            'id': produto_json.id,
            'name': produto_json.nome_produto,
            'brand': produto_json.marca or produto_data.get('marca', ''),
            'description': produto_data.get('descricao', ''),
            'category': produto_json.categoria or produto_data.get('categoria', ''),
            'image_urls': image_urls,  # Lista de URLs das imagens
            'price': price,
            'currency': currency,
            'is_available': True,  # ProdutoJSON sempre disponível por padrão
            'is_featured': False,  # ProdutoJSON não tem featured por padrão
            'group': produto_json.grupo_whatsapp,
            'estabelecimento': None,  # ProdutoJSON não tem estabelecimento direto
            'localizacao_especifica': None,
            'created_at': produto_json.criado_em,
                'dados_json': dados,  # Manter dados completos para acesso
            })()
            
            # DEBUG: Verificar objeto criado
            logger.info(f"[SHOPPER_PRODUCTS] Objeto criado - image_urls: {produto_adaptado.image_urls}, len: {len(produto_adaptado.image_urls) if produto_adaptado.image_urls else 0}")
            
            produtos_adaptados.append(produto_adaptado)
        except Exception as e:
            logger.error(f"[SHOPPER_PRODUCTS] Erro ao processar produto ID {produto_json.id}: {str(e)}", exc_info=True)
            # Continuar com próximo produto mesmo se houver erro
            continue
    
    # Substituir page_obj.object_list com produtos adaptados
    # Criar um objeto mock que simula o Page mas com produtos adaptados
    class AdaptedPage:
        def __init__(self, original_page, adapted_objects):
            self.original_page = original_page
            self.object_list = adapted_objects
            self.number = original_page.number
            self.paginator = original_page.paginator
            self.has_previous = original_page.has_previous
            self.has_next = original_page.has_next
            self.previous_page_number = original_page.previous_page_number
            self.next_page_number = original_page.next_page_number
        
        def __iter__(self):
            """Tornar o objeto iterável para uso em templates Django"""
            return iter(self.object_list)
        
        def __len__(self):
            """Retornar o tamanho da lista de objetos"""
            return len(self.object_list)
    
    page_obj = AdaptedPage(page_obj, produtos_adaptados)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'brand': brand,
        'availability': availability,
        'featured': featured,
        'group_id': group_id,
        'categories': categories,
        'brands': brands,
        'groups': groups,  # GRUPOS PARA O DROPDOWN - ESSENCIAL!
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
        
        # Buscar grupo (obrigatório)
        group_id = data.get('group_id')
        if not group_id:
            return JsonResponse({'error': 'Grupo é obrigatório para criar produto'}, status=400)
        group = get_object_or_404(WhatsappGroup, id=group_id, owner=request.user)
        
        # Buscar estabelecimento
        estabelecimento_id = data.get('estabelecimento_id')
        estabelecimento = None
        if estabelecimento_id:
            estabelecimento = get_object_or_404(Empresa, id=estabelecimento_id)
        
        # Buscar ou criar participante para o owner (obrigatório)
        # Usar telefone do usuário ou username como fallback
        phone = request.user.username
        if hasattr(request.user, 'cliente') and request.user.cliente.telefone:
            phone = request.user.cliente.telefone
        
        participant, _ = WhatsappParticipant.objects.get_or_create(
            group=group,
            phone=phone,
            defaults={
                'name': request.user.get_full_name() or request.user.username,
                'is_admin': True
            }
        )
        
        # Criar produto (message é opcional - None para produtos criados diretamente)
        product = WhatsappProduct.objects.create(
            name=name,
            description=data.get('description', ''),
            price=Decimal(data.get('price', 0)) if data.get('price') else None,
            currency=data.get('currency', 'USD'),
            brand=data.get('brand', ''),
            category=data.get('category', ''),
            group=group,
            posted_by=participant,  # OBRIGATÓRIO
            message=None,  # Opcional - None para produtos criados diretamente
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
