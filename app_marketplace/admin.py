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
    RelacionamentoClienteShopper
)

#from .forms import EventoAdminForm  # seu form personalizado

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

# Registro do Evento no admin
@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    form = EventoAdminForm
    list_display = ['nome', 'personal_shopper', 'data_inicio', 'data_fim', 'status']
    filter_horizontal = ['clientes']
    list_filter = ['status', 'data_inicio']
    search_fields = ['nome', 'personal_shopper__user__username']
    actions = [importar_produtos_de_evento]

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
    list_display = ['nome', 'empresa', 'preco', 'categoria', 'ativo', 'criado_em']
    list_filter = ['empresa', 'categoria', 'ativo']
    search_fields = ['nome', 'descricao']

@admin.register(EnderecoEntrega)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'rua', 'numero', 'cidade', 'estado', 'cep']
    search_fields = ['cliente__user__username', 'rua', 'cidade']

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'status', 'criado_em']
    list_filter = ['status']
    inlines = [ItemPedidoInline]
    search_fields = ['cliente__user__username']

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