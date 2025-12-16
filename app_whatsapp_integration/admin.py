"""
Admin - WhatsApp Integration
=============================

Interface administrativa para gerenciar contatos e logs de mensagens.
"""

from django.contrib import admin
from .models import (
    WhatsAppContact, 
    WhatsAppMessageLog,
    EvolutionInstance,
    EvolutionMessage
)


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


@admin.register(EvolutionInstance)
class EvolutionInstanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'phone_number', 'is_active', 'is_default', 'last_sync', 'created_at']
    list_filter = ['status', 'is_active', 'is_default', 'created_at', 'last_sync']
    search_fields = ['name', 'phone_number', 'phone_name']
    readonly_fields = ['created_at', 'updated_at', 'last_sync', 'metadata']
    
    fieldsets = (
        ('Informações da Instância', {
            'fields': ('name', 'status', 'phone_number', 'phone_name')
        }),
        ('Configurações', {
            'fields': ('is_active', 'is_default')
        }),
        ('QR Code', {
            'fields': ('qrcode', 'qrcode_url'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('last_sync', 'metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_with_evolution_api']
    
    def sync_with_evolution_api(self, request, queryset):
        """Sincroniza instâncias selecionadas com Evolution API"""
        from .evolution_service import EvolutionAPIService
        service = EvolutionAPIService()
        
        for instance in queryset:
            result = service.get_instance_status(instance.name)
            if result.get('success'):
                self.message_user(request, f"✅ Instância {instance.name} sincronizada")
            else:
                self.message_user(request, f"❌ Erro ao sincronizar {instance.name}: {result.get('error')}")
    
    sync_with_evolution_api.short_description = "Sincronizar com Evolution API"


@admin.register(EvolutionMessage)
class EvolutionMessageAdmin(admin.ModelAdmin):
    list_display = ['phone', 'message_type', 'direction', 'status', 'processed', 'instance', 'timestamp']
    list_filter = ['message_type', 'direction', 'status', 'processed', 'instance', 'timestamp']
    search_fields = ['phone', 'content', 'evolution_message_id', 'contact__name']
    readonly_fields = ['created_at', 'updated_at', 'timestamp', 'raw_payload', 'error_message']
    
    fieldsets = (
        ('Mensagem', {
            'fields': ('instance', 'contact', 'evolution_message_id', 'phone', 'direction', 'message_type', 'content')
        }),
        ('Status', {
            'fields': ('status', 'processed', 'error_message')
        }),
        ('Mídia', {
            'fields': ('media_url', 'media_type'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('timestamp', 'created_at', 'updated_at', 'raw_payload'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Mensagens são criadas apenas via webhook ou envio
        return False
