"""
Script de teste para o módulo WhatsApp
Testa a integração entre gateway FastAPI e Django
"""

import requests
import json

# Configurações
GATEWAY_URL = "http://localhost:8001"
DJANGO_URL = "http://localhost:8000"

def test_gateway_health():
    """Testa health check do gateway"""
    print("🔍 Testando health check do gateway...")
    try:
        response = requests.get(f"{GATEWAY_URL}/health")
        response.raise_for_status()
        print(f"✅ Gateway OK: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_django_health():
    """Testa health check do Django"""
    print("\n🔍 Testando health check do Django...")
    try:
        response = requests.get(f"{DJANGO_URL}/health/")
        response.raise_for_status()
        print(f"✅ Django OK: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_webhook_flow():
    """Testa fluxo completo de webhook"""
    print("\n🔍 Testando fluxo de webhook...")
    
    # Payload simulado do provedor
    payload = {
        "from": "5511999999999",
        "message": "Olá, teste",
        "messageId": "test-123",
        "timestamp": 1234567890,
        "type": "text"
    }
    
    try:
        # Enviar para gateway
        print(f"📤 Enviando para gateway: {payload}")
        response = requests.post(
            f"{GATEWAY_URL}/webhook/whatsapp",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Resposta do gateway: {result}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_django_endpoint_direct():
    """Testa endpoint do Django diretamente"""
    print("\n🔍 Testando endpoint do Django diretamente...")
    
    payload = {
        "from": "5511999999999",
        "message": "Olá, teste direto",
        "message_id": "test-direct-123",
        "timestamp": 1234567890,
        "type": "text"
    }
    
    try:
        response = requests.post(
            f"{DJANGO_URL}/api/whatsapp/webhook-from-gateway/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Resposta do Django: {result}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        if hasattr(e, 'response'):
            print(f"   Resposta: {e.response.text}")
        return False

def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 TESTE DO MÓDULO WHATSAPP - ÉVORA/VITRINEZAP")
    print("=" * 60)
    
    results = []
    
    # Testes básicos
    results.append(("Gateway Health", test_gateway_health()))
    results.append(("Django Health", test_django_health()))
    
    # Testes de integração
    results.append(("Webhook Flow", test_webhook_flow()))
    results.append(("Django Direct", test_django_endpoint_direct()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os logs acima.")

if __name__ == "__main__":
    main()

