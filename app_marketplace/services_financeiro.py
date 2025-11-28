"""
Serviços de cálculo financeiro baseados no modelo oficial do VitrineZap/Évora/KMN.
Implementa o algoritmo oficial de liquidação financeira.
"""

from decimal import Decimal
from typing import Dict, Optional
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Pedido, LigacaoMesh, LiquidacaoFinanceira


class ServicoLiquidacaoFinanceira:
    """
    Serviço para calcular e processar liquidações financeiras de pedidos.
    Implementa o algoritmo oficial do PROMPT.
    """
    
    def calcular_liquidacao(
        self,
        pedido: Pedido,
        mesh_link: Optional[LigacaoMesh] = None
    ) -> Dict[str, Decimal]:
        """
        Calcula a liquidação financeira de um pedido.
        
        Algoritmo oficial:
        P_base = preço base (custo)
        P_final = valor pago pelo cliente
        M = P_final - P_base (Margem)
        
        τ_E = % da margem da ÉVORA
        M_E = τ_E · M (Évora recebe)
        M* = (1 - τ_E) · M (Margem líquida dos agentes)
        
        Se tipo_cliente == "do_shopper":
            alpha_s = 1.0
            valor_shopper = M*
            valor_keeper = 0
        
        Se tipo_cliente == "do_keeper":
            alpha_s + alpha_k = 1
            valor_shopper = alpha_s · M*
            valor_keeper = alpha_k · M*
        
        Args:
            pedido: Pedido a ser liquidado
            mesh_link: Ligação Mesh entre shopper e keeper (opcional)
        
        Returns:
            Dict com valores calculados:
            {
                "valor_margem": M,
                "valor_evora": M_E,
                "valor_shopper": valor_shopper,
                "valor_keeper": valor_keeper
            }
        """
        # 1. Obter preços
        P_base = pedido.preco_base or Decimal('0')
        P_final = pedido.preco_final or pedido.valor_total or Decimal('0')
        
        # 2. Calcular margem
        M = P_final - P_base
        
        # 3. Obter configuração financeira
        if mesh_link:
            conf = mesh_link.config_financeira
        else:
            # Configuração padrão se não houver mesh_link
            conf = {
                "taxa_evora": Decimal('0.10'),  # 10%
                "venda_clientes_shopper": {"alpha_s": Decimal('1.0')},
                "venda_clientes_keeper": {
                    "alpha_s": Decimal('0.60'),
                    "alpha_k": Decimal('0.40')
                }
            }
        
        taxa_evora = Decimal(str(conf.get("taxa_evora", 0.10)))
        
        # 4. Calcular valores da Évora e margem líquida
        M_evora = taxa_evora * M
        M_liquida = M - M_evora
        
        # 5. Determinar valores por tipo de cliente
        if pedido.tipo_cliente == Pedido.TipoCliente.DO_SHOPPER:
            # Venda para clientes do Shopper
            alpha_s = Decimal(str(conf.get("venda_clientes_shopper", {}).get("alpha_s", 1.0)))
            valor_shopper = alpha_s * M_liquida
            valor_keeper = Decimal('0')
            
        elif pedido.tipo_cliente == Pedido.TipoCliente.DO_KEEPER:
            # Venda para clientes do Keeper
            keeper_config = conf.get("venda_clientes_keeper", {})
            alpha_s = Decimal(str(keeper_config.get("alpha_s", 0.60)))
            alpha_k = Decimal(str(keeper_config.get("alpha_k", 0.40)))
            
            valor_shopper = alpha_s * M_liquida
            valor_keeper = alpha_k * M_liquida
            
        else:
            # Tipo não definido - tratar como cliente do shopper
            valor_shopper = M_liquida
            valor_keeper = Decimal('0')
        
        return {
            "valor_margem": M,
            "valor_evora": M_evora,
            "valor_shopper": valor_shopper,
            "valor_keeper": valor_keeper,
        }
    
    def criar_liquidacao(
        self,
        pedido: Pedido,
        mesh_link: Optional[LigacaoMesh] = None,
        salvar: bool = True
    ) -> LiquidacaoFinanceira:
        """
        Cria uma liquidação financeira para um pedido.
        
        Args:
            pedido: Pedido a ser liquidado
            mesh_link: Ligação Mesh (opcional, será buscada se não fornecida)
            salvar: Se True, salva a liquidação no banco
        
        Returns:
            LiquidacaoFinanceira criada
        """
        # Buscar mesh_link se não fornecido
        if not mesh_link and pedido.shopper and pedido.keeper:
            try:
                mesh_link = LigacaoMesh.objects.filter(
                    ativo=True
                ).filter(
                    (Q(agente_a=pedido.shopper, agente_b=pedido.keeper)) |
                    (Q(agente_a=pedido.keeper, agente_b=pedido.shopper))
                ).first()
            except:
                mesh_link = None
        
        # Calcular valores
        valores = self.calcular_liquidacao(pedido, mesh_link)
        
        # Criar liquidação
        liquidacao = LiquidacaoFinanceira(
            pedido=pedido,
            valor_margem=valores["valor_margem"],
            valor_evora=valores["valor_evora"],
            valor_shopper=valores["valor_shopper"],
            valor_keeper=valores["valor_keeper"],
            detalhes={
                "preco_base": float(pedido.preco_base or 0),
                "preco_final": float(pedido.preco_final or pedido.valor_total or 0),
                "taxa_evora": float(mesh_link.config_financeira.get("taxa_evora", 0.10) if mesh_link else 0.10),
                "tipo_cliente": pedido.tipo_cliente,
                "mesh_link_id": mesh_link.id if mesh_link else None,
            },
            status=LiquidacaoFinanceira.StatusLiquidacao.CALCULADA
        )
        
        if salvar:
            liquidacao.save()
        
        return liquidacao
    
    def processar_liquidacao_pedido(self, pedido: Pedido) -> LiquidacaoFinanceira:
        """
        Processa a liquidação completa de um pedido:
        1. Determina tipo_cliente se não definido
        2. Atualiza preços se necessário
        3. Cria liquidação financeira
        
        Args:
            pedido: Pedido a ser processado
        
        Returns:
            LiquidacaoFinanceira criada
        """
        # 1. Determinar tipo_cliente se não definido
        if not pedido.tipo_cliente and pedido.shopper:
            pedido.determinar_tipo_cliente(pedido.shopper)
        
        # 2. Atualizar preços se necessário
        if not pedido.preco_base or not pedido.preco_final:
            pedido.atualizar_precos()
            pedido.save()
        
        # 3. Criar liquidação
        return self.criar_liquidacao(pedido)


# Instância global do serviço
servico_liquidacao = ServicoLiquidacaoFinanceira()

