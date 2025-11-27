#!/usr/bin/env python
"""
Script para testar o sistema de login
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

def test_login():
    """Testa o sistema de login"""
    print("TESTE DE LOGIN - VitrineZap (ÉVORA)")
    print("=" * 30)
    
    # Criar cliente de teste
    client = Client()
    
    # Verificar se existem usuários
    users = User.objects.all()[:3]
    print(f"Usuários disponíveis: {len(users)}")
    for user in users:
        print(f"  - {user.username}")
    
    # Testar acesso à página de login
    print("\nTestando página de login...")
    try:
        response = client.get('/login/')
        print(f"Status da página login: {response.status_code}")
        
        if response.status_code == 200:
            print("OK Página de login acessível")
        else:
            print("ERRO Problema ao acessar página de login")
            return False
    except Exception as e:
        print(f"ERRO Erro ao acessar login: {e}")
        return False
    
    # Testar login com usuário de teste
    print("\nTestando login com usuário 'teste'...")
    try:
        login_data = {
            'username': 'teste',
            'password': '123456'
        }
        
        response = client.post('/login/', login_data)
        print(f"Status do login: {response.status_code}")
        
        if response.status_code == 302:  # Redirect após login
            print("OK Login realizado com sucesso!")
            print(f"Redirecionado para: {response.url}")
            
            # Testar acesso a página protegida
            response = client.get('/home/')
            print(f"Status da home: {response.status_code}")
            
            if response.status_code == 200:
                print("OK Acesso à home autorizado")
            else:
                print("ERRO Problema ao acessar home")
                
        else:
            print("ERRO Falha no login")
            print(f"Conteúdo: {response.content.decode()[:200]}")
            
    except Exception as e:
        print(f"ERRO Erro no teste de login: {e}")
        return False
    
    print("\n" + "=" * 30)
    print("INSTRUÇÕES PARA LOGIN:")
    print("1. Acesse: http://127.0.0.1:8000/login/")
    print("2. Usuário: teste")
    print("3. Senha: 123456")
    print("4. Ou use qualquer usuário existente")
    
    return True

if __name__ == '__main__':
    test_login()
