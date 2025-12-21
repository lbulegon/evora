"""
Views para gerenciar conexão do WhatsApp via QR Code - Evolution API
"""
import os
import json
import base64
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from app_whatsapp_integration.evolution_service import EvolutionAPIService

# Configurações Evolution API
EVOLUTION_API_URL = getattr(settings, 'EVOLUTION_API_URL', 'http://69.169.102.84:8004')
EVOLUTION_API_KEY = getattr(settings, 'EVOLUTION_API_KEY', 'GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg')
INSTANCE_NAME = getattr(settings, 'EVOLUTION_INSTANCE_NAME', 'default')

# Inicializar serviço
evolution_service = EvolutionAPIService()


# ============================================================================
# VIEWS DE CONEXÃO WHATSAPP
# ============================================================================

@login_required
def whatsapp_connect(request):
    """
    Página principal para conectar WhatsApp via QR Code - Evolution API
    """
    from app_marketplace.models import PersonalShopper, AddressKeeper
    
    # Verificar permissões de forma mais robusta
    has_permission = (
        request.user.is_superuser or
        PersonalShopper.objects.filter(user=request.user).exists() or
        AddressKeeper.objects.filter(user=request.user).exists()
    )
    
    if not has_permission:
        messages.error(request, "Acesso restrito. Você precisa ser um Personal Shopper, Address Keeper ou administrador.")
        return redirect('home')
    
    # Verificar status da instância Evolution API
    session_status = get_session_status()
    
    context = {
        'evolution_api_url': EVOLUTION_API_URL,
        'instance_name': INSTANCE_NAME,
        'session_status': session_status,
        'is_connected': session_status.get('status') == 'open',
        'is_connecting': session_status.get('status') == 'connecting',
    }
    
    return render(request, 'app_marketplace/whatsapp_connect.html', context)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_session(request):
    """
    Criar instância e obter QR Code - Evolution API
    POST /whatsapp/connection/create/
    """
    # Verificar permissões - permitir para usuários autenticados que são shoppers, keepers ou superusers
    from app_marketplace.models import PersonalShopper, AddressKeeper
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Log no início da função para confirmar que está sendo chamada
    logger.info(f"[CREATE_SESSION] Função chamada para usuário: {request.user.username} (ID: {request.user.id}, Autenticado: {request.user.is_authenticated}, Superuser: {request.user.is_superuser})")
    
    # Log detalhado para debug
    logger.info(f"Verificando permissão para usuário: {request.user.username} (ID: {request.user.id}, Superuser: {request.user.is_superuser})")
    
    has_permission = False
    if request.user.is_superuser:
        has_permission = True
        logger.info(f"Usuário {request.user.username} é superuser - permitindo acesso")
    else:
        # Verificar se tem perfil PersonalShopper
        shopper_exists = PersonalShopper.objects.filter(user=request.user).exists()
        logger.info(f"Usuário {request.user.username} - PersonalShopper existe: {shopper_exists}")
        
        if shopper_exists:
            has_permission = True
            logger.info(f"Usuário {request.user.username} tem perfil PersonalShopper - permitindo acesso")
        else:
            # Verificar se tem perfil AddressKeeper
            keeper_exists = AddressKeeper.objects.filter(user=request.user).exists()
            logger.info(f"Usuário {request.user.username} - AddressKeeper existe: {keeper_exists}")
            
            if keeper_exists:
                has_permission = True
                logger.info(f"Usuário {request.user.username} tem perfil AddressKeeper - permitindo acesso")
    
    if not has_permission:
        logger.warning(f"ACESSO NEGADO: Usuário {request.user.username} (ID: {request.user.id}) tentou conectar WhatsApp sem permissão")
        return JsonResponse({
            'error': 'Sem permissão. Você precisa ser um Personal Shopper, Address Keeper ou administrador para conectar WhatsApp. Verifique se seu perfil está criado corretamente.'
        }, status=403)
    
    logger.info(f"Permissão confirmada para {request.user.username} - prosseguindo com criação de sessão")
    
    try:
        logger.info(f"Iniciando criação de sessão - Evolution API URL: {EVOLUTION_API_URL}")
        
        # 1. Criar instância se não existir
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
            "Authorization": f"Bearer {EVOLUTION_API_KEY}"
        }
        
        # Verificar se instância já existe
        url_check = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        logger.info(f"Verificando instâncias existentes: {url_check}")
        response_check = requests.get(url_check, headers=headers, timeout=10)
        logger.info(f"Resposta check instâncias: {response_check.status_code}")
        
        instance_exists = False
        if response_check.status_code == 200:
            data_check = response_check.json()
            # A Evolution API pode retornar uma lista diretamente ou um dict com 'instance'
            if isinstance(data_check, list):
                instances = data_check
            elif isinstance(data_check, dict):
                instances = data_check.get('instance', [])
            else:
                instances = []
            
            for inst in instances:
                # Verificar se inst é um dict antes de usar .get()
                if isinstance(inst, dict) and inst.get('instanceName') == INSTANCE_NAME:
                    instance_exists = True
                    break
        
        # Criar instância se não existir
        if not instance_exists:
            url_create = f"{EVOLUTION_API_URL}/instance/create"
            payload_create = {
                "instanceName": INSTANCE_NAME,
                "token": EVOLUTION_API_KEY,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }
            response_create = requests.post(url_create, json=payload_create, headers=headers, timeout=30)
            
            if response_create.status_code not in [200, 201]:
                error_data = response_create.json() if response_create.text else {}
                return JsonResponse({
                    'success': False,
                    'error': error_data.get('message', f'Erro ao criar instância: {response_create.status_code}'),
                }, status=response_create.status_code)
        
        # 2. Obter QR Code
        url_connect = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        response = requests.get(url_connect, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            qrcode_data = data.get('qrcode', {})
            qrcode_base64 = qrcode_data.get('base64')
            qrcode_url = qrcode_data.get('url')
            
            # Configurar webhook
            webhook_url = f"{request.build_absolute_uri('/')[:-1]}/api/whatsapp/webhook/evolution/"
            url_webhook = f"{EVOLUTION_API_URL}/webhook/set/{INSTANCE_NAME}"
            webhook_payload = {
                "url": webhook_url,
                "webhook_by_events": True,
                "events": [
                    "MESSAGES_UPSERT",
                    "MESSAGES_UPDATE",
                    "MESSAGES_DELETE",
                    "SEND_MESSAGE",
                    "CONNECTION_UPDATE",
                    "QRCODE_UPDATED"
                ]
            }
            requests.post(url_webhook, json=webhook_payload, headers=headers, timeout=10)
            
            if qrcode_base64:
                return JsonResponse({
                    'success': True,
                    'instance': INSTANCE_NAME,
                    'status': 'connecting',
                    'qrCode': qrcode_base64,
                    'qrCodeUrl': qrcode_url,
                    'message': 'Instância criada! Escaneie o QR Code.',
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'QR Code não disponível. Instância pode já estar conectada.',
                    'status': data.get('status', 'unknown'),
                })
        else:
            error_data = response.json() if response.text else {}
            return JsonResponse({
                'success': False,
                'error': error_data.get('message', f'Erro ao obter QR Code: {response.status_code}'),
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Evolution API não está rodando! Verifique se o serviço está ativo.',
        }, status=503)
    except Exception as e:
        logger.error(f"EXCEÇÃO em create_session para {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Erro ao criar sessão: {str(e)}',
        }, status=500)


@login_required
def get_qr_code(request):
    """
    Obter QR Code atual da instância - Evolution API
    GET /whatsapp/connection/qrcode/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
            "Authorization": f"Bearer {EVOLUTION_API_KEY}"
        }
        
        url = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            qrcode_data = data.get('qrcode', {})
            qr_code = qrcode_data.get('base64')
            qrcode_url = qrcode_data.get('url')
            
            if qr_code:
                return JsonResponse({
                    'success': True,
                    'qrCode': qr_code,
                    'qrCodeUrl': qrcode_url,
                    'status': data.get('status', 'connecting'),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'QR Code não disponível. A instância pode estar conectada ou expirada.',
                    'status': data.get('status', 'unknown'),
                })
        else:
            error_data = response.json() if response.text else {}
            return JsonResponse({
                'success': False,
                'error': error_data.get('message', f'Erro ao obter QR Code: {response.status_code}'),
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Evolution API não está rodando!',
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@login_required
def get_session_status(request):
    """
    Verificar status da sessão
    GET /whatsapp/connection/status/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    status = get_session_status()
    return JsonResponse(status)


def get_session_status():
    """
    Função auxiliar para obter status da instância - Evolution API
    """
    try:
        status_result = evolution_service.get_instance_status(INSTANCE_NAME)
        
        if status_result.get('success'):
            # O status pode vir diretamente ou dentro de 'data'
            evolution_status = status_result.get('status', 'close')
            
            # Tentar pegar de 'data' se disponível
            data = status_result.get('data', {})
            if isinstance(data, dict) and data.get('status'):
                evolution_status = data.get('status', evolution_status)
            
            # Pegar phone e name de 'data' ou diretamente
            if isinstance(data, dict):
                phone = data.get('phone_number') or status_result.get('instance', {}).get('phone_number')
                phone_name = data.get('phone_name') or status_result.get('instance', {}).get('phone_name')
            else:
                instance_info = status_result.get('instance', {})
                phone = instance_info.get('phone_number') if isinstance(instance_info, dict) else None
                phone_name = instance_info.get('phone_name') if isinstance(instance_info, dict) else None
            
            return {
                'success': True,
                'status': evolution_status or 'close',
                'connected': evolution_status == 'open',
                'phone': phone,
                'name': phone_name,
            }
        else:
            return {
                'success': False,
                'status': 'close',
                'connected': False,
                'error': status_result.get('error', 'Erro ao verificar conexão'),
            }
    
    except Exception as e:
        return {
            'success': False,
            'status': 'close',
            'connected': False,
            'error': str(e),
        }


@login_required
@require_http_methods(["POST"])
def logout_session(request):
    """
    Desconectar instância do WhatsApp - Evolution API
    POST /whatsapp/connection/logout/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
            "Authorization": f"Bearer {EVOLUTION_API_KEY}"
        }
        
        url = f"{EVOLUTION_API_URL}/instance/logout/{INSTANCE_NAME}"
        response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            return JsonResponse({
                'success': True,
                'message': 'Instância desconectada com sucesso!',
            })
        else:
            error_data = response.json() if response.text else {}
            return JsonResponse({
                'success': False,
                'error': error_data.get('message', f'Erro ao desconectar: {response.status_code}'),
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Evolution API não está rodando!',
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@login_required
@require_http_methods(["DELETE", "POST"])
def delete_session(request):
    """
    Deletar instância completamente - Evolution API
    DELETE /whatsapp/connection/delete/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
            "Authorization": f"Bearer {EVOLUTION_API_KEY}"
        }
        
        url = f"{EVOLUTION_API_URL}/instance/delete/{INSTANCE_NAME}"
        response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            return JsonResponse({
                'success': True,
                'message': 'Instância deletada com sucesso!',
            })
        else:
            error_data = response.json() if response.text else {}
            return JsonResponse({
                'success': False,
                'error': error_data.get('message', f'Erro ao deletar instância: {response.status_code}'),
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Evolution API não está rodando!',
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)

