"""
App configuration for whatsapp_integration
"""

from django.apps import AppConfig


class WhatsappIntegrationConfig(AppConfig):
    """Configuração do app whatsapp_integration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whatsapp_integration'
    verbose_name = 'WhatsApp Integration'

