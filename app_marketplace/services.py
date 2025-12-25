"""
KMN (Keeper Mesh Network) Services
Sistema de resolução de papéis, ofertas e comissionamento para DropKeeper

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
# PROMPT SERVICES - Mapeamento de Prompts do Core_SinapUm
# ============================================================================

def get_prompt_from_database(prompt_key, fallback_prompt=None):
    """
    Busca um prompt do banco de dados (Core_SinapUm) usando o mapeamento configurado.
    
    Args:
        prompt_key: Chave do mapeamento (ex: 'analise_produto_imagem')
        fallback_prompt: Prompt padrão caso não encontre no banco (opcional)
    
    Returns:
        str: Conteúdo do prompt ou fallback_prompt se não encontrar
    """
    from django.conf import settings
    from django.apps import apps
    
    try:
        # Obter tipo_servico do mapeamento
        prompt_mapping = getattr(settings, 'PROMPT_MAPPING', {})
        tipo_servico = prompt_mapping.get(prompt_key)
        
        if not tipo_servico:
            logger.warning(f"Chave '{prompt_key}' não encontrada no PROMPT_MAPPING, usando fallback")
            return fallback_prompt
        
        logger.info(f"Buscando prompt: chave='{prompt_key}', tipo_servico='{tipo_servico}'")
        
        try:
            PromptTemplate = apps.get_model('app_sinapum', 'PromptTemplate')
            # Buscar por tipo_prompt (campo correto do modelo)
            prompt_obj = PromptTemplate.objects.filter(
                tipo_prompt=tipo_servico,  # tipo_servico aqui é na verdade o tipo_prompt
                ativo=True
            ).first()
            
            if prompt_obj:
                logger.info(f"✅ Prompt obtido: {prompt_obj.nome} (tipo: {tipo_servico}, {len(prompt_obj.prompt_text)} caracteres)")
                return prompt_obj.prompt_text
            else:
                logger.warning(f"⚠️ Nenhum PromptTemplate ativo encontrado para '{tipo_servico}'")
        except LookupError:
            logger.warning("App 'app_sinapum' não encontrado ou modelo PromptTemplate não existe")
        except Exception as e:
            logger.warning(f"Erro ao buscar prompt do banco: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao buscar prompt: {str(e)}", exc_info=True)
    
    # Retornar fallback se não encontrou
    if fallback_prompt:
        logger.info("Usando prompt padrão (fallback)")
        return fallback_prompt
    
    return None

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
# MCP SERVICES - Análise de Imagens via MCP
# ============================================================================

MCP_SERVICE_URL = None
MCP_API_KEY = None

def _get_mcp_config():
    """Obtém configurações do MCP Service do Django settings"""
    global MCP_SERVICE_URL, MCP_API_KEY
    if MCP_SERVICE_URL is None:
        from django.conf import settings
        # URL padrão do MCP Service
        default_url = 'http://69.169.102.84:7010'
        MCP_SERVICE_URL = getattr(settings, 'MCP_SERVICE_URL', default_url)
        MCP_API_KEY = getattr(settings, 'MCP_API_KEY', None)
        # Fallback: usar SINAPUM_API_KEY se MCP_API_KEY não estiver configurado
        if not MCP_API_KEY:
            MCP_API_KEY = getattr(settings, 'SINAPUM_API_KEY', None)
    return MCP_SERVICE_URL, MCP_API_KEY


# ============================================================================
# OPENMIND AI SERVICES (Legado - mantido para compatibilidade)
# ============================================================================

OPENMIND_AI_URL = None
OPENMIND_AI_KEY = None

def _get_openmind_config():
    """Obtém configurações do OpenMind AI do Django settings"""
    global OPENMIND_AI_URL, OPENMIND_AI_KEY
    if OPENMIND_AI_URL is None:
        from django.conf import settings
        # URL padrão do servidor (OpenMind AI)
        default_url = 'http://127.0.0.1:5000'
        OPENMIND_AI_URL = getattr(settings, 'OPENMIND_AI_URL', default_url)
        OPENMIND_AI_KEY = getattr(settings, 'OPENMIND_AI_KEY', None)
    return OPENMIND_AI_URL, OPENMIND_AI_KEY


def _detect_user_language(user):
    """
    Detecta o idioma preferido do usuário a partir do perfil (PersonalShopper ou AddressKeeper).
    
    Args:
        user: Usuário Django
    
    Returns:
        str: Código do idioma (ex: 'pt-BR', 'en-US') ou None
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        # Tentar obter do PersonalShopper
        if hasattr(user, 'personalshopper'):
            return user.personalshopper.idioma
    except Exception:
        pass
    
    try:
        # Tentar obter do AddressKeeper
        if hasattr(user, 'address_keeper'):
            return user.address_keeper.idioma
    except Exception:
        pass
    
    return None


def analyze_image_with_mcp(image_file, language='pt-BR', user=None, context_pack=None):
    """
    Analisa uma imagem usando o MCP Service (Model Context Protocol).
    
    Esta é a função recomendada para análise de imagens, usando a arquitetura MCP-aware
    com Context Pack para rastreamento completo e contexto enriquecido.
    
    Args:
        image_file: Arquivo de imagem (Django UploadedFile)
        language: Código do idioma (ex: 'pt-BR', 'en-US', 'es-ES'). Padrão: 'pt-BR'
        user: Usuário Django (opcional) - para detectar idioma do perfil e enriquecer Context Pack
        context_pack: Context Pack MCP-aware (opcional) - se não fornecido, será gerado automaticamente
    
    Returns:
        dict: Resposta da tool MCP com dados extraídos
    """
    import uuid
    import base64
    from datetime import datetime
    
    try:
        # Detectar idioma do usuário se fornecido
        if user:
            detected_lang = _detect_user_language(user)
            if detected_lang:
                language = detected_lang
        
        # Obter configurações do MCP Service
        mcp_url, mcp_api_key = _get_mcp_config()
        
        if not mcp_api_key:
            logger.warning("MCP_API_KEY não configurada, tentando usar método legado")
            return analyze_image_with_openmind(image_file, language, user)
        
        # Preparar imagem para envio
        image_file.seek(0)
        image_data = image_file.read()
        image_filename = image_file.name or "product_image.jpg"
        
        # Converter imagem para base64 (MCP aceita base64 ou URL)
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Gerar Context Pack se não fornecido
        if context_pack is None:
            request_id = str(uuid.uuid4())
            trace_id = str(uuid.uuid4())
            
            # Enriquecer com informações do usuário se disponível
            actor = {"type": "service", "id": "evora_marketplace"}
            source = {"channel": "web", "conversation_id": None}
            
            if user and user.is_authenticated:
                actor = {
                    "type": "user",
                    "id": str(user.id),
                    "username": user.username
                }
                source["conversation_id"] = f"user_{user.id}"
            
            context_pack = {
                "meta": {
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "actor": actor,
                    "source": source
                },
                "task": {
                    "name": "analisar_produto_imagem",
                    "goal": "Extrair informações estruturadas de produto a partir de imagem",
                    "constraints": [
                        "Não inventar informações",
                        "Extrair apenas dados visíveis na imagem",
                        f"Responder em {language}"
                    ]
                },
                "context": {
                    "user_profile": {
                        "language": language,
                        "user_id": str(user.id) if user and user.is_authenticated else None
                    },
                    "domain_profile": {
                        "business_type": "marketplace",
                        "region": "BR"
                    }
                },
                "response_contract": {
                    "mode": "json",
                    "language": language
                }
            }
        
        # Preparar input da tool
        tool_input = {
            "image_base64": f"data:image/jpeg;base64,{image_base64}",
            "prompt_params": {
                "language": language
            }
        }
        
        # Preparar requisição para MCP Service
        mcp_request = {
            "tool": "vitrinezap.analisar_produto",
            "version": "1.0",  # Usar versão atual
            "context_pack": context_pack,
            "input": tool_input
        }
        
        # Fazer requisição ao MCP Service
        mcp_endpoint = f"{mcp_url.rstrip('/')}/mcp/call"
        headers = {
            "Content-Type": "application/json",
            "X-SINAPUM-KEY": mcp_api_key
        }
        
        logger.info(f"[MCP] Enviando requisição para MCP Service: {mcp_endpoint}")
        logger.info(f"[MCP] Request ID: {context_pack['meta']['request_id']}")
        logger.info(f"[MCP] Trace ID: {context_pack['meta']['trace_id']}")
        
        response = requests.post(
            mcp_endpoint,
            json=mcp_request,
            headers=headers,
            timeout=90  # Timeout maior para análise de IA
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Verificar se a tool foi executada com sucesso
            if result.get('ok'):
                output = result.get('output', {})
                
                # Extrair dados da resposta
                data = output.get('data', {})
                image_url = output.get('image_url')
                image_path = output.get('image_path')
                saved_filename = output.get('saved_filename')
                
                # Formatar resposta no formato esperado pelo Evora
                return {
                    'success': True,
                    'data': data,
                    'image_url': image_url,
                    'image_path': image_path,
                    'saved_filename': saved_filename,
                    'request_id': result.get('request_id'),
                    'trace_id': result.get('trace_id'),
                    'latency_ms': result.get('latency_ms', 0)
                }
            else:
                # Tool retornou erro
                error = result.get('error', {})
                error_message = error.get('message', 'Erro desconhecido na análise')
                error_code = error.get('code', 'TOOL_ERROR')
                
                logger.error(f"[MCP] Erro na tool: {error_message}")
                
                return {
                    'success': False,
                    'error': error_message,
                    'error_code': error_code,
                    'request_id': result.get('request_id'),
                    'trace_id': result.get('trace_id')
                }
        else:
            # Erro HTTP
            error_text = response.text
            logger.error(f"[MCP] Erro HTTP {response.status_code}: {error_text}")
            
            try:
                error_json = response.json()
                error_message = error_json.get('detail', error_text)
            except:
                error_message = error_text
            
            return {
                'success': False,
                'error': f"Erro ao chamar MCP Service: {error_message}",
                'error_code': 'MCP_SERVICE_ERROR',
                'status_code': response.status_code
            }
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro de conexão com MCP Service: {str(e)}"
        logger.error(error_msg)
        # Fallback para método legado
        logger.info("Tentando fallback para método legado (OpenMind direto)")
        return analyze_image_with_openmind(image_file, language, user)
    except Exception as e:
        error_msg = f"Erro inesperado ao usar MCP: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Fallback para método legado
        logger.info("Tentando fallback para método legado (OpenMind direto)")
        return analyze_image_with_openmind(image_file, language, user)


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
        
        # Buscar prompt do banco de dados usando mapeamento configurável
        fallback_prompt = """Analise esta imagem de um produto e extraia TODAS as informações visíveis no rótulo, etiqueta ou embalagem.

Extraia as seguintes informações:
- Nome do produto
- Marca
- Categoria (se visível)
- Código de barras (se visível)
- Descrição/ingredientes (se visível)
- Informações nutricionais (se visível)
- Dimensões da embalagem (se visível)
- Peso/volume (se visível)
- Qualquer outra informação relevante visível na imagem

Retorne os dados em formato JSON estruturado compatível com o modelo ÉVORA."""
        
        prompt = get_prompt_from_database(
            prompt_key='analise_produto_imagem',
            fallback_prompt=fallback_prompt
        )
        
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
        
        data = {
            'prompt': prompt,
            'language': language
        }
        
        logger.info(f"Enviando imagem para análise: {image_file.name} (idioma: {language})")
        logger.info(f"Prompt incluído: {len(prompt)} caracteres")
        response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
        
        # Verificar se a resposta é JSON válido
        content_type = response.headers.get('Content-Type', '')
        
        if response.status_code == 200:
            try:
                # Verificar se o Content-Type indica JSON
                if 'application/json' in content_type:
                    result = response.json()
                    logger.info(f"Análise concluída com sucesso: {result.get('success', False)}")
                    
                    # DEBUG: Log completo da resposta do SinapUm
                    import json as json_module
                    logger.info(f"[SERVICES] Resposta completa do SinapUm (primeiros 3000 chars):")
                    logger.info(f"{json_module.dumps(result, indent=2, ensure_ascii=False)[:3000]}")
                    
                    # Verificar se há dados detalhados na resposta
                    if result.get('data'):
                        dados_ia = result['data']
                        logger.info(f"[SERVICES] Dados da análise (result['data']):")
                        logger.info(f"[SERVICES]   Tipo: {type(dados_ia)}")
                        logger.info(f"[SERVICES]   Chaves: {list(dados_ia.keys()) if isinstance(dados_ia, dict) else 'não é dict'}")
                        if isinstance(dados_ia, dict):
                            logger.info(f"[SERVICES]   Tem 'caracteristicas': {'caracteristicas' in dados_ia}")
                            logger.info(f"[SERVICES]   Tem 'compatibilidade': {'compatibilidade' in dados_ia}")
                            logger.info(f"[SERVICES]   Tem 'dimensoes_embalagem': {'dimensoes_embalagem' in dados_ia}")
                            logger.info(f"[SERVICES]   Dados completos (primeiros 2000 chars): {json_module.dumps(dados_ia, indent=2, ensure_ascii=False)[:2000]}")
                    
                    # Extrair informações da imagem salva no SinapUm (se retornada)
                    image_url = result.get('image_url') or result.get('saved_image_url')
                    image_path = result.get('image_path')  # Caminho relativo (ex: media/uploads/uuid.jpg)
                    saved_filename = result.get('saved_filename')  # Nome do arquivo salvo
                    
                    # DEBUG: Log dos dados recebidos do SinapUm
                    logger.info(f"[SERVICES] Dados recebidos do SinapUm:")
                    logger.info(f"[SERVICES]   image_url original: {image_url}")
                    logger.info(f"[SERVICES]   image_path original: {image_path}")
                    logger.info(f"[SERVICES]   saved_filename: {saved_filename}")
                    
                    # Corrigir URL malformada (ex: mediauploads -> media/uploads)
                    if image_url and 'mediauploads' in image_url:
                        logger.warning(f"[SERVICES] URL malformada detectada, corrigindo: {image_url}")
                        image_url = image_url.replace('mediauploads', 'media/uploads')
                        logger.info(f"[SERVICES]   image_url corrigida: {image_url}")
                    
                    # Se image_url estiver incorreto ou ausente, construir a partir do image_path
                    if image_path and (not image_url or 'mediauploads' in image_url):
                        url_base, _ = _get_openmind_config()
                        sinapum_base = url_base.replace('/api/v1', '').rstrip('/')
                        logger.info(f"[SERVICES] Construindo URL a partir do image_path: {image_path}")
                        logger.info(f"[SERVICES]   sinapum_base: {sinapum_base}")
                        
                        # Garantir que image_path começa com media/
                        if image_path.startswith('media/'):
                            image_url = f"{sinapum_base}/{image_path}"
                        elif image_path.startswith('/media/'):
                            image_url = f"{sinapum_base}{image_path}"
                        else:
                            # Adicionar media/ se não tiver
                            image_url = f"{sinapum_base}/media/{image_path.lstrip('/')}"
                        
                        logger.info(f"[SERVICES]   image_url construída: {image_url}")
                    
                    # Usar image_path no JSON do produto (caminho relativo) e image_url para acesso
                    image_path_for_json = image_path or image_url
                    
                    # DEBUG: Log final
                    logger.info(f"[SERVICES] Dados finais:")
                    logger.info(f"[SERVICES]   image_url final: {image_url}")
                    logger.info(f"[SERVICES]   image_path_for_json: {image_path_for_json}")
                    
                    # Verificar se dados já estão no formato modelo.json ou precisam transformação
                    if result.get('success') and result.get('data'):
                        try:
                            # DEBUG: Log dos dados recebidos do SinapUm ANTES da transformação
                            import json as json_module
                            dados_originais = result['data']
                            logger.info(f"[SERVICES] Dados recebidos do SinapUm (ANTES transformação):")
                            logger.info(f"[SERVICES]   Tipo: {type(dados_originais)}")
                            logger.info(f"[SERVICES]   Chaves principais: {list(dados_originais.keys()) if isinstance(dados_originais, dict) else 'não é dict'}")
                            
                            # Verificar se já está no formato modelo.json (tem 'produto', 'produto_generico_catalogo', etc.)
                            ja_esta_modelo_json = (
                                isinstance(dados_originais, dict) and
                                'produto' in dados_originais and
                                'produto_generico_catalogo' in dados_originais
                            )
                            
                            if ja_esta_modelo_json:
                                logger.info(f"[SERVICES] ✓ Dados já estão no formato modelo.json - preservando estrutura original")
                                # Fazer deep copy para não modificar o original
                                import copy
                                modelo_json = copy.deepcopy(dados_originais)
                                
                                # IMPORTANTE: Garantir que TODOS os campos do produto original sejam preservados DIRETAMENTE no produto
                                # Não apenas no analise_ia, mas diretamente acessíveis
                                if 'produto' in modelo_json and isinstance(modelo_json['produto'], dict):
                                    produto_original = dados_originais.get('produto', {})
                                    produto_atualizado = modelo_json['produto']
                                    
                                    # PRESERVAR TODOS os campos do produto original diretamente no produto
                                    # Mesmo que já existam, garantir que não sejam sobrescritos
                                    for campo, valor in produto_original.items():
                                        # Se o campo não existe ou está None/vazio, usar o valor original
                                        if campo not in produto_atualizado or not produto_atualizado.get(campo):
                                            produto_atualizado[campo] = valor
                                        # Se ambos existem, preservar o original se o atual está vazio/null
                                        elif produto_atualizado.get(campo) is None or produto_atualizado.get(campo) == '':
                                            produto_atualizado[campo] = valor
                                        # Se ambos têm valores, preservar o original como backup
                                        elif campo in ['caracteristicas', 'dimensoes_embalagem', 'fabricacao']:
                                            # Para campos complexos, garantir que todos os subcampos sejam preservados
                                            if isinstance(valor, dict) and isinstance(produto_atualizado.get(campo), dict):
                                                # Mesclar dicionários para preservar todas as chaves
                                                for subcampo, subvalor in valor.items():
                                                    if subcampo not in produto_atualizado[campo] or produto_atualizado[campo][subcampo] is None:
                                                        produto_atualizado[campo][subcampo] = subvalor
                                    
                                    # Garantir que imagens estão no array produto.imagens
                                    if 'imagens' not in produto_atualizado:
                                        produto_atualizado['imagens'] = []
                                    if image_path_for_json and image_path_for_json not in produto_atualizado['imagens']:
                                        produto_atualizado['imagens'].insert(0, image_path_for_json)
                                
                                # Criar ou atualizar campo analise_ia com TODOS os dados originais preservados
                                if 'analise_ia' not in modelo_json:
                                    modelo_json['analise_ia'] = {}
                                
                                # PRESERVAR TODA A ESTRUTURA ORIGINAL no analise_ia como backup completo
                                # Isso garante que nenhum dado seja perdido, mesmo que não esteja no produto principal
                                modelo_json['analise_ia']['dados_originais_completos'] = copy.deepcopy(dados_originais)
                                
                                # Preservar dados específicos do produto que podem ser úteis
                                if isinstance(dados_originais.get('produto'), dict):
                                    produto_original = dados_originais['produto']
                                    
                                    # Preservar características completas (mesmo que tenham nulls)
                                    if 'caracteristicas' in produto_original:
                                        modelo_json['analise_ia']['caracteristicas_completas'] = copy.deepcopy(produto_original['caracteristicas'])
                                    
                                    # Preservar dimensões completas (mesmo que tenham nulls)
                                    if 'dimensoes_embalagem' in produto_original:
                                        modelo_json['analise_ia']['dimensoes_embalagem_completas'] = copy.deepcopy(produto_original['dimensoes_embalagem'])
                                    
                                    # Preservar fabricação completa
                                    if 'fabricacao' in produto_original:
                                        modelo_json['analise_ia']['fabricacao_completa'] = copy.deepcopy(produto_original['fabricacao'])
                                    
                                    # Preservar TODOS os outros campos do produto (mesmo que None) como backup
                                    campos_produto_principais = {'nome', 'marca', 'descricao', 'categoria', 'subcategoria', 
                                                              'codigo_barras', 'imagens', 'caracteristicas', 'dimensoes_embalagem',
                                                              'peso_embalagem_gramas', 'preco_visivel', 'fabricacao'}
                                    for campo, valor in produto_original.items():
                                        if campo not in campos_produto_principais:
                                            # Preservar mesmo se None, como documentação do que foi retornado
                                            modelo_json['analise_ia'][f'produto_{campo}'] = valor
                                
                                # Preservar TODOS os outros campos do nível raiz que não estão mapeados
                                campos_raiz_mapeados = {'produto', 'produto_generico_catalogo', 'produto_viagem', 
                                                        'estabelecimento', 'campanha', 'shopper', 'cadastro_meta', 'analise_ia'}
                                for campo, valor in dados_originais.items():
                                    if campo not in campos_raiz_mapeados:
                                        # Preservar mesmo se None
                                        modelo_json['analise_ia'][f'raiz_{campo}'] = valor
                                
                                # Preservar metadados da análise original
                                if 'cadastro_meta' in dados_originais:
                                    modelo_json['analise_ia']['cadastro_meta_original'] = copy.deepcopy(dados_originais['cadastro_meta'])
                                
                                logger.info(f"[SERVICES] ✓ Estrutura original preservada com TODOS os campos. Campo analise_ia criado com backup completo.")
                                
                            else:
                                logger.info(f"[SERVICES] Dados no formato ÉVORA - aplicando transformação")
                                modelo_json = transform_evora_to_modelo_json(
                                    result['data'],
                                    image_file.name,
                                    image_path=image_path_for_json  # Usar image_path (relativo) ou image_url (completo)
                                )
                            
                            # DEBUG: Log dos dados APÓS processamento
                            logger.info(f"[SERVICES] Dados processados (APÓS processamento):")
                            logger.info(f"[SERVICES]   Chaves principais: {list(modelo_json.keys()) if isinstance(modelo_json, dict) else 'não é dict'}")
                            logger.info(f"[SERVICES]   Tem campo 'analise_ia': {'analise_ia' in modelo_json if isinstance(modelo_json, dict) else False}")
                            if isinstance(modelo_json, dict) and 'analise_ia' in modelo_json:
                                logger.info(f"[SERVICES]   analise_ia chaves: {list(modelo_json['analise_ia'].keys()) if isinstance(modelo_json['analise_ia'], dict) else 'não é dict'}")
                                logger.info(f"[SERVICES]   analise_ia completo: {json_module.dumps(modelo_json['analise_ia'], indent=2, ensure_ascii=False)[:1500]}")
                            
                            # Substituir data pelo formato modelo.json
                            result['data'] = modelo_json
                            # Adicionar informações da imagem salva no SinapUm
                            if image_url:
                                result['image_url'] = image_url
                            if image_path:
                                result['image_path'] = image_path
                            if saved_filename:
                                result['saved_filename'] = saved_filename
                            logger.info(f"Dados processados para formato modelo.json. Imagem salva: {image_url or 'não retornada'}")
                        except Exception as transform_error:
                            logger.error(f"Erro ao processar dados: {str(transform_error)}", exc_info=True)
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
                        
                        # Corrigir URL malformada (ex: mediauploads -> media/uploads)
                        if image_url and 'mediauploads' in image_url:
                            image_url = image_url.replace('mediauploads', 'media/uploads')
                        
                        # Se image_url estiver incorreto ou ausente, construir a partir do image_path
                        if image_path and (not image_url or 'mediauploads' in image_url):
                            url_base, _ = _get_openmind_config()
                            sinapum_base = url_base.replace('/api/v1', '').rstrip('/')
                            # Garantir que image_path começa com media/
                            if image_path.startswith('media/'):
                                image_url = f"{sinapum_base}/{image_path}"
                            elif image_path.startswith('/media/'):
                                image_url = f"{sinapum_base}{image_path}"
                            else:
                                # Adicionar media/ se não tiver
                                image_url = f"{sinapum_base}/media/{image_path.lstrip('/')}"
                        
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
            
            # Tentar extrair mensagem de erro mais clara do JSON de resposta
            error_detail = response_text
            error_code_detected = 'API_ERROR'
            
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    error_detail = error_json.get('error', response_text)
                    error_code_detected = error_json.get('error_code', error_code_detected)
                    
                    # Melhorar mensagens de erro comuns
                    if 'Root not found' in error_detail or '404' in error_detail:
                        error_detail = f"Erro de configuração no servidor Openmind AI: API OpenMind.org não encontrada. Verifique a configuração OPENMIND_ORG_BASE_URL no servidor. Detalhes: {error_detail}"
                        error_code_detected = 'OPENMIND_CONFIG_ERROR'
                    elif 'ANALYSIS_ERROR' in str(error_code_detected):
                        error_detail = f"Erro na análise de IA: {error_detail}. Verifique as configurações do servidor Openmind AI."
            except:
                pass  # Usar response_text original se não for JSON
            
            error_msg = f"Erro na API OpenMind AI (status {response.status_code}): {error_detail}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_detail if len(error_detail) < 500 else error_detail[:500] + '...',
                'error_code': error_code_detected,
                'status_code': response.status_code,
                'raw_response': response_text[:1000] if len(response_text) > 1000 else response_text
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
