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
import requests
from PIL import Image
from io import BytesIO

from .models import (
    WhatsappGroup, WhatsappParticipant,
    Categoria, Empresa, ProdutoJSON
)
from .services import analyze_image_with_openmind, analyze_multiple_images
from .utils import transform_evora_to_modelo_json
from pathlib import Path
import uuid
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
def verificar_produto_fotos(request):
    """
    API para verificar se múltiplas fotos são do mesmo produto (primeira análise).
    POST /api/produtos/verificar_produto/
    
    Recebe múltiplas imagens e verifica se são do mesmo produto.
    Não gera JSON completo, apenas verifica consistência.
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        # Verificar se há imagens na requisição
        if 'images' in request.FILES:
            image_files = request.FILES.getlist('images')
        elif 'image' in request.FILES:
            image_files = [request.FILES['image']]
        else:
            return JsonResponse({
                'error': 'Imagens são obrigatórias',
                'debug': {
                    'files_keys': list(request.FILES.keys()),
                }
            }, status=400)
        
        if not image_files:
            return JsonResponse({'error': 'Nenhuma imagem fornecida'}, status=400)
        
        # Validar tipos de arquivo
        for image_file in image_files:
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'error': f'O arquivo "{image_file.name}" deve ser uma imagem.'}, status=400)
        
        # Processar imagens em memória (sem salvar)
        processed_images = []
        for image_file in image_files:
            # Processar e otimizar imagem em memória
            img = Image.open(image_file)
            
            # Converter para RGB se necessário
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Salvar imagem processada em memória
            output = BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Criar arquivo em memória para envio
            from django.core.files.uploadedfile import InMemoryUploadedFile
            from django.core.files.base import ContentFile
            
            processed_file = InMemoryUploadedFile(
                ContentFile(output.read()),
                None,
                image_file.name,
                'image/jpeg',
                output.tell(),
                None
            )
            
            processed_images.append(processed_file)
        
        # Verificar se são do mesmo produto (análise rápida)
        # Passar usuário para detectar idioma
        result = analyze_multiple_images(processed_images, user=request.user)
        
        # Extrair URLs das imagens salvas no SinapUm (para reutilizar na análise completa)
        image_urls = []
        image_paths = []
        saved_filenames = []
        
        if result.get('analises_individuais'):
            for analise in result['analises_individuais']:
                analise_result = analise.get('result', {})
                if analise_result.get('image_url'):
                    image_urls.append(analise_result['image_url'])
                if analise_result.get('image_path'):
                    image_paths.append(analise_result['image_path'])
                if analise_result.get('saved_filename'):
                    saved_filenames.append(analise_result['saved_filename'])
        
        # Retornar informações de verificação + URLs das imagens salvas
        return JsonResponse({
            'success': True,
            'mesmo_produto': result.get('mesmo_produto', False),
            'consistencia': result.get('consistencia', {}),
            'total_imagens': len(processed_images),
            'aviso': result.get('aviso'),
            'produtos_identificados': len(result.get('produtos_diferentes', [])) if not result.get('mesmo_produto') else 1,
            # URLs das imagens salvas no SinapUm (para reutilizar)
            'image_urls': image_urls,
            'image_paths': image_paths,
            'saved_filenames': saved_filenames
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao verificar produto: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'Erro ao verificar produto: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def analise_completa_produto(request):
    """
    API para análise completa de múltiplas fotos do mesmo produto (segunda análise).
    POST /api/produtos/analise_completa/
    
    Recebe múltiplas imagens do mesmo produto e gera JSON completo.
    Pode receber:
    - images[] (arquivos) - se for primeira vez
    - image_urls[] (JSON) - se as imagens já foram salvas no SinapUm (otimização)
    """
    logger.info(f"[ANALISE_COMPLETA] Iniciando - Usuário: {request.user.id} ({request.user.username})")
    logger.info(f"[ANALISE_COMPLETA] Content-Type: {request.content_type}")
    logger.info(f"[ANALISE_COMPLETA] Método: {request.method}")
    logger.info(f"[ANALISE_COMPLETA] FILES keys: {list(request.FILES.keys())}")
    
    if not (request.user.is_shopper or request.user.is_address_keeper):
        logger.warning(f"[ANALISE_COMPLETA] Acesso negado - Usuário: {request.user.id}")
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        # Verificar se recebeu URLs das imagens já salvas (otimização)
        data = {}
        if request.content_type and 'application/json' in request.content_type:
            try:
                logger.info(f"[ANALISE_COMPLETA] Lendo JSON do body - Tamanho: {len(request.body)} bytes")
                data = json.loads(request.body)
                logger.info(f"[ANALISE_COMPLETA] JSON parseado - Chaves: {list(data.keys())}")
            except Exception as e:
                logger.warning(f"[ANALISE_COMPLETA] Erro ao parsear JSON: {str(e)}")
                pass
        
        image_urls = data.get('image_urls', [])
        image_paths = data.get('image_paths', [])
        logger.info(f"[ANALISE_COMPLETA] image_urls: {len(image_urls)}, image_paths: {len(image_paths)}")
        
        # Se tiver URLs, baixar imagens do SinapUm e usar (evita reenvio)
        if image_urls or image_paths:
            logger.info(f"[ANALISE_COMPLETA] Usando URLs já salvas: {len(image_urls or image_paths)} imagens")
            urls_to_use = image_urls if image_urls else image_paths
            # Construir URLs completas se necessário
            urls_completas = []
            for url in urls_to_use:
                if url.startswith('http'):
                    urls_completas.append(url)
                else:
                    # Se for path relativo, construir URL completa
                    base_url = getattr(settings, 'OPENMIND_AI_URL', 'http://127.0.0.1:8001')
                    if '/api/v1' in base_url:
                        base_url = base_url.replace('/api/v1', '')
                    urls_completas.append(f"{base_url}/{url.lstrip('/')}")
            
            # Baixar imagens das URLs e fazer análise
            try:
                from django.core.files.uploadedfile import InMemoryUploadedFile
                from django.core.files.base import ContentFile
                
                downloaded_images = []
                for idx, url in enumerate(urls_completas):
                    logger.info(f"Baixando imagem {idx + 1}/{len(urls_completas)} de {url}")
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        # Criar arquivo em memória
                        file_obj = InMemoryUploadedFile(
                            ContentFile(response.content),
                            None,
                            f"image_{idx}.jpg",
                            'image/jpeg',
                            len(response.content),
                            None
                        )
                        downloaded_images.append(file_obj)
                    else:
                        logger.warning(f"Erro ao baixar imagem {url}: status {response.status_code}")
                
                if downloaded_images:
                    # Usar imagens baixadas para análise
                    processed_images = downloaded_images
                else:
                    return JsonResponse({'error': 'Erro ao baixar imagens das URLs'}, status=400)
            except Exception as e:
                logger.error(f"Erro ao baixar imagens: {str(e)}", exc_info=True)
                return JsonResponse({'error': f'Erro ao baixar imagens: {str(e)}'}, status=500)
        
        # Caso contrário, receber arquivos normalmente
        if 'images' in request.FILES:
            image_files = request.FILES.getlist('images')
            logger.info(f"[ANALISE_COMPLETA] Recebidos {len(image_files)} arquivos via 'images'")
        elif 'image' in request.FILES:
            image_files = [request.FILES['image']]
            logger.info(f"[ANALISE_COMPLETA] Recebido 1 arquivo via 'image'")
        else:
            logger.error(f"[ANALISE_COMPLETA] Nenhuma imagem fornecida - FILES keys: {list(request.FILES.keys())}")
            return JsonResponse({
                'error': 'Imagens são obrigatórias (arquivos ou URLs)',
                'debug': {
                    'files_keys': list(request.FILES.keys()),
                }
            }, status=400)
        
        if not image_files:
            logger.error("[ANALISE_COMPLETA] image_files está vazio")
            return JsonResponse({'error': 'Nenhuma imagem fornecida'}, status=400)
        
        logger.info(f"[ANALISE_COMPLETA] Processando {len(image_files)} imagens")
        
        # Validar tipos de arquivo
        for image_file in image_files:
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'error': f'O arquivo "{image_file.name}" deve ser uma imagem.'}, status=400)
        
        # Processar imagens em memória (sem salvar)
        processed_images = []
        for image_file in image_files:
            # Processar e otimizar imagem em memória
            img = Image.open(image_file)
            
            # Converter para RGB se necessário
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Salvar imagem processada em memória
            output = BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Criar arquivo em memória para envio
            from django.core.files.uploadedfile import InMemoryUploadedFile
            from django.core.files.base import ContentFile
            
            processed_file = InMemoryUploadedFile(
                ContentFile(output.read()),
                None,
                image_file.name,
                'image/jpeg',
                output.tell(),
                None
            )
            
            processed_images.append(processed_file)
        
        # Análise completa (gera JSON)
        if len(processed_images) == 1:
            # Uma única imagem
            image_file = processed_images[0]
            image_file.seek(0)
            result = analyze_image_with_openmind(image_file, user=request.user)
            
            produto_data = result.get('data', {})
            image_url_from_sinapum = result.get('image_url')
            image_path_from_sinapum = result.get('image_path')
            
            # Corrigir URL malformada (ex: mediauploads -> media/uploads)
            if image_url_from_sinapum and 'mediauploads' in image_url_from_sinapum:
                image_url_from_sinapum = image_url_from_sinapum.replace('mediauploads', 'media/uploads')
            
            # Se image_url estiver incorreto ou ausente, construir a partir do image_path
            if image_path_from_sinapum and (not image_url_from_sinapum or 'mediauploads' in image_url_from_sinapum):
                from django.conf import settings
                openmind_url = getattr(settings, 'OPENMIND_AI_URL', 'http://127.0.0.1:8001')
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                # Garantir que image_path começa com media/
                if image_path_from_sinapum.startswith('media/'):
                    image_url_from_sinapum = f"{sinapum_base}/{image_path_from_sinapum}"
                elif image_path_from_sinapum.startswith('/media/'):
                    image_url_from_sinapum = f"{sinapum_base}{image_path_from_sinapum}"
                else:
                    # Adicionar media/ se não tiver
                    image_url_from_sinapum = f"{sinapum_base}/media/{image_path_from_sinapum.lstrip('/')}"
            saved_filename = result.get('saved_filename')
            
            # Garantir que o array de imagens existe
            if produto_data and result.get('success'):
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    image_path_for_json = image_path_from_sinapum or image_url_from_sinapum
                    if image_path_for_json and image_path_for_json not in produto_data['produto']['imagens']:
                        produto_data['produto']['imagens'].insert(0, image_path_for_json)
                    if not produto_data['produto']['imagens'] and image_path_for_json:
                        produto_data['produto']['imagens'] = [image_path_for_json]
            
            return JsonResponse({
                'success': True,
                'produto_json': produto_data,
                'image_url': image_url_from_sinapum or '',
                'image_path': image_path_from_sinapum or '',
                'saved_filename': saved_filename or '',
                'total_imagens': 1
            })
        else:
            # Múltiplas imagens - análise completa
            result = analyze_multiple_images(processed_images, user=request.user)
            
            # Extrair informações das imagens retornadas pelo SinapUm
            image_urls = []
            image_paths = []
            saved_filenames = []
            
            if result.get('analises_individuais'):
                from django.conf import settings
                openmind_url = getattr(settings, 'OPENMIND_AI_URL', 'http://127.0.0.1:8001')
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                
                for analise in result['analises_individuais']:
                    analise_result = analise.get('result', {})
                    img_url = analise_result.get('image_url')
                    img_path = analise_result.get('image_path')
                    
                    # Corrigir URL malformada (ex: mediauploads -> media/uploads)
                    if img_url and 'mediauploads' in img_url:
                        img_url = img_url.replace('mediauploads', 'media/uploads')
                    
                    # Se image_url estiver incorreto ou ausente, construir a partir do image_path
                    if img_path and (not img_url or 'mediauploads' in img_url):
                        # Garantir que image_path começa com media/
                        if img_path.startswith('media/'):
                            img_url = f"{sinapum_base}/{img_path}"
                        elif img_path.startswith('/media/'):
                            img_url = f"{sinapum_base}{img_path}"
                        else:
                            # Adicionar media/ se não tiver
                            img_url = f"{sinapum_base}/media/{img_path.lstrip('/')}"
                    
                    if img_url:
                        image_urls.append(img_url)
                    if img_path:
                        image_paths.append(img_path)
                    if analise_result.get('saved_filename'):
                        saved_filenames.append(analise_result['saved_filename'])
            
            # Usar image_paths (relativos) preferencialmente no JSON do produto
            image_paths_for_json = image_paths if image_paths else image_urls
            
            # Adicionar caminhos das imagens salvas no SinapUm
            if result.get('mesmo_produto') and result.get('produto_consolidado'):
                produto_data = result['produto_consolidado']
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    for img_path in image_paths_for_json:
                        if img_path and img_path not in produto_data['produto']['imagens']:
                            produto_data['produto']['imagens'].append(img_path)
            else:
                # Produtos diferentes - usar primeiro produto como base
                produto_data = result.get('produtos_diferentes', [{}])[0].get('produto_data', {}) if result.get('produtos_diferentes') else {}
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    for img_path in image_paths_for_json:
                        if img_path and img_path not in produto_data['produto']['imagens']:
                            produto_data['produto']['imagens'].append(img_path)
            
            return JsonResponse({
                'success': True,
                'produto_json': produto_data,
                'mesmo_produto': result.get('mesmo_produto', False),
                'image_urls': image_urls,
                'image_paths': image_paths,
                'saved_filenames': saved_filenames,
                'total_imagens': len(processed_images),
                'aviso': result.get('aviso')
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro na análise completa: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'Erro na análise completa: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def detect_product_by_photo(request):
    """
    API para detectar produto por foto (suporta múltiplas imagens)
    POST /api/produtos/detectar_por_foto/
    
    Adaptado das melhorias do SinapUm: usa OpenMind AI melhorado e suporta múltiplas imagens
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        # Verificar se há imagens na requisição (suporta múltiplas)
        if 'images' in request.FILES:
            image_files = request.FILES.getlist('images')
        elif 'image' in request.FILES:
            # Fallback para compatibilidade com upload único
            image_files = [request.FILES['image']]
        else:
            return JsonResponse({
                'error': 'Imagem é obrigatória',
                'debug': {
                    'files_keys': list(request.FILES.keys()),
                    'content_type': request.content_type,
                }
            }, status=400)
        
        if not image_files:
            return JsonResponse({'error': 'Nenhuma imagem fornecida'}, status=400)
        
        # Validar tipos de arquivo
        for image_file in image_files:
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'error': f'O arquivo "{image_file.name}" deve ser uma imagem.'}, status=400)
        
        # NÃO salvar imagens localmente - serão salvas no SinapUm
        # Preparar imagens para envio (sem salvar)
        saved_images = []  # Lista de imagens preparadas (sem salvar localmente)
        
        for image_file in image_files:
            # Processar e otimizar imagem em memória (sem salvar)
            img = Image.open(image_file)
            
            # Converter para RGB se necessário
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Salvar imagem processada em memória
            output = BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Criar arquivo em memória para envio
            from django.core.files.uploadedfile import InMemoryUploadedFile
            from django.core.files.base import ContentFile
            
            processed_file = InMemoryUploadedFile(
                ContentFile(output.read()),
                None,
                image_file.name,
                'image/jpeg',
                output.tell(),
                None
            )
            
            saved_images.append({
                'file': processed_file,
                'filename': image_file.name,
                'original_file': image_file  # Manter referência ao original
            })
        
        # Analisar imagens
        if len(saved_images) == 1:
            # Uma única imagem - usar método simples
            image_file = saved_images[0]['file']
            image_file.seek(0)
            result = analyze_image_with_openmind(image_file, user=request.user)
            
            produto_data = result.get('data', {})
            # Extrair informações da imagem retornada pelo SinapUm
            image_url_from_sinapum = result.get('image_url')  # URL completa
            image_path_from_sinapum = result.get('image_path')  # Caminho relativo (preferido para JSON)
            saved_filename = result.get('saved_filename')  # Nome do arquivo salvo
            
            # Corrigir URL malformada (ex: mediauploads -> media/uploads)
            if image_url_from_sinapum and 'mediauploads' in image_url_from_sinapum:
                image_url_from_sinapum = image_url_from_sinapum.replace('mediauploads', 'media/uploads')
            
            # Se image_url estiver incorreto ou ausente, construir a partir do image_path
            if image_path_from_sinapum and (not image_url_from_sinapum or 'mediauploads' in image_url_from_sinapum):
                from django.conf import settings
                openmind_url = getattr(settings, 'OPENMIND_AI_URL', 'http://127.0.0.1:8001')
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                # Garantir que image_path começa com media/
                if image_path_from_sinapum.startswith('media/'):
                    image_url_from_sinapum = f"{sinapum_base}/{image_path_from_sinapum}"
                elif image_path_from_sinapum.startswith('/media/'):
                    image_url_from_sinapum = f"{sinapum_base}{image_path_from_sinapum}"
                else:
                    # Adicionar media/ se não tiver
                    image_url_from_sinapum = f"{sinapum_base}/media/{image_path_from_sinapum.lstrip('/')}"
            
            # Usar image_path (relativo) no JSON do produto, image_url para acesso/exibição
            image_path_for_json = image_path_from_sinapum or image_url_from_sinapum
            
            # Transformar e adicionar caminho da imagem
            if produto_data and result.get('success'):
                # Se os dados já estão no formato modelo.json, não precisa transformar
                if 'produto' not in produto_data or 'produto_generico_catalogo' not in produto_data:
                    produto_data = transform_evora_to_modelo_json(
                        produto_data,
                        image_filename=image_file.name,
                        image_path=image_path_for_json  # Usar image_path (relativo) preferencialmente
                    )
                
                # Garantir que o array de imagens existe e contém a imagem atual
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    # Adicionar image_path (relativo) preferencialmente, ou image_url se não houver
                    if image_path_for_json:
                        if image_path_for_json not in produto_data['produto']['imagens']:
                            produto_data['produto']['imagens'].insert(0, image_path_for_json)
                    # Se o array estiver vazio, garantir que tem pelo menos esta imagem
                    if not produto_data['produto']['imagens'] and image_path_for_json:
                        produto_data['produto']['imagens'] = [image_path_for_json]
            
            # Preparar imagens para JSON (usando informações do SinapUm)
            saved_images_json = [{
                'filename': saved_images[0]['filename'],
                'image_url': image_url_from_sinapum or '',  # URL completa para exibição
                'image_path': image_path_from_sinapum or '',  # Caminho relativo para JSON
                'saved_filename': saved_filename or '',
                'saved_on': 'sinapum' if image_url_from_sinapum else 'none'
            }]
            
            # Extrair dados simplificados para formulário
            produto = produto_data.get('produto', {}) if produto_data else {}
            product_data = {
                'nome_sugerido': produto.get('nome', ''),
                'marca_sugerida': produto.get('marca', ''),
                'categoria_sugerida': produto.get('categoria', ''),
                'subcategoria_sugerida': produto.get('subcategoria', ''),
                'descricao_observacoes': produto.get('descricao', ''),
                'codigo_barras': produto.get('codigo_barras', ''),
                'preco_visivel': produto_data.get('produto_viagem', {}).get('preco_venda_brl', ''),
            }
            
            return JsonResponse({
                'success': True,
                'produto_json': produto_data,  # JSON completo no formato modelo.json
                'product_data': product_data,  # Dados simplificados para formulário
                'image_url': image_url_from_sinapum or '',  # URL completa do SinapUm (para exibição)
                'image_path': image_path_from_sinapum or '',  # Caminho relativo (para JSON)
                'saved_filename': saved_filename or '',  # Nome do arquivo salvo
                'saved_images': saved_images_json,
                'multiple_images': False
            })
        else:
            # Múltiplas imagens - usar análise comparativa
            image_files_list = [img['file'] for img in saved_images]
            result = analyze_multiple_images(image_files_list, user=request.user)
            
            # Extrair informações das imagens retornadas pelo SinapUm
            image_urls = []  # URLs completas (para exibição)
            image_paths = []  # Caminhos relativos (para JSON do produto)
            saved_filenames = []  # Nomes dos arquivos salvos
            
            if result.get('analises_individuais'):
                for analise in result['analises_individuais']:
                    analise_result = analise.get('result', {})
                    if analise_result.get('image_url'):
                        image_urls.append(analise_result['image_url'])
                    if analise_result.get('image_path'):
                        image_paths.append(analise_result['image_path'])
                    if analise_result.get('saved_filename'):
                        saved_filenames.append(analise_result['saved_filename'])
            
            # Usar image_paths (relativos) preferencialmente no JSON do produto
            image_paths_for_json = image_paths if image_paths else image_urls
            
            # Adicionar caminhos das imagens salvas no SinapUm
            if result.get('mesmo_produto') and result.get('produto_consolidado'):
                produto_data = result['produto_consolidado']
                # Adicionar todos os caminhos retornados pelo SinapUm
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    # Adicionar image_paths (relativos) preferencialmente
                    for img_path in image_paths_for_json:
                        if img_path and img_path not in produto_data['produto']['imagens']:
                            produto_data['produto']['imagens'].append(img_path)
                # Se não tiver produto, criar estrutura básica
                elif not produto_data:
                    produto_data = {
                        'produto': {
                            'imagens': image_paths_for_json
                        }
                    }
            else:
                # Produtos diferentes - usar primeiro produto como base e adicionar todas as imagens
                produto_data = result.get('produtos_diferentes', [{}])[0].get('produto_data', {}) if result.get('produtos_diferentes') else {}
                # Garantir que todas as imagens estão no array
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    # Adicionar image_paths (relativos) preferencialmente
                    for img_path in image_paths_for_json:
                        if img_path and img_path not in produto_data['produto']['imagens']:
                            produto_data['produto']['imagens'].append(img_path)
                else:
                    # Criar estrutura básica com todas as imagens
                    produto_data = {
                        'produto': {
                            'imagens': image_paths_for_json
                        }
                    }
            
            # Preparar imagens para JSON (usando informações do SinapUm)
            saved_images_for_template = []
            for idx, img_info in enumerate(saved_images):
                img_url = image_urls[idx] if idx < len(image_urls) else ''
                img_path = image_paths[idx] if idx < len(image_paths) else ''
                saved_filename = saved_filenames[idx] if idx < len(saved_filenames) else ''
                saved_images_for_template.append({
                    'filename': img_info['filename'],
                    'image_url': img_url,  # URL completa do SinapUm (para exibição)
                    'image_path': img_path,  # Caminho relativo (para JSON)
                    'saved_filename': saved_filename,  # Nome do arquivo salvo
                    'saved_on': 'sinapum' if img_url else 'none'
                })
            
            # Extrair dados simplificados para formulário
            produto = produto_data.get('produto', {}) if produto_data else {}
            product_data = {
                'nome_sugerido': produto.get('nome', ''),
                'marca_sugerida': produto.get('marca', ''),
                'categoria_sugerida': produto.get('categoria', ''),
                'subcategoria_sugerida': produto.get('subcategoria', ''),
                'descricao_observacoes': produto.get('descricao', ''),
                'codigo_barras': produto.get('codigo_barras', ''),
                'preco_visivel': produto_data.get('produto_viagem', {}).get('preco_venda_brl', ''),
            }
            
            return JsonResponse({
                'success': True,
                'produto_json': produto_data,  # JSON completo no formato modelo.json
                'product_data': product_data,  # Dados simplificados para formulário
                'saved_images': saved_images_for_template,
                'multiple_images': True,
                'mesmo_produto': result.get('mesmo_produto', False),
                'consistencia': result.get('consistencia', {}),
                'aviso': result.get('aviso')
            })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao analisar imagem: {str(e)}", exc_info=True)
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
            codigo_barras_final = (evora_json.get('codigo_barras', data.get('codigo_barras', '')) or '').strip() or None
            sku_final = evora_json.get('sku_interno', data.get('sku', ''))
        else:
            nome_final = name
            descricao_final = data.get('description', '')
            categoria_final = data.get('category', '')
            marca_final = data.get('brand', '')
            codigo_barras_final = (data.get('codigo_barras', '') or '').strip() or None
            sku_final = data.get('sku', '')
        
        # Criar ProdutoJSON
        empresa_id = data.get('empresa_id')
        produto_payload = {
            'nome': nome_final,
            'descricao': descricao_final,
            'preco': float(price_decimal) if price_decimal is not None else None,
            'moeda': data.get('currency', 'BRL'),
            'categoria': categoria_final,
            'marca': marca_final,
            'imagens': [final_image_url] if final_image_url else [],
            'codigo_barras': codigo_barras_final,
            'sku': sku_final,
            'estabelecimento_id': empresa_id,
            'is_featured': data.get('is_featured', False),
            'is_available': True,
            'localizacao_especifica': data.get('localizacao_especifica', ''),
        }
        
        dados_json = {'produto': produto_payload}
        
        produto = ProdutoJSON.objects.create(
            dados_json=dados_json,
            nome_produto=nome_final,
            marca=marca_final,
            categoria=categoria_final,
            codigo_barras=codigo_barras_final,
            imagem_original=final_image_url,
            criado_por=request.user,
            grupo_whatsapp=group
        )
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': produto.id,
                'name': produto.nome_produto,
                'price': str(price_decimal) if price_decimal else None,
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_product_json(request):
    """
    View para salvar produto no banco de dados em formato JSON (PostgreSQL JSONB)
    Adaptado das melhorias do SinapUm
    """
    logger.info(f"[SAVE_PRODUCT] Iniciando salvamento - Usuário: {request.user.id} ({request.user.username})")
    
    if not (request.user.is_shopper or request.user.is_address_keeper):
        logger.warning(f"[SAVE_PRODUCT] Acesso negado - Usuário: {request.user.id}")
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        logger.info(f"[SAVE_PRODUCT] Lendo body da requisição - Tamanho: {len(request.body)} bytes")
        data = json.loads(request.body)
        logger.info(f"[SAVE_PRODUCT] JSON parseado - Chaves: {list(data.keys())}")
        
        produto_json = data.get('produto_json')
        
        if not produto_json:
            logger.error("[SAVE_PRODUCT] produto_json não fornecido nos dados")
            return JsonResponse({
                'success': False,
                'error': 'Dados do produto não fornecidos'
            }, status=400)
        
        logger.info(f"[SAVE_PRODUCT] produto_json recebido - Tipo: {type(produto_json)}, Tem 'produto': {'produto' in produto_json if isinstance(produto_json, dict) else False}")
        
        # Log completo do produto_json para debug
        import json as json_module
        logger.info(f"[SAVE_PRODUCT] produto_json completo (primeiros 2000 chars): {json_module.dumps(produto_json, indent=2, ensure_ascii=False)[:2000]}")
        logger.info(f"[SAVE_PRODUCT] produto_json tem campo 'analise_ia': {'analise_ia' in produto_json if isinstance(produto_json, dict) else False}")
        if isinstance(produto_json, dict) and 'analise_ia' in produto_json:
            logger.info(f"[SAVE_PRODUCT] analise_ia chaves: {list(produto_json['analise_ia'].keys()) if isinstance(produto_json['analise_ia'], dict) else 'não é dict'}")
            logger.info(f"[SAVE_PRODUCT] analise_ia completo: {json_module.dumps(produto_json['analise_ia'], indent=2, ensure_ascii=False)[:1500]}")
        
        # Extrair informações básicas para indexação
        produto = produto_json.get('produto', {})
        nome_produto = produto.get('nome', 'Produto sem nome')
        marca = produto.get('marca')
        categoria = produto.get('categoria')
        codigo_barras = (produto.get('codigo_barras') or '').strip() or None
        
        # Extrair preço e estoque do formulário se fornecidos
        preco = data.get('price')
        estoque = data.get('estoque')
        
        # Atualizar JSON com preço e estoque se fornecidos
        if preco:
            try:
                preco_decimal = Decimal(str(preco))
                # Adicionar preço no produto_viagem se não existir
                if 'produto_viagem' not in produto_json:
                    produto_json['produto_viagem'] = {}
                produto_json['produto_viagem']['preco_venda_brl'] = str(preco_decimal)
                # Também adicionar no produto se não existir
                if 'preco' not in produto:
                    produto['preco'] = str(preco_decimal)
            except (ValueError, TypeError):
                logger.warning(f"[SAVE_PRODUCT] Erro ao processar preço: {preco}")
        
        if estoque:
            try:
                estoque_int = int(estoque)
                produto['estoque'] = estoque_int
            except (ValueError, TypeError):
                logger.warning(f"[SAVE_PRODUCT] Erro ao processar estoque: {estoque}")
        
        logger.info(f"[SAVE_PRODUCT] Dados extraídos - Nome: {nome_produto}, Marca: {marca}, Categoria: {categoria}, Código: {codigo_barras}")
        
        # Obter caminho da imagem (primeira imagem do array para referência)
        # Todas as imagens estão no array produto['imagens']
        imagem_original = None
        
        # Verificar se tem array de imagens
        imagens = produto.get('imagens')
        logger.info(f"[SAVE_PRODUCT] produto.get('imagens'): {imagens}")
        logger.info(f"[SAVE_PRODUCT] Tipo de imagens: {type(imagens)}")
        
        if imagens:
            if isinstance(imagens, list) and len(imagens) > 0:
                # Usar primeira imagem do array como referência principal
                imagem_original = imagens[0]
                logger.info(f"[SAVE_PRODUCT] ✓ Imagem original encontrada no array (lista): {imagem_original}")
                logger.info(f"[SAVE_PRODUCT] ✓ Total de imagens no array: {len(imagens)}")
                logger.info(f"[SAVE_PRODUCT] ✓ Array completo de imagens: {imagens}")
            elif isinstance(imagens, str) and imagens.strip():
                # Se for string única
                imagem_original = imagens.strip()
                logger.info(f"[SAVE_PRODUCT] ✓ Imagem original encontrada (string): {imagem_original}")
            else:
                logger.warning(f"[SAVE_PRODUCT] ⚠ imagens existe mas está vazio ou em formato inesperado: {imagens}")
        elif produto_json.get('cadastro_meta', {}).get('fonte'):
            # Fallback: tentar extrair do campo fonte se não houver no array
            fonte = produto_json.get('cadastro_meta', {}).get('fonte', '')
            if 'imagem' in fonte.lower():
                imagem_original = fonte.split(':')[-1].strip() if ':' in fonte else fonte
                logger.info(f"[SAVE_PRODUCT] ✓ Imagem original extraída da fonte: {imagem_original}")
        
        if not imagem_original:
            logger.warning("[SAVE_PRODUCT] ⚠⚠⚠ Nenhuma imagem original encontrada no produto.imagens ou fonte")
            logger.warning(f"[SAVE_PRODUCT] ⚠ produto.get('imagens'): {produto.get('imagens')}")
            logger.warning(f"[SAVE_PRODUCT] ⚠ produto completo: {json_module.dumps(produto, indent=2, ensure_ascii=False)[:500]}")
        
        # Garantir que o campo imagem_original seja salvo mesmo que seja um caminho relativo do SinapUm
        # Isso permite que a imagem seja encontrada depois na exibição
        
        # Verificar se produto já existe pelo código de barras
        produto_existente = None
        if codigo_barras:
            logger.info(f"[SAVE_PRODUCT] Verificando produto existente com código: {codigo_barras}")
            produto_existente = ProdutoJSON.objects.filter(codigo_barras=codigo_barras).first()
            if produto_existente:
                logger.info(f"[SAVE_PRODUCT] Produto existente encontrado - ID: {produto_existente.id}, atualizando...")
                # Atualizar produto existente
                produto_existente.dados_json = produto_json
                produto_existente.nome_produto = nome_produto
                produto_existente.marca = marca
                produto_existente.categoria = categoria
                produto_existente.imagem_original = imagem_original
                produto_existente.criado_por = request.user
                produto_existente.save()
                logger.info(f"[SAVE_PRODUCT] Produto atualizado com sucesso - ID: {produto_existente.id}")
                return JsonResponse({
                    'success': True,
                    'message': 'Produto atualizado com sucesso!',
                    'action': 'updated',
                    'produto_id': produto_existente.id
                })
            else:
                logger.info(f"[SAVE_PRODUCT] Nenhum produto existente com código: {codigo_barras}")
        
        # Criar novo produto
        grupo_id = data.get('grupo_id')
        logger.info(f"[SAVE_PRODUCT] grupo_id recebido: {grupo_id} (tipo: {type(grupo_id)})")
        grupo = None
        if grupo_id:
            try:
                grupo_id_int = int(grupo_id) if grupo_id else None
                if grupo_id_int:
                    logger.info(f"[SAVE_PRODUCT] Buscando grupo com ID: {grupo_id_int} para usuário: {request.user.id}")
                    grupo = WhatsappGroup.objects.filter(id=grupo_id_int, owner=request.user).first()
                    if not grupo:
                        logger.warning(f"[SAVE_PRODUCT] Grupo {grupo_id_int} não encontrado ou não pertence ao usuário {request.user.id}")
                    else:
                        logger.info(f"[SAVE_PRODUCT] Grupo encontrado: {grupo.name}")
            except (ValueError, TypeError) as e:
                logger.warning(f"[SAVE_PRODUCT] Erro ao processar grupo_id {grupo_id}: {str(e)}")
        
        logger.info(f"[SAVE_PRODUCT] Criando novo produto no banco de dados...")
        novo_produto = ProdutoJSON.objects.create(
            dados_json=produto_json,
            nome_produto=nome_produto,
            marca=marca,
            categoria=categoria,
            codigo_barras=codigo_barras,
            imagem_original=imagem_original,
            criado_por=request.user,
            grupo_whatsapp=grupo
        )
        
        logger.info(f"[SAVE_PRODUCT] Produto criado com sucesso - ID: {novo_produto.id}, Nome: {nome_produto}")
        
        return JsonResponse({
            'success': True,
            'message': 'Produto salvo com sucesso!',
            'action': 'created',
            'produto_id': novo_produto.id
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"[SAVE_PRODUCT] Erro ao decodificar JSON: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"[SAVE_PRODUCT] Erro ao salvar produto JSON: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

