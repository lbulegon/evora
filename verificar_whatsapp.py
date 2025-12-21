#!/usr/bin/env python3
"""
Script para verificar status do WhatsApp
"""

import requests
import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.conf import settings
from app_whatsapp_integration.evolution_service import EvolutionAPIService

EVOLUTION_API_URL = getattr(settings, 'EVOLUTION_API_URL', 'http://69.169.102.84:8004')
EVOLUTION_API_KEY = getattr(settings, 'EVOLUTION_API_KEY', 'GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg')
INSTANCE_NAME = getattr(settings, 'EVOLUTION_INSTANCE_NAME', 'default')


def main():
    print("🔍 Verificando status do WhatsApp...\n")
    
    service = EvolutionAPIService()
    status = service.get_instance_status(INSTANCE_NAME)
    
    if status.get('success'):
        instance_data = status.get('data', {})
        evolution_status = instance_data.get('status', 'unknown')
        phone = instance_data.get('phone_number', 'N/A')
        
        print(f"✅ Instância: {INSTANCE_NAME}")
        print(f"   Status: {evolution_status}")
        print(f"   Telefone: {phone}")
        
        if evolution_status == 'open':
            print("\n✅ WhatsApp está conectado e funcionando!")
        elif evolution_status == 'close':
            print("\n⚠️  WhatsApp está desconectado. Execute conectar_whatsapp.py")
        elif evolution_status == 'connecting':
            print("\n🔄 WhatsApp está conectando...")
        else:
            print(f"\n❓ Status desconhecido: {evolution_status}")
    else:
        print(f"❌ Erro: {status.get('error', 'Erro desconhecido')}")


if __name__ == "__main__":
    main()

