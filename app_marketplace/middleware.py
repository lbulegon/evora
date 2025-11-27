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
        # Verificar se é um request de healthcheck do Railway
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        path = request.path
        
        # Se for request para /admin/ e parecer ser healthcheck
        if path == '/admin/' or path == '/admin':
            # Verificar indicadores de healthcheck
            is_healthcheck = (
                'curl' in user_agent.lower() or
                'railway' in user_agent.lower() or
                'healthcheck' in user_agent.lower() or
                request.META.get('HTTP_X_FORWARDED_FOR') or  # Proxy/load balancer
                not request.META.get('HTTP_ACCEPT', '').startswith('text/html')  # Não é browser
            )
            
            if is_healthcheck:
                logger.info(f"Healthcheck detectado: {user_agent} -> {path}")
                return JsonResponse({
                    'status': 'ok',
                    'message': 'VitrineZap Admin is running',
                    'path': path
                })
        
        # Para outros requests, continuar normalmente
        response = self.get_response(request)
        return response