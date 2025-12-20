"""
WhatsApp Flow Engine - Motor do Fluxo Conversacional
====================================================

Implementa os princípios fundadores do Évora/VitrineZap:
- Click-to-Chat como Ato Comercial
- Intenção Social Assistida (no grupo)
- Pedido em Estado Social
- Conversa Privada como Espaço de Negociação
- Carrinho Invisível
- IA-Vendedor (não IA-Bot)

Arquitetura:
GRUPO → Atenção coletiva → Intenção Social Assistida
CLICK-TO-CHAT → Ato de passagem
PRIVADO → Negociação → Carrinho Invisível → Fechamento
KMN → Execução → Entrega → Confiança
RETORNO AO GRUPO → Prova social → Reaquecimento do ciclo
"""

import logging
import requests
from typing import Dict, Optional, List
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .models import (
    WhatsappGroup, WhatsappParticipant, WhatsappConversation,
    OfertaProduto, IntencaoSocial, ConversaContextualizada, CarrinhoInvisivel,
    ProdutoJSON, PersonalShopper, AddressKeeper
)
from app_whatsapp_integration.evolution_service import EvolutionAPIService

logger = logging.getLogger(__name__)


class WhatsAppFlowEngine:
    """
    Motor do fluxo conversacional WhatsApp.
    Gerencia transições entre grupo e privado, mantendo contexto.
    """
    
    def __init__(self):
        self.evolution_service = EvolutionAPIService()
    
    # ========================================================================
    # FLUXO GRUPO: Intenção Social Assistida
    # ========================================================================
    
    def processar_mensagem_grupo(
        self,
        grupo: WhatsappGroup,
        participante: WhatsappParticipant,
        mensagem: str,
        mensagem_id: str,
        tipo_mensagem: str = 'texto'
    ) -> Dict:
        """
        Processa mensagem no grupo WhatsApp.
        
        Princípio: No grupo nasce o desejo. No privado nasce o compromisso.
        - Intenção social é visível, reversível, não vinculante
        - NÃO gera pedido, NÃO gera carrinho, NÃO gera cobrança
        - Serve para prova social e influência coletiva
        """
        logger.info(f"[GRUPO] Mensagem de {participante.name} no grupo {grupo.name}: {mensagem[:50]}")
        
        # Verificar se mensagem referencia uma oferta (via oferta_id ou produto)
        oferta = self._identificar_oferta_na_mensagem(grupo, mensagem)
        
        if oferta:
            # Criar Intenção Social Assistida
            intencao = self._criar_intencao_social(
                oferta=oferta,
                participante=participante,
                conteudo=mensagem,
                tipo=self._classificar_intencao(mensagem),
                mensagem_id=mensagem_id
            )
            
            # Responder no grupo (prova social, sem pressão)
            resposta_grupo = self._gerar_resposta_intencao_social(intencao)
            
            return {
                'tipo': 'intencao_social',
                'intencao_id': intencao.id,
                'oferta_id': oferta.oferta_id,
                'resposta_grupo': resposta_grupo,
                'click_to_chat_disponivel': True
            }
        
        # Mensagem não relacionada a oferta
        return {
            'tipo': 'mensagem_grupo',
            'processado': True
        }
    
    def _identificar_oferta_na_mensagem(
        self,
        grupo: WhatsappGroup,
        mensagem: str
    ) -> Optional[OfertaProduto]:
        """
        Identifica se mensagem referencia uma oferta ativa.
        Pode ser via:
        - oferta_id mencionado (ex: "OFT-12345")
        - resposta a mensagem que contém oferta_id
        - menção a produto recente
        """
        # Buscar ofertas ativas do grupo (últimas 24h)
        ofertas_recentes = OfertaProduto.objects.filter(
            grupo=grupo,
            ativo=True,
            criado_em__gte=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('-criado_em')[:10]
        
        # Verificar se mensagem contém oferta_id
        for oferta in ofertas_recentes:
            if oferta.oferta_id.lower() in mensagem.lower():
                return oferta
        
        # Se não encontrou, retornar oferta mais recente (assumindo contexto)
        if ofertas_recentes.exists():
            return ofertas_recentes.first()
        
        return None
    
    def _classificar_intencao(self, mensagem: str) -> str:
        """Classifica tipo de intenção social"""
        mensagem_lower = mensagem.lower()
        
        # Emojis
        emojis_interesse = ['❤️', '👍', '🔥', '💯', '😍', '👏', '✅']
        if any(emoji in mensagem for emoji in emojis_interesse):
            return IntencaoSocial.TipoIntencao.EMOJI
        
        # Perguntas
        if any(palavra in mensagem_lower for palavra in ['quanto', 'preço', 'custa', 'tem', 'disponível']):
            return IntencaoSocial.TipoIntencao.PERGUNTA
        
        # Manifestação de interesse
        if any(palavra in mensagem_lower for palavra in ['quero', 'eu quero', 'vou querer', 'me interessa']):
            return IntencaoSocial.TipoIntencao.TEXTO
        
        # Comentário
        return IntencaoSocial.TipoIntencao.COMENTARIO
    
    def _criar_intencao_social(
        self,
        oferta: OfertaProduto,
        participante: WhatsappParticipant,
        conteudo: str,
        tipo: str,
        mensagem_id: str
    ) -> IntencaoSocial:
        """Cria registro de intenção social (não vinculante)"""
        intencao, created = IntencaoSocial.objects.get_or_create(
            oferta=oferta,
            participante=participante,
            mensagem_id=mensagem_id,
            defaults={
                'tipo': tipo,
                'conteudo': conteudo
            }
        )
        return intencao
    
    def _gerar_resposta_intencao_social(self, intencao: IntencaoSocial) -> str:
        """
        Gera resposta no grupo para intenção social.
        Princípio: Prova social, sem pressão.
        """
        oferta = intencao.oferta
        
        # Resposta leve, sem pressionar
        if intencao.tipo == IntencaoSocial.TipoIntencao.PERGUNTA:
            return f"Olá {intencao.participante.name}! 💬\n\n" \
                   f"Posso te ajudar no privado com mais detalhes sobre este produto."
        
        # Resposta para manifestação de interesse
        return f"Obrigado pelo interesse, {intencao.participante.name}! 😊\n\n" \
               f"Vou te chamar no privado para conversarmos melhor."
    
    # ========================================================================
    # CLICK-TO-CHAT: Ato de Passagem
    # ========================================================================
    
    def iniciar_click_to_chat(
        self,
        oferta_id: str,
        participante: WhatsappParticipant,
        grupo: WhatsappGroup
    ) -> ConversaContextualizada:
        """
        Inicia conversa privada via click-to-chat.
        
        Princípio: Click-to-Chat como Ato Comercial
        - Chat inicia já contextualizado com produto/oferta
        - Permite negociação real no privado
        """
        logger.info(f"[CLICK-TO-CHAT] Iniciando conversa para {participante.name} - Oferta {oferta_id}")
        
        # Buscar oferta
        try:
            oferta = OfertaProduto.objects.get(oferta_id=oferta_id, ativo=True)
        except OfertaProduto.DoesNotExist:
            raise ValueError(f"Oferta {oferta_id} não encontrada ou inativa")
        
        # Buscar ou criar conversa privada
        conversa, created = WhatsappConversation.objects.get_or_create(
            participant=participante,
            group=grupo,
            defaults={
                'conversation_id': f"PRIV-{participante.phone}-{timezone.now().timestamp()}",
                'status': 'open',
                'assigned_to': grupo.owner
            }
        )
        
        # Criar contexto da conversa
        conversa_contextualizada, created = ConversaContextualizada.objects.get_or_create(
            oferta=oferta,
            participante=participante,
            conversa=conversa,
            defaults={
                'status': ConversaContextualizada.StatusConversa.ABERTA
            }
        )
        
        # Enviar mensagem inicial contextualizada
        if not conversa_contextualizada.mensagem_inicial_enviada:
            self._enviar_mensagem_inicial_contextualizada(conversa_contextualizada)
            conversa_contextualizada.mensagem_inicial_enviada = True
            conversa_contextualizada.save()
        
        return conversa_contextualizada
    
    def _enviar_mensagem_inicial_contextualizada(
        self,
        conversa_contextualizada: ConversaContextualizada
    ):
        """Envia mensagem inicial contextualizada no privado"""
        oferta = conversa_contextualizada.oferta
        produto = oferta.produto
        participante = conversa_contextualizada.participante
        
        # Construir mensagem contextualizada
        mensagem = f"Olá {participante.name}! 👋\n\n" \
                   f"Vi seu interesse no produto:\n" \
                   f"*{produto.nome_produto}*\n"
        
        if oferta.preco_exibido:
            mensagem += f"💰 *Preço:* {oferta.moeda} {oferta.preco_exibido}\n"
        
        mensagem += f"\nComo posso te ajudar? Posso adicionar ao seu pedido se quiser."
        
        # Enviar via Evolution API
        try:
            self.evolution_service.send_text_message(
                number=participante.phone,
                text=mensagem
            )
            
            # Se houver imagem, enviar também
            if oferta.imagem_url:
                self.evolution_service.send_image_message(
                    number=participante.phone,
                    image_url=oferta.imagem_url,
                    caption=f"{produto.nome_produto}"
                )
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem inicial contextualizada: {e}")
    
    # ========================================================================
    # FLUXO PRIVADO: Negociação e Carrinho Invisível
    # ========================================================================
    
    def processar_mensagem_privada(
        self,
        conversa: WhatsappConversation,
        participante: WhatsappParticipant,
        mensagem: str,
        mensagem_id: str
    ) -> Dict:
        """
        Processa mensagem em conversa privada.
        
        Princípio: Conversa Privada como Espaço de Negociação
        - Aqui podem existir: quantidades, ajustes, valores, entrega, pagamento
        - Carrinho invisível é mantido silenciosamente
        """
        logger.info(f"[PRIVADO] Mensagem de {participante.name}: {mensagem[:50]}")
        
        # Verificar se conversa tem contexto (click-to-chat)
        try:
            conversa_contextualizada = ConversaContextualizada.objects.get(
                conversa=conversa,
                status__in=[
                    ConversaContextualizada.StatusConversa.ABERTA,
                    ConversaContextualizada.StatusConversa.NEGOCIANDO
                ]
            )
        except ConversaContextualizada.DoesNotExist:
            # Conversa sem contexto - tratar como conversa normal
            return {
                'tipo': 'conversa_sem_contexto',
                'processado': True
            }
        
        # Atualizar status para "negociando"
        if conversa_contextualizada.status == ConversaContextualizada.StatusConversa.ABERTA:
            conversa_contextualizada.status = ConversaContextualizada.StatusConversa.NEGOCIANDO
            conversa_contextualizada.save()
        
        # Processar com Agente Ágnosto do SinapUm
        resposta = self._processar_com_agente_sinapum(
            conversa_contextualizada=conversa_contextualizada,
            mensagem_cliente=mensagem,
            participante=participante
        )
        
        return {
            'tipo': 'negociacao_privada',
            'resposta': resposta.get('resposta', ''),
            'acao_tomada': resposta.get('acao_tomada', 'conversa_geral'),
            'carrinho_atualizado': resposta.get('carrinho_atualizado', False),
            'dados_adicionais': resposta.get('dados_adicionais', {})
        }
    
    def _processar_com_agente_sinapum(
        self,
        conversa_contextualizada: ConversaContextualizada,
        mensagem_cliente: str,
        participante: WhatsappParticipant
    ) -> Dict:
        """
        Processa mensagem usando Agente Ágnosto do SinapUm.
        
        Toda a lógica de IA fica no SinapUm - Django apenas faz chamada HTTP.
        """
        sinapum_url = getattr(
            settings,
            'SINAPUM_AGENT_URL',
            'http://69.169.102.84:8000/api/v1/process-message'
        )
        sinapum_api_key = getattr(
            settings,
            'SINAPUM_API_KEY',
            getattr(settings, 'OPENMIND_AI_API_KEY', None)
        )
        
        if not sinapum_api_key:
            logger.error("SINAPUM_API_KEY não configurada")
            return {
                'resposta': 'Desculpe, o sistema de atendimento está temporariamente indisponível.',
                'acao_tomada': 'erro',
                'carrinho_atualizado': False
            }
        
        try:
            # Preparar contexto
            oferta = conversa_contextualizada.oferta
            conversa = conversa_contextualizada.conversa
            
            # Obter idioma do usuário
            idioma = self._obter_idioma_usuario(conversa_contextualizada)
            
            # Preparar payload para SinapUm
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
                    "produto_nome": oferta.produto.nome_produto if oferta else None,
                    "preco": str(oferta.preco_exibido) if oferta and oferta.preco_exibido else None,
                    "moeda": oferta.moeda if oferta else 'BRL',
                    "imagem_url": oferta.imagem_url if oferta else None
                }
            }
            
            # Chamar agente SinapUm
            headers = {
                "Authorization": f"Bearer {sinapum_api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"[FLOW_ENGINE] Chamando agente SinapUm: {sinapum_url}")
            response = requests.post(
                sinapum_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[FLOW_ENGINE] Resposta do SinapUm: {data.get('action', 'N/A')}")
                
                # Processar ação se necessário (ex: adicionar ao carrinho)
                if data.get('action') == 'add_to_cart':
                    quantidade = data.get('data', {}).get('quantity', 1)
                    self.adicionar_ao_carrinho_invisivel(
                        conversa_contextualizada,
                        quantidade=quantidade
                    )
                
                return {
                    'resposta': data.get('message', ''),
                    'acao_tomada': data.get('action', 'conversa_geral'),
                    'carrinho_atualizado': data.get('action') == 'add_to_cart',
                    'dados_adicionais': data.get('data', {})
                }
            else:
                logger.error(f"Erro ao chamar agente SinapUm: {response.status_code} - {response.text}")
                return {
                    'resposta': 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
                    'acao_tomada': 'erro',
                    'carrinho_atualizado': False
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com agente SinapUm: {e}")
            return {
                'resposta': 'Desculpe, o sistema de atendimento está temporariamente indisponível. Tente novamente em alguns instantes.',
                'acao_tomada': 'erro',
                'carrinho_atualizado': False
            }
        except Exception as e:
            logger.error(f"Erro ao processar com agente SinapUm: {e}", exc_info=True)
            return {
                'resposta': 'Desculpe, ocorreu um erro inesperado. Nossa equipe foi notificada.',
                'acao_tomada': 'erro',
                'carrinho_atualizado': False
            }
    
    def _obter_idioma_usuario(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> str:
        """
        Obtém idioma preferido do usuário (Shopper ou Keeper).
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
    
    # ========================================================================
    # CARRINHO INVISÍVEL
    # ========================================================================
    
    def obter_ou_criar_carrinho(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> CarrinhoInvisivel:
        """
        Obtém ou cria carrinho invisível para conversa.
        
        Princípio: Carrinho Invisível
        - Cliente conversa, sistema anota silenciosamente
        - Nunca exibido como tela obrigatória
        """
        carrinho, created = CarrinhoInvisivel.objects.get_or_create(
            conversa_contextualizada=conversa_contextualizada
        )
        return carrinho
    
    def adicionar_ao_carrinho_invisivel(
        self,
        conversa_contextualizada: ConversaContextualizada,
        quantidade: int = 1
    ) -> CarrinhoInvisivel:
        """Adiciona produto ao carrinho invisível"""
        carrinho = self.obter_ou_criar_carrinho(conversa_contextualizada)
        oferta = conversa_contextualizada.oferta
        produto = oferta.produto
        
        # Obter preço
        preco = oferta.preco_exibido or 0
        
        # Adicionar item
        carrinho.adicionar_item(
            produto_id=produto.id,
            quantidade=quantidade,
            preco=preco,
            nome=produto.nome_produto
        )
        
        logger.info(f"[CARRINHO] Adicionado {quantidade}x {produto.nome_produto} ao carrinho invisível")
        
        return carrinho
    
    # ========================================================================
    # FECHAMENTO INDIVIDUAL
    # ========================================================================
    
    def finalizar_pedido(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> Dict:
        """
        Finaliza pedido a partir do carrinho invisível.
        
        Princípio: Fechamento Individual
        - Nunca acontece no grupo
        - Sempre acontece no privado
        - Inclui: confirmação, pagamento, entrega, responsabilidade clara
        """
        carrinho = self.obter_ou_criar_carrinho(conversa_contextualizada)
        
        if not carrinho.itens or len(carrinho.itens) == 0:
            return {
                'sucesso': False,
                'erro': 'Carrinho vazio'
            }
        
        # TODO: Criar pedido real (WhatsappOrder ou Pedido)
        # Por enquanto, apenas marcar conversa como fechada
        
        conversa_contextualizada.status = ConversaContextualizada.StatusConversa.FECHADA
        conversa_contextualizada.fechada_em = timezone.now()
        conversa_contextualizada.save()
        
        logger.info(f"[FECHAMENTO] Pedido finalizado para {conversa_contextualizada.participante.name}")
        
        return {
            'sucesso': True,
            'carrinho': {
                'itens': carrinho.itens,
                'total': str(carrinho.total),
                'moeda': carrinho.moeda
            }
        }

