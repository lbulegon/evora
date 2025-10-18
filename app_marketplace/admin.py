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
    Estabelecimento,
    CupomDesconto,
    # Novos modelos
    Keeper,
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
    GroupLinkRequest,
    ShopperOnboardingToken,
    KeeperOnboardingToken
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
    list_display = ['nome', 'cnpj', 'email', 'telefone', 'criada_em']
    search_fields = ['nome', 'cnpj', 'email']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefone', 'criado_em']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

@admin.register(PersonalShopper)
class PersonalShopperAdmin(admin.ModelAdmin):
    list_display = ['user', 'empresa', 'ativo', 'criado_em']
    list_filter = ['ativo', 'empresa']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

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

@admin.register(Estabelecimento)
class EstabelecimentoAdmin(admin.ModelAdmin):
    search_fields = ['nome']
    list_display = ['nome', 'endereco', 'telefone']
    ordering = ['nome']


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
        if 'estabelecimentos' in self.fields:
            self.fields['estabelecimentos'].queryset = Estabelecimento.objects.all()
            self.fields['estabelecimentos'].help_text = ''


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    form = EventoForm
    list_display = ['titulo', 'personal_shopper', 'data_inicio', 'data_fim', 'status']
    list_filter = ['status', 'data_inicio', 'data_fim']
    search_fields = ['titulo', 'personal_shopper__user__username']
    autocomplete_fields = ['personal_shopper']
    filter_horizontal = ['clientes', 'estabelecimentos']
    inlines = [ProdutoEventoInline]



@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'status', 'valor_total', 'criado_em')
    list_filter = ('status', 'metodo_pagamento', 'criado_em')
    search_fields = ('cliente__user__username', 'codigo_rastreamento')
    readonly_fields = ('criado_em', 'atualizado_em', 'valor_total')
    autocomplete_fields = ['cliente']

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

@admin.register(Keeper)
class KeeperAdmin(admin.ModelAdmin):
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
    list_display = ['codigo_publico', 'cliente', 'keeper', 'status', 'confirmacao_visual', 'valor_declarado', 'criado_em']
    list_filter = ['status', 'confirmacao_visual', 'keeper', 'criado_em']
    search_fields = ['codigo_publico', 'descricao', 'cliente__user__username']
    readonly_fields = ['criado_em', 'atualizado_em', 'dias_em_guarda', 'custo_guarda_estimado']
    autocomplete_fields = ['cliente', 'personal_shopper', 'keeper']
    inlines = [FotoPacoteInline, MovimentoPacoteInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_publico', 'descricao')
        }),
        ('Pessoas Envolvidas', {
            'fields': ('cliente', 'personal_shopper', 'keeper')
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
    list_display = ['keeper', 'tipo', 'cidade', 'valor_base', 'ativo']
    list_filter = ['tipo', 'ativo', 'keeper']
    search_fields = ['keeper__user__username', 'cidade']
    
    fieldsets = (
        ('Keeper', {
            'fields': ('keeper',)
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
    list_display = ['name', 'shopper', 'chat_id', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'chat_id', 'shopper__user__username']
    readonly_fields = ['chat_id', 'created_at']
    autocomplete_fields = ['shopper']
    
    fieldsets = (
        ('Grupo', {
            'fields': ('chat_id', 'name', 'active')
        }),
        ('Vinculação', {
            'fields': ('shopper',)
        }),
        ('Informações', {
            'fields': ('created_at', 'meta')
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


@admin.register(KeeperOnboardingToken)
class KeeperOnboardingTokenAdmin(admin.ModelAdmin):
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
