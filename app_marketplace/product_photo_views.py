"""
Views para cadastrar produtos por foto (inspirado no app de nutrição)
Fluxo: Foto → IA extrai dados → Formulário editável → Salvar
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
    WhatsappGroup, WhatsappParticipant, WhatsappProduct,
    Categoria, Empresa
)
from .ai_product_extractor import extract_product_data_from_image, format_evora_json, generate_sku_interno
import logging

logger = logging.getLogger(__name__)


@login_required
def product_photo_create(request):
    """
    Página para cadastrar produto por foto
    Inspirado no app de nutrição - similar ao fluxo de fotografia de refeições
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        messages.error(request, "Acesso restrito a Personal Shoppers ou Keepers.")
        return redirect('home')
    
    # Buscar grupos do usuário
    groups = WhatsappGroup.objects.filter(owner=request.user, active=True).order_by('-last_activity')
    
    # Buscar categorias
    categorias = Categoria.objects.all().order_by('nome')
    
    # Buscar empresas
    empresas = Empresa.objects.all().order_by('nome')[:20]
    
    context = {
        'groups': groups,
        'categorias': categorias,
        'empresas': empresas,
    }
    
    return render(request, 'app_marketplace/product_photo_create.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def detect_product_by_photo(request):
    """
    API para detectar produto por foto
    POST /api/produtos/detectar_por_foto/
    
    Similar ao app de nutrição: analisa foto e retorna dados sugeridos
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        # Verificar se há arquivo na requisição
        if 'image' not in request.FILES:
            return JsonResponse({
                'error': 'Imagem é obrigatória',
                'debug': {
                    'files_keys': list(request.FILES.keys()),
                    'content_type': request.content_type,
                }
            }, status=400)
        
        image_file = request.FILES['image']
        
        # Validar se o arquivo tem conteúdo
        if not image_file:
            return JsonResponse({'error': 'Arquivo de imagem vazio'}, status=400)
        
        # Validar tipo (pode ser None se o browser não enviar content_type)
        if hasattr(image_file, 'content_type') and image_file.content_type:
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'error': f'Arquivo deve ser uma imagem. Tipo recebido: {image_file.content_type}'}, status=400)
        
        # Validar tamanho (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'Imagem muito grande. Máximo 10MB'}, status=400)
        
        # Validar tamanho mínimo
        if image_file.size == 0:
            return JsonResponse({'error': 'Arquivo de imagem está vazio'}, status=400)
        
        # Salvar imagem temporariamente para análise e depois recuperar
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"produtos/temp/{request.user.id}/{timestamp}_temp.jpg"
        
        # Processar e otimizar imagem
        img = Image.open(image_file)
        
        # Converter para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Salvar imagem processada
        output = BytesIO()
        img.save(output, format='JPEG', quality=90, optimize=True)
        output.seek(0)
        
        saved_path = default_storage.save(temp_filename, ContentFile(output.read()))
        image_url = default_storage.url(saved_path)
        
        # Analisar imagem com IA
        image_file.seek(0)  # Resetar para ler novamente
        result = extract_product_data_from_image(image_file)
        
        if result.get('error'):
            return JsonResponse({
                'error': result['error'],
                'image_url': image_url  # Retornar URL mesmo se IA falhar
            }, status=400)
        
        # Verificar se tem dados
        if not result.get('success') or not result.get('data'):
            return JsonResponse({
                'error': 'Análise não retornou dados válidos. Verifique se o servidor OpenMind AI está funcionando.',
                'debug': result
            }, status=400)
        
        # Formatar dados no padrão ÉVORA
        ai_data = result['data']
        evora_json = format_evora_json(ai_data, image_url)
        
        # Retornar JSON ÉVORA completo + dados simplificados para formulário
        return JsonResponse({
            'success': True,
            'evora_json': evora_json,  # JSON completo no padrão ÉVORA
            'product_data': {
                # Dados simplificados para preencher formulário
                'nome_sugerido': evora_json.get('nome_produto', ''),
                'marca_sugerida': evora_json.get('caracteristicas', {}).get('marca', ''),
                'categoria_sugerida': evora_json.get('categoria', ''),
                'subcategoria_sugerida': evora_json.get('subcategoria', ''),
                'descricao_observacoes': evora_json.get('descricao', ''),
                'codigo_barras': evora_json.get('codigo_barras', ''),
                'sku_interno': evora_json.get('sku_interno', ''),
                'preco_visivel': ai_data.get('preco_visivel', ''),  # Se houver na embalagem
            },
            'image_url': image_url,  # URL da imagem salva para uso posterior
            'temp_path': saved_path  # Para referência
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Erro ao analisar imagem: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_product_from_photo(request):
    """
    API para salvar produto após análise de foto e edição
    POST /api/produtos/salvar_por_foto/
    
    Recebe dados editados e salva no banco
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validar campos obrigatórios
        name = data.get('name', '').strip()
        group_id = data.get('group_id')
        image_url = data.get('image_url')  # URL da imagem já salva
        
        if not name:
            return JsonResponse({'error': 'Nome do produto é obrigatório'}, status=400)
        
        if not group_id:
            return JsonResponse({'error': 'Grupo é obrigatório'}, status=400)
        
        if not image_url:
            return JsonResponse({'error': 'Imagem é obrigatória'}, status=400)
        
        # Buscar grupo
        group = WhatsappGroup.objects.filter(id=group_id, owner=request.user).first()
        if not group:
            return JsonResponse({'error': 'Grupo não encontrado ou sem permissão'}, status=404)
        
        # Se a imagem está em temp, mover para definitivo
        if 'temp' in image_url:
            # Criar nome definitivo
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            final_filename = f"produtos/{request.user.id}/{timestamp}_{name[:50].replace(' ', '_')}.jpg"
            
            # Ler arquivo temporário e salvar no definitivo
            temp_path = image_url.replace(settings.MEDIA_URL, '')
            if default_storage.exists(temp_path):
                with default_storage.open(temp_path, 'rb') as temp_file:
                    final_path = default_storage.save(final_filename, temp_file)
                    final_image_url = default_storage.url(final_path)
                    
                    # Deletar temporário
                    default_storage.delete(temp_path)
            else:
                final_image_url = image_url
        else:
            final_image_url = image_url
        
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
        
        # Processar preço
        price = data.get('price', '')
        try:
            price_decimal = Decimal(str(price).replace(',', '.')) if price else None
        except:
            price_decimal = None
        
        # Processar JSON ÉVORA se fornecido
        evora_json = data.get('evora_json', {})
        
        # Extrair dados do JSON ÉVORA ou usar dados diretos
        if evora_json:
            nome_final = evora_json.get('nome_produto', name)
            descricao_final = evora_json.get('descricao', data.get('description', ''))
            categoria_final = evora_json.get('categoria', data.get('category', ''))
            caracteristicas = evora_json.get('caracteristicas', {})
            marca_final = caracteristicas.get('marca', data.get('brand', ''))
            codigo_barras_final = evora_json.get('codigo_barras', data.get('codigo_barras', ''))
            sku_final = evora_json.get('sku_interno', data.get('sku', ''))
        else:
            nome_final = name
            descricao_final = data.get('description', '')
            categoria_final = data.get('category', '')
            marca_final = data.get('brand', '')
            codigo_barras_final = data.get('codigo_barras', '')
            sku_final = data.get('sku', '')
        
        # Criar produto
        product = WhatsappProduct.objects.create(
            group=group,
            name=nome_final,
            description=descricao_final,
            price=price_decimal,
            currency=data.get('currency', 'BRL'),
            brand=marca_final,
            category=categoria_final,
            image_urls=[final_image_url],  # Imagem salva e recuperável
            posted_by=participant,
            message=None,
            is_available=True,
            is_featured=data.get('is_featured', False),
            codigo_barras=codigo_barras_final,
            sku_loja=sku_final,
        )
        
        # Se empresa_id foi fornecido, vincular
        empresa_id = data.get('empresa_id')
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
                'image_url': final_image_url,
                'group_id': group.id,
                'group_name': group.name
            },
            'message': 'Produto criado com sucesso!'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Erro ao criar produto: {str(e)}'
        }, status=500)

