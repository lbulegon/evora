"""
KMN (Keeper Mesh Network) Services
Sistema de resolução de papéis, ofertas e comissionamento para Dropkeeping
"""
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal
from django.db.models import Q, Max
from django.utils import timezone
from .models import (
    Agente, Cliente, Produto, Oferta, ClienteRelacao, 
    TrustlineKeeper, Pedido, RoleStats
)


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




