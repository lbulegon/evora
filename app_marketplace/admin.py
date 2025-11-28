from django.contrib import admin, messages
from django import forms
from .forms import EventoAdminForm
from .models import (
    Empresa,
    Cliente,
    Categoria,
    Produto, ProdutoEvento,
    EnderecoEntrega,    
    Pedido,
    ItemPedido,
    PersonalShopper, 
    Evento, 
    RelacionamentoClienteShopper, 
    CupomDesconto,
    # Novos modelos
    AddressKeeper,
    Pacote,
    MovimentoPacote,
    FotoPacote,
    OpcaoEnvio,
    PagamentoIntent,
    PagamentoSplit,
    IntentCompra,
    PedidoPacote,
    # Integração WhatsApp
    WhatsappGroup,
    WhatsappParticipant,
    WhatsappMessage,
    WhatsappProduct,
    WhatsappOrder,
    GroupLinkRequest,
    ShopperOnboardingToken,
    AddressKeeperOnboardingToken,
    # Modelos KMN
    Agente,
    ClienteRelacao,
    EstoqueItem,
    Oferta,
    TrustlineKeeper,
    RoleStats,
    # Modelos Oficiais - Reestruturação
    CarteiraCliente,
    LigacaoMesh,
    LiquidacaoFinanceira,
    # Modelos ÁGORA
    PublicacaoAgora,
    EngajamentoAgora
)

# Ação para importar produtos de um evento para outro
def importar_produtos_de_evento(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.error(request, "Selecione apenas um evento de origem para importar produtos.")
        return

    evento_origem = queryset.first()

    # Exemplo fixo (melhore com um formulário futuro)
    evento_destino_id = request.POST.get('evento_destino_id')
    if not evento_destino_id:
        messages.error(request, "ID do evento de destino não informado.")
        return

    try:
        evento_destino = Evento.objects.get(id=evento_destino_id)
    except Evento.DoesNotExist:
        messages.error(request, "Evento de destino não encontrado.")
        return

    produtos_origem = Produto.objects.filter(produto_eventos__evento=evento_origem)

    importados = 0
    for produto in produtos_origem:
        if not ProdutoEvento.objects.filter(evento=evento_destino, produto=produto).exists():
            ProdutoEvento.objects.create(
                evento=evento_destino,
                produto=produto,
                importado_de=ProdutoEvento.objects.get(evento=evento_origem, produto=produto)
            )
            importados += 1

    messages.success(request, f"{importados} produto(s) importado(s) com sucesso de '{evento_origem.nome}' para '{evento_destino.nome}'.")


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cidade', 'estado', 'pais', 'tem_cnpj', 'email', 'telefone', 'ativo', 'criada_em']
    list_filter = ['pais', 'estado', 'ativo', 'criada_em', 'cidade']
    search_fields = ['nome', 'cnpj', 'email', 'cidade', 'estado']
    readonly_fields = ['criada_em', 'atualizado_em']
    
    def tem_cnpj(self, obj):
        """Indica se a empresa tem CNPJ (empresas do Paraguai/Brasil) ou é estabelecimento (Orlando/USA)"""
        if obj.cnpj:
            return "Sim (Paraguai/Brasil)"
        return "Não (Orlando/USA)"
    tem_cnpj.short_description = 'Tipo'
    tem_cnpj.admin_order_field = 'cnpj'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'cnpj')
        }),
        ('Contato', {
            'fields': ('email', 'telefone', 'website')
        }),
        ('Localização', {
            'fields': ('endereco', 'cidade', 'estado', 'pais', 'latitude', 'longitude')
        }),
        ('Operacional', {
            'fields': ('horario_funcionamento', 'categorias', 'ativo')
        }),
        ('Timestamps', {
            'fields': ('criada_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['user', 'wallet', 'telefone', 'criado_em']
    list_filter = ['wallet', 'criado_em']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'telefone']
    autocomplete_fields = ['wallet', 'user']
    readonly_fields = ['criado_em', 'atualizado_em', 'owner_carteira']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'wallet', 'owner_carteira')
        }),
        ('Contato', {
            'fields': ('telefone', 'contato')
        }),
        ('Metadados', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )

@admin.register(PersonalShopper)
class PersonalShopperAdmin(admin.ModelAdmin):
    list_display = ['user', 'nome', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'nome']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'nome', 'bio', 'ativo')
        }),
        ('Redes Sociais', {
            'fields': ('facebook', 'instagram', 'tiktok', 'twitter', 'linkedin', 'pinterest', 'youtube'),
            'classes': ('collapse',)
        }),
        ('Empresa (Opcional)', {
            'fields': ('empresa',),
            'classes': ('collapse',),
            'description': 'Campo opcional - Personal Shopper não precisa estar vinculado a uma empresa'
        }),
        ('Informações', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['criado_em']

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display  = ['nome', 'empresa', 'preco', 'categoria', 'ativo', 'criado_em']
    list_filter   = ['empresa', 'categoria', 'ativo']
    search_fields = ['nome', 'descricao']

@admin.register(EnderecoEntrega)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'rua', 'numero', 'cidade', 'estado', 'cep']
    search_fields = ['cliente__user__username', 'rua', 'cidade']

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'produto', 'quantidade', 'preco_unitario']
    search_fields = ['produto__nome', 'pedido__id']

class EventoAdminForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante que produtos e clientes não sejam obrigatórios
        self.fields['produtos'].required = False
        self.fields['clientes'].required = False

@admin.register(RelacionamentoClienteShopper)
class RelacionamentoClienteShopperAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'personal_shopper', 'status', 'data_criacao']
    list_filter = ['status', 'data_criacao']
    search_fields = ['cliente__user__username', 'personal_shopper__user__username']    

@admin.register(ProdutoEvento)
class ProdutoEventoAdmin(admin.ModelAdmin):
    list_display = ['evento', 'produto', 'importado_de']
    list_filter = ['evento']    



class ProdutoEventoInline(admin.TabularInline):
    model = ProdutoEvento
    extra = 1
    autocomplete_fields = ['produto']


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Permitir filtragem e múltiplos selecionados nos campos ManyToMany
        if 'clientes' in self.fields:
            self.fields['clientes'].queryset = Cliente.objects.all()
            self.fields['clientes'].help_text = ''


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    form = EventoForm
    list_display = ['titulo', 'personal_shopper', 'data_inicio', 'data_fim', 'status']
    list_filter = ['status', 'data_inicio', 'data_fim']
    search_fields = ['titulo', 'personal_shopper__user__username']
    autocomplete_fields = ['personal_shopper']
    filter_horizontal = ['clientes']
    inlines = [ProdutoEventoInline]



@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo_cliente', 'shopper', 'keeper', 'status', 'valor_total', 'criado_em')
    list_filter = ('status', 'tipo_cliente', 'metodo_pagamento', 'criado_em')
    search_fields = ('cliente__user__username', 'codigo_rastreamento', 'shopper__username', 'keeper__username')
    readonly_fields = ('criado_em', 'atualizado_em', 'valor_total')
    autocomplete_fields = ['cliente', 'carteira_cliente', 'shopper', 'keeper']
    
    fieldsets = (
        ('Cliente e Carteira', {
            'fields': ('cliente', 'carteira_cliente', 'tipo_cliente')
        }),
        ('Agentes', {
            'fields': ('shopper', 'keeper')
        }),
        ('Preços (Modelo Oficial)', {
            'fields': ('preco_base', 'preco_final', 'valor_total'),
            'description': 'P_base = custo, P_final = valor pago pelo cliente'
        }),
        ('Entrega', {
            'fields': ('endereco_entrega',)
        }),
        ('Pagamento', {
            'fields': ('metodo_pagamento', 'cupom', 'status')
        }),
        ('Rastreamento', {
            'fields': ('codigo_rastreamento',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'is_revisado', 'is_prioritario')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if change:
            try:
                old_obj = Pedido.objects.get(pk=obj.pk)
                if old_obj.status != obj.status:
                    HistoricoStatusPedido.objects.create(
                        pedido=obj,
                        status_anterior=old_obj.status,
                        novo_status=obj.status,
                        alterado_por=request.user
                    )
            except Pedido.DoesNotExist:
                pass
        obj.salvar_com_total()
        super().save_model(request, obj, form, change)

@admin.register(CupomDesconto)
class CupomDescontoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'desconto_percentual', 'ativo', 'valido_ate')
    list_filter = ('ativo',)
    search_fields = ('codigo',)


# ============================================================================
# NOVOS MODELOS - KEEPER, PACOTE, PAGAMENTOS
# ============================================================================

@admin.register(AddressKeeper)
class AddressKeeperAdmin(admin.ModelAdmin):
    list_display = ['user', 'cidade', 'pais', 'capacidade_itens', 'verificado', 'ativo']
    list_filter = ['verificado', 'ativo', 'pais', 'aceita_retirada', 'aceita_envio']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'cidade', 'apelido_local']
    readonly_fields = ['criado_em', 'ocupacao_percent']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Localização', {
            'fields': ('apelido_local', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep', 'pais')
        }),
        ('Capacidade e Taxas', {
            'fields': ('capacidade_itens', 'ocupacao_percent', 'taxa_guarda_dia', 'taxa_motoboy')
        }),
        ('Opções', {
            'fields': ('aceita_retirada', 'aceita_envio', 'verificado', 'ativo')
        }),
        ('Informações', {
            'fields': ('criado_em',)
        }),
    )


class FotoPacoteInline(admin.TabularInline):
    model = FotoPacote
    extra = 1
    fields = ['imagem', 'legenda']


class MovimentoPacoteInline(admin.TabularInline):
    model = MovimentoPacote
    extra = 0
    readonly_fields = ['status', 'mensagem', 'criado_em', 'autor']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pacote)
class PacoteAdmin(admin.ModelAdmin):
    list_display = ['codigo_publico', 'cliente', 'address_keeper', 'status', 'confirmacao_visual', 'valor_declarado', 'criado_em']
    list_filter = ['status', 'confirmacao_visual', 'address_keeper', 'criado_em']
    search_fields = ['codigo_publico', 'descricao', 'cliente__user__username']
    readonly_fields = ['criado_em', 'atualizado_em', 'dias_em_guarda', 'custo_guarda_estimado']
    autocomplete_fields = ['cliente', 'personal_shopper', 'address_keeper']
    inlines = [FotoPacoteInline, MovimentoPacoteInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_publico', 'descricao')
        }),
        ('Pessoas Envolvidas', {
            'fields': ('cliente', 'personal_shopper', 'address_keeper')
        }),
        ('Detalhes do Pacote', {
            'fields': ('valor_declarado', 'peso_kg', 'dimensoes_cm', 'foto_recebimento')
        }),
        ('Status', {
            'fields': ('status', 'confirmacao_visual')
        }),
        ('Guarda', {
            'fields': ('recebido_em', 'guarda_inicio', 'guarda_fim', 'dias_em_guarda', 'custo_guarda_estimado')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Informações', {
            'fields': ('criado_em', 'atualizado_em')
        }),
    )


@admin.register(MovimentoPacote)
class MovimentoPacoteAdmin(admin.ModelAdmin):
    list_display = ['pacote', 'status', 'mensagem', 'autor', 'criado_em']
    list_filter = ['status', 'criado_em']
    search_fields = ['pacote__codigo_publico', 'mensagem']
    readonly_fields = ['criado_em']


@admin.register(FotoPacote)
class FotoPacoteAdmin(admin.ModelAdmin):
    list_display = ['pacote', 'legenda', 'criado_em']
    search_fields = ['pacote__codigo_publico', 'legenda']
    readonly_fields = ['criado_em']


@admin.register(OpcaoEnvio)
class OpcaoEnvioAdmin(admin.ModelAdmin):
    list_display = ['address_keeper', 'tipo', 'cidade', 'valor_base', 'ativo']
    list_filter = ['tipo', 'ativo', 'address_keeper']
    search_fields = ['address_keeper__user__username', 'cidade']
    
    fieldsets = (
        ('Address Keeper (Ponto de Guarda)', {
            'fields': ('address_keeper',)
        }),
        ('Tipo de Envio', {
            'fields': ('tipo', 'cidade', 'valor_base')
        }),
        ('Detalhes', {
            'fields': ('observacoes', 'ativo')
        }),
    )


class PagamentoSplitInline(admin.TabularInline):
    model = PagamentoSplit
    extra = 1
    fields = ['favorecido', 'percentual', 'valor']
    autocomplete_fields = ['favorecido']


@admin.register(PagamentoIntent)
class PagamentoIntentAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'metodo', 'status', 'valor_total', 'entrada_percent', 'criado_em']
    list_filter = ['metodo', 'status', 'criado_em']
    search_fields = ['pedido__id', 'gateway_ref']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [PagamentoSplitInline]
    
    fieldsets = (
        ('Pedido', {
            'fields': ('pedido',)
        }),
        ('Pagamento', {
            'fields': ('metodo', 'status', 'valor_total', 'entrada_percent')
        }),
        ('Gateway', {
            'fields': ('gateway_ref',)
        }),
        ('Informações', {
            'fields': ('criado_em', 'atualizado_em')
        }),
    )


@admin.register(PagamentoSplit)
class PagamentoSplitAdmin(admin.ModelAdmin):
    list_display = ['intent', 'favorecido', 'percentual', 'valor']
    search_fields = ['favorecido__username', 'intent__id']
    autocomplete_fields = ['favorecido']


@admin.register(IntentCompra)
class IntentCompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'personal_shopper', 'status', 'criado_em']
    list_filter = ['status', 'criado_em']
    search_fields = ['cliente__user__username', 'texto_bruto', 'origem_mid']
    readonly_fields = ['criado_em']
    autocomplete_fields = ['cliente', 'personal_shopper']
    
    fieldsets = (
        ('Origem', {
            'fields': ('cliente', 'personal_shopper', 'origem_mid')
        }),
        ('Conteúdo', {
            'fields': ('texto_bruto', 'interpretado')
        }),
        ('Status', {
            'fields': ('status', 'criado_em')
        }),
    )


@admin.register(PedidoPacote)
class PedidoPacoteAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'pacote', 'finalidade']
    search_fields = ['pedido__id', 'pacote__codigo_publico']
    autocomplete_fields = ['pedido', 'pacote']


# ============================================================================
# INTEGRAÇÃO WHATSAPP
# ============================================================================

@admin.register(WhatsappGroup)
class WhatsappGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'owner_type', 'chat_id', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'chat_id', 'owner__username']
    readonly_fields = ['chat_id', 'created_at', 'owner_type']
    autocomplete_fields = ['owner', 'shopper', 'address_keeper']
    
    # ISOLAMENTO DE DADOS - Cada usuário vê apenas seus grupos
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo grupo
            obj.owner = request.user
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('Grupo', {
            'fields': ('chat_id', 'name', 'active')
        }),
        ('Proprietário', {
            'fields': ('owner', 'owner_type', 'shopper', 'keeper')
        }),
        ('Configurações', {
            'fields': ('auto_approve_orders', 'send_notifications', 'max_participants')
        }),
        ('Informações', {
            'fields': ('created_at', 'last_activity')
        }),
    )


@admin.register(GroupLinkRequest)
class GroupLinkRequestAdmin(admin.ModelAdmin):
    list_display = ['token', 'shopper', 'created_at', 'expires_at', 'is_valid', 'used_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['token', 'shopper__user__username']
    readonly_fields = ['token', 'created_at', 'is_valid']
    autocomplete_fields = ['shopper']
    
    def is_valid(self, obj):
        return "✅" if obj.is_valid else "❌"
    is_valid.short_description = 'Válido'


@admin.register(ShopperOnboardingToken)
class ShopperOnboardingTokenAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'phone', 'created_by', 'is_valid', 'created_at', 'used_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['token', 'phone']
    readonly_fields = ['token', 'created_at', 'is_valid']
    
    fieldsets = (
        ('Token', {
            'fields': ('token', 'phone')
        }),
        ('Criação', {
            'fields': ('created_by', 'created_at', 'expires_at', 'is_valid')
        }),
        ('Uso', {
            'fields': ('used_at', 'used_by')
        }),
    )
    
    def is_valid(self, obj):
        return "✅" if obj.is_valid else "❌"
    is_valid.short_description = 'Válido'


@admin.register(AddressKeeperOnboardingToken)
class AddressKeeperOnboardingTokenAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'phone', 'created_by', 'is_valid', 'created_at', 'used_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['token', 'phone']
    readonly_fields = ['token', 'created_at', 'is_valid']
    
    fieldsets = (
        ('Token', {
            'fields': ('token', 'phone')
        }),
        ('Criação', {
            'fields': ('created_by', 'created_at', 'expires_at', 'is_valid')
        }),
        ('Uso', {
            'fields': ('used_at', 'used_by')
        }),
    )
    
    def is_valid(self, obj):
        return "✅" if obj.is_valid else "❌"
    is_valid.short_description = 'Válido'


# ============================================================================
# NOVOS MODELOS WHATSAPP - COM ISOLAMENTO DE DADOS
# ============================================================================

@admin.register(WhatsappParticipant)
class WhatsappParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'group', 'is_admin', 'joined_at']
    list_filter = ['is_admin', 'joined_at', 'group__owner']
    search_fields = ['name', 'phone', 'group__name']
    autocomplete_fields = ['group', 'cliente']
    
    # ISOLAMENTO - Apenas participantes dos grupos do usuário
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__owner=request.user)


@admin.register(WhatsappMessage)
class WhatsappMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'message_type', 'content_preview', 'group', 'timestamp', 'processed']
    list_filter = ['message_type', 'processed', 'timestamp', 'group__owner']
    search_fields = ['content', 'sender__name', 'group__name']
    readonly_fields = ['message_id', 'timestamp', 'created_at']
    autocomplete_fields = ['group', 'sender']
    
    # ISOLAMENTO - Apenas mensagens dos grupos do usuário
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__owner=request.user)
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Conteúdo'


# EstabelecimentoAdmin já foi registrado anteriormente


@admin.register(WhatsappProduct)
class WhatsappProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'currency', 'estabelecimento', 'group', 'is_available', 'created_at']
    list_filter = ['is_available', 'is_featured', 'currency', 'created_at', 'group__owner', 'estabelecimento']
    search_fields = ['name', 'brand', 'description', 'group__name', 'estabelecimento__nome']
    autocomplete_fields = ['group', 'message', 'posted_by', 'estabelecimento']
    
    # ISOLAMENTO - Apenas produtos dos grupos do usuário
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__owner=request.user)
    
    fieldsets = (
        ('Produto', {
            'fields': ('name', 'description', 'brand', 'category', 'price', 'currency')
        }),
        ('Localização', {
            'fields': ('estabelecimento', 'localizacao_especifica', 'codigo_barras', 'sku_loja')
        }),
        ('Grupo', {
            'fields': ('group', 'message', 'posted_by')
        }),
        ('Mídia', {
            'fields': ('image_urls',)
        }),
        ('Status', {
            'fields': ('is_available', 'is_featured', 'created_at')
        }),
    )


@admin.register(WhatsappOrder)
class WhatsappOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'group', 'status', 'total_amount', 'currency', 'created_at']
    list_filter = ['status', 'payment_status', 'currency', 'created_at', 'group__owner']
    search_fields = ['order_number', 'customer__name', 'group__name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    autocomplete_fields = ['group', 'customer', 'cliente']
    
    # ISOLAMENTO - Apenas pedidos dos grupos do usuário
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__owner=request.user)
    
    fieldsets = (
        ('Pedido', {
            'fields': ('order_number', 'group', 'customer', 'cliente')
        }),
        ('Status', {
            'fields': ('status', 'total_amount', 'currency')
        }),
        ('Produtos', {
            'fields': ('products',)
        }),
        ('Entrega', {
            'fields': ('delivery_method', 'delivery_address')
        }),
        ('Pagamento', {
            'fields': ('payment_method', 'payment_status', 'payment_reference')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'paid_at')
        }),
    )


# ============================================================================
# ADMIN KMN - KEEPER MESH NETWORK
# ============================================================================

class ClienteRelacaoInline(admin.TabularInline):
    model = ClienteRelacao
    extra = 0
    readonly_fields = ['total_pedidos', 'valor_total_pedidos', 'ultimo_pedido', 'criado_em']


class EstoqueItemInline(admin.TabularInline):
    model = EstoqueItem
    extra = 0
    readonly_fields = ['quantidade_total', 'criado_em', 'atualizado_em']


class OfertaInline(admin.TabularInline):
    model = Oferta
    fk_name = 'agente_ofertante'
    extra = 0
    readonly_fields = ['markup_local', 'percentual_markup', 'criado_em']


@admin.register(Agente)
class AgenteAdmin(admin.ModelAdmin):
    list_display = ['user', 'nome_comercial', 'score_keeper', 'score_shopper', 'dual_role_score', 'ativo_como_keeper', 'ativo_como_shopper', 'verificado_kmn']
    list_filter = ['ativo_como_keeper', 'ativo_como_shopper', 'verificado_kmn', 'criado_em']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'nome_comercial']
    readonly_fields = ['score_keeper', 'score_shopper', 'dual_role_score', 'is_dual_role', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'nome_comercial', 'bio_agente')
        }),
        ('Papéis KMN', {
            'fields': ('ativo_como_keeper', 'ativo_como_shopper', 'verificado_kmn')
        }),
        ('Scores', {
            'fields': ('score_keeper', 'score_shopper', 'dual_role_score', 'is_dual_role'),
            'classes': ('collapse',)
        }),
        ('Vinculações', {
            'fields': ('personal_shopper', 'keeper'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ClienteRelacaoInline, EstoqueItemInline, OfertaInline]


@admin.register(ClienteRelacao)
class ClienteRelacaoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'agente', 'forca_relacao', 'status', 'total_pedidos', 'valor_total_pedidos', 'ultimo_pedido']
    list_filter = ['status', 'criado_em', 'ultimo_pedido']
    search_fields = ['cliente__user__username', 'agente__user__username']
    readonly_fields = ['total_pedidos', 'valor_total_pedidos', 'ultimo_pedido', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Relação', {
            'fields': ('cliente', 'agente', 'forca_relacao', 'status')
        }),
        ('Histórico', {
            'fields': ('total_pedidos', 'valor_total_pedidos', 'ultimo_pedido', 'satisfacao_media')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )


@admin.register(EstoqueItem)
class EstoqueItemAdmin(admin.ModelAdmin):
    list_display = ['produto', 'agente', 'quantidade_disponivel', 'quantidade_reservada', 'quantidade_total', 'preco_base', 'ativo']
    list_filter = ['ativo', 'disponivel_para_rede', 'estabelecimento', 'criado_em']
    search_fields = ['produto__nome', 'agente__user__username', 'estabelecimento__nome']
    readonly_fields = ['quantidade_total', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Produto e Agente', {
            'fields': ('agente', 'produto')
        }),
        ('Estoque', {
            'fields': ('quantidade_disponivel', 'quantidade_reservada', 'quantidade_total')
        }),
        ('Localização', {
            'fields': ('estabelecimento', 'localizacao_especifica')
        }),
        ('Preços', {
            'fields': ('preco_custo', 'preco_base')
        }),
        ('Status', {
            'fields': ('ativo', 'disponivel_para_rede')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = ['produto', 'agente_ofertante', 'preco_base', 'preco_oferta', 'markup_local', 'percentual_markup', 'quantidade_disponivel', 'ativo']
    list_filter = ['ativo', 'exclusiva_para_clientes', 'criado_em']
    search_fields = ['produto__nome', 'agente_ofertante__user__username', 'agente_origem__user__username']
    readonly_fields = ['markup_local', 'percentual_markup', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Produto e Agentes', {
            'fields': ('produto', 'agente_origem', 'agente_ofertante')
        }),
        ('Preços', {
            'fields': ('preco_base', 'preco_oferta', 'markup_local', 'percentual_markup')
        }),
        ('Disponibilidade', {
            'fields': ('quantidade_disponivel', 'ativo', 'exclusiva_para_clientes', 'valida_ate')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )


@admin.register(TrustlineKeeper)
class TrustlineKeeperAdmin(admin.ModelAdmin):
    list_display = ['agente_a', 'agente_b', 'nivel_confianca_medio', 'perc_shopper', 'perc_keeper', 'status', 'aceito_em']
    list_filter = ['status', 'permite_indicacao', 'criado_em', 'aceito_em']
    search_fields = ['agente_a__user__username', 'agente_b__user__username']
    readonly_fields = ['nivel_confianca_medio', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Agentes', {
            'fields': ('agente_a', 'agente_b')
        }),
        ('Confiança', {
            'fields': ('nivel_confianca_a_para_b', 'nivel_confianca_b_para_a', 'nivel_confianca_medio')
        }),
        ('Comissionamento', {
            'fields': ('perc_shopper', 'perc_keeper')
        }),
        ('Indicação', {
            'fields': ('permite_indicacao', 'perc_indicacao')
        }),
        ('Status', {
            'fields': ('status', 'aceito_em')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )


@admin.register(RoleStats)
class RoleStatsAdmin(admin.ModelAdmin):
    list_display = ['agente', 'pedidos_como_keeper', 'valor_total_como_keeper', 'pedidos_como_shopper', 'valor_total_como_shopper', 'total_clientes_atendidos']
    search_fields = ['agente__user__username']
    readonly_fields = ['atualizado_em']
    
    fieldsets = (
        ('Agente', {
            'fields': ('agente',)
        }),
        ('Stats como Keeper', {
            'fields': ('pedidos_como_keeper', 'valor_total_como_keeper', 'satisfacao_media_keeper')
        }),
        ('Stats como Shopper', {
            'fields': ('pedidos_como_shopper', 'valor_total_como_shopper', 'satisfacao_media_shopper')
        }),
        ('Stats Gerais', {
            'fields': ('total_clientes_atendidos', 'total_agentes_parceiros')
        }),
        ('Timestamps', {
            'fields': ('atualizado_em',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['atualizar_scores']
    
    def atualizar_scores(self, request, queryset):
        """Ação para atualizar scores dos agentes selecionados"""
        for stats in queryset:
            stats.atualizar_scores()
        self.message_user(request, f"Scores atualizados para {queryset.count()} agentes.")
    atualizar_scores.short_description = "Atualizar scores dos agentes selecionados"


# ============================================================================
# ADMIN - MODELOS OFICIAIS (REESTRUTURAÇÃO)
# ============================================================================

class ClienteInline(admin.TabularInline):
    """Inline para mostrar clientes de uma carteira"""
    model = Cliente
    extra = 0
    fields = ['user', 'telefone', 'criado_em']
    readonly_fields = ['criado_em']


@admin.register(CarteiraCliente)
class CarteiraClienteAdmin(admin.ModelAdmin):
    list_display = ['nome_exibicao', 'owner', 'total_clientes', 'criado_em']
    list_filter = ['criado_em', 'owner']
    search_fields = ['nome_exibicao', 'owner__username', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['criado_em', 'atualizado_em', 'total_clientes']
    autocomplete_fields = ['owner']
    inlines = [ClienteInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('owner', 'nome_exibicao')
        }),
        ('Estatísticas', {
            'fields': ('total_clientes',)
        }),
        ('Metadados', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    def total_clientes(self, obj):
        return obj.clientes.count()
    total_clientes.short_description = 'Total de Clientes'


@admin.register(LigacaoMesh)
class LigacaoMeshAdmin(admin.ModelAdmin):
    list_display = ['agente_a', 'agente_b', 'tipo', 'ativo', 'aceito_em', 'criado_em']
    list_filter = ['tipo', 'ativo', 'criado_em', 'aceito_em']
    search_fields = ['agente_a__username', 'agente_b__username']
    readonly_fields = ['criado_em', 'atualizado_em']
    autocomplete_fields = ['agente_a', 'agente_b']
    
    fieldsets = (
        ('Agentes', {
            'fields': ('agente_a', 'agente_b')
        }),
        ('Tipo e Status', {
            'fields': ('tipo', 'ativo', 'aceito_em')
        }),
        ('Configuração Financeira', {
            'fields': ('config_financeira',),
            'description': 'JSON com taxa_evora, venda_clientes_shopper e venda_clientes_keeper'
        }),
        ('Metadados', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        # Validar config_financeira antes de salvar
        obj.clean()
        super().save_model(request, obj, form, change)


@admin.register(LiquidacaoFinanceira)
class LiquidacaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'valor_margem', 'valor_evora', 'valor_shopper', 'valor_keeper', 'status', 'criado_em']
    list_filter = ['status', 'criado_em', 'liquidado_em']
    search_fields = ['pedido__id', 'pedido__cliente__user__username']
    readonly_fields = ['criado_em', 'atualizado_em', 'valor_margem', 'valor_evora', 'valor_shopper', 'valor_keeper']
    autocomplete_fields = ['pedido']
    
    fieldsets = (
        ('Pedido', {
            'fields': ('pedido',)
        }),
        ('Valores', {
            'fields': ('valor_margem', 'valor_evora', 'valor_shopper', 'valor_keeper')
        }),
        ('Status', {
            'fields': ('status', 'liquidado_em')
        }),
        ('Detalhes', {
            'fields': ('detalhes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['marcar_como_liquidada']
    
    def marcar_como_liquidada(self, request, queryset):
        """Marca liquidações como liquidadas"""
        from django.utils import timezone
        atualizadas = 0
        for liquidacao in queryset:
            liquidacao.status = LiquidacaoFinanceira.StatusLiquidacao.LIQUIDADA
            if not liquidacao.liquidado_em:
                liquidacao.liquidado_em = timezone.now()
            liquidacao.save()
            atualizadas += 1
        self.message_user(request, f"{atualizadas} liquidação(ões) marcada(s) como liquidada(s).")
    marcar_como_liquidada.short_description = "Marcar como liquidada"


# ============================================================================
# ÁGORA - ADMIN
# ============================================================================

@admin.register(PublicacaoAgora)
class PublicacaoAgoraAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'autor', 'produto', 'tipo_conteudo', 'mesh_type',
        'spark_score_admin', 'ppa', 'total_views_admin', 'total_likes_admin',
        'total_add_carrinho_admin', 'ativo', 'criado_em'
    ]
    list_filter = ['tipo_conteudo', 'mesh_type', 'ativo', 'evento', 'criado_em']
    search_fields = ['legenda', 'autor__username', 'produto__nome', 'evento__titulo']
    readonly_fields = ['spark_score', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Conteúdo', {
            'fields': ('autor', 'tipo_conteudo', 'video_url', 'imagem_url', 'legenda')
        }),
        ('Produto e Oferta', {
            'fields': ('produto', 'preco_oferta')
        }),
        ('Contexto', {
            'fields': ('mesh_type', 'evento')
        }),
        ('Algoritmo', {
            'fields': ('spark_score', 'ppa')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Anotar estatísticas para exibição"""
        qs = super().get_queryset(request)
        from django.db.models import Count, Sum, Q
        return qs.annotate(
            _total_views=Count('engajamentos', filter=Q(engajamentos__tipo='view')),
            _total_likes=Count('engajamentos', filter=Q(engajamentos__tipo='like')),
            _total_add_carrinho=Count('engajamentos', filter=Q(engajamentos__tipo='add_carrinho')),
        )
    
    def spark_score_admin(self, obj):
        return f"{obj.spark_score:.2f}"
    spark_score_admin.short_description = 'Spark Score'
    spark_score_admin.admin_order_field = 'spark_score'
    
    def total_views_admin(self, obj):
        return getattr(obj, '_total_views', 0)
    total_views_admin.short_description = 'Views'
    total_views_admin.admin_order_field = '_total_views'
    
    def total_likes_admin(self, obj):
        return getattr(obj, '_total_likes', 0)
    total_likes_admin.short_description = 'Likes'
    total_likes_admin.admin_order_field = '_total_likes'
    
    def total_add_carrinho_admin(self, obj):
        return getattr(obj, '_total_add_carrinho', 0)
    total_add_carrinho_admin.short_description = 'Add Carrinho'
    total_add_carrinho_admin.admin_order_field = '_total_add_carrinho'
    
    def get_urls(self):
        """Adicionar URLs customizadas para dashboard e PPA em lote"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(agora_dashboard_view), name='agora_dashboard'),
            path('ppa-bulk/', self.admin_site.admin_view(ppa_bulk_update_view), name='agora_ppa_bulk'),
        ]
        return custom_urls + urls


@admin.register(EngajamentoAgora)
class EngajamentoAgoraAdmin(admin.ModelAdmin):
    list_display = ['id', 'publicacao', 'usuario', 'tipo', 'view_time_segundos', 'criado_em']
    list_filter = ['tipo', 'criado_em']
    search_fields = ['publicacao__legenda', 'usuario__username']
    readonly_fields = ['criado_em']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('publicacao', 'usuario')


# ============================================================================
# ÁGORA - VIEWS ADMIN CUSTOMIZADAS
# ============================================================================

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, F
from django.db.models.functions import Greatest, Least
from django.http import JsonResponse
import json


@staff_member_required
def agora_dashboard_view(request):
    """Dashboard de analytics do Ágora com Chart.js"""
    # Buscar dados da API
    import requests
    from django.conf import settings
    
    try:
        # Usar a própria API interna
        from .agora_api_views import agora_analytics
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        api_request = factory.get('/api/agora/analytics/?limit=50')
        api_request.user = request.user
        
        response = agora_analytics(api_request)
        analytics_data = response.data if hasattr(response, 'data') else []
    except Exception as e:
        analytics_data = []
        messages.error(request, f"Erro ao carregar analytics: {str(e)}")
    
    context = {
        'title': 'Dashboard Ágora',
        'analytics_data': json.dumps(analytics_data, default=str),
    }
    
    return render(request, 'admin/agora/dashboard.html', context)


@staff_member_required
def ppa_bulk_update_view(request):
    """View para atualização de PPA em lote"""
    from .forms import PpaBulkUpdateForm
    
    if request.method == 'POST':
        form = PpaBulkUpdateForm(request.POST)
        if form.is_valid():
            # Montar queryset com filtros
            qs = PublicacaoAgora.objects.filter(ativo=True)
            
            evento = form.cleaned_data.get('evento')
            mesh_type = form.cleaned_data.get('mesh_type')
            only_zero = form.cleaned_data.get('only_zero')
            
            if evento:
                qs = qs.filter(evento=evento)
            if mesh_type:
                qs = qs.filter(mesh_type=mesh_type)
            if only_zero:
                qs = qs.filter(ppa=0.0)
            
            ppa_value = form.cleaned_data['ppa_value']
            apply_mode = form.cleaned_data['apply_mode']
            
            atualizadas = 0
            if apply_mode == 'set':
                atualizadas = qs.update(ppa=ppa_value)
            elif apply_mode == 'increment':
                atualizadas = qs.update(
                    ppa=Least(1.0, Greatest(0.0, F('ppa') + ppa_value))
                )
            elif apply_mode == 'decrement':
                atualizadas = qs.update(
                    ppa=Least(1.0, Greatest(0.0, F('ppa') - ppa_value))
                )
            
            messages.success(
                request,
                f"PPA atualizado em {atualizadas} publicação(ões) usando modo '{apply_mode}'."
            )
            return redirect('admin:app_marketplace_publicacaoagora_changelist')
    else:
        form = PpaBulkUpdateForm()
    
    context = {
        'title': 'Atualizar PPA em Lote',
        'form': form,
    }
    
    return render(request, 'admin/agora/ppa_bulk_update.html', context)
