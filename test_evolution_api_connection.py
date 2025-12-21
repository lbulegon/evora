#!/usr/bin/env python3
"""
Script para testar conexão com Evolution API
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

def get_headers():
    return {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
        "Authorization": f"Bearer {EVOLUTION_API_KEY}"
    }

def test_evolution_api():
    print("=" * 60)
    print("🧪 Teste de Conexão com Evolution API")
    print("=" * 60)
    
    # 1. Testar se Evolution API está respondendo
    print("\n1️⃣ Testando se Evolution API está respondendo...")
    try:
        response = requests.get(EVOLUTION_API_URL, headers=get_headers(), timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Evolution API está respondendo!")
            print(f"   Versão: {data.get('version', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
        else:
            print(f"❌ Evolution API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com Evolution API: {str(e)}")
        return False
    
    # 2. Listar instâncias
    print("\n2️⃣ Listando instâncias...")
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                instances = data
            elif isinstance(data, dict):
                instances = data.get('instance', [])
            else:
                instances = []
            
            print(f"✅ Encontradas {len(instances)} instância(s):")
            for inst in instances:
                if isinstance(inst, dict):
                    name = inst.get('name', 'N/A')
                    status = inst.get('connectionStatus', 'N/A')
                    number = inst.get('number', 'N/A')
                    print(f"   - {name}: {status} ({number})")
        else:
            print(f"❌ Erro ao listar instâncias: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao listar instâncias: {str(e)}")
        return False
    
    # 3. Verificar instância específica
    print(f"\n3️⃣ Verificando instância '{INSTANCE_NAME}'...")
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchStatus/{INSTANCE_NAME}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            instance_data = data.get('instance', {}).get('instance', {})
            status = instance_data.get('connectionStatus', 'N/A')
            number = instance_data.get('number', 'N/A')
            print(f"✅ Instância '{INSTANCE_NAME}' encontrada!")
            print(f"   Status: {status}")
            print(f"   Número: {number}")
        else:
            print(f"⚠️  Instância '{INSTANCE_NAME}' não encontrada ou erro: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Erro ao verificar instância: {str(e)}")
    
    # 4. Testar obtenção de QR Code
    print(f"\n4️⃣ Testando obtenção de QR Code para '{INSTANCE_NAME}'...")
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        response = requests.get(url, headers=get_headers(), timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            qrcode_data = data.get('qrcode', {})
            qrcode_base64 = qrcode_data.get('base64')
            qrcode_url = qrcode_data.get('url')
            
            if qrcode_base64:
                print(f"✅ QR Code disponível!")
                print(f"   URL: {qrcode_url}")
                print(f"   Base64 presente: Sim ({len(qrcode_base64)} caracteres)")
            else:
                print(f"⚠️  QR Code não disponível (instância pode estar conectada)")
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', f'Status {response.status_code}')
            print(f"❌ Erro ao obter QR Code: {error_msg}")
    except Exception as e:
        print(f"❌ Erro ao obter QR Code: {str(e)}")
    
    # 5. Testar serviço Django
    print(f"\n5️⃣ Testando serviço EvolutionAPIService do Django...")
    try:
        service = EvolutionAPIService()
        status = service.get_instance_status(INSTANCE_NAME)
        
        if status.get('success'):
            print(f"✅ Serviço Django funcionando!")
            print(f"   Status retornado: {status.get('status', 'N/A')}")
        else:
            print(f"⚠️  Serviço Django retornou erro: {status.get('error', 'Erro desconhecido')}")
    except Exception as e:
        print(f"❌ Erro ao testar serviço Django: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_evolution_api()

