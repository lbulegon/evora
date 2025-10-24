#!/usr/bin/env python
"""
Script para criar novo shopper Marcia
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from app_marketplace.models import PersonalShopper

def create_shopper_marcia():
    """Criar shopper Marcia"""
    print("👩 Criando novo shopper Marcia...")
    
    # Criar usuário
    user, created = User.objects.get_or_create(
        username='marcia',
        defaults={
            'first_name': 'Marcia',
            'last_name': 'Silva',
            'email': 'marcia@evora.com'
        }
    )
    
    if created:
        user.set_password('123456')
        user.save()
        print(f"✅ Usuário criado: {user.username}")
    else:
        print(f"⚠️  Usuário já existe: {user.username}")
    
    # Criar perfil de Personal Shopper
    shopper, created = PersonalShopper.objects.get_or_create(
        user=user,
        defaults={
            'nome': 'Marcia Silva',
            'ativo': True
        }
    )
    
    if created:
        print(f"✅ Personal Shopper criado: {shopper.nome}")
    else:
        print(f"⚠️  Personal Shopper já existe: {shopper.nome}")
    
    print(f"\n🎉 Shopper Marcia criado com sucesso!")
    print(f"📧 Email: {user.email}")
    print(f"👤 Username: {user.username}")
    print(f"🔑 Senha: 123456")
    print(f"🛍️  Status: {'Ativo' if shopper.ativo else 'Inativo'}")
    
    return user, shopper

def main():
    """Função principal"""
    print("👩 Criando novo shopper Marcia...")
    
    try:
        user, shopper = create_shopper_marcia()
        
        print("\n" + "="*60)
        print("✅ SHOPPER MARCIA CRIADO COM SUCESSO!")
        print("="*60)
        print(f"\n🔐 Credenciais de acesso:")
        print(f"   Username: marcia")
        print(f"   Senha: 123456")
        print(f"   URL: http://127.0.0.1:8000/login/")
        
        print(f"\n🎯 Funcionalidades disponíveis:")
        print(f"   ✅ Dashboard Shopper")
        print(f"   ✅ Gerenciar Grupos WhatsApp")
        print(f"   ✅ Catálogo de Produtos")
        print(f"   ✅ Controle de Pedidos")
        print(f"   ✅ Analytics Detalhados")
        
        print(f"\n🏪 Próximos passos:")
        print(f"   1. Fazer login com as credenciais")
        print(f"   2. Criar grupos WhatsApp")
        print(f"   3. Adicionar estabelecimentos")
        print(f"   4. Começar a postar produtos")
        
    except Exception as e:
        print(f"\n❌ Erro ao criar shopper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
