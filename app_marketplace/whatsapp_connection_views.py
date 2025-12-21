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
@require_http_methods(["POST"])
def create_session(request):
    """
    Criar instância e obter QR Code - Evolution API
    POST /whatsapp/connection/create/
    """
    # Verificar autenticação manualmente (já que removemos @login_required para debug)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Não autenticado'}, status=401)
    
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
        logger.info(f"Request method: {request.method}, Content-Type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # 1. Criar instância se não existir
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
            "Authorization": f"Bearer {EVOLUTION_API_KEY}"
        }
        
        # Verificar se instância já existe
        url_check = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        logger.info(f"Verificando instâncias existentes: {url_check}")
        try:
            response_check = requests.get(url_check, headers=headers, timeout=10)
            logger.info(f"Resposta check instâncias: {response_check.status_code}")
        except Exception as e:
            logger.error(f"Erro ao verificar instâncias: {str(e)}", exc_info=True)
            raise
        
        instance_exists = False
        instance_status = None
        if response_check.status_code == 200:
            try:
                data_check = response_check.json()
                logger.info(f"Dados recebidos da Evolution API: tipo={type(data_check)}")
                # A Evolution API pode retornar uma lista diretamente ou um dict com 'instance'
                if isinstance(data_check, list):
                    instances = data_check
                elif isinstance(data_check, dict):
                    instances = data_check.get('instance', [])
                else:
                    instances = []
                
                logger.info(f"Total de instâncias encontradas: {len(instances)}")
                for inst in instances:
                    # Verificar se inst é um dict antes de usar .get()
                    if isinstance(inst, dict) and inst.get('name') == INSTANCE_NAME:
                        instance_exists = True
                        instance_status = inst.get('connectionStatus', 'unknown')
                        logger.info(f"Instância {INSTANCE_NAME} já existe com status: {instance_status}")
                        break
            except Exception as e:
                logger.error(f"Erro ao processar resposta de instâncias: {str(e)}", exc_info=True)
                raise
        
        # Se instância existe mas está desconectada, deletar para recriar
        if instance_exists and instance_status in ['close', 'unpaired']:
            logger.info(f"Instância {INSTANCE_NAME} está desconectada ({instance_status}). Deletando para recriar...")
            url_delete = f"{EVOLUTION_API_URL}/instance/delete/{INSTANCE_NAME}"
            try:
                delete_response = requests.delete(url_delete, headers=headers, timeout=10)
                logger.info(f"Resposta DELETE: {delete_response.status_code}")
                if delete_response.status_code in [200, 201]:
                    logger.info(f"Instância {INSTANCE_NAME} deletada com sucesso. Aguardando processamento...")
                    import time
                    time.sleep(3)  # Aguardar processamento da deleção
                    
                    # Verificar se realmente foi deletada
                    verify_response = requests.get(url_check, headers=headers, timeout=10)
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        verify_instances = verify_data if isinstance(verify_data, list) else verify_data.get('instance', [])
                        still_exists = any(
                            isinstance(inst, dict) and inst.get('name') == INSTANCE_NAME 
                            for inst in verify_instances
                        )
                        if still_exists:
                            logger.warning(f"Instância {INSTANCE_NAME} ainda existe após deleção. Tentando novamente...")
                            # Tentar deletar novamente
                            requests.delete(url_delete, headers=headers, timeout=10)
                            time.sleep(2)
                        else:
                            logger.info(f"Instância {INSTANCE_NAME} confirmada como deletada")
                    instance_exists = False
                else:
                    logger.warning(f"Erro ao deletar instância: {delete_response.status_code} - {delete_response.text}")
            except Exception as e:
                logger.warning(f"Erro ao deletar instância (continuando): {str(e)}")
        
        logger.info(f"Estado final: instance_exists={instance_exists}, prosseguindo para criação se necessário...")
        
        # Se instância não existe ou foi deletada, criar nova
        if not instance_exists:
            logger.info(f"Criando nova instância {INSTANCE_NAME}...")
            url_create = f"{EVOLUTION_API_URL}/instance/create"
            payload_create = {
                "instanceName": INSTANCE_NAME,
                "token": EVOLUTION_API_KEY,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }
            logger.info(f"Enviando POST para criar instância: {url_create}")
            logger.info(f"Payload: {payload_create}")
            logger.info(f"Headers: {headers}")
            try:
                response_create = requests.post(url_create, json=payload_create, headers=headers, timeout=30)
                logger.info(f"Resposta criação instância: {response_create.status_code}")
                logger.info(f"Resposta texto: {response_create.text[:500]}")
                
                # Verificar se o QR Code já vem na resposta de criação
                if response_create.status_code in [200, 201]:
                    try:
                        create_data = response_create.json()
                        # Verificar se o QR Code está na resposta
                        if isinstance(create_data, dict):
                            qrcode_in_response = create_data.get('qrcode', {})
                            if isinstance(qrcode_in_response, dict) and qrcode_in_response.get('base64'):
                                logger.info("QR Code encontrado na resposta de criação da instância!")
                                qrcode_base64 = qrcode_in_response.get('base64')
                                qrcode_url = qrcode_in_response.get('url')
                    except Exception as parse_error:
                        logger.warning(f"Erro ao parsear resposta de criação: {str(parse_error)}")
            except Exception as e:
                logger.error(f"Exceção ao criar instância: {str(e)}", exc_info=True)
                raise
            
            if response_create.status_code not in [200, 201]:
                error_data = {}
                try:
                    error_data = response_create.json() if response_create.text else {}
                except:
                    error_data = {'raw': response_create.text[:500]}
                
                error_msg = error_data.get('message') or error_data.get('error') or f'Erro ao criar instância: {response_create.status_code}'
                logger.error(f"Erro ao criar instância: {error_msg} - Dados completos: {error_data}")
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'details': error_data if isinstance(error_data, dict) else str(error_data),
                }, status=response_create.status_code)
            else:
                logger.info(f"Instância {INSTANCE_NAME} criada com sucesso! Aguardando 10 segundos para Evolution API gerar QR Code...")
                import time
                time.sleep(10)  # Aguardar Evolution API processar e gerar QR Code
        
        # 2. Obter QR Code (com retry)
        # O endpoint correto é /instance/connect/{instanceName} que retorna o QR Code quando disponível
        # Mas também podemos tentar /instance/fetchInstances e verificar o qrcode dentro da instância
        url_connect = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        logger.info(f"Obtendo QR Code: {url_connect}")
        
        qrcode_base64 = None
        qrcode_url = None
        
        # Tentar obter QR Code até 10 vezes com intervalo maior (QR Code pode demorar para ser gerado)
        for attempt in range(10):
            try:
                response = requests.get(url_connect, headers=headers, timeout=30)
                logger.info(f"Resposta QR Code (tentativa {attempt + 1}/10): {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Dados QR Code recebidos: {list(data.keys()) if isinstance(data, dict) else 'não é dict'}")
                    
                    # Verificar se retornou qrcode diretamente ou dentro de um objeto
                    if isinstance(data, dict):
                        # Tentar diferentes formatos de resposta
                        qrcode_data = data.get('qrcode', {})
                        if not qrcode_data and 'base64' in data:
                            qrcode_data = data
                        elif not qrcode_data and 'instance' in data:
                            # Pode estar dentro de instance
                            instance_data = data.get('instance', {})
                            qrcode_data = instance_data.get('qrcode', {})
                        
                        qrcode_base64 = qrcode_data.get('base64') if isinstance(qrcode_data, dict) else None
                        qrcode_url = qrcode_data.get('url') if isinstance(qrcode_data, dict) else None
                        
                        # Log detalhado
                        if qrcode_base64:
                            logger.info(f"QR Code obtido com sucesso na tentativa {attempt + 1}!")
                            break
                        else:
                            logger.info(f"QR Code ainda não disponível (tentativa {attempt + 1}/10). Dados: {data}")
                    else:
                        logger.info(f"Resposta não é dict: {type(data)}")
                    
                    if not qrcode_base64 and attempt < 9:
                        # Aumentar tempo de espera progressivamente: 5s, 5s, 7s, 7s, 10s...
                        wait_time = 5 if attempt < 2 else (7 if attempt < 5 else 10)
                        logger.info(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                        time.sleep(wait_time)
                else:
                    logger.warning(f"Erro ao obter QR Code: {response.status_code}")
                    if attempt < 9:
                        time.sleep(5)
            except Exception as e:
                logger.error(f"Erro ao obter QR Code (tentativa {attempt + 1}): {str(e)}", exc_info=True)
                if attempt < 9:
                    time.sleep(5)
        
        # Configurar webhook (antes de retornar) - Formato correto da Evolution API
        webhook_url = f"{request.build_absolute_uri('/')[:-1]}/api/whatsapp/webhook/evolution/"
        url_webhook = f"{EVOLUTION_API_URL}/webhook/set/{INSTANCE_NAME}"
        # Formato correto: webhook como objeto com url, enabled e events
        webhook_payload = {
            "webhook": {
                "url": webhook_url,
                "enabled": True,
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
        }
        logger.info(f"Configurando webhook: {url_webhook} para {webhook_url}")
        try:
            webhook_response = requests.post(url_webhook, json=webhook_payload, headers=headers, timeout=10)
            logger.info(f"Webhook resposta: {webhook_response.status_code} - {webhook_response.text[:200]}")
            if webhook_response.status_code not in [200, 201]:
                logger.warning(f"Erro ao configurar webhook: {webhook_response.status_code} - {webhook_response.text}")
        except Exception as e:
            logger.warning(f"Erro ao configurar webhook (não crítico): {str(e)}")
        
        if qrcode_base64:
            logger.info(f"Retornando QR Code com sucesso para {request.user.username}")
            result = JsonResponse({
                'success': True,
                'instance': INSTANCE_NAME,
                'status': 'connecting',
                'qrCode': qrcode_base64,
                'qrCodeUrl': qrcode_url,
                'message': 'Instância criada! Escaneie o QR Code.',
            })
            logger.info(f"JsonResponse criado, retornando...")
            return result
        else:
            logger.warning(f"QR Code não disponível para {request.user.username} após 10 tentativas")
            return JsonResponse({
                'success': False,
                'error': 'QR Code não disponível. A instância pode estar conectada ou ainda processando. Tente novamente em alguns segundos.',
                'status': 'processing',
            })
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão com Evolution API em {EVOLUTION_API_URL}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Evolution API não está rodando! Verifique se o serviço está ativo.',
        }, status=503)
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição para Evolution API: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Erro ao comunicar com Evolution API: {str(e)}',
        }, status=500)
    except Exception as e:
        logger.error(f"EXCEÇÃO em create_session para {request.user.username}: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
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

