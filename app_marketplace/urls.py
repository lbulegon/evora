from django.urls import path, include
from . import views
from . import whatsapp_views
from . import whatsapp_dashboard_views
from . import shopper_dashboard_views
from . import kmn_views

urlpatterns = [
    path('', views.index, name='index'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_view, name='login'),  # nova rota
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
   
    path('evento/<int:evento_id>/solicitar/', views.solicitar_evento, name='solicitar_evento'),
    path('clientes/', views.clientes, name='clientes'),
    path('personal_shoppers/', views.personal_shoppers, name='personal_shoppers'),
    path('escolher_shoppers/', views.escolher_shoppers, name='escolher_shoppers'),
    path('pedidos/', views.pedidos, name='pedidos'),
    
    # WhatsApp Integration
    path('webhooks/whatsapp/', whatsapp_views.whatsapp_webhook, name='whatsapp_webhook'),
    path('api/whatsapp/reply/', whatsapp_views.reply_to_group, name='whatsapp_reply'),
    
    # WhatsApp Dashboard
    path('whatsapp/dashboard/', whatsapp_dashboard_views.whatsapp_dashboard, name='whatsapp_dashboard'),
    path('whatsapp/groups/', whatsapp_dashboard_views.groups_list, name='whatsapp_groups_list'),
    path('whatsapp/groups/<int:group_id>/', whatsapp_dashboard_views.group_detail, name='whatsapp_group_detail'),
    path('whatsapp/groups/<int:group_id>/products/', whatsapp_dashboard_views.products_list, name='whatsapp_products_list'),
    path('whatsapp/groups/<int:group_id>/orders/', whatsapp_dashboard_views.orders_list, name='whatsapp_orders_list'),
    path('whatsapp/analytics/', whatsapp_dashboard_views.whatsapp_analytics, name='whatsapp_analytics'),
    
           # API Endpoints
           path('api/whatsapp/groups/create/', whatsapp_dashboard_views.create_group, name='api_create_group'),
           path('api/whatsapp/groups/<int:group_id>/update/', whatsapp_dashboard_views.update_group, name='api_update_group'),
           path('api/whatsapp/groups/<int:group_id>/participants/add/', whatsapp_dashboard_views.add_participant, name='api_add_participant'),
           path('api/whatsapp/groups/<int:group_id>/products/create/', whatsapp_dashboard_views.create_product, name='api_create_product'),
           path('api/whatsapp/orders/<int:order_id>/update-status/', whatsapp_dashboard_views.update_order_status, name='api_update_order_status'),
           path('api/whatsapp/groups/<int:group_id>/send-message/', whatsapp_dashboard_views.send_group_message, name='api_send_group_message'),
           
           # API para criação de produtos (sem grupo específico)
           path('api/products/create/', shopper_dashboard_views.create_product, name='api_create_product_general'),
    
    # Dashboard Específico do Shopper
    path('shopper/dashboard/', shopper_dashboard_views.shopper_dashboard, name='shopper_dashboard'),
    path('shopper/groups/', shopper_dashboard_views.shopper_groups, name='shopper_groups'),
    path('shopper/groups/<int:group_id>/', shopper_dashboard_views.shopper_group_detail, name='shopper_group_detail'),
    path('shopper/products/', shopper_dashboard_views.shopper_products, name='shopper_products'),
    path('shopper/orders/', shopper_dashboard_views.shopper_orders, name='shopper_orders'),
    path('shopper/analytics/', shopper_dashboard_views.shopper_analytics, name='shopper_analytics'),
    
    # Helper para Chat ID WhatsApp (comentado temporariamente)
    # path('shopper/chat-id-helper/', shopper_dashboard_views.chat_id_helper, name='chat_id_helper'),
    
    # API KMN
    path('api/kmn/', include('app_marketplace.api_urls')),
    
    # API ÁGORA
    path('api/agora/', include('app_marketplace.agora_urls')),
    
    # API PAGAMENTOS
    path('api/v1/pagamentos/', include('app_marketplace.payment_urls')),
    
    # KMN Frontend
    path('kmn/', kmn_views.kmn_dashboard, name='kmn_dashboard'),
    path('kmn/clientes/', kmn_views.kmn_clientes, name='kmn_clientes'),
    path('kmn/ofertas/', kmn_views.kmn_ofertas, name='kmn_ofertas'),
    path('kmn/estoque/', kmn_views.kmn_estoque, name='kmn_estoque'),
    path('kmn/trustlines/', kmn_views.kmn_trustlines, name='kmn_trustlines'),
    path('kmn/catalogo/<int:cliente_id>/', kmn_views.kmn_catalogo_cliente, name='kmn_catalogo_cliente'),
    
    # AJAX KMN
    path('ajax/kmn/criar-oferta/', kmn_views.ajax_criar_oferta, name='ajax_criar_oferta'),
    path('ajax/kmn/atualizar-estoque/', kmn_views.ajax_atualizar_estoque, name='ajax_atualizar_estoque'),
    path('ajax/kmn/aceitar-trustline/', kmn_views.ajax_aceitar_trustline, name='ajax_aceitar_trustline'),
]