#!/usr/bin/env python
"""
Script de teste para integração KMN com frontend VitrineZap (ÉVORA)
Testa as views e templates KMN
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from app_marketplace.models import Agente, Cliente, PersonalShopper, Keeper


def test_frontend_integration():
    """Testa a integração do frontend KMN"""
    print("TESTE DE INTEGRAÇÃO FRONTEND KMN")
    print("=" * 50)
    
    # Criar cliente de teste
    client = Client()
    
    # Criar usuário shopper
    try:
        user = User.objects.get(username='junior_orlando')
        print(f"Usuário encontrado: {user.username}")
    except User.DoesNotExist:
        print("Usuário de teste não encontrado. Execute primeiro: python test_kmn_system.py")
        return False
    
    # Fazer login
    client.force_login(user)
    print(f"Login realizado como: {user.username}")
    
    # Testar URLs KMN
    urls_to_test = [
        ('kmn_dashboard', 'Dashboard KMN'),
        ('kmn_clientes', 'Clientes KMN'),
        ('kmn_ofertas', 'Ofertas KMN'),
    ]
    
    print("\nTestando URLs KMN:")
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            response = client.get(url)
            
            if response.status_code == 200:
                print(f"OK {description}: OK (200)")
            elif response.status_code == 302:
                print(f"-> {description}: Redirect (302)")
            else:
                print(f"ERROR {description}: Error ({response.status_code})")
                
        except Exception as e:
            print(f"ERROR {description}: Exception - {e}")
    
    # Testar API endpoints
    print("\nTestando APIs KMN:")
    api_urls = [
        '/api/kmn/agentes/',
        '/api/kmn/clientes/',
        '/api/kmn/produtos/',
        '/api/kmn/ofertas/',
    ]
    
    for api_url in api_urls:
        try:
            response = client.get(api_url)
            if response.status_code == 200:
                print(f"OK {api_url}: OK (200)")
            elif response.status_code == 302:
                print(f"-> {api_url}: Redirect (302)")
            else:
                print(f"ERROR {api_url}: Error ({response.status_code})")
        except Exception as e:
            print(f"ERROR {api_url}: Exception - {e}")
    
    print("\n" + "=" * 50)
    print("INTEGRAÇÃO FRONTEND TESTADA!")
    print("\nPara acessar o sistema:")
    print("1. Acesse: http://localhost:8000/")
    print("2. Faça login com um usuário shopper/keeper")
    print("3. Use o menu 'KMN' na navegação")
    print("4. APIs disponíveis em: http://localhost:8000/api/kmn/")
    
    return True


if __name__ == '__main__':
    test_frontend_integration()
