"""
URLs - WhatsApp Integration
============================

Rotas para integração com WhatsApp.
"""

from django.urls import path
from . import views

app_name = 'app_whatsapp_integration'

urlpatterns = [
    # Webhooks
    path(
        'api/whatsapp/webhook/evolution/',
        views.webhook_evolution_api,
        name='webhook_evolution_api'
    ),
    path(
        'api/whatsapp/webhook-from-gateway/',
        views.webhook_from_gateway,
        name='webhook_from_gateway'
    ),
    # Enviar mensagens
    path(
        'api/whatsapp/send/',
        views.send_message,
        name='send_message'
    ),
    path(
        'api/whatsapp/send-product/',
        views.send_product,
        name='send_product'
    ),
    # Status
    path(
        'api/whatsapp/status/',
        views.instance_status,
        name='instance_status'
    ),
]
