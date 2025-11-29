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
        # Interceptar healthcheck do Railway para resposta rápida
        if request.path == '/health/':
            from django.http import JsonResponse
            return JsonResponse({
                'status': 'ok',
                'message': 'ÉVORA Connect is running',
                'version': '1.0.0'
            }, status=200)
        
        # Para outros requests, continuar normalmente
        response = self.get_response(request)
        return response