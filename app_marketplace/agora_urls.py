"""
URLs da API ÁGORA - Feed Social do Évora
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import agora_api_views

# Router para ViewSets
router = DefaultRouter()
router.register(r'publicacoes', agora_api_views.PublicacaoAgoraViewSet, basename='publicacao-agora')

# URLs da API
urlpatterns = [
    # ViewSets via router
    path('', include(router.urls)),
    
    # Endpoints específicos
    path('feed/', agora_api_views.agora_feed, name='agora_feed'),
    path('publicar/', agora_api_views.agora_publicar, name='agora_publicar'),
    path('analytics/', agora_api_views.agora_analytics, name='agora_analytics'),
]

