"""
URL configuration for setup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.conf.urls.static import static

@csrf_exempt
@never_cache
def health_check(request):
    """
    View para healthcheck do Railway.
    Responde rapidamente sem depender do banco de dados.
    """
    try:
        # Verificação básica - apenas retornar OK
        # Não verificar banco para evitar timeout
        return JsonResponse({
            'status': 'ok',
            'message': 'ÉVORA Connect is running',
            'version': '1.0.0',
            'service': 'vitrinezap'
        }, status=200)
    except Exception as e:
        # Em caso de erro, ainda retornar 200 para não quebrar healthcheck
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=200)

# Customizar a página inicial do admin para aceitar healthcheck
admin.site.site_header = "VitrineZap Admin"
admin.site.site_title = "VitrineZap"
admin.site.index_title = "Administração VitrineZap"

urlpatterns = [
    path('health/', health_check, name='health_check'),
    # Incluir app_marketplace.urls ANTES do admin para capturar /admin/dashboard/
    path('', include('app_marketplace.urls')),
    path('admin/', admin.site.urls),
    path('', include('app_whatsapp_integration.urls')),  # WhatsApp Integration
]

# Servir arquivos de mídia em desenvolvimento e produção
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Em produção (Railway), também servir arquivos de mídia
    # Nota: Para produção em escala, considere usar S3 ou similar
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
