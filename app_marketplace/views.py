from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import CadastroClienteForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import (
    Evento,
    Cliente,
    PersonalShopper,
    RelacionamentoClienteShopper
)



@login_required
def home_view(request):
    # Redirecionar Shoppers para dashboard específico
    if request.user.is_shopper:
        return redirect('shopper_dashboard')
    elif request.user.is_keeper:
        return redirect('whatsapp_dashboard')
    
    # Dashboard geral para outros usuários
    eventos = Evento.objects.all().order_by('-criado_em') # ordena por mais recente
    return render(request, 'app_marketplace/home.html', {'eventos': eventos})

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



def clientes(request):
    return render(request, 'app_marketplace/clientes.html')

def personal_shoppers(request):
    """Lista de Personal Shoppers disponíveis"""
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
        status='seguindo'
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
                    defaults={'status': 'seguindo'}
                )
                if not created:
                    relacao.status = 'seguindo'
                    relacao.save()
                messages.success(request, f'Você agora está seguindo {shopper.user.get_full_name() or shopper.user.username}!')
            
            elif acao == 'deixar_seguir':
                # Atualizar relacionamento
                relacao = RelacionamentoClienteShopper.objects.filter(
                    cliente=cliente,
                    personal_shopper=shopper
                ).first()
                if relacao:
                    relacao.status = 'bloqueado'  # ou 'inativo' dependendo da lógica
                    relacao.save()
                    messages.info(request, f'Você deixou de seguir {shopper.user.get_full_name() or shopper.user.username}.')
            
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


def pedidos(request):
    return render(request, 'app_marketplace/pedidos.html')