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
    
    # Prompt melhorado para extrair MÁXIMO de informações
    prompt = """Analise esta imagem de um produto e extraia TODAS as informações possíveis visíveis no rótulo, etiqueta ou embalagem.

🔍 MISSÃO: Identificar e extrair CADA TEXTO, NÚMERO, CÓDIGO, LOGO e INFORMAÇÃO visível na imagem.

IMPORTANTE: 
- Leia TODOS os textos da imagem, incluindo textos pequenos, números de série, códigos, ingredientes, instruções
- Extraia dados REAIS que estão visíveis na imagem. NÃO invente informações.
- Se uma informação estiver parcialmente visível, extraia o que conseguir
- Seja EXTREMAMENTE DETALHADO na descrição - inclua todos os textos que conseguir ler

Retorne APENAS um JSON válido no formato ÉVORA com esta estrutura EXATA (preencha TODOS os campos possíveis):
{
    "nome_produto": "Nome COMPLETO exatamente como aparece no rótulo/embalagem",
    "categoria": "Categoria principal (ex: Eletrônicos, Roupas, Cosméticos, Alimentos, Bebidas, Produtos de Limpeza, etc.)",
    "subcategoria": "Subcategoria específica e detalhada",
    "descricao": "Descrição COMPLETA incluindo TODOS os textos visíveis: características, benefícios, ingredientes, modo de uso, advertências, etc.",
    "caracteristicas": {
        "marca": "Marca do produto (se visível)",
        "modelo": "Modelo/versão específica (se visível)",
        "tipo": "Tipo específico do produto (ex: Eau de Parfum, Shampoo Anticaspa, etc.)",
        "funcoes": ["lista de todas as funções mencionadas"],
        "conectividade": "Tipo de conexão se aplicável",
        "aplicativo_compativel": "Nome do app se mencionado",
        "plataformas": ["iOS", "Android", "PC"],
        "bateria": "Informações de bateria se visível",
        "material": "Material(s) do produto (se visível)",
        "cor": "Cor(s) do produto (se visível)",
        "alcance_estimado": "Alcance ou distância (se visível)",
        "volume_ml": "Volume em ml se visível",
        "peso_kg": "Peso em kg se visível",
        "tamanho": "Tamanho/porte se visível (ex: Grande, Médio, P, M, G, GG)",
        "fragrancia": "Fragrância se for produto perfumado",
        "ingredientes": "Lista de ingredientes se visível (pode ser resumida)",
        "certificacoes": "Certificações se visível (ex: Orgânico, Vegano, Cruelty Free)",
        "beneficios": "Benefícios mencionados no produto",
        "uso": "Modo de uso se visível",
        "validade": "Validade ou prazo de validade se visível",
        "lote": "Número de lote se visível"
    },
    "compatibilidade": {
        "ios": "Modelos iOS compatíveis se visível",
        "android": "Versão Android mínima se visível",
        "sistemas": ["iOS", "Android", "PC", "Windows", "Mac"]
    },
    "dimensoes_embalagem": {
        "altura_cm": "altura se visível (número)",
        "largura_cm": "largura se visível (número)",
        "profundidade_cm": "profundidade se visível (número)",
        "diametro_cm": "diâmetro se for produto cilíndrico",
        "formato": "Formato da embalagem se relevante"
    },
    "peso_embalagem_gramas": "peso em gramas se visível (número)",
    "codigo_barras": "Código de barras COMPLETO se visível (EAN, UPC, etc.)",
    "codigo_interno": "Código interno/ref do fabricante se visível",
    "fabricante": "Nome completo do fabricante se visível",
    "pais_origem": "País de origem/fabricação se visível",
    "data_fabricacao": "Data de fabricação se visível (formato YYYY-MM-DD)",
    "preco_visivel": "Preço se estiver IMPRESSO na embalagem original (não etiqueta de loja)",
    "informacoes_adicionais": "Qualquer outro texto ou informação visível que não se encaixe nos campos acima"
}

REGRAS CRÍTICAS:
1. LEIA CADA TEXTO da imagem - não pule informações
2. Se alguma informação NÃO estiver visível, use null (não invente)
3. Preço: apenas se estiver IMPRESSO na EMBALAGEM do produto, NÃO em etiquetas de loja
4. Descrição: seja EXTREMAMENTE DETALHADO - inclua textos de ingredientes, benefícios, advertências, modo de uso
5. Características: extraia TODOS os detalhes visíveis (tamanho, cor, material, tipo, etc.)
6. Código de barras: se visível, copie COMPLETO
7. Ingredientes: se houver lista longa, mencione os principais e indique quantidade
8. Certificações: identifique todas as certificações/logos visíveis
9. Para categoria/subcategoria, use termos comerciais padrão e seja específico
10. Retorne APENAS o JSON válido, sem markdown, sem explicações adicionais"""
    
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
        max_tokens=4000,
        temperature=0.1
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
    
    # Prompt melhorado para extrair MÁXIMO de informações
    prompt = """Analise esta imagem de um produto e extraia TODAS as informações possíveis visíveis no rótulo, etiqueta ou embalagem.

🔍 MISSÃO: Identificar e extrair CADA TEXTO, NÚMERO, CÓDIGO, LOGO e INFORMAÇÃO visível na imagem.

IMPORTANTE: 
- Leia TODOS os textos da imagem, incluindo textos pequenos, números de série, códigos, ingredientes, instruções
- Extraia dados REAIS que estão visíveis na imagem. NÃO invente informações.
- Se uma informação estiver parcialmente visível, extraia o que conseguir
- Seja EXTREMAMENTE DETALHADO na descrição - inclua todos os textos que conseguir ler

Retorne APENAS um JSON válido no formato ÉVORA com esta estrutura EXATA (preencha TODOS os campos possíveis):
{
    "nome_produto": "Nome COMPLETO exatamente como aparece no rótulo/embalagem",
    "categoria": "Categoria principal (ex: Eletrônicos, Roupas, Cosméticos, Alimentos, Bebidas, Produtos de Limpeza, etc.)",
    "subcategoria": "Subcategoria específica e detalhada",
    "descricao": "Descrição COMPLETA incluindo TODOS os textos visíveis: características, benefícios, ingredientes, modo de uso, advertências, etc.",
    "caracteristicas": {
        "marca": "Marca do produto (se visível)",
        "modelo": "Modelo/versão específica (se visível)",
        "tipo": "Tipo específico do produto (ex: Eau de Parfum, Shampoo Anticaspa, etc.)",
        "funcoes": ["lista de todas as funções mencionadas"],
        "conectividade": "Tipo de conexão se aplicável",
        "aplicativo_compativel": "Nome do app se mencionado",
        "plataformas": ["iOS", "Android", "PC"],
        "bateria": "Informações de bateria se visível",
        "material": "Material(s) do produto (se visível)",
        "cor": "Cor(s) do produto (se visível)",
        "alcance_estimado": "Alcance ou distância (se visível)",
        "volume_ml": "Volume em ml se visível",
        "peso_kg": "Peso em kg se visível",
        "tamanho": "Tamanho/porte se visível (ex: Grande, Médio, P, M, G, GG)",
        "fragrancia": "Fragrância se for produto perfumado",
        "ingredientes": "Lista de ingredientes se visível (pode ser resumida)",
        "certificacoes": "Certificações se visível (ex: Orgânico, Vegano, Cruelty Free)",
        "beneficios": "Benefícios mencionados no produto",
        "uso": "Modo de uso se visível",
        "validade": "Validade ou prazo de validade se visível",
        "lote": "Número de lote se visível"
    },
    "compatibilidade": {
        "ios": "Modelos iOS compatíveis se visível",
        "android": "Versão Android mínima se visível",
        "sistemas": ["iOS", "Android", "PC", "Windows", "Mac"]
    },
    "dimensoes_embalagem": {
        "altura_cm": "altura se visível (número)",
        "largura_cm": "largura se visível (número)",
        "profundidade_cm": "profundidade se visível (número)",
        "diametro_cm": "diâmetro se for produto cilíndrico",
        "formato": "Formato da embalagem se relevante"
    },
    "peso_embalagem_gramas": "peso em gramas se visível (número)",
    "codigo_barras": "Código de barras COMPLETO se visível (EAN, UPC, etc.)",
    "codigo_interno": "Código interno/ref do fabricante se visível",
    "fabricante": "Nome completo do fabricante se visível",
    "pais_origem": "País de origem/fabricação se visível",
    "data_fabricacao": "Data de fabricação se visível (formato YYYY-MM-DD)",
    "preco_visivel": "Preço se estiver IMPRESSO na embalagem original (não etiqueta de loja)",
    "informacoes_adicionais": "Qualquer outro texto ou informação visível que não se encaixe nos campos acima"
}

REGRAS CRÍTICAS:
1. LEIA CADA TEXTO da imagem - não pule informações
2. Se alguma informação NÃO estiver visível, use null (não invente)
3. Preço: apenas se estiver IMPRESSO na EMBALAGEM do produto, NÃO em etiquetas de loja
4. Descrição: seja EXTREMAMENTE DETALHADO - inclua textos de ingredientes, benefícios, advertências, modo de uso
5. Características: extraia TODOS os detalhes visíveis (tamanho, cor, material, tipo, etc.)
6. Código de barras: se visível, copie COMPLETO
7. Ingredientes: se houver lista longa, mencione os principais e indique quantidade
8. Certificações: identifique todas as certificações/logos visíveis
9. Para categoria/subcategoria, use termos comerciais padrão e seja específico
10. Retorne APENAS o JSON válido, sem markdown, sem explicações adicionais"""
    
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
        max_tokens=4000,
        temperature=0.1
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
