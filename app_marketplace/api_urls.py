"""
URLs da API KMN (Keeper Mesh Network)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Router para ViewSets
router = DefaultRouter()
router.register(r'agentes', api_views.AgenteViewSet)
router.register(r'clientes', api_views.ClienteViewSet)
router.register(r'produtos', api_views.ProdutoViewSet)
router.register(r'produtos-json', api_views.ProdutoJSONViewSet, basename='produtojson')
router.register(r'ofertas', api_views.OfertaViewSet)
router.register(r'estoque', api_views.EstoqueItemViewSet)
router.register(r'trustlines', api_views.TrustlineKeeperViewSet)

# URLs da API
urlpatterns = [
    # ViewSets via router
    path('', include(router.urls)),
    
    # Endpoints específicos
    path('pedido/criar/', api_views.criar_pedido_kmn, name='api_criar_pedido_kmn'),
    path('catalogo/<int:cliente_id>/', api_views.catalogo_cliente, name='api_catalogo_cliente'),
    path('agente/<int:agente_id>/score/', api_views.score_agente, name='api_score_agente'),
    path('resolver-operacao/', api_views.resolver_operacao, name='api_resolver_operacao'),
]






