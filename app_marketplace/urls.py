from django.urls import path
from . import views
from . import whatsapp_views

urlpatterns = [
    path('', views.index, name='index'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_view, name='login'),  # nova rota
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
   
    path('evento/<int:evento_id>/solicitar/', views.solicitar_evento, name='solicitar_evento'),
    path('clientes/', views.clientes, name='clientes'),
    path('personal_shoppers/', views.personal_shoppers, name='personal_shoppers'),
    path('pedidos/', views.pedidos, name='pedidos'),
    
    # WhatsApp Integration
    path('webhooks/whatsapp/', whatsapp_views.whatsapp_webhook, name='whatsapp_webhook'),
    path('api/whatsapp/reply/', whatsapp_views.reply_to_group, name='whatsapp_reply'),
]