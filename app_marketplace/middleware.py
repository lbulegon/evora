"""
Middleware para healthcheck do Railway
"""
from django.http import HttpResponse, JsonResponse
import logging

logger = logging.getLogger(__name__)

class RailwayHealthCheckMiddleware:
    """
    Middleware que intercepta requests de healthcheck do Railway
    e responde com status 200 para evitar falha no deploy
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # O healthcheck do Railway está configurado para /health/
        # Não precisamos interceptar /admin/ - deixar funcionar normalmente
        # Este middleware pode ser usado para outros healthchecks se necessário
        
        # Para outros requests, continuar normalmente
        response = self.get_response(request)
        return response