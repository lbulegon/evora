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
        
        # Salvar todas as imagens no servidor
        upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        saved_images = []  # Lista de imagens salvas com seus caminhos
        
        for image_file in image_files:
            file_extension = os.path.splitext(image_file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename
            image_path = f"media/uploads/{unique_filename}"
            image_url = f"{settings.MEDIA_URL}uploads/{unique_filename}"
            
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
            
            # Salvar arquivo
            with open(file_path, 'wb+') as destination:
                destination.write(output.read())
            
            saved_images.append({
                'file': image_file,
                'filename': image_file.name,
                'saved_filename': unique_filename,
                'image_path': image_path,
                'image_url': image_url
            })
        
        # Analisar imagens
        if len(saved_images) == 1:
            # Uma única imagem - usar método simples
            image_file = saved_images[0]['file']
            image_file.seek(0)
            result = analyze_image_with_openmind(image_file)
            
            produto_data = result.get('data', {})
            image_path = saved_images[0]['image_path']
            
            # Transformar e adicionar caminho da imagem
            if produto_data and result.get('success'):
                # Se os dados já estão no formato modelo.json, não precisa transformar
                if 'produto' not in produto_data or 'produto_generico_catalogo' not in produto_data:
                    produto_data = transform_evora_to_modelo_json(
                        produto_data,
                        image_filename=image_file.name,
                        image_path=image_path
                    )
                
                # Garantir que o array de imagens existe e contém a imagem atual
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    # Adicionar imagem se não estiver presente
                    if image_path not in produto_data['produto']['imagens']:
                        produto_data['produto']['imagens'].insert(0, image_path)
                    # Se o array estiver vazio, garantir que tem pelo menos esta imagem
                    if not produto_data['produto']['imagens']:
                        produto_data['produto']['imagens'] = [image_path]
            
            # Preparar imagens para JSON (sem objetos file)
            saved_images_json = [{
                'filename': img['filename'],
                'saved_filename': img['saved_filename'],
                'image_path': img['image_path'],
                'image_url': img['image_url']
            } for img in saved_images]
            
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
                'image_url': saved_images[0]['image_url'],
                'saved_images': saved_images_json,
                'multiple_images': False
            })
        else:
            # Múltiplas imagens - usar análise comparativa
            image_files_list = [img['file'] for img in saved_images]
            result = analyze_multiple_images(image_files_list)
            
            # Adicionar caminhos das imagens salvas
            if result.get('mesmo_produto') and result.get('produto_consolidado'):
                produto_data = result['produto_consolidado']
                # Adicionar todos os caminhos das imagens salvas
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    # Adicionar caminhos de todas as imagens salvas (garantir ordem)
                    for img_info in saved_images:
                        if img_info['image_path'] not in produto_data['produto']['imagens']:
                            produto_data['produto']['imagens'].append(img_info['image_path'])
                # Se não tiver produto, criar estrutura básica
                elif not produto_data:
                    produto_data = {
                        'produto': {
                            'imagens': [img['image_path'] for img in saved_images]
                        }
                    }
            else:
                # Produtos diferentes - usar primeiro produto como base e adicionar todas as imagens
                produto_data = result.get('produtos_diferentes', [{}])[0].get('produto_data', {}) if result.get('produtos_diferentes') else {}
                # Garantir que todas as imagens estão no array
                if 'produto' in produto_data:
                    if 'imagens' not in produto_data['produto']:
                        produto_data['produto']['imagens'] = []
                    # Adicionar todas as imagens salvas
                    for img_info in saved_images:
                        if img_info['image_path'] not in produto_data['produto']['imagens']:
                            produto_data['produto']['imagens'].append(img_info['image_path'])
                else:
                    # Criar estrutura básica com todas as imagens
                    produto_data = {
                        'produto': {
                            'imagens': [img['image_path'] for img in saved_images]
                        }
                    }
            
            # Preparar imagens para JSON (sem objetos file)
            saved_images_for_template = [{
                'filename': img['filename'],
                'saved_filename': img['saved_filename'],
                'image_path': img['image_path'],
                'image_url': img['image_url']
            } for img in saved_images]
            
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_product_json(request):
    """
    View para salvar produto no banco de dados em formato JSON (PostgreSQL JSONB)
    Adaptado das melhorias do SinapUm
    """
    if not (request.user.is_shopper or request.user.is_address_keeper):
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    try:
        data = json.loads(request.body)
        produto_json = data.get('produto_json')
        
        if not produto_json:
            return JsonResponse({
                'success': False,
                'error': 'Dados do produto não fornecidos'
            }, status=400)
        
        # Extrair informações básicas para indexação
        produto = produto_json.get('produto', {})
        nome_produto = produto.get('nome', 'Produto sem nome')
        marca = produto.get('marca')
        categoria = produto.get('categoria')
        codigo_barras = produto.get('codigo_barras')
        
        # Obter caminho da imagem (primeira imagem do array para referência)
        # Todas as imagens estão no array produto['imagens']
        imagem_original = None
        if produto.get('imagens') and len(produto.get('imagens', [])) > 0:
            # Usar primeira imagem do array como referência principal
            imagem_original = produto['imagens'][0] if isinstance(produto['imagens'], list) else produto['imagens']
        elif produto_json.get('cadastro_meta', {}).get('fonte'):
            # Fallback: tentar extrair do campo fonte se não houver no array
            fonte = produto_json.get('cadastro_meta', {}).get('fonte', '')
            if 'imagem' in fonte.lower():
                imagem_original = fonte.split(':')[-1].strip() if ':' in fonte else fonte
        
        # Verificar se produto já existe pelo código de barras
        produto_existente = None
        if codigo_barras:
            produto_existente = ProdutoJSON.objects.filter(codigo_barras=codigo_barras).first()
            if produto_existente:
                # Atualizar produto existente
                produto_existente.dados_json = produto_json
                produto_existente.nome_produto = nome_produto
                produto_existente.marca = marca
                produto_existente.categoria = categoria
                produto_existente.imagem_original = imagem_original
                produto_existente.criado_por = request.user
                produto_existente.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Produto atualizado com sucesso!',
                    'action': 'updated',
                    'produto_id': produto_existente.id
                })
        
        # Criar novo produto
        grupo_id = data.get('grupo_id')
        grupo = None
        if grupo_id:
            grupo = WhatsappGroup.objects.filter(id=grupo_id, owner=request.user).first()
        
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
        
        return JsonResponse({
            'success': True,
            'message': 'Produto salvo com sucesso!',
            'action': 'created',
            'produto_id': novo_produto.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro ao salvar produto JSON: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

