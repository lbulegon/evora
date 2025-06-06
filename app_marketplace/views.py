from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import CadastroClienteForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

@login_required
def home_view(request):
    return render(request, 'app_marketplace/home.html')


def index(request):
    return render(request, 'app_marketplace/index.html')

def cadastro(request):
    if request.method == 'POST':
        form = CadastroClienteForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Encripta senha
            user.save()
            login(request, user)
            return redirect('/')  # redireciona após cadastro
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


def clientes(request):
    return render(request, 'app_marketplace/clientes.html')

def personal_shoppers(request):
    return render(request, 'app_marketplace/personal_shoppers.html')

def pedidos(request):
    return render(request, 'app_marketplace/pedidos.html')