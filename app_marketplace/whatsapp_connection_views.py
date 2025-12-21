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
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        messages.error(request, "Acesso restrito.")
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


@login_required
@require_http_methods(["POST"])
def create_session(request):
    """
    Criar instância e obter QR Code - Evolution API
    POST /whatsapp/connection/create/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        # 1. Criar instância se não existir
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
            "Authorization": f"Bearer {EVOLUTION_API_KEY}"
        }
        
        # Verificar se instância já existe
        url_check = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        response_check = requests.get(url_check, headers=headers, timeout=10)
        
        instance_exists = False
        if response_check.status_code == 200:
            instances = response_check.json().get('instance', [])
            for inst in instances:
                if inst.get('instanceName') == INSTANCE_NAME:
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
            instance_data = status_result.get('data', {})
            evolution_status = instance_data.get('status', 'close')
            phone = instance_data.get('phone_number')
            phone_name = instance_data.get('phone_name')
            
            return {
                'success': True,
                'status': evolution_status,
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

