"""
KMN (Keeper Mesh Network) Services
Sistema de resolução de papéis, ofertas e comissionamento para Dropkeeping

+ OpenMind AI Services
Serviços para integração com OpenMind AI (melhorias do SinapUm)
"""
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal
from django.db.models import Q, Max
from django.utils import timezone
import requests
import logging

from .models import (
    Agente, Cliente, Produto, Oferta, ClienteRelacao, 
    TrustlineKeeper, Pedido, RoleStats
)
from .utils import transform_evora_to_modelo_json

logger = logging.getLogger(__name__)

# ============================================================================
# KMN SERVICES
# ============================================================================

class KMNRoleEngine:
    """
    Motor de resolução de papéis e operações KMN.
    Determina automaticamente Shopper, Keeper, ofertas e comissionamento.
    """
    
    # Tipos de operação
    VENDA_DIRETA_SHOPPER = 'venda_direta_shopper'
    VENDA_MESH_COOPERADA = 'venda_mesh_cooperada'
    VENDA_AMBIGUA_RESOLVIDA = 'venda_ambigua_resolvida'
    
    def __init__(self):
        self.debug_info = {}
    
    def get_primary_owner(self, cliente_id: int) -> Optional[Agente]:
        """
        Determina o dono primário de um cliente baseado na força da relação.
        """
        try:
            relacao_principal = ClienteRelacao.objects.filter(
                cliente_id=cliente_id,
                status=ClienteRelacao.StatusRelacao.ATIVA
            ).order_by(
                '-forca_relacao',
                '-ultimo_pedido',
                '-total_pedidos'
            ).first()
            
            return relacao_principal.agente if relacao_principal else None
        except Exception as e:
            self.debug_info['error_primary_owner'] = str(e)
            return None
    
    def escolher_oferta_para_cliente(self, cliente: Cliente, produto: Produto) -> Optional[Oferta]:
        """
        Escolhe a oferta correta para um cliente específico.
        Regra: cliente deve ver apenas a oferta do seu owner primário.
        """
        try:
            # 1. Buscar owner primário do cliente
            owner_primario = self.get_primary_owner(cliente.id)
            
            # 2. Se tem owner primário, buscar oferta dele
            if owner_primario:
                oferta_owner = Oferta.objects.filter(
                    produto=produto,
                    agente_ofertante=owner_primario,
                    ativo=True,
                    quantidade_disponivel__gt=0
                ).first()
                
                if oferta_owner:
                    self.debug_info['oferta_escolhida'] = 'owner_primario'
                    return oferta_owner
            
            # 3. Fallback: menor preço disponível
            oferta_menor_preco = Oferta.objects.filter(
                produto=produto,
                ativo=True,
                quantidade_disponivel__gt=0
            ).order_by('preco_oferta').first()
            
            self.debug_info['oferta_escolhida'] = 'menor_preco_fallback'
            return oferta_menor_preco
            
        except Exception as e:
            self.debug_info['error_escolher_oferta'] = str(e)
            return None
    
    def resolver_papeis_operacao(self, cliente: Cliente, produto: Produto) -> Dict[str, Any]:
        """
        Resolve os papéis (Shopper/Keeper/Canal) para uma operação específica.
        """
        resultado = {
            'shopper': None,
            'keeper': None,
            'canal_entrada': None,
            'oferta': None,
            'tipo_operacao': None,
            'trustline': None,
            'debug': {}
        }
        
        try:
            # 1. Escolher a oferta correta
            oferta = self.escolher_oferta_para_cliente(cliente, produto)
            if not oferta:
                resultado['debug']['error'] = 'Nenhuma oferta disponível'
                return resultado
            
            resultado['oferta'] = oferta
            
            # 2. Determinar Shopper (quem tem o produto)
            shopper = oferta.agente_origem
            resultado['shopper'] = shopper
            
            # 3. Determinar Keeper (dono do cliente)
            owner_cliente = self.get_primary_owner(cliente.id)
            
            # 4. Resolver tipo de operação
            if owner_cliente == shopper:
                # Caso 1: Cliente é do Shopper - Venda Direta
                resultado['keeper'] = shopper
                resultado['tipo_operacao'] = self.VENDA_DIRETA_SHOPPER
                resultado['debug']['caso'] = 'cliente_do_shopper'
                
            elif owner_cliente and owner_cliente != shopper:
                # Caso 2: Cliente é de outro agente - Venda Cooperada
                resultado['keeper'] = owner_cliente
                resultado['tipo_operacao'] = self.VENDA_MESH_COOPERADA
                resultado['debug']['caso'] = 'venda_cooperada'
                
                # Buscar Trustline entre Shopper e Keeper
                trustline = self.buscar_trustline(shopper, owner_cliente)
                resultado['trustline'] = trustline
                
            else:
                # Caso 3: Vínculo ambíguo - Resolver por critérios
                resultado['keeper'] = shopper  # Fallback
                resultado['tipo_operacao'] = self.VENDA_AMBIGUA_RESOLVIDA
                resultado['debug']['caso'] = 'vinculo_ambiguo'
            
            return resultado
            
        except Exception as e:
            resultado['debug']['error'] = str(e)
            return resultado
    
    def buscar_trustline(self, agente_a: Agente, agente_b: Agente) -> Optional[TrustlineKeeper]:
        """
        Busca Trustline entre dois agentes (bidirecional).
        """
        try:
            return TrustlineKeeper.objects.filter(
                Q(agente_a=agente_a, agente_b=agente_b) |
                Q(agente_a=agente_b, agente_b=agente_a),
                status=TrustlineKeeper.StatusTrustline.ATIVA
            ).first()
        except Exception:
            return None
    
    def calcular_comissionamento(self, oferta: Oferta, trustline: Optional[TrustlineKeeper] = None) -> Dict[str, Decimal]:
        """
        Calcula as comissões baseado na oferta e trustline.
        """
        resultado = {
            'valor_base': oferta.preco_base,
            'valor_oferta': oferta.preco_oferta,
            'markup_local': oferta.markup_local,
            'comissao_shopper': Decimal('0'),
            'comissao_keeper': Decimal('0'),
            'comissao_indicacao': Decimal('0')
        }
        
        try:
            # Base é dividida conforme Trustline
            if trustline:
                perc_shopper = trustline.perc_shopper / 100
                perc_keeper = trustline.perc_keeper / 100
                perc_indicacao = trustline.perc_indicacao / 100 if trustline.permite_indicacao else 0
            else:
                # Valores padrão sem trustline
                perc_shopper = Decimal('0.6')  # 60%
                perc_keeper = Decimal('0.4')   # 40%
                perc_indicacao = Decimal('0')
            
            # Comissões sobre o preço base
            resultado['comissao_shopper'] = oferta.preco_base * perc_shopper
            resultado['comissao_keeper'] = oferta.preco_base * perc_keeper
            resultado['comissao_indicacao'] = oferta.preco_base * perc_indicacao
            
            # Markup vai 100% para o ofertante
            # (já está incluído no preco_oferta)
            
            return resultado
            
        except Exception as e:
            resultado['error'] = str(e)
            return resultado
    
    def processar_pedido_kmn(self, cliente: Cliente, produto: Produto, quantidade: int = 1) -> Dict[str, Any]:
        """
        Processa um pedido completo usando o sistema KMN.
        Retorna todos os dados necessários para criar o pedido.
        """
        resultado = {
            'sucesso': False,
            'dados_pedido': {},
            'debug': self.debug_info
        }
        
        try:
            # 1. Resolver papéis
            resolucao = self.resolver_papeis_operacao(cliente, produto)
            if not resolucao['oferta']:
                resultado['erro'] = 'Não foi possível resolver a operação'
                return resultado
            
            # 2. Calcular comissionamento
            comissoes = self.calcular_comissionamento(
                resolucao['oferta'], 
                resolucao['trustline']
            )
            
            # 3. Montar dados do pedido
            resultado['dados_pedido'] = {
                'cliente': cliente,
                'produto': produto,
                'quantidade': quantidade,
                'agente_shopper': resolucao['shopper'],
                'agente_keeper': resolucao['keeper'],
                'canal_entrada': resolucao['canal_entrada'],
                'oferta_utilizada': resolucao['oferta'],
                'preco_base_kmn': comissoes['valor_base'],
                'preco_oferta_kmn': comissoes['valor_oferta'],
                'markup_local_kmn': comissoes['markup_local'],
                'tipo_operacao_kmn': resolucao['tipo_operacao'],
                'comissao_shopper': comissoes['comissao_shopper'],
                'comissao_keeper': comissoes['comissao_keeper'],
                'comissao_indicacao': comissoes['comissao_indicacao'],
                'valor_total': comissoes['valor_oferta'] * quantidade
            }
            
            resultado['sucesso'] = True
            resultado['debug'].update(resolucao['debug'])
            
            return resultado
            
        except Exception as e:
            resultado['erro'] = str(e)
            return resultado


class KMNStatsService:
    """
    Serviço para atualização de estatísticas e scores KMN.
    """
    
    @staticmethod
    def atualizar_stats_pedido(pedido, agente_shopper: Agente, agente_keeper: Agente):
        """
        Atualiza estatísticas após conclusão de um pedido.
        """
        try:
            # Atualizar stats do Shopper
            stats_shopper, _ = RoleStats.objects.get_or_create(agente=agente_shopper)
            stats_shopper.pedidos_como_shopper += 1
            stats_shopper.valor_total_como_shopper += pedido.valor_total
            stats_shopper.save()
            stats_shopper.atualizar_scores()
            
            # Atualizar stats do Keeper (se diferente)
            if agente_keeper != agente_shopper:
                stats_keeper, _ = RoleStats.objects.get_or_create(agente=agente_keeper)
                stats_keeper.pedidos_como_keeper += 1
                stats_keeper.valor_total_como_keeper += pedido.valor_total
                stats_keeper.save()
                stats_keeper.atualizar_scores()
            
            # Atualizar relação cliente-agente
            relacao, _ = ClienteRelacao.objects.get_or_create(
                cliente=pedido.cliente,
                agente=agente_keeper
            )
            relacao.total_pedidos += 1
            relacao.valor_total_pedidos += pedido.valor_total
            relacao.ultimo_pedido = timezone.now()
            relacao.save()
            
        except Exception as e:
            # Log error but don't break the flow
            print(f"Erro ao atualizar stats KMN: {e}")
    
    @staticmethod
    def calcular_score_agente(agente: Agente) -> Dict[str, float]:
        """
        Calcula scores detalhados de um agente.
        """
        try:
            stats = agente.stats
            
            # Score baseado em volume e satisfação
            score_keeper = float(stats.satisfacao_media_keeper)
            if stats.pedidos_como_keeper > 0:
                volume_factor = min(stats.pedidos_como_keeper / 10, 1.0)
                score_keeper *= volume_factor
            
            score_shopper = float(stats.satisfacao_media_shopper)
            if stats.pedidos_como_shopper > 0:
                volume_factor = min(stats.pedidos_como_shopper / 10, 1.0)
                score_shopper *= volume_factor
            
            return {
                'score_keeper': score_keeper,
                'score_shopper': score_shopper,
                'dual_role_score': agente.dual_role_score,
                'total_pedidos': stats.pedidos_como_keeper + stats.pedidos_como_shopper,
                'valor_total': float(stats.valor_total_como_keeper + stats.valor_total_como_shopper)
            }
            
        except Exception:
            return {
                'score_keeper': 5.0,
                'score_shopper': 5.0,
                'dual_role_score': 5.0,
                'total_pedidos': 0,
                'valor_total': 0.0
            }


class CatalogoService:
    """
    Serviço para geração de catálogos personalizados por cliente.
    """
    
    @staticmethod
    def gerar_catalogo_cliente(cliente: Cliente) -> Dict[str, Any]:
        """
        Gera catálogo personalizado para um cliente específico.
        Cada produto mostra apenas UMA oferta (a correta para o cliente).
        """
        engine = KMNRoleEngine()
        catalogo = {
            'cliente': cliente,
            'produtos': [],
            'debug': {}
        }
        
        try:
            # Buscar todos os produtos ativos
            produtos = Produto.objects.filter(ativo=True)
            
            for produto in produtos:
                # Escolher a oferta correta para este cliente
                oferta = engine.escolher_oferta_para_cliente(cliente, produto)
                
                if oferta:
                    item_catalogo = {
                        'produto': produto,
                        'oferta': oferta,
                        'preco': oferta.preco_oferta,
                        'agente': oferta.agente_ofertante,
                        'disponivel': oferta.quantidade_disponivel > 0,
                        'markup_percentual': oferta.percentual_markup
                    }
                    catalogo['produtos'].append(item_catalogo)
            
            # Ordenar por preço
            catalogo['produtos'].sort(key=lambda x: x['preco'])
            
            return catalogo
            
        except Exception as e:
            catalogo['debug']['error'] = str(e)
            return catalogo


# ============================================================================
# OPENMIND AI SERVICES
# ============================================================================

OPENMIND_AI_URL = None
OPENMIND_AI_KEY = None

def _get_openmind_config():
    """Obtém configurações do OpenMind AI do Django settings"""
    global OPENMIND_AI_URL, OPENMIND_AI_KEY
    if OPENMIND_AI_URL is None:
        from django.conf import settings
        # URL padrão do servidor SinapUm (OpenMind AI)
        default_url = 'http://69.169.102.84:8000'
        OPENMIND_AI_URL = getattr(settings, 'OPENMIND_AI_URL', default_url)
        OPENMIND_AI_KEY = getattr(settings, 'OPENMIND_AI_KEY', None)
    return OPENMIND_AI_URL, OPENMIND_AI_KEY


def analyze_image_with_openmind(image_file, language='pt-BR', user=None):
    """
    Analisa uma imagem usando o OpenMind AI Server.
    
    Args:
        image_file: Arquivo de imagem (Django UploadedFile)
        language: Código do idioma (ex: 'pt-BR', 'en-US', 'es-ES'). Padrão: 'pt-BR'
        user: Usuário Django (opcional) - para detectar idioma do perfil
    
    Returns:
        dict: Resposta da API do OpenMind AI
    """
    try:
        # Detectar idioma do usuário se fornecido
        if user:
            detected_lang = _detect_user_language(user)
            if detected_lang:
                language = detected_lang
        
        url_base, api_key = _get_openmind_config()
        # Construir URL do endpoint - verificar se já inclui /api/v1
        if '/api/v1' in url_base:
            url = f"{url_base}/analyze-product-image"
        else:
            url = f"{url_base}/api/v1/analyze-product-image"
        
        # Adicionar parâmetro de idioma na URL
        url = f"{url}?language={language}"
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        files = {
            'image': (image_file.name, image_file.read(), image_file.content_type)
        }
        
        logger.info(f"Enviando imagem para análise: {image_file.name} (idioma: {language})")
        response = requests.post(url, files=files, headers=headers, timeout=60)
        
        # Verificar se a resposta é JSON válido
        content_type = response.headers.get('Content-Type', '')
        
        if response.status_code == 200:
            try:
                # Verificar se o Content-Type indica JSON
                if 'application/json' in content_type:
                    result = response.json()
                    logger.info(f"Análise concluída com sucesso: {result.get('success', False)}")
                    
                    # Extrair informações da imagem salva no SinapUm (se retornada)
                    image_url = result.get('image_url') or result.get('saved_image_url')
                    image_path = result.get('image_path')  # Caminho relativo (ex: media/uploads/uuid.jpg)
                    saved_filename = result.get('saved_filename')  # Nome do arquivo salvo
                    
                    # Usar image_path no JSON do produto (caminho relativo) e image_url para acesso
                    image_path_for_json = image_path or image_url
                    
                    # Transformar dados ÉVORA para formato modelo.json
                    if result.get('success') and result.get('data'):
                        try:
                            modelo_json = transform_evora_to_modelo_json(
                                result['data'],
                                image_file.name,
                                image_path=image_path_for_json  # Usar image_path (relativo) ou image_url (completo)
                            )
                            # Substituir data pelo formato modelo.json
                            result['data'] = modelo_json
                            # Adicionar informações da imagem salva no SinapUm
                            if image_url:
                                result['image_url'] = image_url
                            if image_path:
                                result['image_path'] = image_path
                            if saved_filename:
                                result['saved_filename'] = saved_filename
                            logger.info(f"Dados transformados para formato modelo.json. Imagem salva: {image_url or 'não retornada'}")
                        except Exception as transform_error:
                            logger.error(f"Erro ao transformar dados: {str(transform_error)}", exc_info=True)
                            # Continuar com dados originais se houver erro na transformação
                    
                    return result
                else:
                    # Tentar parsear mesmo sem Content-Type correto
                    try:
                        result = response.json()
                        logger.info(f"Análise concluída com sucesso: {result.get('success', False)}")
                        
                        # Extrair informações da imagem salva no SinapUm (se retornada)
                        image_url = result.get('image_url') or result.get('saved_image_url')
                        image_path = result.get('image_path')  # Caminho relativo (ex: media/uploads/uuid.jpg)
                        saved_filename = result.get('saved_filename')  # Nome do arquivo salvo
                        
                        # Usar image_path no JSON do produto (caminho relativo) e image_url para acesso
                        image_path_for_json = image_path or image_url
                        
                        # Transformar dados ÉVORA para formato modelo.json
                        if result.get('success') and result.get('data'):
                            try:
                                modelo_json = transform_evora_to_modelo_json(
                                    result['data'],
                                    image_file.name,
                                    image_path=image_path_for_json  # Usar image_path (relativo) ou image_url (completo)
                                )
                                result['data'] = modelo_json
                                # Adicionar informações da imagem salva no SinapUm
                                if image_url:
                                    result['image_url'] = image_url
                                if image_path:
                                    result['image_path'] = image_path
                                if saved_filename:
                                    result['saved_filename'] = saved_filename
                                logger.info(f"Dados transformados para formato modelo.json. Imagem salva: {image_url or 'não retornada'}")
                            except Exception as transform_error:
                                logger.error(f"Erro ao transformar dados: {str(transform_error)}", exc_info=True)
                        
                        return result
                    except ValueError:
                        # Resposta não é JSON - tratar como erro
                        response_text = response.text.strip()
                        logger.error(f"Resposta não-JSON recebida: {response_text}")
                        return {
                            'success': False,
                            'error': f"Resposta inesperada do servidor: {response_text}",
                            'error_code': 'INVALID_RESPONSE',
                            'raw_response': response_text
                        }
            except ValueError as json_error:
                # Erro ao parsear JSON
                response_text = response.text.strip()
                logger.error(f"Erro ao parsear JSON da resposta: {str(json_error)}. Conteúdo: {response_text}")
                return {
                    'success': False,
                    'error': f"Erro ao processar imagem: Erro ao parsear JSON da resposta: {str(json_error)}. Conteúdo: {response_text}",
                    'error_code': 'JSON_PARSE_ERROR',
                    'raw_response': response_text
                }
        else:
            # Status code diferente de 200
            response_text = response.text.strip()
            error_msg = f"Erro na API OpenMind AI (status {response.status_code}): {response_text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_code': 'API_ERROR',
                'status_code': response.status_code,
                'raw_response': response_text
            }
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro de conexão com OpenMind AI: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'error_code': 'CONNECTION_ERROR'
        }
    except Exception as e:
        error_msg = f"Erro inesperado: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg,
            'error_code': 'UNKNOWN_ERROR'
        }


def analyze_multiple_images(image_files, language='pt-BR', user=None):
    """
    Analisa múltiplas imagens e verifica se são do mesmo produto.
    
    Args:
        image_files: Lista de arquivos de imagem (Django UploadedFile)
        language: Código do idioma (ex: 'pt-BR', 'en-US', 'es-ES'). Padrão: 'pt-BR'
        user: Usuário Django (opcional) - para detectar idioma do perfil
    
    Returns:
        dict: Resultado da análise com informações sobre consistência dos produtos
    """
    results = []
    produtos_identificados = []
    
    # Detectar idioma do usuário se fornecido
    if user:
        detected_lang = _detect_user_language(user)
        if detected_lang:
            language = detected_lang
    
    for idx, image_file in enumerate(image_files):
        logger.info(f"Analisando imagem {idx + 1}/{len(image_files)}: {image_file.name}")
        
        # Resetar ponteiro do arquivo
        image_file.seek(0)
        
        # Analisar imagem com idioma
        result = analyze_image_with_openmind(image_file, language=language, user=user)
        
        if result.get('success') and result.get('data'):
            produto_data = result['data']
            produtos_identificados.append({
                'index': idx,
                'filename': image_file.name,
                'produto_data': produto_data
            })
        
        results.append({
            'index': idx,
            'filename': image_file.name,
            'result': result
        })
    
    # Verificar consistência dos produtos
    consistencia = verificar_consistencia_produtos(produtos_identificados)
    
    # Se todas as imagens são do mesmo produto, consolidar dados
    if consistencia['mesmo_produto'] and len(produtos_identificados) > 0:
        produto_consolidado = consolidar_produto_multiplas_imagens(produtos_identificados)
        return {
            'success': True,
            'mesmo_produto': True,
            'produto_consolidado': produto_consolidado,
            'analises_individuais': results,
            'consistencia': consistencia,
            'total_imagens': len(image_files)
        }
    else:
        # Produtos diferentes ou erro na análise
        return {
            'success': True,
            'mesmo_produto': False,
            'produtos_diferentes': produtos_identificados,
            'analises_individuais': results,
            'consistencia': consistencia,
            'total_imagens': len(image_files),
            'aviso': 'As imagens parecem ser de produtos diferentes. Verifique antes de salvar.'
        }


def verificar_consistencia_produtos(produtos_identificados):
    """
    Verifica se as imagens são do mesmo produto comparando nome, marca e código de barras.
    
    Args:
        produtos_identificados: Lista de dicionários com dados dos produtos identificados
    
    Returns:
        dict: Informações sobre consistência
    """
    if len(produtos_identificados) < 2:
        return {
            'mesmo_produto': True,
            'confianca': 1.0,
            'detalhes': 'Apenas uma imagem analisada'
        }
    
    # Extrair informações principais de cada produto
    produtos_info = []
    for prod in produtos_identificados:
        produto = prod['produto_data'].get('produto', {})
        produtos_info.append({
            'nome': produto.get('nome', '').lower().strip(),
            'marca': produto.get('marca', '').lower().strip(),
            'codigo_barras': produto.get('codigo_barras', ''),
            'categoria': produto.get('categoria', '').lower().strip()
        })
    
    # Comparar produtos
    mesmo_nome = all(p['nome'] == produtos_info[0]['nome'] for p in produtos_info if p['nome'])
    mesma_marca = all(p['marca'] == produtos_info[0]['marca'] for p in produtos_info if p['marca'])
    mesmo_codigo = all(p['codigo_barras'] == produtos_info[0]['codigo_barras'] for p in produtos_info if p['codigo_barras'] and produtos_info[0]['codigo_barras'])
    mesma_categoria = all(p['categoria'] == produtos_info[0]['categoria'] for p in produtos_info if p['categoria'])
    
    # Calcular confiança
    fatores = [mesmo_nome, mesma_marca, mesmo_codigo, mesma_categoria]
    confianca = sum(fatores) / len(fatores) if fatores else 0.0
    
    mesmo_produto = confianca >= 0.75  # 75% de similaridade
    
    return {
        'mesmo_produto': mesmo_produto,
        'confianca': confianca,
        'detalhes': {
            'mesmo_nome': mesmo_nome,
            'mesma_marca': mesma_marca,
            'mesmo_codigo_barras': mesmo_codigo,
            'mesma_categoria': mesma_categoria
        },
        'produtos_comparados': len(produtos_identificados)
    }


def consolidar_produto_multiplas_imagens(produtos_identificados):
    """
    Consolida dados de múltiplas imagens do mesmo produto.
    
    Args:
        produtos_identificados: Lista de produtos identificados (mesmo produto)
    
    Returns:
        dict: Produto consolidado com todas as imagens
    """
    if not produtos_identificados:
        return None
    
    # Usar o primeiro produto como base
    produto_base = produtos_identificados[0]['produto_data'].copy()
    
    # Coletar todas as imagens
    todas_imagens = []
    for prod in produtos_identificados:
        imagens = prod['produto_data'].get('produto', {}).get('imagens', [])
        todas_imagens.extend(imagens)
    
    # Remover duplicatas mantendo ordem
    imagens_unicas = []
    for img in todas_imagens:
        if img not in imagens_unicas:
            imagens_unicas.append(img)
    
    # Atualizar array de imagens
    if 'produto' in produto_base:
        produto_base['produto']['imagens'] = imagens_unicas
    
    # Atualizar fonte do cadastro_meta para indicar múltiplas imagens
    if 'cadastro_meta' in produto_base:
        total_imagens = len(produtos_identificados)
        produto_base['cadastro_meta']['fonte'] = f"Análise automática de {total_imagens} imagem(ns) do mesmo produto"
    
    return produto_base
