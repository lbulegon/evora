"""
App Config - WhatsApp Integration
"""

from django.apps import AppConfig


class WhatsappIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_whatsapp_integration'
    verbose_name = 'Integração WhatsApp'
