"""
Views para gerenciar conexão do WhatsApp via QR Code - WPPConnect
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

# Configurações WPPConnect
WPP_BASE = os.getenv("WPP_BASE", "http://localhost:21465")
WPP_SESSION = os.getenv("WPP_SESSION", "session-evora")


# ============================================================================
# VIEWS DE CONEXÃO WHATSAPP
# ============================================================================

@login_required
def whatsapp_connect(request):
    """
    Página principal para conectar WhatsApp via QR Code
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        messages.error(request, "Acesso restrito.")
        return redirect('home')
    
    # Verificar status da sessão
    session_status = get_session_status()
    
    context = {
        'wpp_base': WPP_BASE,
        'wpp_session': WPP_SESSION,
        'session_status': session_status,
        'is_connected': session_status.get('status') == 'CONNECTED',
        'is_paired': session_status.get('status') == 'PAIRING',
    }
    
    return render(request, 'app_marketplace/whatsapp_connect.html', context)


@login_required
@require_http_methods(["POST"])
def create_session(request):
    """
    Criar nova sessão do WPPConnect
    POST /whatsapp/connection/create/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        # Criar sessão no WPPConnect
        url = f"{WPP_BASE}/api/{WPP_SESSION}/start-session"
        payload = {
            "webhook": f"{request.build_absolute_uri('/')[:-1]}/webhooks/whatsapp/",
            "waitQrCode": True,  # Aguardar QR Code
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 201:
            data = response.json()
            return JsonResponse({
                'success': True,
                'session': WPP_SESSION,
                'status': data.get('status'),
                'qrCode': data.get('qrcode', {}).get('base64'),
                'message': 'Sessão criada com sucesso! Escaneie o QR Code.',
            })
        else:
            error_data = response.json() if response.content else {}
            return JsonResponse({
                'success': False,
                'error': error_data.get('message', f'Erro ao criar sessão: {response.status_code}'),
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'WPPConnect não está rodando! Verifique se o serviço está ativo.',
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao criar sessão: {str(e)}',
        }, status=500)


@login_required
def get_qr_code(request):
    """
    Obter QR Code atual da sessão
    GET /whatsapp/connection/qrcode/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        # Obter QR Code da sessão
        url = f"{WPP_BASE}/api/{WPP_SESSION}/qrcode"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            qr_code = data.get('qrcode', {}).get('base64')
            
            if qr_code:
                return JsonResponse({
                    'success': True,
                    'qrCode': qr_code,
                    'status': data.get('status'),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'QR Code não disponível. A sessão pode estar conectada ou expirada.',
                    'status': data.get('status'),
                })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao obter QR Code: {response.status_code}',
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'WPPConnect não está rodando!',
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
    Função auxiliar para obter status da sessão
    """
    try:
        url = f"{WPP_BASE}/api/{WPP_SESSION}/check-connection-session"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'status': data.get('status', 'DISCONNECTED'),
                'connected': data.get('status') == 'CONNECTED',
                'phone': data.get('phone', {}).get('number'),
                'name': data.get('phone', {}).get('pushname'),
            }
        else:
            return {
                'success': False,
                'status': 'DISCONNECTED',
                'connected': False,
                'error': f'Erro ao verificar conexão: {response.status_code}',
            }
    
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'status': 'DISCONNECTED',
            'connected': False,
            'error': 'WPPConnect não está rodando!',
        }
    except Exception as e:
        return {
            'success': False,
            'status': 'DISCONNECTED',
            'connected': False,
            'error': str(e),
        }


@login_required
@require_http_methods(["POST"])
def logout_session(request):
    """
    Desconectar sessão do WhatsApp
    POST /whatsapp/connection/logout/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        url = f"{WPP_BASE}/api/{WPP_SESSION}/logout-session"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            return JsonResponse({
                'success': True,
                'message': 'Sessão desconectada com sucesso!',
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao desconectar: {response.status_code}',
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'WPPConnect não está rodando!',
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
    Deletar sessão completamente
    DELETE /whatsapp/connection/delete/
    """
    if not (request.user.is_shopper or request.user.is_address_keeper or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        url = f"{WPP_BASE}/api/{WPP_SESSION}/close-session"
        response = requests.delete(url, timeout=10)
        
        if response.status_code == 200:
            return JsonResponse({
                'success': True,
                'message': 'Sessão deletada com sucesso!',
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao deletar sessão: {response.status_code}',
            }, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'WPPConnect não está rodando!',
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)

