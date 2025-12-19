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
from typing import Dict, Optional, List
from django.utils import timezone
from django.db import transaction
from .models import (
    WhatsappGroup, WhatsappParticipant, WhatsappConversation,
    OfertaProduto, IntencaoSocial, ConversaContextualizada, CarrinhoInvisivel,
    ProdutoJSON
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
        
        # Processar intenção da mensagem
        intencao = self._detectar_intencao_negociacao(mensagem)
        
        # Processar com IA-Vendedor
        from .ia_vendedor_agent import IAVendedorAgent
        ia_vendedor = IAVendedorAgent()
        resposta = ia_vendedor.processar_mensagem(
            conversa_contextualizada=conversa_contextualizada,
            mensagem_cliente=mensagem,
            intencao=intencao
        )
        
        return {
            'tipo': 'negociacao_privada',
            'intencao': intencao,
            'resposta': resposta,
            'carrinho_atualizado': resposta.get('carrinho_atualizado', False)
        }
    
    def _detectar_intencao_negociacao(self, mensagem: str) -> Dict:
        """Detecta intenção na mensagem do cliente"""
        mensagem_lower = mensagem.lower()
        
        # Adicionar ao pedido
        if any(palavra in mensagem_lower for palavra in ['quero', 'adiciona', 'coloca', 'vou querer']):
            return {'acao': 'adicionar_pedido', 'quantidade': self._extrair_quantidade(mensagem)}
        
        # Pergunta sobre preço
        if any(palavra in mensagem_lower for palavra in ['quanto', 'preço', 'custa', 'valor']):
            return {'acao': 'pergunta_preco'}
        
        # Pergunta sobre entrega
        if any(palavra in mensagem_lower for palavra in ['entrega', 'envio', 'frete', 'chega']):
            return {'acao': 'pergunta_entrega'}
        
        # Finalizar pedido
        if any(palavra in mensagem_lower for palavra in ['finalizar', 'fechar', 'pagar', 'confirmar']):
            return {'acao': 'finalizar_pedido'}
        
        # Quantidade específica
        if any(palavra in mensagem_lower for palavra in ['2x', '3x', 'duas', 'três', 'quatro']):
            return {'acao': 'definir_quantidade', 'quantidade': self._extrair_quantidade(mensagem)}
        
        return {'acao': 'conversa_geral'}
    
    def _extrair_quantidade(self, mensagem: str) -> int:
        """Extrai quantidade mencionada na mensagem"""
        import re
        # Buscar padrões como "2x", "duas", "3 unidades"
        match = re.search(r'(\d+)\s*(x|unidades?|un\.?)', mensagem.lower())
        if match:
            return int(match.group(1))
        
        # Buscar palavras numéricas
        numeros = {
            'uma': 1, 'um': 1, 'dois': 2, 'duas': 2,
            'três': 3, 'quatro': 4, 'cinco': 5
        }
        for palavra, num in numeros.items():
            if palavra in mensagem.lower():
                return num
        
        return 1
    
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

