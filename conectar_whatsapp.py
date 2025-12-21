#!/usr/bin/env python3
"""
Script para conectar WhatsApp ao Évora
=======================================

Este script ajuda a:
1. Verificar status da Evolution API
2. Criar instância WhatsApp
3. Gerar QR Code para conectar celular
4. Configurar webhook para receber mensagens
"""

import requests
import json
import sys
import os
from django.core.management import setup_environ
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.conf import settings
from app_whatsapp_integration.evolution_service import EvolutionAPIService

# Configurações
EVOLUTION_API_URL = getattr(settings, 'EVOLUTION_API_URL', 'http://69.169.102.84:8004')
EVOLUTION_API_KEY = getattr(settings, 'EVOLUTION_API_KEY', 'GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg')
INSTANCE_NAME = getattr(settings, 'EVOLUTION_INSTANCE_NAME', 'default')

# URL do webhook Django (ajustar conforme necessário)
DJANGO_WEBHOOK_URL = "http://69.169.102.84:8001/api/whatsapp/webhook/evolution/"


def get_headers():
    """Retorna headers para requisições"""
    return {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
        "Authorization": f"Bearer {EVOLUTION_API_KEY}"
    }


def verificar_evolution_api():
    """Verifica se Evolution API está rodando"""
    print("🔍 Verificando Evolution API...")
    try:
        url = f"{EVOLUTION_API_URL}/"
        response = requests.get(url, headers=get_headers(), timeout=5)
        if response.status_code == 200:
            print("✅ Evolution API está rodando!")
            return True
        else:
            print(f"❌ Evolution API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com Evolution API: {str(e)}")
        print(f"   URL: {EVOLUTION_API_URL}")
        return False


def listar_instancias():
    """Lista instâncias existentes"""
    print("\n📋 Listando instâncias...")
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            instances = data.get('instance', [])
            
            if instances:
                print(f"✅ Encontradas {len(instances)} instância(s):")
                for inst in instances:
                    name = inst.get('instanceName', 'N/A')
                    status = inst.get('status', 'N/A')
                    phone = inst.get('phoneNumber', 'N/A')
                    print(f"   - {name}: {status} ({phone})")
            else:
                print("⚠️  Nenhuma instância encontrada")
            
            return instances
        else:
            print(f"❌ Erro ao listar instâncias: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro ao listar instâncias: {str(e)}")
        return []


def criar_instancia(instance_name=None):
    """Cria uma nova instância WhatsApp"""
    instance_name = instance_name or INSTANCE_NAME
    print(f"\n🔧 Criando instância '{instance_name}'...")
    
    try:
        url = f"{EVOLUTION_API_URL}/instance/create"
        payload = {
            "instanceName": instance_name,
            "token": EVOLUTION_API_KEY,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Instância '{instance_name}' criada com sucesso!")
            return data
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', f'Status {response.status_code}')
            print(f"❌ Erro ao criar instância: {error_msg}")
            return None
    except Exception as e:
        print(f"❌ Erro ao criar instância: {str(e)}")
        return None


def obter_qrcode(instance_name=None):
    """Obtém QR Code para conectar celular"""
    instance_name = instance_name or INSTANCE_NAME
    print(f"\n📱 Obtendo QR Code para instância '{instance_name}'...")
    
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{instance_name}"
        response = requests.get(url, headers=get_headers(), timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            qrcode = data.get('qrcode', {}).get('base64')
            qrcode_url = data.get('qrcode', {}).get('url')
            
            if qrcode:
                print("✅ QR Code gerado!")
                print("\n📱 Escaneie o QR Code com seu WhatsApp:")
                print(f"   URL: {qrcode_url}")
                print("\n💡 Para ver o QR Code em imagem, salve o base64 em um arquivo HTML")
                
                # Salvar QR Code em arquivo HTML para visualização
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>QR Code WhatsApp - {instance_name}</title>
    <style>
        body {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
        }}
        .container {{
            text-align: center;
        }}
        img {{
            max-width: 400px;
            border: 2px solid #25D366;
            padding: 20px;
            background: white;
        }}
        h1 {{
            color: #25D366;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Conectar WhatsApp</h1>
        <p>Escaneie este QR Code com seu WhatsApp</p>
        <img src="data:image/png;base64,{qrcode}" alt="QR Code">
        <p><strong>Instância:</strong> {instance_name}</p>
    </div>
</body>
</html>
"""
                qrcode_file = f"/tmp/qrcode_{instance_name}.html"
                with open(qrcode_file, 'w') as f:
                    f.write(html_content)
                print(f"\n💾 QR Code salvo em: {qrcode_file}")
                print(f"   Abra no navegador: file://{qrcode_file}")
                
                return qrcode
            else:
                print("⚠️  QR Code não disponível. Instância pode já estar conectada.")
                return None
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', f'Status {response.status_code}')
            print(f"❌ Erro ao obter QR Code: {error_msg}")
            return None
    except Exception as e:
        print(f"❌ Erro ao obter QR Code: {str(e)}")
        return None


def configurar_webhook(instance_name=None):
    """Configura webhook para receber mensagens no Django"""
    instance_name = instance_name or INSTANCE_NAME
    print(f"\n🔗 Configurando webhook para instância '{instance_name}'...")
    
    try:
        url = f"{EVOLUTION_API_URL}/webhook/set/{instance_name}"
        payload = {
            "url": DJANGO_WEBHOOK_URL,
            "webhook_by_events": False,
            "webhook_base64": False,
            "events": [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "MESSAGES_DELETE",
                "SEND_MESSAGE",
                "CONNECTION_UPDATE",
                "QRCODE_UPDATED"
            ],
            "webhook_by_events": True
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Webhook configurado com sucesso!")
            print(f"   URL: {DJANGO_WEBHOOK_URL}")
            return True
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', f'Status {response.status_code}')
            print(f"❌ Erro ao configurar webhook: {error_msg}")
            return False
    except Exception as e:
        print(f"❌ Erro ao configurar webhook: {str(e)}")
        return False


def verificar_status_instancia(instance_name=None):
    """Verifica status da instância"""
    instance_name = instance_name or INSTANCE_NAME
    print(f"\n📊 Verificando status da instância '{instance_name}'...")
    
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchStatus/{instance_name}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('instance', {}).get('instance', {}).get('status', 'N/A')
            phone = data.get('instance', {}).get('instance', {}).get('phoneNumber', 'N/A')
            
            print(f"✅ Status: {status}")
            if phone != 'N/A':
                print(f"   Telefone: {phone}")
            
            return status
        else:
            print(f"❌ Erro ao verificar status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao verificar status: {str(e)}")
        return None


def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 Conectar WhatsApp ao Évora")
    print("=" * 60)
    
    # 1. Verificar Evolution API
    if not verificar_evolution_api():
        print("\n❌ Evolution API não está disponível!")
        print("   Execute: cd /root/MCP_SinapUm/services/evolution_api && docker compose up -d")
        return
    
    # 2. Listar instâncias
    instances = listar_instancias()
    
    # 3. Verificar se instância já existe
    instance_exists = False
    for inst in instances:
        if inst.get('instanceName') == INSTANCE_NAME:
            instance_exists = True
            status = inst.get('status', 'unknown')
            print(f"\n✅ Instância '{INSTANCE_NAME}' já existe (status: {status})")
            
            if status == 'open':
                print("✅ WhatsApp já está conectado!")
            elif status == 'close':
                print("⚠️  Instância está fechada. Obtenha novo QR Code.")
            break
    
    # 4. Criar instância se não existir
    if not instance_exists:
        criar_instancia(INSTANCE_NAME)
    
    # 5. Obter QR Code
    qrcode = obter_qrcode(INSTANCE_NAME)
    
    # 6. Configurar webhook
    configurar_webhook(INSTANCE_NAME)
    
    # 7. Verificar status final
    verificar_status_instancia(INSTANCE_NAME)
    
    print("\n" + "=" * 60)
    print("✅ Processo concluído!")
    print("=" * 60)
    print("\n📝 Próximos passos:")
    print("   1. Escaneie o QR Code com seu WhatsApp")
    print("   2. Aguarde a conexão (status: open)")
    print("   3. Envie uma mensagem de teste")
    print("   4. Verifique se chegou no Django")


if __name__ == "__main__":
    main()

