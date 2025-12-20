"""
IA-Vendedor Agent - Cliente para Agente Ágnosto SinapUm
========================================================

NOTA IMPORTANTE: Toda a lógica de IA está no servidor SinapUm.
Este módulo é apenas um wrapper HTTP que chama o SinapUm.

O Django NÃO processa mensagens localmente - sempre chama o SinapUm.
Se SinapUm não estiver disponível, retorna erro apropriado.

Este módulo está DEPRECATED - use WhatsAppFlowEngine._processar_com_agente_sinapum() diretamente.
"""

import logging
from typing import Dict, Optional
from django.conf import settings
from .whatsapp_flow_engine import WhatsAppFlowEngine

logger = logging.getLogger(__name__)


class IAVendedorAgent:
    """
    Cliente para Agente Ágnosto SinapUm.
    
    DEPRECATED: Use WhatsAppFlowEngine._processar_com_agente_sinapum() diretamente.
    
    Este é apenas um wrapper para compatibilidade com código antigo.
    Toda a lógica de IA está no servidor SinapUm.
    """
    
    def __init__(self):
        logger.warning("IAVendedorAgent está deprecated. Use WhatsAppFlowEngine._processar_com_agente_sinapum()")
        self.flow_engine = WhatsAppFlowEngine()
    
    def processar_mensagem(
        self,
        conversa_contextualizada,
        mensagem_cliente: str,
        intencao: Dict
    ) -> Dict:
        """
        DEPRECATED: Use WhatsAppFlowEngine._processar_com_agente_sinapum() diretamente.
        
        Este método apenas redireciona para o flow_engine.
        """
        # Obter participante da conversa
        participante = conversa_contextualizada.participante
        
        return self.flow_engine._processar_com_agente_sinapum(
            conversa_contextualizada=conversa_contextualizada,
            mensagem_cliente=mensagem_cliente,
            participante=participante
        )
