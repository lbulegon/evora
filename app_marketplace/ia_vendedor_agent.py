"""
IA-Vendedor Agent - Agente Conversacional Humano
=================================================

Implementa o Princípio 7: IA-VENDEDOR (NÃO IA-BOT)

A IA deve agir como um bom vendedor humano:
- Confirma ("anotado", "ok")
- Sugere com cuidado
- Espera o tempo do cliente
- Percebe o momento de fechar
- Fala de forma natural

Frase-canônica: "Podemos adicionar isso ao seu pedido?"

Nunca:
- Empurre
- Pressione
- Use linguagem robótica
- Acelere artificialmente

Integração com Agente Ágnosto do SinapUm:
- Pode usar agente ágnosto do servidor SinapUm para processamento
- Fallback para processamento local se SinapUm não disponível
"""

import logging
import requests
from typing import Dict, Optional
from django.utils import timezone
from django.conf import settings
from .models import (
    ConversaContextualizada, CarrinhoInvisivel,
    PersonalShopper, AddressKeeper
)
from .whatsapp_flow_engine import WhatsAppFlowEngine

logger = logging.getLogger(__name__)


class IAVendedorAgent:
    """
    Agente IA que age como vendedor humano.
    Processa mensagens do cliente e gera respostas naturais.
    
    Pode usar agente ágnosto do SinapUm ou processar localmente.
    """
    
    def __init__(self, use_sinapum_agent: bool = True):
        self.flow_engine = WhatsAppFlowEngine()
        self.use_sinapum_agent = use_sinapum_agent
        self.sinapum_agent_url = getattr(
            settings,
            'SINAPUM_AGENT_URL',
            'http://69.169.102.84:8000/api/v1/process-message'
        )
        self.sinapum_api_key = getattr(
            settings,
            'SINAPUM_API_KEY',
            getattr(settings, 'OPENMIND_AI_API_KEY', None)
        )
    
    def processar_mensagem(
        self,
        conversa_contextualizada: ConversaContextualizada,
        mensagem_cliente: str,
        intencao: Dict
    ) -> Dict:
        """
        Processa mensagem do cliente e gera resposta de vendedor humano.
        
        Tenta usar agente ágnosto do SinapUm se disponível, caso contrário
        processa localmente.
        
        Returns:
            Dict com resposta e ações tomadas
        """
        logger.info(f"[IA-VENDEDOR] Processando mensagem: {mensagem_cliente[:50]}")
        
        # Tentar usar agente ágnosto do SinapUm
        if self.use_sinapum_agent and self.sinapum_api_key:
            try:
                resultado_sinapum = self._processar_via_sinapum(
                    conversa_contextualizada,
                    mensagem_cliente
                )
                if resultado_sinapum:
                    return resultado_sinapum
            except Exception as e:
                logger.warning(f"Erro ao usar agente SinapUm, usando processamento local: {e}")
        
        # Fallback: processamento local
        return self._processar_local(conversa_contextualizada, mensagem_cliente, intencao)
    
    def _processar_via_sinapum(
        self,
        conversa_contextualizada: ConversaContextualizada,
        mensagem_cliente: str
    ) -> Optional[Dict]:
        """
        Processa mensagem via agente ágnosto do SinapUm.
        
        Returns:
            Dict com resposta ou None se erro
        """
        try:
            # Preparar contexto
            oferta = conversa_contextualizada.oferta
            participante = conversa_contextualizada.participante
            conversa = conversa_contextualizada.conversa
            
            # Obter idioma
            idioma = self._obter_idioma_usuario(conversa_contextualizada)
            
            # Preparar request
            payload = {
                "message": mensagem_cliente,
                "conversation_id": conversa.conversation_id,
                "user_phone": participante.phone,
                "user_name": participante.name,
                "group_id": conversa.group.chat_id if conversa.group else None,
                "is_group": False,  # Sempre privado aqui
                "offer_id": oferta.oferta_id if oferta else None,
                "language": idioma,
                "agent_role": "vendedor",
                "metadata": {
                    "produto_id": oferta.produto.id if oferta else None,
                    "preco": str(oferta.preco_exibido) if oferta and oferta.preco_exibido else None
                }
            }
            
            # Chamar agente SinapUm
            headers = {
                "Authorization": f"Bearer {self.sinapum_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.sinapum_agent_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'resposta': data.get('message', ''),
                    'acao_tomada': data.get('action', 'conversa_geral'),
                    'carrinho_atualizado': data.get('action') == 'add_to_cart',
                    'dados_adicionais': data.get('data', {})
                }
            else:
                logger.error(f"Erro ao chamar agente SinapUm: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com agente SinapUm: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao processar via SinapUm: {e}")
            return None
    
    def _processar_local(
        self,
        conversa_contextualizada: ConversaContextualizada,
        mensagem_cliente: str,
        intencao: Dict
    ) -> Dict:
        """
        Processa mensagem localmente (fallback).
        """
        acao = intencao.get('acao', 'conversa_geral')
        
        # Roteamento por ação
        if acao == 'adicionar_pedido':
            return self._processar_adicionar_pedido(conversa_contextualizada, intencao)
        
        elif acao == 'pergunta_preco':
            return self._processar_pergunta_preco(conversa_contextualizada)
        
        elif acao == 'pergunta_entrega':
            return self._processar_pergunta_entrega(conversa_contextualizada)
        
        elif acao == 'definir_quantidade':
            return self._processar_definir_quantidade(conversa_contextualizada, intencao)
        
        elif acao == 'finalizar_pedido':
            return self._processar_finalizar_pedido(conversa_contextualizada)
        
        else:
            return self._processar_conversa_geral(conversa_contextualizada, mensagem_cliente)
    
    def _processar_adicionar_pedido(
        self,
        conversa_contextualizada: ConversaContextualizada,
        intencao: Dict
    ) -> Dict:
        """
        Processa adição de produto ao pedido.
        
        Princípio: Confirma ("anotado", "ok")
        """
        quantidade = intencao.get('quantidade', 1)
        
        # Adicionar ao carrinho invisível
        carrinho = self.flow_engine.adicionar_ao_carrinho_invisivel(
            conversa_contextualizada,
            quantidade=quantidade
        )
        
        produto = conversa_contextualizada.oferta.produto
        
        # Resposta natural de vendedor
        if quantidade > 1:
            resposta = f"Perfeito! Anotei {quantidade} unidades de *{produto.nome_produto}* no seu pedido. ✅\n\n"
        else:
            resposta = f"Anotado! *{produto.nome_produto}* adicionado ao seu pedido. ✅\n\n"
        
        # Mostrar resumo do carrinho (sem pressionar)
        if len(carrinho.itens) > 1:
            resposta += f"Você já tem {len(carrinho.itens)} itens no pedido.\n"
            resposta += f"Total: {conversa_contextualizada.oferta.moeda} {carrinho.total}\n\n"
        
        resposta += "Quer adicionar mais alguma coisa ou podemos fechar o pedido?"
        
        return {
            'resposta': resposta,
            'carrinho_atualizado': True,
            'acao_tomada': 'produto_adicionado'
        }
    
    def _processar_pergunta_preco(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> Dict:
        """Responde pergunta sobre preço"""
        oferta = conversa_contextualizada.oferta
        produto = conversa_contextualizada.oferta.produto
        
        resposta = f"O *{produto.nome_produto}* está por "
        
        if oferta.preco_exibido:
            resposta += f"*{oferta.moeda} {oferta.preco_exibido}*"
        else:
            resposta += "preço a combinar"
        
        resposta += ".\n\n"
        
        # Sugestão leve (sem pressionar)
        resposta += "Quer que eu adicione ao seu pedido?"
        
        return {
            'resposta': resposta,
            'acao_tomada': 'preco_informado'
        }
    
    def _processar_pergunta_entrega(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> Dict:
        """Responde pergunta sobre entrega"""
        # TODO: Integrar com KMN para informações de entrega
        
        resposta = "Sobre a entrega, temos algumas opções:\n\n"
        resposta += "📦 *Retirada no ponto de guarda* (Keeper)\n"
        resposta += "🚚 *Entrega via correio* (com frete)\n"
        resposta += "👤 *Você busca* (sem custo)\n\n"
        resposta += "Qual opção prefere? Posso te ajudar a escolher."
        
        return {
            'resposta': resposta,
            'acao_tomada': 'entrega_informada'
        }
    
    def _processar_definir_quantidade(
        self,
        conversa_contextualizada: ConversaContextualizada,
        intencao: Dict
    ) -> Dict:
        """Processa definição de quantidade"""
        quantidade = intencao.get('quantidade', 1)
        
        resposta = f"Entendi! Você quer {quantidade} unidades.\n\n"
        resposta += "Posso adicionar ao seu pedido?"
        
        return {
            'resposta': resposta,
            'quantidade_sugerida': quantidade,
            'acao_tomada': 'quantidade_definida'
        }
    
    def _processar_finalizar_pedido(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> Dict:
        """
        Processa finalização do pedido.
        
        Princípio: Percebe o momento de fechar
        """
        resultado = self.flow_engine.finalizar_pedido(conversa_contextualizada)
        
        if not resultado.get('sucesso'):
            return {
                'resposta': "Seu pedido ainda está vazio. Quer adicionar algo?",
                'acao_tomada': 'pedido_vazio'
            }
        
        carrinho_data = resultado.get('carrinho', {})
        
        resposta = "Perfeito! Seu pedido está quase pronto. 📝\n\n"
        resposta += "*Resumo do pedido:*\n"
        
        for item in carrinho_data.get('itens', []):
            resposta += f"• {item.get('quantidade')}x {item.get('nome')}\n"
        
        resposta += f"\n*Total: {carrinho_data.get('moeda')} {carrinho_data.get('total')}*\n\n"
        resposta += "Agora preciso de algumas informações:\n"
        resposta += "1️⃣ Forma de pagamento (PIX, cartão, etc.)\n"
        resposta += "2️⃣ Endereço de entrega ou retirada\n\n"
        resposta += "Pode me passar essas informações?"
        
        return {
            'resposta': resposta,
            'acao_tomada': 'pedido_finalizado',
            'carrinho': carrinho_data
        }
    
    def _processar_conversa_geral(
        self,
        conversa_contextualizada: ConversaContextualizada,
        mensagem_cliente: str
    ) -> Dict:
        """
        Processa conversa geral (não identificada como ação específica).
        
        Princípio: Fala de forma natural, espera o tempo do cliente
        """
        produto = conversa_contextualizada.oferta.produto
        
        # Resposta empática e natural
        resposta = "Entendi! 😊\n\n"
        resposta += f"Estou aqui para te ajudar com o *{produto.nome_produto}*.\n\n"
        resposta += "Se quiser, posso adicionar ao seu pedido. Ou se tiver alguma dúvida, pode perguntar!"
        
        return {
            'resposta': resposta,
            'acao_tomada': 'conversa_geral'
        }
    
    def _obter_idioma_usuario(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> str:
        """
        Obtém idioma preferido do usuário (Shopper ou Keeper).
        Usado para respostas no idioma correto.
        """
        grupo = conversa_contextualizada.conversa.group
        owner = grupo.owner if grupo else None
        
        if not owner:
            return 'pt-BR'
        
        # Verificar se é PersonalShopper
        try:
            shopper = PersonalShopper.objects.get(user=owner)
            return shopper.idioma or 'pt-BR'
        except PersonalShopper.DoesNotExist:
            pass
        
        # Verificar se é AddressKeeper
        try:
            keeper = AddressKeeper.objects.get(user=owner)
            return keeper.idioma or 'pt-BR'
        except AddressKeeper.DoesNotExist:
            pass
        
        return 'pt-BR'

