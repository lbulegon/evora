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
    ProdutoJSON, PersonalShopper, AddressKeeper, WhatsappOrder,
    Pacote, Cliente
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
    # ESCOLHA DE MÉTODO DE ENTREGA
    # ========================================================================
    
    def processar_escolha_entrega(
        self,
        conversa_contextualizada: ConversaContextualizada,
        metodo_entrega: str,
        endereco_entrega: Optional[str] = None,
        address_keeper_id: Optional[int] = None
    ) -> Dict:
        """
        Processa escolha de método de entrega pelo cliente.
        
        Métodos disponíveis:
        - 'keeper': Entrega via Address Keeper (ponto de guarda)
        - 'correio': Entrega via Correios
        - 'retirada': Retirada no ponto de guarda
        - 'motoboy': Entrega via motoboy (se disponível)
        
        Princípio: Conversa Privada como Espaço de Negociação
        - Cliente escolhe método de entrega no privado
        - Informações são salvas no carrinho/pedido
        """
        try:
            carrinho = self.obter_ou_criar_carrinho(conversa_contextualizada)
            
            # Validar método de entrega
            metodos_validos = ['keeper', 'correio', 'retirada', 'motoboy']
            if metodo_entrega not in metodos_validos:
                return {
                    'sucesso': False,
                    'erro': f'Método de entrega inválido. Opções: {", ".join(metodos_validos)}'
                }
            
            # Salvar método de entrega na conversa contextualizada
            # Usar campo observacoes ou criar estrutura de dados
            # Por enquanto, vamos armazenar como parte dos dados da conversa
            # que serão usados ao criar o pedido
            
            # Armazenar dados de entrega (será usado ao criar o pedido)
            # Podemos usar um campo JSONField ou salvar em um dicionário auxiliar
            # Por enquanto, vamos criar um atributo temporário que será usado no finalizar_pedido
            if not hasattr(conversa_contextualizada, '_dados_entrega'):
                conversa_contextualizada._dados_entrega = {}
            
            conversa_contextualizada._dados_entrega = {
                'metodo_entrega': metodo_entrega,
                'endereco_entrega': endereco_entrega,
                'address_keeper_id': address_keeper_id
            }
            
            carrinho.save()
            
            logger.info(
                f"[ENTREGA] Método de entrega escolhido: {metodo_entrega} "
                f"para conversa {conversa_contextualizada.id}"
            )
            
            # Gerar mensagem de confirmação
            mensagem_confirmacao = self._gerar_mensagem_confirmacao_entrega(
                metodo_entrega,
                endereco_entrega,
                address_keeper_id
            )
            
            return {
                'sucesso': True,
                'metodo_entrega': metodo_entrega,
                'mensagem_confirmacao': mensagem_confirmacao
            }
            
        except Exception as e:
            logger.error(
                f"[ENTREGA] Erro ao processar escolha de entrega: {str(e)}",
                exc_info=True
            )
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def listar_opcoes_entrega(
        self,
        conversa_contextualizada: ConversaContextualizada
    ) -> Dict:
        """
        Lista opções de entrega disponíveis para o cliente.
        
        Busca Address Keepers disponíveis e métodos de entrega.
        """
        try:
            grupo = conversa_contextualizada.oferta.grupo
            
            # Buscar Address Keepers disponíveis no grupo ou região
            address_keepers = AddressKeeper.objects.filter(
                ativo=True,
                verificado=True
            )[:5]  # Limitar a 5 opções
            
            opcoes = []
            
            # Opção 1: Address Keeper (ponto de guarda)
            if address_keepers.exists():
                for keeper in address_keepers:
                    opcoes.append({
                        'tipo': 'keeper',
                        'id': keeper.id,
                        'nome': keeper.apelido_local or f"{keeper.cidade}, {keeper.estado}",
                        'endereco': f"{keeper.rua}, {keeper.numero} - {keeper.bairro}",
                        'cidade': keeper.cidade,
                        'aceita_retirada': keeper.aceita_retirada,
                        'aceita_envio': keeper.aceita_envio,
                        'taxa_guarda_dia': float(keeper.taxa_guarda_dia) if keeper.taxa_guarda_dia else 0
                    })
            
            # Opção 2: Correios (sempre disponível)
            opcoes.append({
                'tipo': 'correio',
                'nome': 'Correios',
                'descricao': 'Entrega via Correios (PAC ou SEDEX)',
                'prazo_estimado': '5-15 dias úteis'
            })
            
            # Opção 3: Retirada (se houver keeper disponível)
            if address_keepers.exists():
                opcoes.append({
                    'tipo': 'retirada',
                    'nome': 'Retirada no ponto de guarda',
                    'descricao': 'Retire seu pedido no ponto de guarda mais próximo'
                })
            
            return {
                'sucesso': True,
                'opcoes': opcoes
            }
            
        except Exception as e:
            logger.error(
                f"[ENTREGA] Erro ao listar opções de entrega: {str(e)}",
                exc_info=True
            )
            return {
                'sucesso': False,
                'erro': str(e),
                'opcoes': []
            }
    
    def _gerar_mensagem_confirmacao_entrega(
        self,
        metodo_entrega: str,
        endereco_entrega: Optional[str] = None,
        address_keeper_id: Optional[int] = None
    ) -> str:
        """Gera mensagem de confirmação do método de entrega escolhido"""
        mensagens = {
            'keeper': '📦 Entrega via ponto de guarda (Address Keeper)',
            'correio': '📮 Entrega via Correios',
            'retirada': '🏪 Retirada no ponto de guarda',
            'motoboy': '🏍️ Entrega via motoboy'
        }
        
        mensagem = f"✅ {mensagens.get(metodo_entrega, 'Método de entrega escolhido')}\n\n"
        
        if endereco_entrega:
            mensagem += f"📍 Endereço: {endereco_entrega}\n\n"
        
        if address_keeper_id:
            try:
                keeper = AddressKeeper.objects.get(id=address_keeper_id)
                mensagem += f"🏪 Ponto de guarda: {keeper.apelido_local or keeper.cidade}\n\n"
            except AddressKeeper.DoesNotExist:
                pass
        
        mensagem += "Perfeito! Quando finalizar o pedido, usaremos este método de entrega."
        
        return mensagem
    
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
        
        # Criar pedido real (WhatsappOrder)
        try:
            with transaction.atomic():
                # Validações
                if not conversa_contextualizada.oferta:
                    return {
                        'sucesso': False,
                        'erro': 'Oferta não encontrada na conversa contextualizada'
                    }
                
                oferta = conversa_contextualizada.oferta
                
                if not oferta.grupo:
                    return {
                        'sucesso': False,
                        'erro': 'Grupo não encontrado na oferta'
                    }
                
                grupo = oferta.grupo
                participante = conversa_contextualizada.participante
                
                if not participante:
                    return {
                        'sucesso': False,
                        'erro': 'Participante não encontrado na conversa'
                    }
                
                # Validar itens do carrinho
                if not isinstance(carrinho.itens, list):
                    return {
                        'sucesso': False,
                        'erro': 'Formato inválido dos itens do carrinho'
                    }
                
                # Preparar lista de produtos para o pedido
                produtos_pedido = []
                for item in carrinho.itens:
                    if not isinstance(item, dict):
                        logger.warning(f"[FECHAMENTO] Item inválido no carrinho: {item}")
                        continue
                    
                    quantidade = int(item.get('quantidade', 1))
                    preco = float(item.get('preco', 0))
                    
                    if quantidade <= 0:
                        logger.warning(f"[FECHAMENTO] Quantidade inválida: {quantidade}")
                        continue
                    
                    if preco < 0:
                        logger.warning(f"[FECHAMENTO] Preço inválido: {preco}")
                        continue
                    
                    produto_info = {
                        'produto_id': item.get('produto_id'),
                        'nome': item.get('nome', 'Produto'),
                        'quantidade': quantidade,
                        'preco_unitario': preco,
                        'preco_total': preco * quantidade,
                        'oferta_id': oferta.oferta_id
                    }
                    produtos_pedido.append(produto_info)
                
                if not produtos_pedido:
                    return {
                        'sucesso': False,
                        'erro': 'Nenhum item válido no carrinho'
                    }
                
                # Obter dados de entrega (se foram escolhidos)
                metodo_entrega = ''
                endereco_entrega = ''
                
                if hasattr(conversa_contextualizada, '_dados_entrega'):
                    dados_entrega = conversa_contextualizada._dados_entrega
                    metodo_entrega = dados_entrega.get('metodo_entrega', '')
                    endereco_entrega = dados_entrega.get('endereco_entrega', '')
                    
                    # Se escolheu keeper, buscar nome do keeper
                    if dados_entrega.get('address_keeper_id'):
                        try:
                            keeper = AddressKeeper.objects.get(id=dados_entrega['address_keeper_id'])
                            if not endereco_entrega:
                                endereco_entrega = f"{keeper.apelido_local or keeper.cidade}, {keeper.estado}"
                        except AddressKeeper.DoesNotExist:
                            pass
                
                # Criar WhatsappOrder
                pedido = WhatsappOrder.objects.create(
                    group=grupo,
                    customer=participante,
                    channel='whatsapp',
                    status='pending',
                    total_amount=carrinho.total,
                    currency=carrinho.moeda,
                    products=produtos_pedido,
                    payment_status='pending',
                    delivery_method=metodo_entrega or 'correio',  # Default: correio
                    delivery_address=endereco_entrega or ''  # Será preenchido depois se necessário
                )
                
                # Gerar order_number se não foi gerado automaticamente
                if not pedido.order_number:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%y%m%d%H%M")
                    pedido.order_number = f"WAP{timestamp}{pedido.id:04d}"
                    pedido.save()
                
                # Marcar conversa como fechada
                conversa_contextualizada.status = ConversaContextualizada.StatusConversa.FECHADA
                conversa_contextualizada.fechada_em = timezone.now()
                conversa_contextualizada.save()
                
                logger.info(
                    f"[FECHAMENTO] Pedido {pedido.order_number} criado para {participante.name}. "
                    f"Total: {carrinho.moeda} {carrinho.total}. Itens: {len(produtos_pedido)}"
                )
                
                # Processar pagamento (inicializar)
                resultado_pagamento = self._processar_pagamento_pedido(pedido, carrinho)
                
                # Enviar link de pagamento ao cliente no privado (se disponível)
                resultado_pagamento['pedido_numero'] = pedido.order_number
                if resultado_pagamento.get('checkout_url') or resultado_pagamento.get('qr_code'):
                    self._enviar_link_pagamento_privado(
                        conversa_contextualizada,
                        resultado_pagamento
                    )
                
                # Conectar com KMN (criar pacote para entrega)
                resultado_kmn = self._conectar_kmn_entrega(pedido, participante, produtos_pedido)
                
                # Enviar notificação de prova social no grupo
                self._enviar_notificacao_prova_social(pedido, grupo, participante, produtos_pedido)
                
                return {
                    'sucesso': True,
                    'pedido_id': pedido.id,
                    'pedido_numero': pedido.order_number,
                    'carrinho': {
                        'itens': carrinho.itens,
                        'total': str(carrinho.total),
                        'moeda': carrinho.moeda
                    },
                    'produtos': produtos_pedido,
                    'pagamento': resultado_pagamento
                }
                
        except Exception as e:
            logger.error(f"[FECHAMENTO] Erro ao criar pedido: {str(e)}", exc_info=True)
            return {
                'sucesso': False,
                'erro': f'Erro ao criar pedido: {str(e)}'
            }
    
    def _enviar_notificacao_prova_social(
        self,
        pedido: WhatsappOrder,
        grupo: WhatsappGroup,
        participante: WhatsappParticipant,
        produtos: List[Dict]
    ):
        """
        Envia notificação de prova social no grupo após fechamento do pedido.
        
        Princípio: Retorno ao Grupo → Prova Social → Reaquecimento do ciclo
        - Mensagem natural, sem pressão
        - Mostra que alguém comprou (prova social)
        - Reaquece interesse no produto
        """
        try:
            # Construir mensagem natural de prova social
            nome_cliente = participante.name or participante.phone
            
            # Listar produtos comprados
            produtos_texto = []
            for produto in produtos[:3]:  # Limitar a 3 produtos para não ficar muito longo
                nome_produto = produto.get('nome', 'Produto')
                quantidade = produto.get('quantidade', 1)
                if quantidade > 1:
                    produtos_texto.append(f"{quantidade}x {nome_produto}")
                else:
                    produtos_texto.append(nome_produto)
            
            if len(produtos) > 3:
                produtos_texto.append(f"e mais {len(produtos) - 3} item(ns)")
            
            produtos_str = ", ".join(produtos_texto)
            
            # Mensagem natural e positiva (sem pressão)
            mensagem = f"✅ {nome_cliente} comprou {produtos_str}! Obrigado! 🙏\n\n"
            mensagem += f"Pedido: {pedido.order_number}"
            
            # Enviar mensagem no grupo
            # Usar o chat_id do grupo para enviar mensagem
            grupo_chat_id = grupo.chat_id
            
            # Enviar via Evolution API
            self.evolution_service.send_text_message(
                number=grupo_chat_id,
                text=mensagem
            )
            
            logger.info(
                f"[PROVA_SOCIAL] Notificação enviada no grupo {grupo.name} "
                f"para pedido {pedido.order_number}"
            )
            
        except Exception as e:
            # Não falhar o fechamento se a notificação falhar
            logger.error(
                f"[PROVA_SOCIAL] Erro ao enviar notificação de prova social: {str(e)}",
                exc_info=True
            )
    
    def _processar_pagamento_pedido(
        self,
        pedido: WhatsappOrder,
        carrinho: CarrinhoInvisivel
    ) -> Dict:
        """
        Processa pagamento do pedido WhatsApp.
        
        Integra com gateway de pagamento (Mercado Pago) para criar link/QR Code.
        
        Princípio: Fechamento Individual
        - Pagamento sempre no privado
        - Cliente escolhe método (PIX, cartão, etc.)
        - Link/QR Code enviado via WhatsApp
        """
        try:
            from .payment_services import MercadoPagoService
            from .models import Pagamento, Pedido
            
            # Por padrão, usar PIX (mais comum no Brasil via WhatsApp)
            metodo_pagamento = 'pix'
            
            # Criar Pedido vinculado ao WhatsappOrder (se necessário para o sistema de pagamento)
            # Por enquanto, vamos criar um Pagamento diretamente ou adaptar
            
            # Verificar se há configuração do Mercado Pago
            mercadopago_service = MercadoPagoService()
            
            if not mercadopago_service.api_key:
                # Se não houver configuração, apenas inicializar como pendente
                pedido.payment_status = 'pending'
                pedido.payment_method = metodo_pagamento
                pedido.save()
                
                logger.warning(
                    f"[PAGAMENTO] Mercado Pago não configurado. "
                    f"Pagamento inicializado como pendente para pedido {pedido.order_number}"
                )
                
                return {
                    'status': 'pending',
                    'metodo': metodo_pagamento,
                    'mensagem': 'Pagamento pendente. Aguardando configuração do gateway.'
                }
            
            # Criar pagamento via gateway
            # Por enquanto, vamos criar uma estrutura básica
            # TODO: Adaptar para criar Pagamento vinculado ou usar API direta
            
            pedido.payment_status = 'pending'
            pedido.payment_method = metodo_pagamento
            pedido.save()
            
            logger.info(
                f"[PAGAMENTO] Pagamento inicializado para pedido {pedido.order_number}. "
                f"Método: {metodo_pagamento}, Status: {pedido.payment_status}"
            )
            
            # TODO: Integrar com gateway de pagamento real
            # - Criar link de pagamento (PIX QR Code, link de checkout, etc.)
            # - Enviar link para cliente no privado via WhatsApp
            # - Processar webhook quando pagamento for confirmado
            
            return {
                'status': 'pending',
                'metodo': metodo_pagamento,
                'mensagem': 'Pagamento pendente. Link será enviado em breve.',
                'gateway_configurado': bool(mercadopago_service.api_key)
            }
            
        except Exception as e:
            logger.error(
                f"[PAGAMENTO] Erro ao processar pagamento: {str(e)}",
                exc_info=True
            )
            # Não falhar o pedido se o pagamento falhar
            pedido.payment_status = 'pending'
            pedido.save()
            
            return {
                'status': 'erro',
                'erro': str(e),
                'mensagem': 'Erro ao processar pagamento. Pedido criado, pagamento pendente.'
            }
    
    def _conectar_kmn_entrega(
        self,
        pedido: WhatsappOrder,
        participante: WhatsappParticipant,
        produtos: List[Dict]
    ) -> Dict:
        """
        Conecta pedido com sistema KMN para gestão de entrega.
        
        Princípio: KMN Integration
        - Conecta conversa → operação
        - Entrega e confiança
        - Cria pacote para gestão de entrega
        """
        try:
            # Buscar ou criar cliente a partir do participante
            cliente = None
            if participante.cliente:
                cliente = participante.cliente
            else:
                # Criar cliente básico se não existir
                # TODO: Melhorar criação de cliente com dados completos
                from django.contrib.auth.models import User
                cliente_user, _ = User.objects.get_or_create(
                    username=f"whatsapp_{participante.phone}",
                    defaults={
                        'first_name': participante.name.split()[0] if participante.name else 'Cliente',
                        'last_name': ' '.join(participante.name.split()[1:]) if participante.name and len(participante.name.split()) > 1 else '',
                        'email': f"{participante.phone}@whatsapp.evora.com"
                    }
                )
                
                cliente, _ = Cliente.objects.get_or_create(
                    user=cliente_user,
                    defaults={
                        'nome': participante.name or f"Cliente {participante.phone}",
                        'whatsapp': participante.phone
                    }
                )
            
            # Buscar shopper do grupo
            grupo = pedido.group
            shopper = None
            if grupo.owner:
                try:
                    shopper = PersonalShopper.objects.get(user=grupo.owner)
                except PersonalShopper.DoesNotExist:
                    pass
            
            # Criar pacote no sistema KMN
            import uuid
            codigo_publico = f"PKG-{uuid.uuid4().hex[:8].upper()}"
            
            # Calcular valor total dos produtos
            valor_total = sum(
                Decimal(str(produto.get('preco_total', 0)))
                for produto in produtos
            )
            
            # Descrição do pacote
            produtos_nomes = [p.get('nome', 'Produto') for p in produtos[:3]]
            descricao = f"Pedido {pedido.order_number}: {', '.join(produtos_nomes)}"
            if len(produtos) > 3:
                descricao += f" e mais {len(produtos) - 3} item(ns)"
            
            pacote = Pacote.objects.create(
                codigo_publico=codigo_publico,
                cliente=cliente,
                personal_shopper=shopper,
                address_keeper=None,  # Será definido depois quando cliente escolher método de entrega
                descricao=descricao,
                valor_declarado=valor_total,
                status=Pacote.Status.CRIADO,
                observacoes=f"Pedido criado via WhatsApp: {pedido.order_number}"
            )
            
            # Atualizar pedido com referência ao pacote (se houver campo)
            # Por enquanto, apenas logar
            
            logger.info(
                f"[KMN] Pacote {pacote.codigo_publico} criado para pedido {pedido.order_number}. "
                f"Cliente: {cliente.nome}, Valor: {valor_total}"
            )
            
            return {
                'sucesso': True,
                'pacote_id': pacote.id,
                'pacote_codigo': pacote.codigo_publico,
                'status': pacote.get_status_display()
            }
            
        except Exception as e:
            logger.error(
                f"[KMN] Erro ao conectar com KMN: {str(e)}",
                exc_info=True
            )
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def _enviar_link_pagamento_privado(
        self,
        conversa_contextualizada: ConversaContextualizada,
        resultado_pagamento: Dict
    ):
        """
        Envia link de pagamento ou QR Code PIX ao cliente no privado.
        
        Princípio: Fechamento Individual
        - Pagamento sempre no privado
        - Link/QR Code enviado via WhatsApp
        """
        try:
            participante = conversa_contextualizada.participante
            
            # Obter dados do pagamento
            pedido_numero = resultado_pagamento.get('pedido_numero', 'N/A')
            metodo = resultado_pagamento.get('metodo', 'pix')
            
            # Construir mensagem de pagamento
            mensagem = f"💳 *Pagamento do Pedido {pedido_numero}*\n\n"
            
            if metodo == 'pix':
                if resultado_pagamento.get('qr_code'):
                    mensagem += "📱 *PIX - Escaneie o QR Code abaixo:*\n\n"
                    # TODO: Converter QR Code base64 em imagem e enviar
                    mensagem += f"QR Code disponível\n\n"
                elif resultado_pagamento.get('checkout_url'):
                    mensagem += f"🔗 *Link de Pagamento PIX:*\n{resultado_pagamento.get('checkout_url')}\n\n"
                else:
                    mensagem += "⏳ Link de pagamento será enviado em breve.\n\n"
            else:
                if resultado_pagamento.get('checkout_url'):
                    mensagem += f"🔗 *Link de Pagamento:*\n{resultado_pagamento.get('checkout_url')}\n\n"
                else:
                    mensagem += "⏳ Link de pagamento será enviado em breve.\n\n"
            
            mensagem += "Após o pagamento, você receberá a confirmação aqui mesmo! ✅"
            
            # Enviar via Evolution API
            self.evolution_service.send_text_message(
                number=participante.phone,
                text=mensagem
            )
            
            logger.info(
                f"[PAGAMENTO] Link de pagamento enviado para {participante.name}"
            )
            
        except Exception as e:
            # Não falhar o fechamento se o envio falhar
            logger.error(
                f"[PAGAMENTO] Erro ao enviar link de pagamento: {str(e)}",
                exc_info=True
            )
    
    def processar_confirmacao_pagamento(
        self,
        pedido_id: int,
        gateway_payment_id: str,
        status_pagamento: str,
        gateway: str = 'mercadopago'
    ) -> Dict:
        """
        Processa confirmação de pagamento via webhook.
        
        Atualiza status do pedido e envia notificações.
        
        Args:
            pedido_id: ID do WhatsappOrder
            gateway_payment_id: ID do pagamento no gateway
            status_pagamento: Status do pagamento (approved, rejected, etc.)
            gateway: Gateway usado (mercadopago, stripe, etc.)
        
        Returns:
            Dict com resultado do processamento
        """
        try:
            # Buscar pedido
            try:
                pedido = WhatsappOrder.objects.get(id=pedido_id)
            except WhatsappOrder.DoesNotExist:
                logger.error(f"[WEBHOOK] Pedido {pedido_id} não encontrado")
                return {
                    'sucesso': False,
                    'erro': f'Pedido {pedido_id} não encontrado'
                }
            
            # Mapear status do gateway para status do pedido
            status_map = {
                'approved': 'paid',
                'pending': 'pending',
                'rejected': 'pending',  # Manter como pending para cliente tentar novamente
                'cancelled': 'pending',
                'refunded': 'pending'
            }
            
            novo_status = status_map.get(status_pagamento.lower(), 'pending')
            
            # Atualizar pedido
            pedido.payment_status = novo_status
            pedido.payment_reference = gateway_payment_id
            
            if novo_status == 'paid':
                pedido.status = 'confirmed'  # Mudar status do pedido para confirmado
                pedido.paid_at = timezone.now()
                
                # Buscar conversa contextualizada relacionada
                try:
                    # Buscar através do grupo e participante
                    grupo = pedido.group
                    participante = pedido.customer
                    
                    # Buscar conversa contextualizada
                    conversa_contextualizada = ConversaContextualizada.objects.filter(
                        oferta__grupo=grupo,
                        participante=participante,
                        status=ConversaContextualizada.StatusConversa.FECHADA
                    ).order_by('-fechada_em').first()
                    
                    if conversa_contextualizada:
                        # Enviar notificação de confirmação de pagamento
                        self._enviar_notificacao_confirmacao_pagamento(
                            conversa_contextualizada,
                            pedido
                        )
                except Exception as e:
                    logger.error(f"[WEBHOOK] Erro ao enviar notificação: {e}")
            
            pedido.save()
            
            logger.info(
                f"[WEBHOOK] Pagamento processado: Pedido {pedido.order_number}, "
                f"Status: {novo_status}, Gateway: {gateway}"
            )
            
            return {
                'sucesso': True,
                'pedido_numero': pedido.order_number,
                'status_anterior': pedido.status,
                'status_novo': novo_status
            }
            
        except Exception as e:
            logger.error(
                f"[WEBHOOK] Erro ao processar confirmação de pagamento: {str(e)}",
                exc_info=True
            )
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def _enviar_notificacao_confirmacao_pagamento(
        self,
        conversa_contextualizada: ConversaContextualizada,
        pedido: WhatsappOrder
    ):
        """
        Envia notificação de confirmação de pagamento ao cliente.
        
        Princípio: Fechamento Individual
        - Confirmação sempre no privado
        - Cliente recebe confirmação imediata
        """
        try:
            participante = conversa_contextualizada.participante
            
            mensagem = f"✅ *Pagamento Confirmado!*\n\n"
            mensagem += f"Pedido: *{pedido.order_number}*\n"
            mensagem += f"Valor: {pedido.currency} {pedido.total_amount}\n\n"
            mensagem += "Seu pedido foi confirmado e está sendo processado! 🎉\n\n"
            mensagem += "Você receberá atualizações sobre o envio aqui mesmo."
            
            # Enviar via Evolution API
            self.evolution_service.send_text_message(
                number=participante.phone,
                text=mensagem
            )
            
            logger.info(
                f"[PAGAMENTO] Notificação de confirmação enviada para {participante.name} "
                f"no pedido {pedido.order_number}"
            )
            
        except Exception as e:
            logger.error(
                f"[PAGAMENTO] Erro ao enviar notificação de confirmação: {str(e)}",
                exc_info=True
            )

