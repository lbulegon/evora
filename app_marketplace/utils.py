"""
Utilitários para transformação de dados de produtos
Adaptado das melhorias do SinapUm para qualidade de informações geradas no JSON
"""
from datetime import datetime
from typing import Dict, Any, Optional
import re
from django.conf import settings


def transform_evora_to_modelo_json(evora_data: Dict[str, Any], image_filename: str = None, image_path: str = None) -> Dict[str, Any]:
    """
    Transforma dados no formato ÉVORA para o formato modelo.json
    
    Args:
        evora_data: Dados no formato ÉVORA retornados pelo OpenMind AI
        image_filename: Nome do arquivo de imagem (opcional)
        image_path: Caminho completo da imagem salva no servidor (ex: "media/uploads/nome.jpg")
    
    Returns:
        dict: Dados no formato modelo.json
    """
    # Extrair dados do formato ÉVORA
    nome_produto = evora_data.get('nome_produto', 'Produto não identificado')
    
    # Características pode ser dict ou list
    caracteristicas = evora_data.get('caracteristicas', {})
    if isinstance(caracteristicas, list):
        # Se for lista, tentar extrair informações de strings
        caracteristicas_dict = {}
        for item in caracteristicas:
            if isinstance(item, str):
                # Tentar identificar informações nas strings
                if 'kg' in item.lower():
                    try:
                        match = re.search(r'(\d+(?:\.\d+)?)\s*kg', item, re.IGNORECASE)
                        if match:
                            caracteristicas_dict['peso_kg'] = float(match.group(1))
                    except:
                        pass
        marca = evora_data.get('marca') or 'Marca não identificada'
        caracteristicas = caracteristicas_dict
    else:
        marca = caracteristicas.get('marca') if isinstance(caracteristicas, dict) else None
        marca = marca or evora_data.get('marca') or 'Marca não identificada'
    
    # Garantir que marca sempre seja uma string, nunca None
    if not marca or marca == 'None':
        marca = 'Marca não identificada'
    marca = str(marca).strip()
    
    descricao = evora_data.get('descricao', 'Descrição não disponível')
    categoria = evora_data.get('categoria', 'Não categorizado')
    subcategoria = evora_data.get('subcategoria', '')
    codigo_barras = evora_data.get('codigo_barras')
    
    # Extrair informações específicas de produto
    volume_ml = None
    peso_kg = None
    tipo = None
    familia_olfativa = None
    
    # Tentar extrair volume (para perfumaria)
    if isinstance(caracteristicas, dict) and caracteristicas.get('volume_ml'):
        volume_ml = caracteristicas.get('volume_ml')
    else:
        # Procurar por volume em diferentes campos
        for key, value in evora_data.items():
            if isinstance(value, str) and 'ml' in value.lower():
                try:
                    match = re.search(r'(\d+)\s*ml', value, re.IGNORECASE)
                    if match:
                        volume_ml = int(match.group(1))
                        break
                except:
                    pass
    
    # Extrair peso em kg (e converter para gramas se necessário)
    peso_embalagem_gramas = evora_data.get('peso_embalagem_gramas')
    
    if isinstance(caracteristicas, dict):
        peso_kg = caracteristicas.get('peso_kg')
        if peso_kg:
            try:
                peso_kg = float(peso_kg)
                peso_embalagem_gramas = int(peso_kg * 1000)
            except:
                pass
    
    # Se temos peso_embalagem_gramas mas não está convertido
    if not peso_embalagem_gramas:
        # Tentar extrair de strings como "4kg"
        for key, value in evora_data.items():
            if isinstance(value, str):
                match = re.search(r'(\d+(?:\.\d+)?)\s*kg', value, re.IGNORECASE)
                if match:
                    try:
                        peso_kg = float(match.group(1))
                        peso_embalagem_gramas = int(peso_kg * 1000)
                        break
                    except:
                        pass
    
    # Extrair tipo de produto
    if isinstance(caracteristicas, dict):
        tipo = caracteristicas.get('tipo')
    
    # Tentar identificar tipo de produto
    if categoria.lower() in ['perfumaria', 'cosméticos', 'cosmeticos']:
        # Para perfumes
        tipo_indicadores = ['parfum', 'eau de parfum', 'eau de toilette', 'eau de cologne']
        descricao_lower = descricao.lower()
        for indicador in tipo_indicadores:
            if indicador in descricao_lower:
                tipo = indicador.title()
                break
        
        # Tentar extrair família olfativa
        if 'olfativa' in str(evora_data).lower() or 'fragrância' in descricao_lower:
            # Procurar por família olfativa no texto
            pass  # Implementar extração se necessário
    
    # Preparar lista de imagens
    imagens = []
    # Priorizar caminho completo da imagem, depois nome do arquivo
    if image_path:
        imagens.append(image_path)
    elif image_filename:
        # Se não tiver caminho completo, usar apenas o nome do arquivo
        imagens.append(image_filename)
    elif evora_data.get('imagens'):
        if isinstance(evora_data['imagens'], list):
            imagens = [img.get('descricao', '') if isinstance(img, dict) else str(img) for img in evora_data['imagens']]
        else:
            imagens = [str(evora_data['imagens'])]
    
    # Construir nome completo do produto (nome + marca se não estiver incluído)
    nome_completo = nome_produto
    if marca and marca.lower() not in nome_completo.lower():
        nome_completo = f"{nome_produto} – {marca}"
    
    # Extrair tipo de descrição ou características
    if not tipo:
        # Tentar identificar tipo a partir da descrição ou subcategoria
        if 'sabão' in descricao.lower() or 'detergente' in descricao.lower():
            tipo = descricao.split()[0] if descricao else subcategoria
        elif subcategoria:
            tipo = subcategoria
        else:
            tipo = None
    
    # Construir estrutura produto
    produto = {
        "nome": nome_completo,
        "marca": marca,
        "descricao": descricao if descricao and len(descricao) > 20 else f"{subcategoria} {marca}. {descricao}" if descricao else f"{nome_produto} da marca {marca}.",
        "categoria": categoria,
        "subcategoria": subcategoria,
        "familia_olfativa": familia_olfativa,
        "volume_ml": volume_ml,
        "tipo": tipo,
        "codigo_barras": codigo_barras if codigo_barras else None,
        "imagens": imagens if imagens else []
    }
    
    # Adicionar peso se disponível
    if peso_embalagem_gramas:
        # Converter gramas para kg se for muito grande (>1000g)
        if peso_embalagem_gramas >= 1000:
            produto["peso"] = f"{peso_embalagem_gramas/1000:.0f}kg"
    
    # Produto genérico do catálogo
    # Extrair nome genérico (sem especificações como volume, tipo, peso, etc.)
    nome_generico = nome_produto
    # Remover indicadores de volume, tipo, peso
    nome_generico = re.sub(r'\d+\s*ml', '', nome_generico, flags=re.IGNORECASE)
    nome_generico = re.sub(r'\d+\s*kg', '', nome_generico, flags=re.IGNORECASE)
    nome_generico = re.sub(r'(parfum|eau de parfum|eau de toilette|eau de cologne)', '', nome_generico, flags=re.IGNORECASE)
    # Remover marca apenas se não for None
    if marca:
        nome_generico = re.sub(r'–\s*' + re.escape(str(marca)), '', nome_generico, flags=re.IGNORECASE)
    nome_generico = ' '.join(nome_generico.split()).strip()
    
    if not nome_generico:
        nome_generico = nome_produto
    
    # Criar nome do catálogo: "Marca Nome Genérico"
    nome_catalogo = f"{marca} {nome_generico}" if marca and marca.lower() not in nome_generico.lower() else nome_generico
    
    # Extrair variantes
    variantes = []
    if volume_ml:
        variantes.append(f"{volume_ml}ml")
    if peso_kg:
        variantes.append(f"{peso_kg:.0f}kg" if peso_kg >= 1 else f"{int(peso_kg * 1000)}g")
    elif peso_embalagem_gramas and peso_embalagem_gramas >= 1000:
        variantes.append(f"{peso_embalagem_gramas/1000:.0f}kg")
    
    # Adicionar características das variantes se disponíveis
    if isinstance(evora_data.get('caracteristicas'), list):
        for item in evora_data.get('caracteristicas', []):
            if isinstance(item, str) and item not in variantes:
                # Adicionar características relevantes como variantes
                if any(keyword in item.lower() for keyword in ['perfume', 'intenso', 'mático', 'matic', 'limão', 'coco']):
                    variantes.append(item)
    
    produto_generico_catalogo = {
        "nome": nome_catalogo,
        "marca": marca,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "variantes": variantes if variantes else []
    }
    
    # Produto viagem (valores padrão - podem ser preenchidos depois)
    produto_viagem = {
        "preco_compra_usd": None,
        "preco_compra_brl": None,
        "margem_lucro_percentual": None,
        "preco_venda_usd": None,
        "preco_venda_brl": None
    }
    
    # Tentar extrair preço se disponível
    preco_visivel = evora_data.get('preco_visivel')
    if preco_visivel:
        try:
            # Tentar converter para float
            preco = float(str(preco_visivel).replace(',', '.').replace('$', '').strip())
            produto_viagem["preco_venda_brl"] = preco
        except:
            pass
    
    # Verificar se há preço sugerido do enriquecimento
    if evora_data.get('produto_viagem') and isinstance(evora_data['produto_viagem'], dict):
        if evora_data['produto_viagem'].get('preco_venda_brl'):
            produto_viagem["preco_venda_brl"] = evora_data['produto_viagem']['preco_venda_brl']
        if evora_data['produto_viagem'].get('preco_compra_brl'):
            produto_viagem["preco_compra_brl"] = evora_data['produto_viagem']['preco_compra_brl']
        if evora_data['produto_viagem'].get('margem_lucro_percentual'):
            produto_viagem["margem_lucro_percentual"] = evora_data['produto_viagem']['margem_lucro_percentual']
    
    # Estabelecimento (padrão vazio - será preenchido depois)
    estabelecimento = {
        "nome": None,
        "endereco": None,
        "localizacao_geografica": {
            "latitude": None,
            "longitude": None
        },
        "observacao": None
    }
    
    # Campanha (padrão vazio - será preenchido depois)
    campanha = {
        "id": None,
        "nome": None,
        "data_registro": None
    }
    
    # Shopper (padrão vazio - será preenchido depois)
    shopper = {
        "id": None,
        "nome": None,
        "pais": None
    }
    
    # Cadastro meta
    cadastro_meta = {
        "capturado_por": "VitrineZap (IA Évora)",
        "data_captura": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fonte": f"Análise automática de imagem: {image_path or image_filename or 'uploaded_image'}",
        "confianca_da_leitura": 0.95,  # Valor padrão, pode ser ajustado
        "detalhes_rotulo": {}
    }
    
    # Adicionar informações enriquecidas do cadastro_meta se disponíveis
    if evora_data.get('cadastro_meta') and isinstance(evora_data['cadastro_meta'], dict):
        if evora_data['cadastro_meta'].get('detalhes_rotulo'):
            cadastro_meta['detalhes_rotulo'] = evora_data['cadastro_meta']['detalhes_rotulo']
    
    # Extrair detalhes do rótulo do formato ÉVORA
    detalhes_rotulo = {}
    
    # Procurar por informações de origem
    pais_origem = evora_data.get('pais_origem') or evora_data.get('caracteristicas', {}).get('fabricacao', {}).get('pais')
    if pais_origem:
        detalhes_rotulo['origem'] = pais_origem
    
    # Procurar por informações em caracteristicas ou outros campos
    fabricante = evora_data.get('fabricante')
    if fabricante:
        detalhes_rotulo['fabricante'] = fabricante
    
    # Extrair informações adicionais que possam estar em caracteristicas
    caracteristicas_texto = str(caracteristicas).lower()
    if 'vegan' in caracteristicas_texto or 'vegano' in caracteristicas_texto:
        detalhes_rotulo['vegano'] = True
    if 'organic' in caracteristicas_texto or 'orgânico' in caracteristicas_texto:
        detalhes_rotulo['organico'] = True
    if 'conscious' in caracteristicas_texto or 'consciente' in caracteristicas_texto:
        detalhes_rotulo['frase'] = "conscious & vegan formula"
    
    # Extrair duração se mencionada (especialmente para perfumes)
    if 'duração' in descricao.lower() or 'duration' in descricao.lower() or 'lasting' in descricao.lower():
        match = re.search(r'(long-lasting|duração longa|muito duradouro)', descricao, re.IGNORECASE)
        if match:
            detalhes_rotulo['duracao'] = match.group(1)
    
    cadastro_meta["detalhes_rotulo"] = detalhes_rotulo if detalhes_rotulo else {
        "frase": None,
        "origem": None,
        "duracao": None
    }
    
    # Construir resposta final no formato modelo.json
    resultado = {
        "produto": produto,
        "produto_generico_catalogo": produto_generico_catalogo,
        "produto_viagem": produto_viagem,
        "estabelecimento": estabelecimento,
        "campanha": campanha,
        "shopper": shopper,
        "cadastro_meta": cadastro_meta
    }
    
    # PRESERVAR TODOS OS DADOS ORIGINAIS DA ANÁLISE DE IA
    # Adicionar campo analise_ia com todos os dados originais que não foram mapeados
    analise_ia = {}
    
    # Preservar características completas se existirem
    if evora_data.get('caracteristicas'):
        if isinstance(evora_data['caracteristicas'], dict):
            # Adicionar características completas que não foram mapeadas
            analise_ia['caracteristicas_completas'] = evora_data['caracteristicas']
        elif isinstance(evora_data['caracteristicas'], list):
            analise_ia['caracteristicas_lista'] = evora_data['caracteristicas']
    
    # Preservar compatibilidade completa
    if evora_data.get('compatibilidade'):
        analise_ia['compatibilidade'] = evora_data['compatibilidade']
    
    # Preservar dimensões completas
    if evora_data.get('dimensoes_embalagem'):
        if isinstance(evora_data['dimensoes_embalagem'], dict):
            # Adicionar dimensões completas (pode ter mais campos que altura/largura/profundidade)
            analise_ia['dimensoes_embalagem_completas'] = evora_data['dimensoes_embalagem']
    
    # Preservar outros campos importantes da análise
    campos_analise = [
        'sku_interno', 'preco_compra', 'percentual_lucro', 'preco_venda_sugerido',
        'pais_origem', 'fabricante', 'modelo', 'cor', 'material',
        'plataformas', 'funcoes', 'observacoes', 'tags', 'palavras_chave',
        'analise_texto', 'extracao_ocr', 'confianca_extracao'
    ]
    
    for campo in campos_analise:
        if evora_data.get(campo) is not None:
            analise_ia[campo] = evora_data[campo]
    
    # Preservar dados completos do produto_viagem se existirem
    if evora_data.get('produto_viagem') and isinstance(evora_data['produto_viagem'], dict):
        produto_viagem_original = evora_data['produto_viagem']
        # Adicionar campos que não foram mapeados
        for key, value in produto_viagem_original.items():
            if key not in produto_viagem and value is not None:
                analise_ia[f'produto_viagem_{key}'] = value
    
    # Preservar metadados completos do cadastro_meta original
    if evora_data.get('cadastro_meta') and isinstance(evora_data['cadastro_meta'], dict):
        cadastro_meta_original = evora_data['cadastro_meta']
        # Adicionar campos que não foram mapeados
        for key, value in cadastro_meta_original.items():
            if key not in cadastro_meta or (key == 'detalhes_rotulo' and isinstance(value, dict)):
                if key == 'detalhes_rotulo' and isinstance(value, dict):
                    # Mesclar detalhes_rotulo originais com os extraídos
                    if 'detalhes_rotulo_completos' not in analise_ia:
                        analise_ia['detalhes_rotulo_completos'] = value
                else:
                    analise_ia[f'cadastro_meta_{key}'] = value
    
    # Adicionar todos os outros campos que não foram mapeados
    campos_mapeados = {
        'nome_produto', 'marca', 'descricao', 'categoria', 'subcategoria',
        'codigo_barras', 'caracteristicas', 'compatibilidade', 'dimensoes_embalagem',
        'peso_embalagem_gramas', 'imagens', 'preco_visivel', 'produto_viagem',
        'cadastro_meta', 'pais_origem', 'fabricante'
    }
    
    for key, value in evora_data.items():
        if key not in campos_mapeados and value is not None:
            analise_ia[key] = value
    
    # Adicionar campo analise_ia ao resultado se houver dados preservados
    if analise_ia:
        resultado['analise_ia'] = analise_ia
    
    return resultado


def build_image_url(img_path, openmind_url=None, media_url=None, use_proxy=True):
    """
    Constrói URL completa para imagem - busca no SinapUm se necessário
    Usa proxy interno em produção (HTTPS) para evitar problemas de mixed content
    
    Args:
        img_path: Caminho da imagem (relativo ou absoluto)
        openmind_url: URL base do servidor OpenMind AI (opcional, busca das settings se não fornecido)
        media_url: URL base de media local (opcional, busca das settings se não fornecido)
        use_proxy: Se True, usa proxy interno quando em HTTPS (padrão: True)
    
    Returns:
        str: URL completa da imagem ou None se não houver path
    """
    # Importar settings no início da função
    from django.conf import settings as django_settings
    
    if not img_path:
        return None
    
    if isinstance(img_path, str):
        # Se já é URL completa (HTTP/HTTPS), verificar se precisa usar proxy
        if img_path.startswith('http://') or img_path.startswith('https://'):
            # Se é HTTPS, retornar como está
            if img_path.startswith('https://'):
                return img_path
            
            # Se é HTTP e estamos em produção HTTPS, usar proxy
            if use_proxy:
                is_railway = getattr(django_settings, 'IS_RAILWAY', False)
                if is_railway:
                    # Extrair path da URL HTTP e usar proxy
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(img_path)
                        # Manter o path completo (incluindo /media/ se houver)
                        path = parsed.path.lstrip('/')
                        return f"/api/images/proxy/{path}"
                    except:
                        pass
            
            return img_path
        
        # Obter URL base do SinapUm (se não fornecido)
        if openmind_url is None:
            openmind_url = getattr(django_settings, 'OPENMIND_AI_URL', '')
        
        # Obter URL base de media local (se não fornecido)
        if media_url is None:
            media_url = getattr(django_settings, 'MEDIA_URL', '/media/')
        
        # Se o path não começa com /, é provável que seja uma imagem do SinapUm
        # Imagens salvas no SinapUm durante análise têm paths como:
        # - "photo_0.jpg"
        # - "media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg"
        # - "produtos/temp/15/20251202_043814_temp.jpg"
        if not img_path.startswith('/'):
            # É uma imagem do SinapUm - construir URL completa
            if openmind_url:
                # Remover /api/v1 se existir para obter base URL do servidor
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                # Limpar o path (remover / no início se houver)
                clean_path = img_path.lstrip('/')
                
                # Se o path já começa com "media/", não adicionar /media/ novamente
                if clean_path.startswith('media/'):
                    url = f"{sinapum_base}/{clean_path}"
                else:
                    # Caso contrário, adicionar /media/ antes do path
                    url = f"{sinapum_base}/media/{clean_path}"
                
                # Se use_proxy está ativado e estamos em Railway (HTTPS), usar proxy
                if use_proxy:
                    is_railway = getattr(django_settings, 'IS_RAILWAY', False)
                    if is_railway:
                        # Usar proxy interno (HTTPS)
                        return f"/api/images/proxy/{clean_path}"
                
                return url
            else:
                # Fallback: tentar construir com IP padrão
                clean_path = img_path.lstrip('/')
                if clean_path.startswith('media/'):
                    url = f"http://69.169.102.84:8000/{clean_path}"
                else:
                    url = f"http://69.169.102.84:8000/media/{clean_path}"
                
                # Se use_proxy está ativado e estamos em Railway (HTTPS), usar proxy
                if use_proxy:
                    is_railway = getattr(django_settings, 'IS_RAILWAY', False)
                    if is_railway:
                        # Usar proxy interno (HTTPS)
                        return f"/api/images/proxy/{clean_path}"
                
                return url
        
        # Se começa com /, pode ser:
        # - Path local (tentar MEDIA_URL local primeiro)
        # - Path do SinapUm que começa com /media/
        if img_path.startswith('/media/'):
            # Pode ser do SinapUm ou local
            # Se não começar com http, assumir que é local
            if openmind_url and ('produtos/temp' in img_path or 'photo_' in img_path):
                # Parece ser do SinapUm (tem padrões típicos)
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                return f"{sinapum_base}{img_path}"
            # Caso contrário, retornar como path local
            return img_path
        
        # Path absoluto local (sem /media)
        if img_path.startswith('/'):
            return img_path
        
        # Caso contrário, adicionar MEDIA_URL local
        if img_path.startswith(media_url.lstrip('/')):
            return f"/{img_path}"
        return f"{media_url}{img_path}".replace('//', '/')
    
    return None

