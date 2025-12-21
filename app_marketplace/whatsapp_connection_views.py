"""
Views para gerenciar conexão do WhatsApp via QR Code - Evolution API
"""
import os
import json
import base64
import requests
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError
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
        
        # Timeouts aumentados para operações que podem demorar
        SHORT_TIMEOUT = 15  # Para verificações rápidas
        MEDIUM_TIMEOUT = 30  # Para operações normais
        LONG_TIMEOUT = 60  # Para criação de instância e obtenção de QR Code
        
        # ========== ESTRATÉGIA DEFINITIVA: SEMPRE DELETAR E RECRIAR ==========
        # Para garantir QR Code limpo, sempre deletamos a instância existente (se houver)
        # e criamos uma nova instância limpa
        logger.info(f"[CLEAN_INSTANCE] ========== LIMPEZA E CRIAÇÃO DE INSTÂNCIA ==========")
        logger.info(f"[CLEAN_INSTANCE] Instância alvo: {INSTANCE_NAME}")
        
        url_check = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        url_delete = f"{EVOLUTION_API_URL}/instance/delete/{INSTANCE_NAME}"
        
        # PASSO 1: Verificar se instância existe e SEMPRE deletar (se existir)
        logger.info(f"[CLEAN_INSTANCE] PASSO 1: Verificando e deletando instância existente (se houver)...")
        instance_exists = False
        
        try:
            # Verificar se Evolution API está acessível primeiro
            logger.info(f"[CLEAN_INSTANCE] Verificando se Evolution API está acessível...")
            try:
                health_check = requests.get(f"{EVOLUTION_API_URL}/health", headers=headers, timeout=5)
                if health_check.status_code != 200:
                    logger.warning(f"[CLEAN_INSTANCE] ⚠️ Evolution API health check retornou {health_check.status_code}")
            except Exception as health_error:
                logger.error(f"[CLEAN_INSTANCE] ❌ Evolution API não está acessível: {str(health_error)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Evolution API não está acessível em {EVOLUTION_API_URL}. Verifique se o serviço está rodando.',
                    'details': str(health_error)
                }, status=503)
            
            response_check = requests.get(url_check, headers=headers, timeout=SHORT_TIMEOUT)
            logger.info(f"[CLEAN_INSTANCE] GET /instance/fetchInstances - Status: {response_check.status_code}")
            
            if response_check.status_code == 200:
                try:
                    data_check = response_check.json()
                    logger.info(f"[CLEAN_INSTANCE] Dados recebidos (tipo: {type(data_check)}): {json.dumps(data_check, indent=2) if isinstance(data_check, (dict, list)) else str(data_check)[:500]}")
                    
                    # A Evolution API pode retornar uma lista diretamente ou um dict com 'instance'
                    if isinstance(data_check, list):
                        instances = data_check
                    elif isinstance(data_check, dict):
                        instances = data_check.get('instance', [])
                    else:
                        instances = []
                    
                    logger.info(f"[CLEAN_INSTANCE] Total de instâncias encontradas: {len(instances)}")
                    
                    # Verificar se nossa instância existe
                    for inst in instances:
                        if isinstance(inst, dict) and inst.get('name') == INSTANCE_NAME:
                            instance_exists = True
                            instance_status = inst.get('connectionStatus', 'unknown')
                            logger.info(f"[CLEAN_INSTANCE] ✅ Instância '{INSTANCE_NAME}' encontrada com status: {instance_status}")
                            break
                    
                    # Se instância existe, SEMPRE DELETAR (independente do status)
                    if instance_exists:
                        logger.info(f"[CLEAN_INSTANCE] Instância existe. DELETANDO para criar uma nova limpa...")
                        delete_response = requests.delete(url_delete, headers=headers, timeout=MEDIUM_TIMEOUT)
                        logger.info(f"[CLEAN_INSTANCE] DELETE /instance/delete/{INSTANCE_NAME} - Status: {delete_response.status_code}")
                        logger.info(f"[CLEAN_INSTANCE] DELETE Response: {delete_response.text[:500]}")
                        
                        if delete_response.status_code in [200, 201, 204]:
                            logger.info(f"[CLEAN_INSTANCE] ✅ Instância deletada! Aguardando 5 segundos para processamento completo...")
                            time.sleep(5)
                            
                            # Verificar se realmente foi deletada (até 3 tentativas)
                            for verify_attempt in range(3):
                                verify_response = requests.get(url_check, headers=headers, timeout=SHORT_TIMEOUT)
                                if verify_response.status_code == 200:
                                    verify_data = verify_response.json()
                                    verify_instances = verify_data if isinstance(verify_data, list) else verify_data.get('instance', [])
                                    still_exists = any(
                                        isinstance(inst, dict) and inst.get('name') == INSTANCE_NAME 
                                        for inst in verify_instances
                                    )
                                    
                                    if not still_exists:
                                        logger.info(f"[CLEAN_INSTANCE] ✅ Instância confirmada como deletada (tentativa {verify_attempt + 1})")
                                        instance_exists = False
                                        break
                                    else:
                                        logger.warning(f"[CLEAN_INSTANCE] ⚠️ Instância ainda existe (tentativa {verify_attempt + 1}/3). Aguardando mais 3 segundos...")
                                        time.sleep(3)
                                        if verify_attempt == 2:
                                            # Última tentativa: forçar deleção novamente
                                            logger.warning(f"[CLEAN_INSTANCE] Forçando deleção novamente...")
                                            requests.delete(url_delete, headers=headers, timeout=MEDIUM_TIMEOUT)
                                            time.sleep(3)
                        else:
                            logger.warning(f"[CLEAN_INSTANCE] ⚠️ Erro ao deletar: {delete_response.status_code} - {delete_response.text[:500]}")
                            # Continuar mesmo assim, tentar criar nova instância
                    else:
                        logger.info(f"[CLEAN_INSTANCE] ✅ Instância '{INSTANCE_NAME}' não existe. Prosseguindo para criação...")
                        
                except Exception as e:
                    logger.error(f"[CLEAN_INSTANCE] ❌ Erro ao processar verificação: {str(e)}", exc_info=True)
                    # Continuar para tentar criar instância
            else:
                logger.warning(f"[CLEAN_INSTANCE] ⚠️ Erro ao verificar instâncias: {response_check.status_code}")
                # Continuar para tentar criar instância
        except Timeout as timeout_error:
            logger.error(f"[CLEAN_INSTANCE] ❌ Timeout ao conectar com Evolution API: {str(timeout_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Evolution API não está respondendo (timeout). Verifique se o serviço está rodando em {EVOLUTION_API_URL}',
                'details': str(timeout_error)
            }, status=503)
        except RequestsConnectionError as conn_error:
            logger.error(f"[CLEAN_INSTANCE] ❌ Erro de conexão com Evolution API: {str(conn_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Não foi possível conectar com Evolution API em {EVOLUTION_API_URL}. Verifique se o serviço está rodando.',
                'details': str(conn_error)
            }, status=503)
        except Exception as e:
            logger.error(f"[CLEAN_INSTANCE] ❌ Erro ao verificar/deletar instância: {str(e)}", exc_info=True)
            # Se for timeout ou connection error, retornar erro específico
            if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
                return JsonResponse({
                    'success': False,
                    'error': f'Erro de conexão com Evolution API: {str(e)}',
                    'details': 'Verifique se a Evolution API está rodando e acessível'
                }, status=503)
            # Continuar para tentar criar instância
        
        # PASSO 2: Criar nova instância limpa (sempre criar, mesmo que a anterior não tenha sido deletada)
        logger.info(f"[CLEAN_INSTANCE] PASSO 2: Criando nova instância limpa...")
        url_create = f"{EVOLUTION_API_URL}/instance/create"
        payload_create = {
            "instanceName": INSTANCE_NAME,
            "token": EVOLUTION_API_KEY,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        logger.info(f"[CREATE_INSTANCE] Enviando POST para: {url_create}")
        logger.info(f"[CREATE_INSTANCE] Payload: {json.dumps(payload_create, indent=2)}")
        logger.info(f"[CREATE_INSTANCE] Headers: {headers}")
        
        try:
            response_create = requests.post(url_create, json=payload_create, headers=headers, timeout=LONG_TIMEOUT)
            logger.info(f"[CREATE_INSTANCE] Status: {response_create.status_code}")
            logger.info(f"[CREATE_INSTANCE] Resposta completa: {response_create.text}")
            
            if response_create.status_code not in [200, 201]:
                error_data = {}
                try:
                    error_data = response_create.json() if response_create.text else {}
                except:
                    error_data = {'raw': response_create.text[:500]}
                
                error_msg = error_data.get('message') or error_data.get('error') or f'Erro ao criar instância: {response_create.status_code}'
                
                # Se erro é "already in use", tentar deletar novamente e recriar
                if 'already in use' in str(error_msg).lower() or 'already exists' in str(error_msg).lower():
                    logger.warning(f"[CREATE_INSTANCE] ⚠️ Instância ainda existe. Forçando deleção novamente...")
                    delete_response = requests.delete(url_delete, headers=headers, timeout=15)
                    logger.info(f"[CREATE_INSTANCE] DELETE forçado - Status: {delete_response.status_code}")
                    time.sleep(5)
                    
                    # Tentar criar novamente
                    logger.info(f"[CREATE_INSTANCE] Tentando criar novamente após deleção forçada...")
                    response_create = requests.post(url_create, json=payload_create, headers=headers, timeout=LONG_TIMEOUT)
                    logger.info(f"[CREATE_INSTANCE] Status (2ª tentativa): {response_create.status_code}")
                    logger.info(f"[CREATE_INSTANCE] Resposta (2ª tentativa): {response_create.text}")
                    
                    if response_create.status_code not in [200, 201]:
                        error_data = {}
                        try:
                            error_data = response_create.json() if response_create.text else {}
                        except:
                            error_data = {'raw': response_create.text[:500]}
                        error_msg = error_data.get('message') or error_data.get('error') or f'Erro ao criar instância após deleção: {response_create.status_code}'
                        logger.error(f"[CREATE_INSTANCE] ❌ Erro após 2ª tentativa: {error_msg}")
                        return JsonResponse({
                            'success': False,
                            'error': error_msg,
                            'details': error_data if isinstance(error_data, dict) else str(error_data),
                        }, status=response_create.status_code)
                
                if response_create.status_code not in [200, 201]:
                    logger.error(f"[CREATE_INSTANCE] ❌ Erro: {error_msg}")
                    return JsonResponse({
                        'success': False,
                        'error': error_msg,
                        'details': error_data if isinstance(error_data, dict) else str(error_data),
                    }, status=response_create.status_code)
            
            logger.info(f"[CREATE_INSTANCE] ✅ Instância criada com sucesso! Aguardando 10 segundos para Evolution API processar e gerar QR Code...")
            time.sleep(10)  # Aguardar Evolution API processar e iniciar geração do QR Code
            
        except Timeout as timeout_error:
            logger.error(f"[CREATE_INSTANCE] ❌ Timeout ao criar instância: {str(timeout_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Evolution API não está respondendo (timeout ao criar instância). O serviço pode estar sobrecarregado.',
                'details': str(timeout_error)
            }, status=503)
        except RequestsConnectionError as conn_error:
            logger.error(f"[CREATE_INSTANCE] ❌ Erro de conexão: {str(conn_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Não foi possível conectar com Evolution API. Verifique se o serviço está rodando.',
                'details': str(conn_error)
            }, status=503)
        except Exception as e:
            logger.error(f"[CREATE_INSTANCE] ❌ Exceção: {str(e)}", exc_info=True)
            error_msg = f'Erro ao criar instância: {str(e)}'
            if 'timeout' in str(e).lower():
                error_msg = f'Evolution API não está respondendo (timeout). Tente novamente em alguns instantes.'
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)
        
        # 2. OBTER QR CODE - ESTRATÉGIA DEFINITIVA
        # Quando a instância está "close", GET retorna {"count": 0}
        # SOLUÇÃO: Usar POST para forçar conexão e gerar QR Code
        url_connect = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        url_fetch = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        
        qrcode_base64 = None
        qrcode_url = None
        
        logger.info(f"[GET_QRCODE] ========== INICIANDO BUSCA DE QR CODE ==========")
        logger.info(f"[GET_QRCODE] Instância: {INSTANCE_NAME}")
        logger.info(f"[GET_QRCODE] URL Connect: {url_connect}")
        logger.info(f"[GET_QRCODE] URL Fetch: {url_fetch}")
        
        # PASSO 1: Forçar conexão via POST (isso gera o QR Code)
        logger.info(f"[GET_QRCODE] PASSO 1: Forçando conexão via POST para gerar QR Code...")
        try:
            post_response = requests.post(url_connect, headers=headers, timeout=30)
            logger.info(f"[GET_QRCODE] POST /instance/connect/{INSTANCE_NAME} - Status: {post_response.status_code}")
            logger.info(f"[GET_QRCODE] POST Response: {post_response.text[:1000]}")
            
            if post_response.status_code in [200, 201]:
                try:
                    post_data = post_response.json()
                    logger.info(f"[GET_QRCODE] POST Data (tipo: {type(post_data)}): {json.dumps(post_data, indent=2)}")
                    
                    # Verificar se QR Code veio no POST
                    post_qrcode = post_data.get('qrcode', {})
                    if isinstance(post_qrcode, dict) and post_qrcode.get('base64'):
                        logger.info(f"[GET_QRCODE] ✅✅✅ QR Code obtido via POST! ✅✅✅")
                        qrcode_base64 = post_qrcode.get('base64')
                        qrcode_url = post_qrcode.get('url')
                    else:
                        logger.info(f"[GET_QRCODE] QR Code não veio no POST, aguardando 5 segundos...")
                        time.sleep(5)
                except Exception as e:
                    logger.warning(f"[GET_QRCODE] Erro ao parsear POST: {str(e)}")
            else:
                logger.warning(f"[GET_QRCODE] POST falhou com status {post_response.status_code}")
        except Exception as e:
            logger.error(f"[GET_QRCODE] Erro no POST: {str(e)}", exc_info=True)
        
        # PASSO 2: Tentar obter QR Code via GET (com retry)
        # Tentar até 20 vezes com intervalos progressivos
        if not qrcode_base64:
            logger.info(f"[GET_QRCODE] PASSO 2: Buscando QR Code via GET (com retry)...")
            for attempt in range(20):
                try:
                    logger.info(f"[GET_QRCODE] ========== TENTATIVA {attempt + 1}/20 ==========")
                    logger.info(f"[GET_QRCODE] URL: {url_connect}")
                    logger.info(f"[GET_QRCODE] Headers: {headers}")
                    
                    # Método 1: Tentar /instance/connect/{instanceName} (GET)
                    response = requests.get(url_connect, headers=headers, timeout=LONG_TIMEOUT)
                    logger.info(f"[GET_QRCODE] Status code: {response.status_code}")
                    logger.info(f"[GET_QRCODE] Response headers: {dict(response.headers)}")
                    logger.info(f"[GET_QRCODE] Response text (primeiros 1000 chars): {response.text[:1000]}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"[GET_QRCODE] Tipo da resposta: {type(data)}")
                            logger.info(f"[GET_QRCODE] Dados completos (JSON): {json.dumps(data, indent=2)}")
                            
                            # Verificar se retornou qrcode diretamente ou dentro de um objeto
                            if isinstance(data, dict):
                                logger.info(f"[GET_QRCODE] Chaves no dict: {list(data.keys())}")
                            
                            # Tentar diferentes formatos de resposta
                            qrcode_data = data.get('qrcode', {})
                            logger.info(f"[GET_QRCODE] qrcode_data (tipo: {type(qrcode_data)}): {qrcode_data}")
                            
                            if not qrcode_data and 'base64' in data:
                                logger.info(f"[GET_QRCODE] base64 encontrado diretamente no dict")
                                qrcode_data = data
                            elif not qrcode_data and 'instance' in data:
                                logger.info(f"[GET_QRCODE] Verificando dentro de instance...")
                                instance_data = data.get('instance', {})
                                logger.info(f"[GET_QRCODE] instance_data: {json.dumps(instance_data, indent=2)}")
                                qrcode_data = instance_data.get('qrcode', {})
                                logger.info(f"[GET_QRCODE] qrcode_data dentro de instance: {qrcode_data}")
                            
                            if isinstance(qrcode_data, dict):
                                logger.info(f"[GET_QRCODE] Chaves no qrcode_data: {list(qrcode_data.keys())}")
                                logger.info(f"[GET_QRCODE] qrcode_data.count: {qrcode_data.get('count')}")
                                logger.info(f"[GET_QRCODE] qrcode_data.base64 existe: {'base64' in qrcode_data}")
                                logger.info(f"[GET_QRCODE] qrcode_data.url existe: {'url' in qrcode_data}")
                                
                                if 'base64' in qrcode_data:
                                    base64_value = qrcode_data.get('base64')
                                    logger.info(f"[GET_QRCODE] base64 encontrado! Tipo: {type(base64_value)}, Tamanho: {len(str(base64_value)) if base64_value else 0}")
                                
                                qrcode_base64 = qrcode_data.get('base64') if isinstance(qrcode_data, dict) else None
                                qrcode_url = qrcode_data.get('url') if isinstance(qrcode_data, dict) else None
                                
                                # Log detalhado
                                if qrcode_base64:
                                    logger.info(f"[GET_QRCODE] ✅✅✅ QR Code obtido com sucesso na tentativa {attempt + 1}! ✅✅✅")
                                    logger.info(f"[GET_QRCODE] Tamanho do base64: {len(qrcode_base64)} caracteres")
                                    logger.info(f"[GET_QRCODE] URL do QR Code: {qrcode_url}")
                                    break
                                else:
                                    logger.warning(f"[GET_QRCODE] ⚠️ QR Code ainda não disponível (tentativa {attempt + 1}/20)")
                                    if attempt < 3:  # Log completo apenas nas primeiras tentativas
                                        logger.warning(f"[GET_QRCODE] Dados completos: {json.dumps(data, indent=2)}")
                            else:
                                logger.warning(f"[GET_QRCODE] qrcode_data não é dict: {type(qrcode_data)}")
                            
                            # Método 2: Tentar buscar via fetchInstances (a cada 3 tentativas)
                            if attempt % 3 == 0 and not qrcode_base64:
                                logger.info(f"[GET_QRCODE] Tentando método alternativo: fetchInstances...")
                                try:
                                    fetch_response = requests.get(url_fetch, headers=headers, timeout=SHORT_TIMEOUT)
                                    logger.info(f"[GET_QRCODE] fetchInstances status: {fetch_response.status_code}")
                                    if fetch_response.status_code == 200:
                                        fetch_data = fetch_response.json()
                                        logger.info(f"[GET_QRCODE] fetchInstances dados recebidos")
                                        
                                        instances = fetch_data if isinstance(fetch_data, list) else fetch_data.get('instance', [])
                                        
                                        for inst in instances:
                                            if isinstance(inst, dict) and inst.get('name') == INSTANCE_NAME:
                                                logger.info(f"[GET_QRCODE] ✅ Instância '{INSTANCE_NAME}' encontrada! Status: {inst.get('connectionStatus')}")
                                                inst_qrcode = inst.get('qrcode', {})
                                                
                                                if isinstance(inst_qrcode, dict) and inst_qrcode.get('base64'):
                                                    qrcode_base64 = inst_qrcode.get('base64')
                                                    qrcode_url = inst_qrcode.get('url')
                                                    logger.info(f"[GET_QRCODE] ✅✅✅ QR Code encontrado via fetchInstances na tentativa {attempt + 1}! ✅✅✅")
                                                    logger.info(f"[GET_QRCODE] Tamanho do base64: {len(qrcode_base64)} caracteres")
                                                    break
                                except Exception as fetch_error:
                                    logger.error(f"[GET_QRCODE] ❌ Erro ao buscar QR Code via fetchInstances: {str(fetch_error)}", exc_info=True)
                                
                                if qrcode_base64:
                                    break
                            else:
                                logger.warning(f"[GET_QRCODE] ⚠️ Resposta não é dict: {type(data)}")
                                logger.warning(f"[GET_QRCODE] Conteúdo: {str(data)[:500]}")
                        except json.JSONDecodeError as json_error:
                            logger.error(f"[GET_QRCODE] ❌ Erro ao parsear JSON: {str(json_error)}")
                            logger.error(f"[GET_QRCODE] Response text: {response.text[:500]}")
                    
                    else:
                        logger.error(f"[GET_QRCODE] ❌ Erro ao obter QR Code: {response.status_code}")
                        logger.error(f"[GET_QRCODE] Response text: {response.text[:500]}")
                        if attempt < 19:
                            time.sleep(5)
                    
                    # Se ainda não tem QR Code, aguardar antes da próxima tentativa
                    if not qrcode_base64:
                        # Aumentar tempo de espera progressivamente: 3s, 5s, 7s, 10s...
                        if attempt < 3:
                            wait_time = 3
                        elif attempt < 6:
                            wait_time = 5
                        elif attempt < 10:
                            wait_time = 7
                        else:
                            wait_time = 10
                        
                        logger.info(f"[GET_QRCODE] ⏳ Aguardando {wait_time} segundos antes da próxima tentativa...")
                        time.sleep(wait_time)
                    else:
                        break  # QR Code encontrado, sair do loop
                except Exception as e:
                    logger.error(f"[GET_QRCODE] ❌❌❌ Erro ao obter QR Code (tentativa {attempt + 1}): {str(e)}", exc_info=True)
                    if attempt < 19:
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

