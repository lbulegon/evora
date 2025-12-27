from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import CadastroClienteForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
import logging
import hmac
import hashlib
import time
import requests
from .models import (
    Evento,
    Cliente,
    PersonalShopper,
    RelacionamentoClienteShopper,
    Pedido
)

logger = logging.getLogger(__name__)



@login_required
def home_view(request):
    # Redirecionar usuários para seus dashboards específicos
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    elif request.user.is_shopper:
        return redirect('shopper_dashboard')
    elif request.user.is_address_keeper:
        return redirect('whatsapp_dashboard')
    elif request.user.is_cliente:
        return redirect('client_dashboard')
    
    # Dashboard geral para outros usuários
    # Buscar eventos ativos primeiro, depois os outros
    eventos_ativos = Evento.objects.filter(status=Evento.Status.ATIVO).order_by('-data_inicio', '-criado_em')
    eventos_outros = Evento.objects.exclude(status=Evento.Status.ATIVO).order_by('-criado_em')
    eventos = list(eventos_ativos) + list(eventos_outros)
    
    # Estatísticas
    total_eventos = len(eventos)
    eventos_ativos_count = eventos_ativos.count()
    shoppers_unicos = len(set(e.personal_shopper_id for e in eventos if e.personal_shopper_id))
    
    context = {
        'eventos': eventos,
        'total_eventos': total_eventos,
        'eventos_ativos_count': eventos_ativos_count,
        'shoppers_unicos': shoppers_unicos,
    }
    
    return render(request, 'app_marketplace/home.html', context)

def index(request):
    return render(request, 'app_marketplace/index.html')

def cadastro(request):
    """
    Cadastro APENAS para Clientes.
    Após cadastro, redireciona para escolher Personal Shoppers.
    """
    # Se já está logado, redirecionar
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CadastroClienteForm(request.POST)
        if form.is_valid():
            # Criar User
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Criar perfil Cliente automaticamente
            telefone = form.cleaned_data.get('telefone', '')
            cliente, created = Cliente.objects.get_or_create(
                user=user,
                defaults={
                    'telefone': telefone,
                    'contato': {
                        'telefone': telefone,
                        'email': user.email
                    }
                }
            )
            
            # Se cliente já existia, atualizar telefone se fornecido
            if not created and telefone:
                cliente.telefone = telefone
                if not cliente.contato:
                    cliente.contato = {}
                cliente.contato['telefone'] = telefone
                cliente.save()
            
            # Fazer login
            login(request, user)
            
            # Redirecionar para escolher shoppers
            messages.success(request, 'Cadastro realizado com sucesso! Agora escolha os Personal Shoppers que deseja seguir.')
            return redirect('escolher_shoppers')
    else:
        form = CadastroClienteForm()
    
    return render(request, 'app_marketplace/cadastro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redireciona para home
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'app_marketplace/login.html')

def logout_view(request):
    logout(request)
    return redirect('/')


def solicitar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    # lógica para adicionar o usuário como solicitante
    # ...
    return redirect('home')  # ou onde quiser redirecionar



@login_required
def clientes(request):
    """
    Lista de clientes.
    
    - Se for Shopper (request.user.is_shopper): mostra apenas clientes da(s)
      carteira(s) do shopper OU clientes que seguem este shopper.
    - Para outros perfis (admin, staff, etc.): mostra todos os clientes.
    """
    if getattr(request.user, 'is_shopper', False):
        # Shopper logado
        try:
            shopper = request.user.personalshopper
        except PersonalShopper.DoesNotExist:
            shopper = None

        # Base: nenhum cliente
        clientes_qs = Cliente.objects.none()

        if shopper:
            # 1) Clientes que seguem este shopper (relacionamento SEGUINDO)
            clientes_seguindo = Cliente.objects.filter(
                relacionamentoclienteshopper__personal_shopper=shopper,
                relacionamentoclienteshopper__status=RelacionamentoClienteShopper.Status.SEGUINDO,
            )

            # 2) (Opcional/futuro) Clientes da(s) carteiras do shopper
            clientes_carteira = Cliente.objects.filter(wallet__owner=request.user)

            # Unir conjuntos e remover duplicados
            clientes_qs = (clientes_seguindo | clientes_carteira).select_related('user').distinct()

        clientes = clientes_qs.order_by('-criado_em')
    else:
        # Admin / outros usuários: ver todos
        clientes = Cliente.objects.select_related('user').all().order_by('-criado_em')
    
    context = {
        'clientes': clientes,
    }
    
    return render(request, 'app_marketplace/clientes.html', context)

def personal_shoppers(request):
    """
    Lista de Personal Shoppers disponíveis.
    Para clientes: mostra apenas os shoppers que está seguindo.
    Para outros usuários: mostra todos os shoppers ativos.
    """
    # Se for cliente, mostrar apenas os shoppers que ele está seguindo
    if request.user.is_authenticated and request.user.is_cliente:
        try:
            cliente = request.user.cliente
            # Obter IDs dos shoppers que o cliente está seguindo
            shoppers_seguindo = RelacionamentoClienteShopper.objects.filter(
                cliente=cliente,
                status=RelacionamentoClienteShopper.Status.SEGUINDO
            ).values_list('personal_shopper_id', flat=True)
            
            # Filtrar apenas os shoppers que o cliente está seguindo e que estão ativos
            shoppers = PersonalShopper.objects.filter(
                id__in=shoppers_seguindo,
                ativo=True
            ).select_related('user')
        except Cliente.DoesNotExist:
            # Se não tem perfil cliente, mostrar todos os shoppers ativos
            shoppers = PersonalShopper.objects.filter(ativo=True).select_related('user')
    else:
        # Para usuários não clientes, mostrar todos os shoppers ativos
        shoppers = PersonalShopper.objects.filter(ativo=True).select_related('user')
    
    return render(request, 'app_marketplace/personal_shoppers.html', {'shoppers': shoppers})


@login_required
def escolher_shoppers(request):
    """
    Página para cliente escolher quais Personal Shoppers seguir.
    Aparece após cadastro ou pode ser acessada depois.
    """
    # Verificar se é cliente
    if not request.user.is_cliente:
        messages.error(request, 'Esta página é apenas para clientes.')
        return redirect('home')
    
    cliente = request.user.cliente
    
    # Obter todos os shoppers ativos
    todos_shoppers = PersonalShopper.objects.filter(ativo=True).select_related('user')
    
    # Obter shoppers que o cliente já segue
    shoppers_seguindo = RelacionamentoClienteShopper.objects.filter(
        cliente=cliente,
        status=RelacionamentoClienteShopper.Status.SEGUINDO
    ).values_list('personal_shopper_id', flat=True)
    
    # Processar ação (seguir/deixar de seguir)
    if request.method == 'POST':
        shopper_id = request.POST.get('shopper_id')
        acao = request.POST.get('acao')  # 'seguir' ou 'deixar_seguir'
        
        try:
            shopper = PersonalShopper.objects.get(id=shopper_id, ativo=True)
            
            if acao == 'seguir':
                # Criar ou atualizar relacionamento
                relacao, created = RelacionamentoClienteShopper.objects.get_or_create(
                    cliente=cliente,
                    personal_shopper=shopper,
                    defaults={'status': RelacionamentoClienteShopper.Status.SEGUINDO}
                )
                if not created:
                    relacao.status = RelacionamentoClienteShopper.Status.SEGUINDO
                    relacao.save()
                messages.success(request, f'Você agora está seguindo {shopper.user.get_full_name() or shopper.user.username}!')
            
            elif acao == 'deixar_seguir':
                # Atualizar relacionamento para bloqueado
                relacao = RelacionamentoClienteShopper.objects.filter(
                    cliente=cliente,
                    personal_shopper=shopper
                ).first()
                if relacao:
                    relacao.status = RelacionamentoClienteShopper.Status.BLOQUEADO
                    relacao.save()
                    messages.info(request, f'Você deixou de seguir {shopper.user.get_full_name() or shopper.user.username}. O shopper não aparecerá mais na sua lista.')
                else:
                    # Se não existe relacionamento, criar como bloqueado
                    RelacionamentoClienteShopper.objects.create(
                        cliente=cliente,
                        personal_shopper=shopper,
                        status=RelacionamentoClienteShopper.Status.BLOQUEADO
                    )
                    messages.info(request, f'Você deixou de seguir {shopper.user.get_full_name() or shopper.user.username}. O shopper não aparecerá mais na sua lista.')
            
            return redirect('escolher_shoppers')
            
        except PersonalShopper.DoesNotExist:
            messages.error(request, 'Personal Shopper não encontrado.')
    
    # Preparar dados para template
    shoppers_com_status = []
    for shopper in todos_shoppers:
        esta_seguindo = shopper.id in shoppers_seguindo
        shoppers_com_status.append({
            'shopper': shopper,
            'esta_seguindo': esta_seguindo
        })
    
    context = {
        'shoppers': shoppers_com_status,
        'total_seguindo': len(shoppers_seguindo)
    }
    
    return render(request, 'app_marketplace/escolher_shoppers.html', context)


@login_required
def pedidos(request):
    """
    Lista de pedidos/compras do cliente logado.
    Apenas clientes podem ver seus próprios pedidos.
    """
    # Verificar se é cliente
    if not request.user.is_cliente:
        messages.error(request, 'Esta página é apenas para clientes.')
        return redirect('home')
    
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('home')
    
    try:
        # Buscar apenas pedidos deste cliente
        pedidos_queryset = Pedido.objects.filter(cliente=cliente).select_related(
            'cliente',
            'shopper'
        ).order_by('-criado_em')
        
        # Filtros opcionais
        status_filter = request.GET.get('status', '')
        if status_filter:
            pedidos_queryset = pedidos_queryset.filter(status=status_filter)
        
        # Obter status choices de forma segura
        try:
            status_choices = Pedido.Status.choices
        except AttributeError:
            # Fallback caso Status não tenha choices definidas
            status_choices = []
        
        context = {
            'pedidos': pedidos_queryset,
            'status_filter': status_filter,
            'status_choices': status_choices,
        }
        
        return render(request, 'app_marketplace/pedidos.html', context)
    
    except Exception as e:
        # Log do erro para debug
        logger.error(f"Erro na view pedidos: {str(e)}", exc_info=True)
        
        messages.error(request, 'Ocorreu um erro ao carregar seus pedidos. Por favor, tente novamente.')
        return redirect('home')


@csrf_exempt
@require_http_methods(["POST"])
def capture_lead(request):
    """
    View que recebe o form do frontend e publica o lead no Core_SinapUm.
    Integração com Lead Registry usando autenticação HMAC.
    """
    try:
        # Validar honeypot (anti-bot)
        if request.POST.get('website'):
            logger.warning("Tentativa de captura de lead detectada como bot (honeypot preenchido)")
            return JsonResponse({'ok': False, 'error': 'invalid_request'}, status=400)
        
        # Validar campos obrigatórios
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        whatsapp = request.POST.get('whatsapp', '').strip()
        cidade = request.POST.get('cidade', '').strip()
        
        if not (nome and email and whatsapp):
            return JsonResponse({
                'ok': False,
                'error': 'missing_fields',
                'message': 'Por favor, preencha todos os campos obrigatórios.'
            }, status=400)
        
        # Configurações do Lead Registry
        PROJECT_KEY = settings.VITRINEZAP_LEAD_PROJECT_KEY
        PROJECT_SECRET = settings.VITRINEZAP_LEAD_SECRET
        CORE_URL = settings.CORE_LEAD_URL
        
        # Gerar assinatura HMAC
        timestamp = str(int(time.time()))
        message = f"{PROJECT_KEY}{timestamp}{email}{whatsapp}"
        signature = hmac.new(
            PROJECT_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Log detalhado para debug
        logger.info(
            f"🔐 Gerando HMAC para Core_SinapUm:\n"
            f"   Project Key: {PROJECT_KEY}\n"
            f"   Timestamp: {timestamp}\n"
            f"   Email: {email}\n"
            f"   WhatsApp: {whatsapp}\n"
            f"   Message: {message}\n"
            f"   Signature: {signature[:40]}..."
        )
        
        # Headers de autenticação
        headers = {
            'X-Project-Key': PROJECT_KEY,
            'X-Signature': signature,
            'X-Timestamp': timestamp,
            'X-Requested-With': 'XMLHttpRequest',  # Indica que é uma chamada AJAX
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        # Dados do lead
        data = {
            'nome': nome,
            'email': email,
            'whatsapp': whatsapp,
            'cidade': cidade,
            'source_system': request.POST.get('source_system', 'vitrinezap'),
            'source_entrypoint': request.POST.get('source_entrypoint', 'home'),
            'source_context': request.POST.get('source_context', 'lista_antecipada'),
        }
        
        # UTM parameters (se houver)
        utm_source = request.POST.get('utm_source', '')
        utm_campaign = request.POST.get('utm_campaign', '')
        utm_medium = request.POST.get('utm_medium', '')
        utm_content = request.POST.get('utm_content', '')
        
        if utm_source:
            data['utm_source'] = utm_source
        if utm_campaign:
            data['utm_campaign'] = utm_campaign
        if utm_medium:
            data['utm_medium'] = utm_medium
        if utm_content:
            data['utm_content'] = utm_content
        
        # Enviar para o Core_SinapUm
        api_url = f"{CORE_URL}/api/leads/capture"
        
        logger.info(f"📤 Enviando lead para Core_SinapUm: {api_url}")
        logger.debug(f"   Headers: {headers}")
        logger.debug(f"   Data: {data}")
        
        try:
            response = requests.post(
                api_url,
                data=data,
                headers=headers,
                timeout=10
            )
            
            logger.info(
                f"📥 Resposta do Core_SinapUm: Status {response.status_code} | "
                f"Headers: {dict(response.headers)}"
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Lead capturado com sucesso: {email}")
                    return JsonResponse({
                        'ok': True,
                        'message': 'Cadastro realizado com sucesso! Em breve você receberá vitrines no WhatsApp.'
                    })
                else:
                    logger.error(f"Erro ao capturar lead: {result.get('error')}")
                    return JsonResponse({
                        'ok': False,
                        'error': result.get('error', 'unknown_error'),
                        'message': 'Erro ao processar seu cadastro. Por favor, tente novamente.'
                    }, status=400)
            else:
                logger.error(f"Erro HTTP ao capturar lead: {response.status_code} - {response.text}")
                return JsonResponse({
                    'ok': False,
                    'error': 'server_error',
                    'message': 'Erro ao processar seu cadastro. Por favor, tente novamente.'
                }, status=500)
                
        except requests.exceptions.Timeout:
            logger.error("Timeout ao enviar lead para Core_SinapUm")
            return JsonResponse({
                'ok': False,
                'error': 'timeout',
                'message': 'Tempo de resposta excedido. Por favor, tente novamente.'
            }, status=504)
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão ao enviar lead: {str(e)}")
            return JsonResponse({
                'ok': False,
                'error': 'connection_error',
                'message': 'Erro de conexão. Por favor, verifique sua internet e tente novamente.'
            }, status=503)
            
    except Exception as e:
        logger.error(f"Erro inesperado na captura de lead: {str(e)}", exc_info=True)
        return JsonResponse({
            'ok': False,
            'error': 'unexpected_error',
            'message': 'Ocorreu um erro inesperado. Por favor, tente novamente.'
        }, status=500)