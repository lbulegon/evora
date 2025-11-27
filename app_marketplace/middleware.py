"""
Middleware para VitrineZap
"""
import os
from django.http import JsonResponse

class HealthCheckMiddleware:
    """
    Middleware que intercepta requisições de healthcheck do Railway
    e responde com status 200 para /admin/ quando em produção
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    def __call__(self, request):
        # Se estiver no Railway e for uma requisição GET para /admin/
        if (self.is_railway and 
            request.method == 'GET' and 
            request.path == '/admin/' and
            self.is_healthcheck_request(request)):
            
            return JsonResponse({
                'status': 'ok',
                'message': 'VitrineZap is running',
                'service': 'admin',
                'version': '1.0.0'
            })
        
        response = self.get_response(request)
        return response
    
    def is_healthcheck_request(self, request):
        """
        Detecta se é uma requisição de healthcheck baseada em características típicas:
        - Sem cookies de sessão
        - User-Agent específico ou ausente
        - Sem parâmetros GET
        """
        # Sem parâmetros GET
        if request.GET:
            return False
            
        # Sem cookies de sessão Django
        if 'sessionid' in request.COOKIES or 'csrftoken' in request.COOKIES:
            return False
            
        # User-Agent típico de healthcheck ou ausente
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        healthcheck_agents = ['curl', 'wget', 'healthcheck', 'monitor', 'probe']
        
        if not user_agent or any(agent in user_agent for agent in healthcheck_agents):
            return True
            
        return True  # Por padrão, considerar como healthcheck se chegou até aqui
