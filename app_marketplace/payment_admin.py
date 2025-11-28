"""
Admin para modelos de Pagamento
"""
from django.contrib import admin
from .models import Pagamento, TransacaoGateway


class TransacaoGatewayInline(admin.TabularInline):
    """Inline para transações do gateway"""
    model = TransacaoGateway
    extra = 0
    readonly_fields = ['tipo_evento', 'criado_em']
    can_delete = False


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'pedido', 'metodo', 'valor', 'moeda', 'status',
        'gateway', 'gateway_payment_id', 'criado_em'
    ]
    list_filter = ['metodo', 'status', 'gateway', 'criado_em']
    search_fields = ['pedido__codigo', 'gateway_payment_id', 'pedido__cliente_nome']
    readonly_fields = ['criado_em', 'atualizado_em', 'confirmado_em']
    inlines = [TransacaoGatewayInline]
    
    fieldsets = (
        ('Pedido', {
            'fields': ('pedido',)
        }),
        ('Pagamento', {
            'fields': ('metodo', 'valor', 'moeda', 'status')
        }),
        ('Gateway', {
            'fields': (
                'gateway', 'gateway_payment_id', 'gateway_checkout_url',
                'gateway_qr_code', 'gateway_qr_code_base64'
            )
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em', 'confirmado_em'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['confirmar_pagamento', 'recusar_pagamento']
    
    def confirmar_pagamento(self, request, queryset):
        """Ação para confirmar pagamentos manualmente"""
        atualizados = 0
        for pagamento in queryset.filter(status=Pagamento.Status.PENDENTE):
            pagamento.confirmar()
            atualizados += 1
        self.message_user(request, f"{atualizados} pagamento(s) confirmado(s).")
    confirmar_pagamento.short_description = "Confirmar pagamentos selecionados"
    
    def recusar_pagamento(self, request, queryset):
        """Ação para recusar pagamentos"""
        atualizados = 0
        for pagamento in queryset.filter(status__in=[Pagamento.Status.PENDENTE, Pagamento.Status.CRIADO]):
            pagamento.recusar()
            atualizados += 1
        self.message_user(request, f"{atualizados} pagamento(s) recusado(s).")
    recusar_pagamento.short_description = "Recusar pagamentos selecionados"


@admin.register(TransacaoGateway)
class TransacaoGatewayAdmin(admin.ModelAdmin):
    list_display = ['id', 'pagamento', 'tipo_evento', 'criado_em']
    list_filter = ['tipo_evento', 'criado_em']
    search_fields = ['pagamento__pedido__codigo', 'tipo_evento']
    readonly_fields = ['criado_em']
    
    fieldsets = (
        ('Transação', {
            'fields': ('pagamento', 'tipo_evento')
        }),
        ('Dados', {
            'fields': ('payload', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('criado_em',)
        })
    )

