"""
Lógica de análise de imagens
Integra com modelos de IA (OpenAI, Ollama, ou modelo customizado)
"""
import os
import json
import base64
from io import BytesIO
from PIL import Image
from typing import Dict, Any
from app.core.config import settings

# Tentar importar OpenAI (para usar com OpenMind.org que é compatível)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def analyze_product_image(image_data: bytes, image_filename: str) -> Dict[str, Any]:
    """
    Analisa uma imagem de produto e extrai informações
    
    Args:
        image_data: Dados binários da imagem
        image_filename: Nome do arquivo (para detectar formato)
    
    Returns:
        dict: Dados extraídos no formato ÉVORA
    """
    # Redimensionar imagem se necessário
    img = Image.open(BytesIO(image_data))
    max_dim = settings.IMAGE_MAX_DIMENSION
    
    if img.width > max_dim or img.height > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, format='JPEG', quality=90)
        image_data = output.getvalue()
        img = Image.open(BytesIO(image_data))
    
    # Converter para base64
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    # Chamar modelo de IA - Priorizar OpenMind.org
    # Usa OPENMIND_ORG_API_KEY ou OPENMIND_AI_API_KEY como fallback (mesma chave!)
    org_api_key = settings.OPENMIND_ORG_API_KEY or settings.OPENMIND_AI_API_KEY
    if org_api_key and settings.OPENMIND_ORG_BASE_URL:
        return _analyze_with_openmind_org(img, base64_image, org_api_key)
    elif OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
        return _analyze_with_openai(img, base64_image)
    else:
        # Fallback: retornar estrutura básica
        return {
            "nome_produto": "Produto identificado",
            "categoria": "Não identificada",
            "subcategoria": "",
            "descricao": "Análise de imagem em desenvolvimento - Configure OPENMIND_ORG_API_KEY",
            "caracteristicas": {},
            "compatibilidade": {},
            "codigo_barras": None,
            "dimensoes_embalagem": {
                "altura_cm": None,
                "largura_cm": None,
                "profundidade_cm": None
            },
            "peso_embalagem_gramas": None,
            "preco_visivel": None
        }


def _analyze_with_openmind_org(img: Image.Image, base64_image: str, api_key: str = None) -> Dict[str, Any]:
    """
    Analisa imagem usando OpenMind.org API (compatível com OpenAI)
    Você já pagou por isso! 🎉
    """
    if not OPENAI_AVAILABLE:
        raise ValueError("OpenAI client não está disponível (necessário para OpenMind.org)")
    
    # Usa a chave fornecida ou OPENMIND_ORG_API_KEY ou OPENMIND_AI_API_KEY como fallback
    if not api_key:
        api_key = settings.OPENMIND_ORG_API_KEY or settings.OPENMIND_AI_API_KEY
    
    # OpenMind.org usa API compatível com OpenAI, mas com URL customizada
    client = OpenAI(
        api_key=api_key,
        base_url=settings.OPENMIND_ORG_BASE_URL
    )
    
    # Usar modelo de visão do OpenMind.org (mais barato!)
    model = settings.OPENMIND_ORG_MODEL or "qwen2.5-vl-72b-instruct"
    
    # Prompt específico para formato ÉVORA (mesmo do código original)
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
    
    # Chamar OpenMind.org API (compatível com OpenAI)
    response = client.chat.completions.create(
        model=model,
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
    
    # Extrair resposta (mesmo formato OpenAI)
    content = response.choices[0].message.content.strip()
    
    # Remover markdown code blocks
    import re
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
            raise ValueError(f"Erro ao parsear JSON da resposta: {str(e)}")
    
    return product_data


def _analyze_with_openai(img: Image.Image, base64_image: str) -> Dict[str, Any]:
    """
    Analisa imagem usando OpenAI Vision API
    """
    if not OPENAI_AVAILABLE:
        raise ValueError("OpenAI não está disponível")
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Prompt específico para formato ÉVORA (mesmo do código original)
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
        model=settings.OPENAI_MODEL,
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
    import re
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
            raise ValueError(f"Erro ao parsear JSON da resposta: {str(e)}")
    
    return product_data
