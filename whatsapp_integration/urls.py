"""
URLs para WhatsApp Integration
"""

from django.urls import path
from . import views

app_name = 'whatsapp_integration'

urlpatterns = [
    # Endpoint que recebe webhooks do gateway FastAPI
    path(
        'webhook-from-gateway/',
        views.webhook_from_gateway,
        name='webhook_from_gateway'
    ),
]

