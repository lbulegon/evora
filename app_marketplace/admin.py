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
    CupomDesconto  
   
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
