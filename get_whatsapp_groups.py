#!/usr/bin/env python
"""
Script para obter Chat IDs dos grupos WhatsApp via WPPConnect
"""
import requests
import json

def get_whatsapp_groups():
    """Obter lista de grupos WhatsApp"""
    wppconnect_url = "http://localhost:21465"  # URL do WPPConnect
    
    try:
        # Listar grupos
        response = requests.get(f"{wppconnect_url}/api/groups")
        
        if response.status_code == 200:
            groups = response.json()
            
            print("📱 GRUPOS WHATSAPP DISPONÍVEIS:")
            print("=" * 50)
            
            for group in groups.get('groups', []):
                print(f"📋 Nome: {group.get('name', 'N/A')}")
                print(f"🆔 Chat ID: {group.get('id', 'N/A')}")
                print(f"👥 Participantes: {group.get('participants', 0)}")
                print("-" * 30)
            
            return groups.get('groups', [])
        else:
            print(f"❌ Erro ao conectar com WPPConnect: {response.status_code}")
            return []
            
    except requests.exceptions.ConnectionError:
        print("❌ WPPConnect não está rodando!")
        print("Execute: docker run -p 21465:21465 devlikeapro/wppconnect-server:latest")
        return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def create_group_in_evora(chat_id, name):
    """Criar grupo no ÉVORA usando Chat ID"""
    import os
    import django
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
    django.setup()
    
    from django.contrib.auth.models import User
    from app_marketplace.models import WhatsappGroup, PersonalShopper
    
    try:
        # Buscar usuário (assumindo que é a Marcia)
        user = User.objects.get(username='marcia')
        shopper = PersonalShopper.objects.get(user=user)
        
        # Criar grupo
        group, created = WhatsappGroup.objects.get_or_create(
            chat_id=chat_id,
            defaults={
                'name': name,
                'owner': user,
                'shopper': shopper,
                'active': True
            }
        )
        
        if created:
            print(f"✅ Grupo criado no ÉVORA: {group.name}")
            print(f"🆔 Chat ID: {group.chat_id}")
            return group
        else:
            print(f"⚠️ Grupo já existe: {group.name}")
            return group
            
    except Exception as e:
        print(f"❌ Erro ao criar grupo: {e}")
        return None

def main():
    """Função principal"""
    print("🔍 OBTENDO CHAT IDs DOS GRUPOS WHATSAPP")
    print("=" * 50)
    
    # Obter grupos
    groups = get_whatsapp_groups()
    
    if groups:
        print(f"\n📊 Total de grupos encontrados: {len(groups)}")
        
        # Perguntar se quer criar no ÉVORA
        print("\n❓ Deseja criar estes grupos no ÉVORA?")
        print("1. Sim - Criar todos")
        print("2. Não - Apenas mostrar Chat IDs")
        
        choice = input("Escolha (1/2): ").strip()
        
        if choice == "1":
            for group in groups:
                create_group_in_evora(
                    group.get('id'),
                    group.get('name')
                )
    else:
        print("\n💡 DICAS PARA OBTER CHAT IDs:")
        print("1. Use o WPPConnect: docker run -p 21465:21465 devlikeapro/wppconnect-server:latest")
        print("2. Acesse: http://localhost:21465/api/groups")
        print("3. Ou use o WhatsApp Web e copie da URL")

if __name__ == '__main__':
    main()
