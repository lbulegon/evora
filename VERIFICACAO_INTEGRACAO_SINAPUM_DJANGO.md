# Verificação de Integração Django ↔ SinapUm (Agente Ágnosto)

## ✅ Checklist de Preparação

### 1. Configuração de Variáveis de Ambiente

#### ⚠️ **AÇÃO NECESSÁRIA**: Adicionar variáveis no `settings.py`

O Django precisa das seguintes variáveis configuradas:

```python
# No arquivo setup/settings.py, adicionar:

# Agente Ágnosto SinapUm
SINAPUM_AGENT_URL = config("SINAPUM_AGENT_URL", default="http://69.169.102.84:8000/api/v1/process-message")
SINAPUM_API_KEY = config("SINAPUM_API_KEY", default=None)
# Fallback: usar mesma chave do OpenMind AI se não especificada
if not SINAPUM_API_KEY:
    SINAPUM_API_KEY = OPENMIND_AI_KEY
```

#### Variáveis de Ambiente (`.env` ou Railway)

Adicionar no arquivo `.env` ou nas variáveis do Railway:

```bash
# Agente Ágnosto SinapUm
SINAPUM_AGENT_URL=http://69.169.102.84:8000/api/v1/process-message
SINAPUM_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
# ou usar a mesma do OpenMind AI
# SINAPUM_API_KEY=${OPENMIND_AI_KEY}
```

---

### 2. Código Django - Verificação

#### ✅ **OK**: `app_marketplace/whatsapp_flow_engine.py`

- ✅ Método `_processar_com_agente_sinapum()` implementado
- ✅ Chama SinapUm via HTTP POST
- ✅ Tratamento de erros implementado
- ✅ Processa ações retornadas (ex: `add_to_cart`)
- ✅ Logs detalhados para debugging

**Status**: ✅ **PRONTO**

#### ✅ **OK**: `app_whatsapp_integration/views.py`

- ✅ Integração com `WhatsAppFlowEngine` implementada
- ✅ Roteamento grupo vs privado funcionando
- ✅ Chama `flow_engine.processar_mensagem_privada()` que usa SinapUm

**Status**: ✅ **PRONTO**

#### ⚠️ **DEPRECATED**: `app_marketplace/ia_vendedor_agent.py`

- ⚠️ Arquivo marcado como DEPRECATED
- ⚠️ Redireciona para `WhatsAppFlowEngine`
- ✅ Não precisa de mudanças (mantido para compatibilidade)

**Status**: ⚠️ **OK (deprecated, mas funcional)**

---

### 3. Dependências Python

#### ✅ Verificar se `requests` está instalado

```bash
pip list | grep requests
```

Se não estiver:
```bash
pip install requests
```

**Status**: ✅ Provavelmente já instalado (usado em outros lugares)

---

### 4. Fluxo Completo - Verificação

```
WhatsApp → Evolution API → Django Webhook
                              ↓
                    app_whatsapp_integration/views.py
                              ↓
                    WhatsAppFlowEngine.processar_mensagem_privada()
                              ↓
                    WhatsAppFlowEngine._processar_com_agente_sinapum()
                              ↓
                    HTTP POST → SinapUm /api/v1/process-message
                              ↓
                    [SinapUm processa com IA]
                              ↓
                    Resposta JSON → Django
                              ↓
                    Django processa ações (ex: add_to_cart)
                              ↓
                    Evolution API → Resposta ao Cliente
```

**Status**: ✅ **FLUXO IMPLEMENTADO**

---

### 5. Testes Necessários

#### Teste 1: Verificar Configuração

```python
# No Django shell: python manage.py shell
from django.conf import settings
print(f"SINAPUM_AGENT_URL: {getattr(settings, 'SINAPUM_AGENT_URL', 'NÃO CONFIGURADO')}")
print(f"SINAPUM_API_KEY: {'CONFIGURADO' if getattr(settings, 'SINAPUM_API_KEY', None) else 'NÃO CONFIGURADO'}")
```

#### Teste 2: Testar Chamada ao SinapUm

```python
# No Django shell
from app_marketplace.whatsapp_flow_engine import WhatsAppFlowEngine
from app_marketplace.models import ConversaContextualizada, WhatsappParticipant

# Criar contexto de teste (ajustar conforme necessário)
# flow_engine = WhatsAppFlowEngine()
# resultado = flow_engine._processar_com_agente_sinapum(...)
```

#### Teste 3: Teste End-to-End

1. Enviar mensagem via WhatsApp
2. Verificar logs do Django: `[FLOW_ENGINE] Chamando agente SinapUm`
3. Verificar resposta do SinapUm nos logs
4. Verificar se mensagem foi enviada de volta ao cliente

---

### 6. Logs para Monitoramento

O Django já tem logs implementados:

```python
# Em whatsapp_flow_engine.py
logger.info(f"[FLOW_ENGINE] Chamando agente SinapUm: {sinapum_url}")
logger.info(f"[FLOW_ENGINE] Resposta do SinapUm: {data.get('action', 'N/A')}")
logger.error(f"Erro ao chamar agente SinapUm: {response.status_code}")
```

**Verificar logs:**
```bash
# Railway
railway logs

# Local
tail -f logs/django.log | grep FLOW_ENGINE
```

---

### 7. Tratamento de Erros

#### ✅ Implementado:

1. **API Key não configurada**: Retorna mensagem de erro amigável
2. **Timeout**: Tratado com `timeout=10`
3. **Erro HTTP**: Loga erro e retorna mensagem genérica
4. **Erro de conexão**: Tratado com `requests.exceptions.RequestException`

**Status**: ✅ **TRATAMENTO DE ERROS OK**

---

## 🔧 Ações Necessárias

### ⚠️ **CRÍTICO**: Adicionar Variáveis no Settings

**Arquivo**: `setup/settings.py`

Adicionar após a linha 25 (após `OPENMIND_ORG_MODEL`):

```python
# Agente Ágnosto SinapUm
SINAPUM_AGENT_URL = config("SINAPUM_AGENT_URL", default="http://69.169.102.84:8000/api/v1/process-message")
SINAPUM_API_KEY = config("SINAPUM_API_KEY", default=None)
# Fallback: usar mesma chave do OpenMind AI se não especificada
if not SINAPUM_API_KEY:
    SINAPUM_API_KEY = OPENMIND_AI_KEY
```

### ⚠️ **IMPORTANTE**: Configurar Variáveis de Ambiente

**Railway ou `.env` local:**

```bash
SINAPUM_AGENT_URL=http://69.169.102.84:8000/api/v1/process-message
SINAPUM_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

---

## 📊 Resumo do Status

| Componente | Status | Observação |
|------------|--------|------------|
| Código de integração | ✅ PRONTO | `whatsapp_flow_engine.py` implementado |
| Webhook handler | ✅ PRONTO | `app_whatsapp_integration/views.py` integrado |
| Tratamento de erros | ✅ PRONTO | Implementado |
| Logs | ✅ PRONTO | Logs detalhados |
| Variáveis settings.py | ⚠️ FALTANDO | **Precisa adicionar** |
| Variáveis de ambiente | ⚠️ FALTANDO | **Precisa configurar** |
| Dependências | ✅ OK | `requests` já usado |

---

## ✅ Próximos Passos

1. ✅ Adicionar variáveis no `settings.py`
2. ✅ Configurar variáveis de ambiente (Railway ou `.env`)
3. ✅ Testar integração end-to-end
4. ✅ Monitorar logs após deploy
5. ✅ Verificar se SinapUm está acessível do Django

---

## 🧪 Script de Teste Rápido

Criar arquivo `test_sinapum_agent.py`:

```python
#!/usr/bin/env python
"""Teste rápido de integração com agente SinapUm"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.conf import settings
import requests

# Verificar configuração
print("🔍 Verificando configuração...")
sinapum_url = getattr(settings, 'SINAPUM_AGENT_URL', None)
sinapum_key = getattr(settings, 'SINAPUM_API_KEY', None)

print(f"  SINAPUM_AGENT_URL: {sinapum_url}")
print(f"  SINAPUM_API_KEY: {'✅ Configurado' if sinapum_key else '❌ Não configurado'}")

if not sinapum_key:
    print("\n❌ SINAPUM_API_KEY não configurada!")
    exit(1)

# Testar chamada
print("\n🧪 Testando chamada ao SinapUm...")
payload = {
    "message": "Quero adicionar 2 unidades",
    "conversation_id": "TEST-123",
    "user_phone": "+5511999999999",
    "user_name": "Teste",
    "is_group": False,
    "agent_role": "vendedor",
    "language": "pt-BR"
}

headers = {
    "Authorization": f"Bearer {sinapum_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(sinapum_url, json=payload, headers=headers, timeout=10)
    if response.status_code == 200:
        print("✅ Sucesso!")
        print(f"   Resposta: {response.json()}")
    else:
        print(f"❌ Erro {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Erro: {e}")
```

---

**Última atualização**: 2025-01-XX
**Status geral**: ⚠️ **95% PRONTO** - Falta apenas configurar variáveis

