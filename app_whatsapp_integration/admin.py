"""
Admin - WhatsApp Integration
=============================

Interface administrativa para gerenciar contatos e logs de mensagens.
"""

from django.contrib import admin
from .models import WhatsAppContact, WhatsAppMessageLog


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = ['phone', 'name', 'user_type', 'is_verified', 'last_message_at', 'created_at']
    list_filter = ['is_verified', 'created_at', 'last_message_at']
    search_fields = ['phone', 'name', 'user__username', 'cliente__user__username']
    readonly_fields = ['created_at', 'updated_at', 'last_message_at']
    
    fieldsets = (
        ('Informações do Contato', {
            'fields': ('phone', 'name', 'is_verified')
        }),
        ('Vinculação', {
            'fields': ('user', 'cliente', 'shopper', 'keeper')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    list_display = ['phone', 'message_type', 'direction', 'processed', 'reply_sent', 'timestamp']
    list_filter = ['message_type', 'direction', 'processed', 'reply_sent', 'timestamp']
    search_fields = ['phone', 'content', 'message_id']
    readonly_fields = ['created_at', 'timestamp', 'raw_payload']
    
    fieldsets = (
        ('Mensagem', {
            'fields': ('message_id', 'contact', 'phone', 'direction', 'message_type', 'content')
        }),
        ('Processamento', {
            'fields': ('processed', 'reply_sent', 'reply_content')
        }),
        ('Metadados', {
            'fields': ('timestamp', 'created_at', 'raw_payload'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Logs são criados apenas via webhook
        return False
