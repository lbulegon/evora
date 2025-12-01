from django.urls import path, include
from . import views
from . import whatsapp_views
from . import whatsapp_dashboard_views
from . import conversations_views
from . import shopper_dashboard_views
from . import kmn_views
from . import admin_dashboard_views
from . import client_dashboard_views

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
    
    # Sistema de Conversas Individuais (Umbler Talk Style)
    path('whatsapp/conversations/', conversations_views.conversations_inbox, name='conversations_inbox'),
    path('whatsapp/conversations/<str:conversation_id>/', conversations_views.conversation_detail, name='conversation_detail'),
    path('api/conversations/<str:conversation_id>/send-message/', conversations_views.send_conversation_message, name='api_send_conversation_message'),
    path('api/conversations/<str:conversation_id>/assign/', conversations_views.assign_conversation, name='api_assign_conversation'),
    path('api/conversations/<str:conversation_id>/status/', conversations_views.update_conversation_status, name='api_update_conversation_status'),
    path('api/conversations/<str:conversation_id>/tags/', conversations_views.add_conversation_tag, name='api_add_conversation_tag'),
    path('api/conversations/<str:conversation_id>/notes/', conversations_views.create_conversation_note, name='api_create_conversation_note'),
    
           # API Endpoints
           path('api/whatsapp/groups/create/', whatsapp_dashboard_views.create_group, name='api_create_group'),
           path('api/whatsapp/groups/<int:group_id>/update/', whatsapp_dashboard_views.update_group, name='api_update_group'),
           path('api/whatsapp/groups/<int:group_id>/participants/add/', whatsapp_dashboard_views.add_participant, name='api_add_participant'),
           path('api/whatsapp/groups/<int:group_id>/clients/available/', whatsapp_dashboard_views.get_available_clients, name='api_get_available_clients'),
           path('api/whatsapp/groups/<int:group_id>/permissions/request/', whatsapp_dashboard_views.request_participant_permission, name='api_request_participant_permission'),
           path('api/whatsapp/permissions/<int:permission_id>/respond/', whatsapp_dashboard_views.respond_permission_request, name='api_respond_permission'),
           path('api/whatsapp/groups/<int:group_id>/products/create/', whatsapp_dashboard_views.create_product, name='api_create_product'),
           path('api/whatsapp/groups/<int:group_id>/products/<int:product_id>/', whatsapp_dashboard_views.get_product, name='api_get_product'),
           path('api/whatsapp/groups/<int:group_id>/products/<int:product_id>/update/', whatsapp_dashboard_views.update_product, name='api_update_product'),
           path('api/whatsapp/groups/<int:group_id>/products/<int:product_id>/delete/', whatsapp_dashboard_views.delete_product, name='api_delete_product'),
           path('api/whatsapp/groups/<int:group_id>/products/<int:product_id>/screenshots/', whatsapp_dashboard_views.get_post_screenshots, name='api_get_post_screenshots'),
           path('api/whatsapp/groups/<int:group_id>/products/<int:product_id>/screenshots/capture/', whatsapp_dashboard_views.capture_post_screenshot, name='api_capture_screenshot'),
           path('api/whatsapp/groups/<int:group_id>/products/<int:product_id>/screenshots/<int:screenshot_id>/delete/', whatsapp_dashboard_views.delete_screenshot, name='api_delete_screenshot'),
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
    
    # Dashboard de Administração
    path('admin/dashboard/', admin_dashboard_views.admin_dashboard, name='admin_dashboard'),
    
    # Dashboard do Cliente
    path('client/dashboard/', client_dashboard_views.client_dashboard, name='client_dashboard'),
    path('client/products/', client_dashboard_views.client_products, name='client_products'),
    path('client/orders/', client_dashboard_views.client_orders, name='client_orders'),
    path('api/client/orders/create/', client_dashboard_views.create_whatsapp_order, name='api_create_whatsapp_order'),
    path('client/orders/<int:pedido_id>/', client_dashboard_views.client_order_detail, name='client_order_detail'),
    path('client/packages/', client_dashboard_views.client_packages, name='client_packages'),
    path('client/packages/<int:pacote_id>/', client_dashboard_views.client_package_detail, name='client_package_detail'),
    
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
    path('ajax/kmn/encerrar-trustline/', kmn_views.ajax_encerrar_trustline, name='ajax_encerrar_trustline'),
]