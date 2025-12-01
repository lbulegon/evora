"""
Views para captura de foto de produtos via PWA
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json
import os
from PIL import Image
from io import BytesIO

from .models import (
    PersonalShopper, WhatsappGroup, WhatsappParticipant,
    WhatsappProduct, Categoria, Empresa, Produto
)


@login_required
def product_camera(request):
    """
    Página principal para fotografar produtos
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito a Personal Shoppers ou Keepers.")
        return redirect('home')
    
    # Buscar grupos do usuário para o formulário
    groups = WhatsappGroup.objects.filter(owner=request.user, active=True).order_by('-last_activity')
    
    # Buscar categorias
    categorias = Categoria.objects.all().order_by('nome')
    
    # Buscar empresas/estabelecimentos
    empresas = Empresa.objects.all().order_by('nome')[:20]
    
    context = {
        'groups': groups,
        'categorias': categorias,
        'empresas': empresas,
    }
    
    return render(request, 'app_marketplace/product_camera.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_product_photo(request):
    """
    API para receber foto do produto e criar registro
    POST /api/products/upload-photo/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        # Verificar se é multipart/form-data (upload de arquivo)
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Processar FormData
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price', '').strip()
            currency = request.POST.get('currency', 'BRL')
            brand = request.POST.get('brand', '').strip()
            category = request.POST.get('category', '').strip()
            group_id = request.POST.get('group_id')
            empresa_id = request.POST.get('empresa_id')
            
            if not name:
                return JsonResponse({'error': 'Nome do produto é obrigatório'}, status=400)
            
            if not group_id:
                return JsonResponse({'error': 'Grupo é obrigatório'}, status=400)
            
            # Buscar grupo
            group = WhatsappGroup.objects.filter(id=group_id, owner=request.user).first()
            if not group:
                return JsonResponse({'error': 'Grupo não encontrado ou sem permissão'}, status=404)
            
            # Processar imagem
            image_file = None
            image_url = None
            
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                
                # Validar tipo de arquivo
                if not image_file.content_type.startswith('image/'):
                    return JsonResponse({'error': 'Arquivo deve ser uma imagem'}, status=400)
                
                # Validar tamanho (max 10MB)
                if image_file.size > 10 * 1024 * 1024:
                    return JsonResponse({'error': 'Imagem muito grande. Máximo 10MB'}, status=400)
                
                # Processar e otimizar imagem
                try:
                    # Ler imagem
                    img = Image.open(image_file)
                    
                    # Converter para RGB se necessário (para JPEG)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background
                    
                    # Redimensionar se muito grande (max 1920x1920)
                    max_size = 1920
                    if img.width > max_size or img.height > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Salvar imagem otimizada
                    output = BytesIO()
                    img.save(output, format='JPEG', quality=85, optimize=True)
                    output.seek(0)
                    
                    # Criar nome do arquivo
                    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"produtos/{request.user.id}/{timestamp}_{name[:50].replace(' ', '_')}.jpg"
                    
                    # Salvar usando default_storage
                    saved_path = default_storage.save(filename, ContentFile(output.read()))
                    image_url = default_storage.url(saved_path)
                    
                except Exception as e:
                    return JsonResponse({'error': f'Erro ao processar imagem: {str(e)}'}, status=400)
            
            # Buscar ou criar participante
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
            
            # Criar produto
            product = WhatsappProduct.objects.create(
                group=group,
                name=name,
                description=description,
                price=Decimal(price) if price else None,
                currency=currency,
                brand=brand,
                category=category,
                image_urls=[image_url] if image_url else [],
                posted_by=participant,
                message=None,
                is_available=True,
                is_featured=False
            )
            
            # Se empresa_id foi fornecido, vincular
            if empresa_id:
                try:
                    empresa = Empresa.objects.get(id=empresa_id)
                    product.estabelecimento = empresa
                    product.save()
                except Empresa.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': str(product.price) if product.price else None,
                    'image_url': image_url,
                    'group_id': group.id,
                    'group_name': group.name
                },
                'message': 'Produto criado com sucesso!'
            })
        
        else:
            # JSON (fallback ou dados offline)
            data = json.loads(request.body)
            return JsonResponse({
                'error': 'Use multipart/form-data para upload de imagem',
                'hint': 'Envie como FormData com campo "image"'
            }, status=400)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Erro ao criar produto: {str(e)}'
        }, status=500)

