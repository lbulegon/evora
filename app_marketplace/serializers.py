"""
Serializers para API KMN (Keeper Mesh Network)
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Agente, Cliente, ClienteRelacao, Produto, EstoqueItem,
    Oferta, TrustlineKeeper, RoleStats, Pedido
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
