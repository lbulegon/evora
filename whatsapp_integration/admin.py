"""
Admin interface para WhatsApp Integration
"""

from django.contrib import admin
from .models import WhatsAppContact, WhatsAppMessageLog


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    """Admin para WhatsAppContact"""
    list_display = ['phone_number', 'name', 'contact_type', 'is_active', 'created_at']
    list_filter = ['contact_type', 'is_active', 'created_at']
    search_fields = ['phone_number', 'name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('phone_number', 'name', 'user', 'contact_type', 'is_active')
        }),
        ('Metadados', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    """Admin para WhatsAppMessageLog"""
    list_display = [
        'contact',
        'direction',
        'message_type',
        'message_text_short',
        'processing_status',
        'auto_reply_sent',
        'message_timestamp'
    ]
    list_filter = [
        'direction',
        'message_type',
        'processing_status',
        'auto_reply_sent',
        'message_timestamp'
    ]
    search_fields = ['contact__phone_number', 'message_text', 'provider_message_id']
    readonly_fields = ['created_at', 'message_timestamp']
    date_hierarchy = 'message_timestamp'
    
    fieldsets = (
        ('Mensagem', {
            'fields': (
                'contact',
                'direction',
                'message_type',
                'message_text',
                'provider_message_id'
            )
        }),
        ('Processamento', {
            'fields': ('processing_status', 'auto_reply_sent')
        }),
        ('Timestamps', {
            'fields': ('message_timestamp', 'created_at')
        }),
        ('Metadados', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def message_text_short(self, obj):
        """Exibe versão curta do texto da mensagem"""
        return obj.message_text[:50] + '...' if len(obj.message_text) > 50 else obj.message_text
    message_text_short.short_description = 'Mensagem'

