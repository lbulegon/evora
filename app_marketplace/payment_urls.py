"""
URLs da API de Pagamentos
"""
from django.urls import path
from . import payment_views

urlpatterns = [
    path('checkout/criar-pedido/', payment_views.criar_pedido_checkout, name='criar_pedido_checkout'),
    path('webhook/mercadopago/', payment_views.webhook_mercadopago, name='webhook_mercadopago'),
    path('webhook/stripe/', payment_views.webhook_stripe, name='webhook_stripe'),
    path('<str:pedido_codigo>/regerar-link/', payment_views.regerar_link_pagamento, name='regerar_link_pagamento'),
]

