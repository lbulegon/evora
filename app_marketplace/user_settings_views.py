"""
Views para Configurações do Usuário - ÉVORA Connect
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction

from .models import PersonalShopper, AddressKeeper, Cliente
from .whatsapp_connection_views import get_session_status


@login_required
def user_settings(request):
    """
    Página principal de configurações do usuário
    """
    # Obter perfil do usuário
    user_profile = None
    profile_type = None
    
    if request.user.is_shopper:
        user_profile = getattr(request.user, 'personalshopper', None)
        profile_type = 'shopper'
    elif request.user.is_address_keeper:
        user_profile = getattr(request.user, 'address_keeper', None)
        profile_type = 'keeper'
    elif request.user.is_cliente:
        user_profile = getattr(request.user, 'cliente', None)
        profile_type = 'cliente'
    
    # Status da conexão WhatsApp (apenas para shoppers e keepers)
    whatsapp_status = None
    if request.user.is_shopper or request.user.is_address_keeper:
        whatsapp_status = get_session_status()
    
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'profile_type': profile_type,
        'whatsapp_status': whatsapp_status,
        'whatsapp_connected': whatsapp_status and whatsapp_status.get('connected', False) if whatsapp_status else False,
    }
    
    return render(request, 'app_marketplace/user_settings.html', context)


@login_required
@require_http_methods(["POST"])
def update_profile(request):
    """
    Atualizar informações do perfil
    """
    try:
        user = request.user
        
        # Atualizar dados básicos do usuário
        if 'first_name' in request.POST:
            user.first_name = request.POST['first_name']
        if 'last_name' in request.POST:
            user.last_name = request.POST['last_name']
        if 'email' in request.POST:
            user.email = request.POST['email']
        
        user.save()
        
        # Atualizar perfil específico
        if user.is_shopper:
            profile = getattr(user, 'personalshopper', None)
            if profile:
                if 'phone' in request.POST:
                    profile.telefone = request.POST['phone']
                if 'bio' in request.POST:
                    profile.bio = request.POST['bio']
                profile.save()
        
        elif user.is_address_keeper:
            profile = getattr(user, 'address_keeper', None)
            if profile:
                if 'phone' in request.POST:
                    profile.telefone = request.POST['phone']
                if 'address' in request.POST:
                    profile.endereco = request.POST['address']
                profile.save()
        
        elif user.is_cliente:
            profile = getattr(user, 'cliente', None)
            if profile:
                if 'phone' in request.POST:
                    profile.telefone = request.POST['phone']
                profile.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        return JsonResponse({'success': True})
    
    except Exception as e:
        messages.error(request, f'Erro ao atualizar perfil: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def change_password(request):
    """
    Alterar senha do usuário
    """
    form = PasswordChangeForm(request.user, request.POST)
    
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # Manter usuário logado
        messages.success(request, 'Senha alterada com sucesso!')
        return JsonResponse({'success': True})
    else:
        errors = form.errors.as_json()
        return JsonResponse({'success': False, 'errors': errors}, status=400)

