"""
View para fazer proxy de imagens do servidor SinapUm
Isso resolve o problema de mixed content (HTTPS tentando carregar HTTP)
"""
import requests
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def proxy_image(request, image_path):
    """
    Faz proxy de imagem do servidor SinapUm para evitar problemas de mixed content.
    
    URL esperada: /api/images/proxy/<path:image_path>
    Exemplo: /api/images/proxy/media/uploads/06215ae2-5eca-4ed1-b8e5-90f69e297734.jpg
    """
    try:
        # Construir URL completa no servidor SinapUm
        openmind_url = getattr(settings, 'OPENMIND_AI_URL', '')
        if not openmind_url:
            # Fallback para IP padrão
            sinapum_base = 'http://69.169.102.84:8000'
        else:
            # Remover /api/v1 se existir
            sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
        
        # Construir URL da imagem
        if image_path.startswith('http://') or image_path.startswith('https://'):
            # Já é URL completa, usar diretamente
            image_url = image_path
        else:
            # Adicionar /media/ se não tiver
            clean_path = image_path.lstrip('/')
            if clean_path.startswith('media/'):
                image_url = f"{sinapum_base}/{clean_path}"
            else:
                image_url = f"{sinapum_base}/media/{clean_path}"
        
        logger.info(f"[IMAGE_PROXY] Fazendo proxy de: {image_url}")
        
        # Verificar cache primeiro (opcional - reduz carga no SinapUm)
        cache_key = f"image_proxy_{image_path}"
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info(f"[IMAGE_PROXY] Retornando do cache: {image_path}")
            return HttpResponse(
                cached_response['content'],
                content_type=cached_response['content_type']
            )
        
        # Fazer requisição ao SinapUm
        response = requests.get(
            image_url,
            timeout=10,
            headers={
                'User-Agent': 'ÉVORA-Connect/1.0',
            }
        )
        
        if response.status_code == 200:
            # Determinar content type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            # Cachear a resposta (1 hora)
            cache.set(cache_key, {
                'content': response.content,
                'content_type': content_type
            }, 3600)
            
            logger.info(f"[IMAGE_PROXY] Imagem carregada com sucesso: {image_path} ({len(response.content)} bytes)")
            
            # Retornar imagem com headers apropriados
            http_response = HttpResponse(
                response.content,
                content_type=content_type
            )
            
            # Adicionar headers CORS e cache
            http_response['Access-Control-Allow-Origin'] = '*'
            http_response['Cache-Control'] = 'public, max-age=3600'
            
            return http_response
        else:
            logger.warning(f"[IMAGE_PROXY] Erro ao carregar imagem: {image_url} - Status: {response.status_code}")
            raise Http404(f"Imagem não encontrada: {image_path}")
            
    except requests.exceptions.Timeout:
        logger.error(f"[IMAGE_PROXY] Timeout ao carregar imagem: {image_path}")
        raise Http404(f"Timeout ao carregar imagem: {image_path}")
    except requests.exceptions.ConnectionError:
        logger.error(f"[IMAGE_PROXY] Erro de conexão ao carregar imagem: {image_path}")
        raise Http404(f"Erro de conexão ao carregar imagem: {image_path}")
    except Exception as e:
        logger.error(f"[IMAGE_PROXY] Erro ao fazer proxy de imagem: {str(e)}", exc_info=True)
        raise Http404(f"Erro ao carregar imagem: {image_path}")

