"""
Serializers para API KMN (Keeper Mesh Network)
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Agente, Cliente, ClienteRelacao, Produto, EstoqueItem,
    Oferta, TrustlineKeeper, RoleStats, Pedido, ItemPedido,
    Pagamento, TransacaoGateway, Evento,
    PublicacaoAgora, EngajamentoAgora
)


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para User"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = ['id']


class AgenteSerializer(serializers.ModelSerializer):
    """Serializer para Agente KMN"""
    user = UserBasicSerializer(read_only=True)
    dual_role_score = serializers.ReadOnlyField()
    is_dual_role = serializers.ReadOnlyField()
    
    class Meta:
        model = Agente
        fields = [
            'id', 'user', 'nome_comercial', 'bio_agente',
            'score_keeper', 'score_shopper', 'dual_role_score',
            'ativo_como_keeper', 'ativo_como_shopper', 'is_dual_role',
            'verificado_kmn', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'score_keeper', 'score_shopper', 'criado_em', 'atualizado_em']


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer para Cliente"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Cliente
        fields = ['id', 'user', 'telefone', 'criado_em']
        read_only_fields = ['id', 'criado_em']


class ClienteRelacaoSerializer(serializers.ModelSerializer):
    """Serializer para relação Cliente-Agente"""
    cliente = ClienteSerializer(read_only=True)
    agente = AgenteSerializer(read_only=True)
    
    class Meta:
        model = ClienteRelacao
        fields = [
            'id', 'cliente', 'agente', 'forca_relacao', 'status',
            'total_pedidos', 'valor_total_pedidos', 'ultimo_pedido',
            'satisfacao_media', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'total_pedidos', 'valor_total_pedidos', 'ultimo_pedido', 'criado_em', 'atualizado_em']


class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer para Produto"""
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'descricao', 'preco', 'categoria', 'categoria_nome',
            'empresa', 'empresa_nome', 'imagem', 'ativo', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


class EstoqueItemSerializer(serializers.ModelSerializer):
    """Serializer para Item de Estoque"""
    agente = AgenteSerializer(read_only=True)
    produto = ProdutoSerializer(read_only=True)
    quantidade_total = serializers.ReadOnlyField()
    estabelecimento_nome = serializers.CharField(source='estabelecimento.nome', read_only=True)
    
    class Meta:
        model = EstoqueItem
        fields = [
            'id', 'agente', 'produto', 'quantidade_disponivel', 'quantidade_reservada',
            'quantidade_total', 'estabelecimento', 'estabelecimento_nome',
            'localizacao_especifica', 'preco_custo', 'preco_base',
            'ativo', 'disponivel_para_rede', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class OfertaSerializer(serializers.ModelSerializer):
    """Serializer para Oferta"""
    produto = ProdutoSerializer(read_only=True)
    agente_origem = AgenteSerializer(read_only=True)
    agente_ofertante = AgenteSerializer(read_only=True)
    markup_local = serializers.ReadOnlyField()
    percentual_markup = serializers.ReadOnlyField()
    
    class Meta:
        model = Oferta
        fields = [
            'id', 'produto', 'agente_origem', 'agente_ofertante',
            'preco_base', 'preco_oferta', 'markup_local', 'percentual_markup',
            'quantidade_disponivel', 'ativo', 'exclusiva_para_clientes',
            'criado_em', 'atualizado_em', 'valida_ate'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class OfertaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de Oferta"""
    
    class Meta:
        model = Oferta
        fields = [
            'produto', 'agente_origem', 'preco_base', 'preco_oferta',
            'quantidade_disponivel', 'exclusiva_para_clientes', 'valida_ate'
        ]
    
    def validate(self, data):
        if data['preco_oferta'] < data['preco_base']:
            raise serializers.ValidationError("Preço da oferta não pode ser menor que o preço base")
        return data


class TrustlineKeeperSerializer(serializers.ModelSerializer):
    """Serializer para Trustline KMN"""
    agente_a = AgenteSerializer(read_only=True)
    agente_b = AgenteSerializer(read_only=True)
    nivel_confianca_medio = serializers.ReadOnlyField()
    
    class Meta:
        model = TrustlineKeeper
        fields = [
            'id', 'agente_a', 'agente_b', 'nivel_confianca_a_para_b',
            'nivel_confianca_b_para_a', 'nivel_confianca_medio',
            'perc_shopper', 'perc_keeper', 'status',
            'permite_indicacao', 'perc_indicacao',
            'criado_em', 'aceito_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class TrustlineCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de Trustline"""
    
    class Meta:
        model = TrustlineKeeper
        fields = [
            'agente_b', 'nivel_confianca_a_para_b', 'nivel_confianca_b_para_a',
            'perc_shopper', 'perc_keeper', 'permite_indicacao', 'perc_indicacao'
        ]
    
    def validate(self, data):
        if data['perc_shopper'] + data['perc_keeper'] != 100:
            raise serializers.ValidationError("A soma dos percentuais deve ser 100%")
        return data


class RoleStatsSerializer(serializers.ModelSerializer):
    """Serializer para estatísticas de papel"""
    agente = AgenteSerializer(read_only=True)
    
    class Meta:
        model = RoleStats
        fields = [
            'id', 'agente', 'pedidos_como_keeper', 'valor_total_como_keeper',
            'satisfacao_media_keeper', 'pedidos_como_shopper', 'valor_total_como_shopper',
            'satisfacao_media_shopper', 'total_clientes_atendidos',
            'total_agentes_parceiros', 'atualizado_em'
        ]
        read_only_fields = ['id', 'atualizado_em']


class CatalogoItemSerializer(serializers.Serializer):
    """Serializer para item do catálogo personalizado"""
    produto = ProdutoSerializer(read_only=True)
    oferta = OfertaSerializer(read_only=True)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    agente = AgenteSerializer(read_only=True)
    disponivel = serializers.BooleanField(read_only=True)
    markup_percentual = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)


class CatalogoSerializer(serializers.Serializer):
    """Serializer para catálogo personalizado"""
    cliente = ClienteSerializer(read_only=True)
    produtos = CatalogoItemSerializer(many=True, read_only=True)
    debug = serializers.DictField(read_only=True)


class PedidoKMNCreateSerializer(serializers.Serializer):
    """Serializer para criação de pedido via KMN"""
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1, default=1)
    endereco_entrega_id = serializers.IntegerField()
    observacoes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_produto_id(self, value):
        try:
            Produto.objects.get(id=value, ativo=True)
            return value
        except Produto.DoesNotExist:
            raise serializers.ValidationError("Produto não encontrado ou inativo")


class PedidoKMNSerializer(serializers.ModelSerializer):
    """Serializer para Pedido com dados KMN"""
    cliente = ClienteSerializer(read_only=True)
    agente_shopper = AgenteSerializer(read_only=True)
    agente_keeper = AgenteSerializer(read_only=True)
    canal_entrada = AgenteSerializer(read_only=True)
    oferta_utilizada = OfertaSerializer(read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'cliente', 'status', 'valor_total', 'criado_em', 'atualizado_em',
            'agente_shopper', 'agente_keeper', 'canal_entrada', 'oferta_utilizada',
            'preco_base_kmn', 'preco_oferta_kmn', 'markup_local_kmn',
            'tipo_operacao_kmn', 'comissao_shopper', 'comissao_keeper',
            'comissao_indicacao', 'observacoes'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class ScoreAgenteSerializer(serializers.Serializer):
    """Serializer para score detalhado de agente"""
    score_keeper = serializers.FloatField()
    score_shopper = serializers.FloatField()
    dual_role_score = serializers.FloatField()
    total_pedidos = serializers.IntegerField()
    valor_total = serializers.FloatField()


# ============================================================================
# SISTEMA DE PAGAMENTOS - SERIALIZERS
# ============================================================================

class ItemPedidoSerializer(serializers.ModelSerializer):
    """Serializer para Item de Pedido"""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    
    class Meta:
        model = ItemPedido
        fields = [
            'id', 'produto', 'produto_nome', 'quantidade',
            'preco_unitario', 'descricao', 'moeda', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']


class PedidoSerializer(serializers.ModelSerializer):
    """Serializer para Pedido"""
    itens = ItemPedidoSerializer(many=True, read_only=True)
    pagamento = serializers.SerializerMethodField()
    valor_subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'codigo', 'cliente_nome', 'cliente_whatsapp', 'cliente_email',
            'valor_subtotal', 'valor_frete', 'valor_taxas', 'valor_total', 'moeda',
            'status', 'metodo_pagamento', 'evento', 'criado_em', 'atualizado_em',
            'itens', 'pagamento'
        ]
        read_only_fields = ['id', 'codigo', 'criado_em', 'atualizado_em']
    
    def get_valor_subtotal(self, obj):
        """Retorna valor_subtotal se existir, senão calcula baseado nos itens"""
        try:
            # Tenta obter do banco se o campo existir
            if hasattr(obj, 'valor_subtotal'):
                try:
                    return float(obj.valor_subtotal) if obj.valor_subtotal is not None else 0
                except (AttributeError, KeyError):
                    pass
            # Fallback: calcula baseado nos itens
            if hasattr(obj, 'itens'):
                try:
                    return float(sum(item.subtotal() for item in obj.itens.all())) or 0
                except:
                    return 0
            return 0
        except Exception:
            return 0
    
    def get_pagamento(self, obj):
        """Retorna dados do pagamento se existir"""
        if hasattr(obj, 'pagamento'):
            return PagamentoSerializer(obj.pagamento).data
        return None


class PagamentoSerializer(serializers.ModelSerializer):
    """Serializer para Pagamento"""
    pedido_codigo = serializers.CharField(source='pedido.codigo', read_only=True)
    
    class Meta:
        model = Pagamento
        fields = [
            'id', 'pedido', 'pedido_codigo', 'metodo', 'valor', 'moeda', 'status',
            'gateway', 'gateway_payment_id', 'gateway_checkout_url',
            'gateway_qr_code', 'gateway_qr_code_base64',
            'criado_em', 'atualizado_em', 'confirmado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'confirmado_em']


class TransacaoGatewaySerializer(serializers.ModelSerializer):
    """Serializer para Transação Gateway"""
    pagamento_id = serializers.IntegerField(source='pagamento.id', read_only=True)
    
    class Meta:
        model = TransacaoGateway
        fields = [
            'id', 'pagamento', 'pagamento_id', 'tipo_evento',
            'payload', 'gateway_response', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


class CheckoutCreateSerializer(serializers.Serializer):
    """Serializer para criação de pedido + pagamento via checkout"""
    cliente = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dados do cliente: nome, whatsapp, email"
    )
    itens = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de itens: [{'produto_id': 123, 'quantidade': 2}]"
    )
    entrega = serializers.DictField(
        required=False,
        help_text="Dados de entrega: tipo, keeper_id, endereco"
    )
    pagamento = serializers.DictField(
        help_text="Dados de pagamento: metodo, gateway"
    )
    campanha = serializers.CharField(required=False, allow_blank=True, help_text="Código da campanha")
    evento_id = serializers.IntegerField(required=False, allow_null=True, help_text="ID do evento")
    
    def validate_cliente(self, value):
        """Valida dados do cliente"""
        required_fields = ['nome', 'whatsapp']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Campo '{field}' é obrigatório em cliente")
        return value
    
    def validate_itens(self, value):
        """Valida itens do pedido"""
        if not value:
            raise serializers.ValidationError("Pedido deve ter pelo menos um item")
        for item in value:
            if 'produto_id' not in item or 'quantidade' not in item:
                raise serializers.ValidationError("Cada item deve ter 'produto_id' e 'quantidade'")
            if item['quantidade'] <= 0:
                raise serializers.ValidationError("Quantidade deve ser maior que zero")
        return value
    
    def validate_pagamento(self, value):
        """Valida dados de pagamento"""
        if 'metodo' not in value:
            raise serializers.ValidationError("Campo 'metodo' é obrigatório em pagamento")
        if 'gateway' not in value:
            raise serializers.ValidationError("Campo 'gateway' é obrigatório em pagamento")
        return value


# ============================================================================
# ÁGORA - SERIALIZERS
# ============================================================================

class PublicacaoAgoraSerializer(serializers.ModelSerializer):
    """Serializer para Publicação do Ágora"""
    autor_id = serializers.IntegerField(source='autor.id', read_only=True)
    autor_nome = serializers.CharField(source='autor.get_full_name', read_only=True)
    autor_username = serializers.CharField(source='autor.username', read_only=True)
    
    produto_id = serializers.IntegerField(source='produto.id', read_only=True)
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_imagem = serializers.ImageField(source='produto.imagem', read_only=True)
    
    evento_id = serializers.IntegerField(source='evento.id', read_only=True, allow_null=True)
    evento_titulo = serializers.CharField(source='evento.titulo', read_only=True, allow_null=True)
    
    # Estatísticas de engajamento
    total_views = serializers.IntegerField(read_only=True)
    total_likes = serializers.IntegerField(read_only=True)
    total_add_carrinho = serializers.IntegerField(read_only=True)
    total_compartilhar = serializers.IntegerField(read_only=True)
    total_view_time = serializers.IntegerField(read_only=True)
    
    # Preço exibido (oferta ou produto)
    preco_exibicao = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicacaoAgora
        fields = [
            'id', 'autor_id', 'autor_nome', 'autor_username',
            'tipo_conteudo', 'video_url', 'imagem_url', 'legenda',
            'produto_id', 'produto_nome', 'produto_imagem',
            'preco_oferta', 'preco_exibicao',
            'mesh_type', 'evento_id', 'evento_titulo',
            'spark_score', 'ppa',
            'total_views', 'total_likes', 'total_add_carrinho',
            'total_compartilhar', 'total_view_time',
            'ativo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'spark_score', 'criado_em', 'atualizado_em']
    
    def get_preco_exibicao(self, obj):
        """Retorna o preço a ser exibido (oferta ou produto)"""
        if obj.preco_oferta:
            return obj.preco_oferta
        if obj.produto:
            return obj.produto.preco
        return None


class PublicacaoAgoraCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de publicação no Ágora"""
    
    class Meta:
        model = PublicacaoAgora
        fields = [
            'tipo_conteudo', 'video_url', 'imagem_url', 'legenda',
            'produto', 'preco_oferta', 'mesh_type', 'evento', 'ppa'
        ]
    
    def validate(self, data):
        """Validação: deve ter vídeo OU imagem OU produto"""
        video_url = data.get('video_url')
        imagem_url = data.get('imagem_url')
        produto = data.get('produto')
        
        if not any([video_url, imagem_url, produto]):
            raise serializers.ValidationError(
                "A publicação deve ter pelo menos: vídeo, imagem ou produto vinculado"
            )
        return data


class EngajamentoAgoraSerializer(serializers.ModelSerializer):
    """Serializer para Engajamento do Ágora"""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True, allow_null=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, allow_null=True)
    publicacao_id = serializers.IntegerField(source='publicacao.id', read_only=True)
    
    class Meta:
        model = EngajamentoAgora
        fields = [
            'id', 'publicacao_id', 'usuario_id', 'usuario_username',
            'tipo', 'view_time_segundos', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


class EngajamentoAgoraCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de engajamento"""
    
    class Meta:
        model = EngajamentoAgora
        fields = ['publicacao', 'tipo', 'view_time_segundos']
    
    def validate(self, data):
        """Validação: view_time_segundos apenas para tipo 'view'"""
        if data.get('tipo') != 'view' and data.get('view_time_segundos', 0) > 0:
            raise serializers.ValidationError(
                "view_time_segundos só é válido para tipo 'view'"
            )
        return data


class PublicacaoAgoraAnalyticsSerializer(serializers.Serializer):
    """Serializer para analytics do Ágora (ranking)"""
    id = serializers.IntegerField()
    autor_id = serializers.IntegerField()
    autor_nome = serializers.CharField()
    produto_id = serializers.IntegerField(allow_null=True)
    produto_nome = serializers.CharField(allow_null=True)
    produto_imagem = serializers.ImageField(allow_null=True)
    video_url = serializers.URLField(allow_null=True)
    imagem_url = serializers.URLField(allow_null=True)
    spark_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    ppa = serializers.DecimalField(max_digits=3, decimal_places=2)
    mesh_type = serializers.CharField()
    total_views = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_add_carrinho = serializers.IntegerField()
    total_compartilhar = serializers.IntegerField()
    total_view_time = serializers.IntegerField()
    criado_em = serializers.DateTimeField()


# ============================================================================
# SISTEMA DE PAGAMENTOS - SERIALIZERS
# ============================================================================

class ItemPedidoSerializer(serializers.ModelSerializer):
    """Serializer para Item de Pedido"""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemPedido
        fields = [
            'id', 'produto', 'produto_nome', 'quantidade',
            'preco_unitario', 'descricao', 'moeda', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']
    
    def get_subtotal(self, obj):
        return obj.subtotal()


class PedidoSerializer(serializers.ModelSerializer):
    """Serializer para Pedido"""
    itens = ItemPedidoSerializer(many=True, read_only=True)
    pagamento = serializers.SerializerMethodField()
    valor_subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'codigo', 'cliente_nome', 'cliente_whatsapp', 'cliente_email',
            'valor_subtotal', 'valor_frete', 'valor_taxas', 'valor_total', 'moeda',
            'status', 'metodo_pagamento', 'evento', 'criado_em', 'atualizado_em',
            'itens', 'pagamento'
        ]
        read_only_fields = ['id', 'codigo', 'criado_em', 'atualizado_em']
    
    def get_valor_subtotal(self, obj):
        """Retorna valor_subtotal se existir, senão calcula baseado nos itens"""
        try:
            # Tenta obter do banco se o campo existir
            if hasattr(obj, 'valor_subtotal'):
                try:
                    return float(obj.valor_subtotal) if obj.valor_subtotal is not None else 0
                except (AttributeError, KeyError):
                    pass
            # Fallback: calcula baseado nos itens
            if hasattr(obj, 'itens'):
                try:
                    return float(sum(item.subtotal() for item in obj.itens.all())) or 0
                except:
                    return 0
            return 0
        except Exception:
            return 0
    
    def get_pagamento(self, obj):
        """Retorna dados do pagamento se existir"""
        if hasattr(obj, 'pagamento'):
            return PagamentoSerializer(obj.pagamento).data
        return None


class PagamentoSerializer(serializers.ModelSerializer):
    """Serializer para Pagamento"""
    pedido_codigo = serializers.CharField(source='pedido.codigo', read_only=True)
    
    class Meta:
        model = Pagamento
        fields = [
            'id', 'pedido', 'pedido_codigo', 'metodo', 'valor', 'moeda', 'status',
            'gateway', 'gateway_payment_id', 'gateway_checkout_url',
            'gateway_qr_code', 'gateway_qr_code_base64',
            'criado_em', 'atualizado_em', 'confirmado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'confirmado_em']


class TransacaoGatewaySerializer(serializers.ModelSerializer):
    """Serializer para Transação Gateway"""
    pagamento_id = serializers.IntegerField(source='pagamento.id', read_only=True)
    
    class Meta:
        model = TransacaoGateway
        fields = [
            'id', 'pagamento', 'pagamento_id', 'tipo_evento',
            'payload', 'gateway_response', 'criado_em'
        ]
        read_only_fields = ['id', 'criado_em']


class CheckoutCreateSerializer(serializers.Serializer):
    """Serializer para criação de pedido + pagamento via checkout"""
    cliente = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dados do cliente: nome, whatsapp, email"
    )
    itens = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de itens: [{'produto_id': 123, 'quantidade': 2}]"
    )
    entrega = serializers.DictField(
        required=False,
        help_text="Dados de entrega: tipo, keeper_id, endereco"
    )
    pagamento = serializers.DictField(
        help_text="Dados de pagamento: metodo, gateway"
    )
    campanha = serializers.CharField(required=False, allow_blank=True, help_text="Código da campanha")
    evento_id = serializers.IntegerField(required=False, allow_null=True, help_text="ID do evento")
    
    def validate_cliente(self, value):
        """Valida dados do cliente"""
        required_fields = ['nome', 'whatsapp']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Campo '{field}' é obrigatório em cliente")
        return value
    
    def validate_itens(self, value):
        """Valida itens do pedido"""
        if not value:
            raise serializers.ValidationError("Pedido deve ter pelo menos um item")
        for item in value:
            if 'produto_id' not in item or 'quantidade' not in item:
                raise serializers.ValidationError("Cada item deve ter 'produto_id' e 'quantidade'")
            if item['quantidade'] <= 0:
                raise serializers.ValidationError("Quantidade deve ser maior que zero")
        return value
    
    def validate_pagamento(self, value):
        """Valida dados de pagamento"""
        if 'metodo' not in value:
            raise serializers.ValidationError("Campo 'metodo' é obrigatório em pagamento")
        if 'gateway' not in value:
            raise serializers.ValidationError("Campo 'gateway' é obrigatório em pagamento")
        return value




