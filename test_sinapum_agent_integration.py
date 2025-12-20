#!/usr/bin/env python
"""
Teste de Integração Django ↔ SinapUm (Agente Ágnosto)
======================================================

Script para verificar se a integração está funcionando corretamente.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.conf import settings
import requests

def test_configuration():
    """Testa se as configurações estão corretas"""
    print("=" * 60)
    print("🔍 TESTE 1: Verificação de Configuração")
    print("=" * 60)
    
    sinapum_url = getattr(settings, 'SINAPUM_AGENT_URL', None)
    sinapum_key = getattr(settings, 'SINAPUM_API_KEY', None)
    openmind_key = getattr(settings, 'OPENMIND_AI_KEY', None)
    
    print(f"  SINAPUM_AGENT_URL: {sinapum_url}")
    print(f"  SINAPUM_API_KEY: {'✅ Configurado' if sinapum_key else '❌ Não configurado'}")
    print(f"  OPENMIND_AI_KEY (fallback): {'✅ Configurado' if openmind_key else '❌ Não configurado'}")
    
    if not sinapum_url:
        print("\n❌ ERRO: SINAPUM_AGENT_URL não configurada!")
        return False
    
    if not sinapum_key and not openmind_key:
        print("\n❌ ERRO: Nenhuma API key configurada (SINAPUM_API_KEY ou OPENMIND_AI_KEY)!")
        return False
    
    print("\n✅ Configuração OK")
    return True


def test_sinapum_connection():
    """Testa conexão com SinapUm"""
    print("\n" + "=" * 60)
    print("🧪 TESTE 2: Teste de Conexão com SinapUm")
    print("=" * 60)
    
    sinapum_url = getattr(settings, 'SINAPUM_AGENT_URL', None)
    sinapum_key = getattr(settings, 'SINAPUM_API_KEY') or getattr(settings, 'OPENMIND_AI_KEY', None)
    
    if not sinapum_key:
        print("❌ API key não disponível")
        return False
    
    # Teste 1: Health check
    base_url = sinapum_url.replace('/api/v1/process-message', '')
    health_url = f"{base_url}/health"
    
    print(f"\n1️⃣ Testando health check: {health_url}")
    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check OK")
        else:
            print(f"   ⚠️  Health check retornou {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Teste 2: Listar papéis
    roles_url = f"{base_url}/api/v1/agent/roles"
    print(f"\n2️⃣ Testando listar papéis: {roles_url}")
    try:
        headers = {"Authorization": f"Bearer {sinapum_key}"}
        response = requests.get(roles_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Papéis disponíveis: {data.get('roles', [])}")
        else:
            print(f"   ❌ Erro {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Teste 3: Processar mensagem
    print(f"\n3️⃣ Testando processar mensagem: {sinapum_url}")
    payload = {
        "message": "Quero adicionar 2 unidades",
        "conversation_id": "TEST-INTEGRATION-123",
        "user_phone": "+5511999999999",
        "user_name": "Teste Integração",
        "is_group": False,
        "agent_role": "vendedor",
        "language": "pt-BR",
        "metadata": {
            "produto_id": 1,
            "produto_nome": "Produto Teste",
            "preco": "89.90",
            "moeda": "BRL"
        }
    }
    
    try:
        headers = {
            "Authorization": f"Bearer {sinapum_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(sinapum_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Mensagem processada com sucesso!")
            print(f"   📝 Resposta: {data.get('message', '')[:100]}...")
            print(f"   🎯 Ação: {data.get('action', 'N/A')}")
            return True
        else:
            print(f"   ❌ Erro {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


def test_django_integration():
    """Testa se o Django está preparado para usar o agente"""
    print("\n" + "=" * 60)
    print("🔧 TESTE 3: Verificação de Código Django")
    print("=" * 60)
    
    try:
        from app_marketplace.whatsapp_flow_engine import WhatsAppFlowEngine
        
        # Verificar se método existe
        if hasattr(WhatsAppFlowEngine, '_processar_com_agente_sinapum'):
            print("   ✅ Método _processar_com_agente_sinapum() encontrado")
        else:
            print("   ❌ Método _processar_com_agente_sinapum() NÃO encontrado")
            return False
        
        # Verificar se requests está disponível
        try:
            import requests
            print("   ✅ Biblioteca 'requests' disponível")
        except ImportError:
            print("   ❌ Biblioteca 'requests' NÃO disponível")
            return False
        
        print("\n✅ Código Django OK")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar código: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("🚀 TESTE DE INTEGRAÇÃO DJANGO ↔ SINAPUM (AGENTE ÁGNOSTO)")
    print("=" * 60)
    
    results = []
    
    # Teste 1: Configuração
    results.append(("Configuração", test_configuration()))
    
    # Teste 2: Conexão SinapUm (só se configuração OK)
    if results[0][1]:
        results.append(("Conexão SinapUm", test_sinapum_connection()))
    else:
        results.append(("Conexão SinapUm", False))
        print("\n⚠️  Pulando teste de conexão (configuração inválida)")
    
    # Teste 3: Código Django
    results.append(("Código Django", test_django_integration()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("   A integração está pronta para uso.")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("   Verifique os erros acima e corrija antes de usar.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

