"""
URLs - WhatsApp Integration
============================

Rotas para integração com WhatsApp.
"""

from django.urls import path
from . import views

app_name = 'app_whatsapp_integration'

urlpatterns = [
    path(
        'api/whatsapp/webhook-from-gateway/',
        views.webhook_from_gateway,
        name='webhook_from_gateway'
    ),
]
