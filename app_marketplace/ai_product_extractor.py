"""
Extração de dados de produtos usando IA
Foco: OpenMind AI (servidor próprio no SinapUm)
Fallback: OpenAI (opcional)
Formata JSON no padrão ÉVORA conforme especificação
"""
import os
import json
import base64
import re
from io import BytesIO
from django.conf import settings
from PIL import Image
import requests
import logging

logger = logging.getLogger(__name__)

# Verificar disponibilidade da OpenAI (opcional, para fallback)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def generate_sku_interno(nome_produto, marca=None):
    """
    Gera SKU interno no padrão ÉVORA: EVR-{MARCA}-{TIPO}-{VARIANTE}
    """
    # Normalizar nome
    nome_clean = re.sub(r'[^a-zA-Z0-9\s]', '', nome_produto.upper())
    palavras = nome_clean.split()[:3]  # Primeiras 3 palavras
    
    # Extrair marca se disponível
    marca_code = ''
    if marca:
        marca_clean = re.sub(r'[^a-zA-Z0-9]', '', marca.upper())[:6]
        marca_code = f"{marca_clean}-"
    
    # Tipo do produto (primeira palavra significativa)
    tipo = palavras[0][:4] if palavras else 'PROD'
    
    # Variante (segunda palavra ou abreviação)
    variante = palavras[1][:4] if len(palavras) > 1 else 'GEN'
    
    return f"EVR-{marca_code}{tipo}-{variante}"


def format_evora_json(extracted_data, image_url=None):
    """
    Formata dados extraídos no padrão JSON ÉVORA
    """
    nome_produto = extracted_data.get('nome_produto', extracted_data.get('nome_sugerido', ''))
    marca = extracted_data.get('marca', extracted_data.get('marca_sugerida', ''))
    categoria = extracted_data.get('categoria', extracted_data.get('categoria_sugerida', 'Eletrônicos'))
    
    # Gerar SKU interno
    sku_interno = extracted_data.get('sku_interno')
    if not sku_interno:
        sku_interno = generate_sku_interno(nome_produto, marca)
    
    # Processar código de barras (pode ser array ou string)
    codigo_barras = extracted_data.get('codigo_barras', '')
    if isinstance(codigo_barras, list):
        codigo_barras = codigo_barras[0] if codigo_barras else None
    elif not codigo_barras:
        codigo_barras = None
    
    # Processar características
    caracteristicas = {}
    if isinstance(extracted_data.get('caracteristicas'), dict):
        caracteristicas = extracted_data.get('caracteristicas', {})
    else:
        # Se for lista, converter para objeto
        funcs = extracted_data.get('caracteristicas', [])
        if isinstance(funcs, list):
            caracteristicas = {
                'funcoes': funcs,
                'marca': marca,
                'modelo': extracted_data.get('modelo', ''),
                'cor': extracted_data.get('cor', ''),
                'material': extracted_data.get('material', ''),
            }
    
    # Processar compatibilidade
    compatibilidade = {}
    if isinstance(extracted_data.get('compatibilidade'), dict):
        compatibilidade = extracted_data.get('compatibilidade', {})
    else:
        # Criar compatibilidade básica
        compatibilidade = {
            'sistemas': extracted_data.get('plataformas', []) if isinstance(extracted_data.get('plataformas'), list) else []
        }
    
    # Formatar JSON ÉVORA
    evora_json = {
        "nome_produto": nome_produto,
        "categoria": categoria,
        "subcategoria": extracted_data.get('subcategoria', ''),
        "descricao": extracted_data.get('descricao', extracted_data.get('descricao_observacoes', '')),
        "caracteristicas": caracteristicas,
        "compatibilidade": compatibilidade,
        "dimensoes_embalagem": {
            "altura_cm": extracted_data.get('dimensoes_embalagem', {}).get('altura_cm') if isinstance(extracted_data.get('dimensoes_embalagem'), dict) else None,
            "largura_cm": extracted_data.get('dimensoes_embalagem', {}).get('largura_cm') if isinstance(extracted_data.get('dimensoes_embalagem'), dict) else None,
            "profundidade_cm": extracted_data.get('dimensoes_embalagem', {}).get('profundidade_cm') if isinstance(extracted_data.get('dimensoes_embalagem'), dict) else None
        },
        "peso_embalagem_gramas": extracted_data.get('peso_embalagem_gramas'),
        "codigo_barras": codigo_barras,
        "sku_interno": sku_interno,
        "preco_compra": extracted_data.get('preco_compra'),
        "percentual_lucro": extracted_data.get('percentual_lucro'),
        "preco_venda_sugerido": extracted_data.get('preco_venda_sugerido'),
        "imagens": []
    }
    
    # Adicionar imagem se disponível
    if image_url:
        evora_json["imagens"].append({
            "fonte": "upload",
            "descricao": f"Foto da embalagem do produto {nome_produto}"
        })
    
    return evora_json


def extract_product_data_from_image(image_file):
    """
    Extrai dados de produto de uma imagem usando IA
    Prioriza OpenMind AI, com fallback para OpenAI se configurado
    
    Args:
        image_file: Arquivo de imagem (BytesIO, File, ou caminho)
    
    Returns:
        dict: Dados extraídos no formato ÉVORA ou erro
    """
    # Verificar qual serviço usar (prioridade: OpenMind AI)
    ai_service = os.getenv('AI_SERVICE', 'openmind').lower()
    
    if ai_service == 'openmind':
        return _extract_with_openmind_ai(image_file)
    elif ai_service == 'openai' and OPENAI_AVAILABLE:
        return _extract_with_openai(image_file)
    else:
        return {
            'error': f'Serviço de IA não configurado. AI_SERVICE={ai_service}. Configure OPENMIND_AI_URL ou OPENAI_API_KEY.'
        }


def _extract_with_openmind_ai(image_file):
    """
    Extrai dados usando OpenMind AI (servidor SinapUm)
    """
    openmind_url = os.getenv('OPENMIND_AI_URL') or getattr(settings, 'OPENMIND_AI_URL', None)
    openmind_key = os.getenv('OPENMIND_AI_KEY') or getattr(settings, 'OPENMIND_AI_KEY', None)
    timeout = int(os.getenv('OPENMIND_AI_TIMEOUT', '30'))
    
    if not openmind_url:
        return {
            'error': 'OPENMIND_AI_URL não configurada. Configure no arquivo .env'
        }
    
    if not openmind_key:
        return {
            'error': 'OPENMIND_AI_KEY não configurada. Configure no arquivo .env'
        }
    
    try:
        # Preparar imagem
        if isinstance(image_file, str):
            with open(image_file, 'rb') as f:
                image_data = f.read()
                image_filename = os.path.basename(image_file)
        elif hasattr(image_file, 'read'):
            image_file.seek(0)
            image_data = image_file.read()
            image_filename = getattr(image_file, 'name', 'image.jpg')
        else:
            return {'error': 'Formato de imagem inválido'}
        
        # Construir URL completa do endpoint
        endpoint_url = f"{openmind_url.rstrip('/')}/analyze-product-image"
        
        # Preparar requisição
        files = {
            'image': (image_filename, image_data, 'image/jpeg')
        }
        headers = {
            'Authorization': f'Bearer {openmind_key}'
        }
        
        logger.info(f"Enviando imagem para OpenMind AI: {endpoint_url}")
        
        # Fazer requisição HTTP
        response = requests.post(
            endpoint_url,
            files=files,
            headers=headers,
            timeout=timeout
        )
        
        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                # OpenMind AI já retorna no formato ÉVORA
                return {
                    'success': True,
                    'data': result.get('data', {})
                }
            else:
                return {
                    'error': result.get('error', 'Erro desconhecido do OpenMind AI'),
                    'error_code': result.get('error_code', 'UNKNOWN')
                }
        elif response.status_code == 401:
            return {
                'error': 'Autenticação falhou. Verifique OPENMIND_AI_KEY',
                'error_code': 'UNAUTHORIZED'
            }
        elif response.status_code == 400:
            error_data = response.json() if response.content else {}
            return {
                'error': error_data.get('error', 'Erro na requisição ao OpenMind AI'),
                'error_code': error_data.get('error_code', 'BAD_REQUEST')
            }
        else:
            return {
                'error': f'Erro ao conectar com OpenMind AI: Status {response.status_code}',
                'error_code': 'HTTP_ERROR',
                'status_code': response.status_code
            }
    
    except requests.exceptions.Timeout:
        return {
            'error': f'Timeout ao conectar com OpenMind AI (timeout: {timeout}s)',
            'error_code': 'TIMEOUT'
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'error': f'Não foi possível conectar com OpenMind AI em {openmind_url}. Verifique se o servidor está rodando.',
            'error_code': 'CONNECTION_ERROR'
        }
    except Exception as e:
        import traceback
        logger.error(f"Erro ao processar imagem com OpenMind AI: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'error': f'Erro ao processar imagem com OpenMind AI: {str(e)}'
        }


def _extract_with_openai(image_file):
    """
    Extrai dados usando OpenAI Vision API (fallback)
    """
    if not OPENAI_AVAILABLE:
        return {
            'error': 'OpenAI não está disponível. Instale: pip install openai'
        }
    
    api_key = settings.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {
            'error': 'OPENAI_API_KEY não configurada'
        }
    
    try:
        # Configurar cliente OpenAI
        client = OpenAI(api_key=api_key)
        
        # Converter imagem para base64
        if isinstance(image_file, str):
            with open(image_file, 'rb') as f:
                image_data = f.read()
        elif hasattr(image_file, 'read'):
            image_file.seek(0)
            image_data = image_file.read()
        else:
            return {'error': 'Formato de imagem inválido'}
        
        # Redimensionar se necessário
        img = Image.open(BytesIO(image_data))
        max_size = 2048
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            output = BytesIO()
            img.save(output, format='JPEG', quality=90)
            image_data = output.getvalue()
        
        # Converter para base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Prompt específico para formato ÉVORA
        prompt = """Analise esta imagem de um produto e extraia TODAS as informações visíveis no rótulo, etiqueta ou embalagem.

IMPORTANTE: Extraia dados REAIS que estão visíveis na imagem. NÃO invente informações.

Retorne APENAS um JSON válido no formato ÉVORA com esta estrutura EXATA:
{
    "nome_produto": "Nome completo do produto extraído do rótulo",
    "categoria": "Categoria principal (ex: Eletrônicos, Roupas, Cosméticos, etc.)",
    "subcategoria": "Subcategoria específica (ex: Fones de Ouvido, Lingerie, Perfumes, etc.)",
    "descricao": "Descrição comercial detalhada do produto baseada no que está visível",
    "caracteristicas": {
        "marca": "Marca do produto (se visível)",
        "modelo": "Modelo específico (se visível)",
        "funcoes": ["função 1", "função 2", "função 3"],
        "conectividade": "Tipo de conexão (Bluetooth, USB-C, etc.)",
        "aplicativo_compativel": "Nome do app (se mencionado)",
        "plataformas": ["iOS", "Android", "PC"],
        "bateria": "Tipo de bateria (se visível)",
        "material": "Material do produto (se visível)",
        "cor": "Cor do produto (se visível)",
        "alcance_estimado": "Alcance ou distância (se visível)"
    },
    "compatibilidade": {
        "ios": "Modelos iOS compatíveis (se visível)",
        "android": "Versão Android mínima (se visível)",
        "sistemas": ["iOS", "Android", "PC"]
    },
    "dimensoes_embalagem": {
        "altura_cm": null,
        "largura_cm": null,
        "profundidade_cm": null
    },
    "peso_embalagem_gramas": null,
    "codigo_barras": "Código de barras completo se visível (EAN, UPC, etc.)",
    "fabricante": "Nome do fabricante (se visível)",
    "pais_origem": "País de origem (se visível)",
    "data_fabricacao": "Data de fabricação (se visível no formato YYYY-MM-DD)",
    "preco_visivel": "Preço se estiver visível na etiqueta (apenas números, ex: '15.90') - NÃO inclua se for preço de loja/etiqueta de venda"
}

REGRAS CRÍTICAS:
- Se alguma informação NÃO estiver visível, use null (não invente)
- Preço visível: apenas se estiver na EMBALAGEM do produto, NÃO na etiqueta de loja
- Seja ESPECÍFICO e detalhado na descrição
- Identifique TODOS os textos visíveis
- Para categoria, use termos comerciais padrão
- Para subcategoria, seja mais específico
- Retorne APENAS o JSON, sem markdown, sem explicações
- NÃO inclua preço de venda de loja, apenas preço se estiver na embalagem original do produto"""
        
        # Chamar OpenAI Vision API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.2
        )
        
        # Extrair resposta
        content = response.choices[0].message.content.strip()
        
        # Remover markdown code blocks
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        # Parsear JSON
        try:
            product_data = json.loads(content)
        except json.JSONDecodeError as e:
            # Tentar extrair JSON do texto
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                product_data = json.loads(json_match.group())
            else:
                return {
                    'error': f'Erro ao parsear JSON da resposta: {str(e)}',
                    'raw_response': content
                }
        
        return {
            'success': True,
            'data': product_data
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'error': f'Erro ao processar imagem com IA: {str(e)}'
        }
