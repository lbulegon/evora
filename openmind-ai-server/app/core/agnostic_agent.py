"""
Agente Ágnosto - Sistema de Agentes para WhatsApp
==================================================

Agente ágnosto que pode ser configurado para diferentes comportamentos
sem depender de implementação específica.

Princípios:
- Ágnosto: Não depende de implementação específica
- Configurável: Comportamento definido por configuração
- Extensível: Pode ser estendido com novos comportamentos
- Integrado: Funciona com Django Évora e Evolution API
"""

import logging
from typing import Dict, Optional, Any, List
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Papéis que o agente pode assumir"""
    VENDEDOR = "vendedor"
    ATENDENTE = "atendente"
    ASSISTENTE = "assistente"
    ANALISTA = "analista"


class AgentContext:
    """Contexto do agente para processar mensagens"""
    
    def __init__(
        self,
        conversation_id: str,
        user_phone: str,
        user_name: Optional[str] = None,
        group_id: Optional[str] = None,
        is_group: bool = False,
        offer_id: Optional[str] = None,
        language: str = "pt-BR",
        metadata: Optional[Dict] = None
    ):
        self.conversation_id = conversation_id
        self.user_phone = user_phone
        self.user_name = user_name
        self.group_id = group_id
        self.is_group = is_group
        self.offer_id = offer_id
        self.language = language
        self.metadata = metadata or {}


class AgentResponse:
    """Resposta do agente"""
    
    def __init__(
        self,
        message: str,
        action: Optional[str] = None,
        data: Optional[Dict] = None,
        should_continue: bool = True
    ):
        self.message = message
        self.action = action  # Ex: "add_to_cart", "finalize_order", "ask_question"
        self.data = data or {}
        self.should_continue = should_continue


class AgnosticAgent(ABC):
    """
    Classe base para agentes ágnostos.
    Define interface comum para todos os agentes.
    """
    
    def __init__(self, role: AgentRole, config: Optional[Dict] = None):
        self.role = role
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def process_message(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Processa uma mensagem e retorna resposta do agente.
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            AgentResponse com resposta do agente
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Retorna lista de capacidades do agente.
        Ex: ["add_to_cart", "answer_questions", "finalize_order"]
        """
        pass


class VendedorAgent(AgnosticAgent):
    """
    Agente Vendedor - Implementação do IA-Vendedor para WhatsApp.
    
    Princípio: IA-VENDEDOR (NÃO IA-BOT)
    - Confirma ("anotado", "ok")
    - Sugere com cuidado
    - Espera o tempo do cliente
    - Percebe o momento de fechar
    - Fala de forma natural
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(AgentRole.VENDEDOR, config)
        # Configurações do vendedor
        self.confirm_style = self.config.get("confirm_style", "natural")  # natural, formal, casual
        self.suggestion_level = self.config.get("suggestion_level", "careful")  # careful, moderate, aggressive
        self.language = self.config.get("language", "pt-BR")
    
    def process_message(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Processa mensagem como vendedor humano.
        """
        message_lower = message.lower().strip()
        
        # Detectar intenção
        intent = self._detect_intent(message_lower)
        
        # Processar baseado na intenção
        if intent == "add_to_cart":
            return self._handle_add_to_cart(message, context)
        elif intent == "ask_price":
            return self._handle_ask_price(message, context)
        elif intent == "ask_delivery":
            return self._handle_ask_delivery(message, context)
        elif intent == "finalize_order":
            return self._handle_finalize_order(message, context)
        elif intent == "set_quantity":
            return self._handle_set_quantity(message, context)
        else:
            return self._handle_general_conversation(message, context)
    
    def _detect_intent(self, message: str) -> str:
        """Detecta intenção da mensagem"""
        # Adicionar ao pedido
        if any(word in message for word in ['quero', 'adiciona', 'coloca', 'vou querer']):
            return "add_to_cart"
        
        # Pergunta sobre preço
        if any(word in message for word in ['quanto', 'preço', 'custa', 'valor']):
            return "ask_price"
        
        # Pergunta sobre entrega
        if any(word in message for word in ['entrega', 'envio', 'frete', 'chega']):
            return "ask_delivery"
        
        # Finalizar pedido
        if any(word in message for word in ['finalizar', 'fechar', 'pagar', 'confirmar']):
            return "finalize_order"
        
        # Definir quantidade
        if any(word in message for word in ['2x', '3x', 'duas', 'três', 'quatro']):
            return "set_quantity"
        
        return "general"
    
    def _handle_add_to_cart(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """Processa adição ao carrinho"""
        quantity = self._extract_quantity(message)
        
        response_msg = f"Perfeito! Anotei {quantity} unidade(s) no seu pedido. ✅\n\n"
        response_msg += "Quer adicionar mais alguma coisa ou podemos fechar o pedido?"
        
        return AgentResponse(
            message=response_msg,
            action="add_to_cart",
            data={"quantity": quantity}
        )
    
    def _handle_ask_price(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """Responde pergunta sobre preço"""
        # TODO: Buscar preço do produto do contexto (offer_id)
        response_msg = "O produto está por *R$ 89,90*.\n\n"
        response_msg += "Quer que eu adicione ao seu pedido?"
        
        return AgentResponse(
            message=response_msg,
            action="ask_price"
        )
    
    def _handle_ask_delivery(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """Responde pergunta sobre entrega"""
        response_msg = "Sobre a entrega, temos algumas opções:\n\n"
        response_msg += "📦 *Retirada no ponto de guarda* (Keeper)\n"
        response_msg += "🚚 *Entrega via correio* (com frete)\n"
        response_msg += "👤 *Você busca* (sem custo)\n\n"
        response_msg += "Qual opção prefere? Posso te ajudar a escolher."
        
        return AgentResponse(
            message=response_msg,
            action="ask_delivery"
        )
    
    def _handle_finalize_order(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """Processa finalização do pedido"""
        response_msg = "Perfeito! Seu pedido está quase pronto. 📝\n\n"
        response_msg += "*Resumo do pedido:*\n"
        response_msg += "• 2x Produto Exemplo\n"
        response_msg += "\n*Total: R$ 179,80*\n\n"
        response_msg += "Agora preciso de algumas informações:\n"
        response_msg += "1️⃣ Forma de pagamento (PIX, cartão, etc.)\n"
        response_msg += "2️⃣ Endereço de entrega ou retirada\n\n"
        response_msg += "Pode me passar essas informações?"
        
        return AgentResponse(
            message=response_msg,
            action="finalize_order"
        )
    
    def _handle_set_quantity(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """Processa definição de quantidade"""
        quantity = self._extract_quantity(message)
        
        response_msg = f"Entendi! Você quer {quantity} unidades.\n\n"
        response_msg += "Posso adicionar ao seu pedido?"
        
        return AgentResponse(
            message=response_msg,
            action="set_quantity",
            data={"quantity": quantity}
        )
    
    def _handle_general_conversation(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """Processa conversa geral"""
        response_msg = "Entendi! 😊\n\n"
        response_msg += "Estou aqui para te ajudar.\n\n"
        response_msg += "Se quiser, posso adicionar ao seu pedido. Ou se tiver alguma dúvida, pode perguntar!"
        
        return AgentResponse(
            message=response_msg,
            action="general_conversation"
        )
    
    def _extract_quantity(self, message: str) -> int:
        """Extrai quantidade mencionada na mensagem"""
        import re
        # Buscar padrões como "2x", "duas", "3 unidades"
        match = re.search(r'(\d+)\s*(x|unidades?|un\.?)', message.lower())
        if match:
            return int(match.group(1))
        
        # Buscar palavras numéricas
        numeros = {
            'uma': 1, 'um': 1, 'dois': 2, 'duas': 2,
            'três': 3, 'quatro': 4, 'cinco': 5
        }
        for palavra, num in numeros.items():
            if palavra in message.lower():
                return num
        
        return 1
    
    def get_capabilities(self) -> List[str]:
        """Retorna capacidades do agente vendedor"""
        return [
            "add_to_cart",
            "ask_price",
            "ask_delivery",
            "finalize_order",
            "set_quantity",
            "general_conversation"
        ]


class AgentFactory:
    """
    Factory para criar agentes ágnostos.
    Permite criar diferentes tipos de agentes baseado em configuração.
    """
    
    _agents = {
        AgentRole.VENDEDOR: VendedorAgent,
        # Adicionar outros tipos de agentes aqui
    }
    
    @classmethod
    def create_agent(
        cls,
        role: AgentRole,
        config: Optional[Dict] = None
    ) -> AgnosticAgent:
        """
        Cria um agente baseado no papel e configuração.
        
        Args:
            role: Papel do agente
            config: Configurações do agente
            
        Returns:
            Instância do agente
        """
        agent_class = cls._agents.get(role)
        if not agent_class:
            raise ValueError(f"Agente não encontrado para papel: {role}")
        
        return agent_class(config or {})
    
    @classmethod
    def register_agent(cls, role: AgentRole, agent_class: type):
        """Registra um novo tipo de agente"""
        cls._agents[role] = agent_class

