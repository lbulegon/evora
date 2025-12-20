# Agente Ágnosto - SinapUm Server

## 📍 Localização

O agente ágnosto foi criado no servidor **SinapUm** (openmind-ai-server) para processar mensagens do WhatsApp de forma independente e configurável.

## 🏗️ Estrutura Criada

### 1. Core do Agente (`openmind-ai-server/app/core/agnostic_agent.py`)

- **`AgnosticAgent`**: Classe base abstrata para todos os agentes
- **`VendedorAgent`**: Implementação do agente vendedor (IA-Vendedor)
- **`AgentFactory`**: Factory para criar agentes baseado em configuração
- **`AgentContext`**: Contexto da conversa (telefone, grupo, oferta, etc.)
- **`AgentResponse`**: Resposta padronizada do agente

### 2. Endpoint API (`openmind-ai-server/app/api/v1/endpoints/agent.py`)

- **`POST /api/v1/process-message`**: Processa mensagem do WhatsApp
- **`GET /api/v1/agent/capabilities`**: Lista capacidades do agente
- **`GET /api/v1/agent/roles`**: Lista papéis disponíveis

### 3. Integração Django (`app_marketplace/whatsapp_flow_engine.py`)

- **`WhatsAppFlowEngine._processar_com_agente_sinapum()`**: Chama agente SinapUm via HTTP
- **Sem fallback local**: Se SinapUm não disponível, retorna erro apropriado
- **Configuração**: Via `SINAPUM_AGENT_URL` e `SINAPUM_API_KEY`
- **`IAVendedorAgent`**: DEPRECATED - mantido apenas para compatibilidade

## 🔄 Fluxo de Integração

**IMPORTANTE: Toda a lógica de IA está no SinapUm. Django apenas faz chamadas HTTP.**

```
WhatsApp → Evolution API → Django Webhook
                              ↓
                    WhatsAppFlowEngine
                              ↓
                    HTTP POST → Agente Ágnosto SinapUm
                              ↓
                    [Processa com IA] → Resposta
                              ↓
                    Django recebe resposta
                              ↓
                    Resposta ao Cliente via Evolution API
```

**NÃO há processamento local no Django. Se SinapUm não estiver disponível, retorna erro apropriado.**

## 🚀 Como Usar

### 1. Configurar Variáveis de Ambiente (Django)

```python
# settings.py
SINAPUM_AGENT_URL = "http://69.169.102.84:8000/api/v1/process-message"
SINAPUM_API_KEY = "sua-chave-api-aqui"
```

### 2. Chamar Agente do SinapUm

```python
# Exemplo de request
POST http://69.169.102.84:8000/api/v1/process-message
Authorization: Bearer sua-chave-api
Content-Type: application/json

{
    "message": "Quero adicionar 2 unidades",
    "conversation_id": "PRIV-5511999999999-1234567890",
    "user_phone": "+5511999999999",
    "user_name": "João",
    "is_group": false,
    "offer_id": "OFT-12345",
    "language": "pt-BR",
    "agent_role": "vendedor"
}
```

### 3. Resposta do Agente

```json
{
    "success": true,
    "message": "Perfeito! Anotei 2 unidades no seu pedido. ✅\n\nQuer adicionar mais alguma coisa?",
    "action": "add_to_cart",
    "data": {
        "quantity": 2
    },
    "should_continue": true,
    "agent_role": "vendedor",
    "capabilities": ["add_to_cart", "ask_price", "ask_delivery", ...]
}
```

## 🎯 Características do Agente Ágnosto

### ✅ Ágnosto
- Não depende de implementação específica
- Configurável via parâmetros
- Extensível com novos comportamentos

### ✅ Configurável
- **Papel**: vendedor, atendente, assistente, analista
- **Idioma**: pt-BR, en-US, es-ES, etc.
- **Estilo**: natural, formal, casual
- **Nível de sugestão**: careful, moderate, aggressive

### ✅ Integrado
- Funciona com Django Évora
- Integra com Evolution API
- Suporta múltiplos idiomas
- Respeita princípios fundadores

## 📋 Capacidades do Agente Vendedor

1. **Adicionar ao carrinho** (`add_to_cart`)
2. **Perguntar preço** (`ask_price`)
3. **Perguntar entrega** (`ask_delivery`)
4. **Finalizar pedido** (`finalize_order`)
5. **Definir quantidade** (`set_quantity`)
6. **Conversa geral** (`general_conversation`)

## 🔧 Próximos Passos

1. ✅ Agente ágnosto criado no SinapUm
2. ✅ Endpoint API criado
3. ✅ Integração Django implementada
4. ⏳ Testar integração completa
5. ⏳ Adicionar mais tipos de agentes (atendente, analista)
6. ⏳ Melhorar detecção de intenções com NLP
7. ⏳ Adicionar memória de conversa

## 📝 Notas Importantes

- ✅ **Toda a lógica de IA está no servidor SinapUm** (69.169.102.84:8000)
- ✅ Django **apenas faz chamadas HTTP** ao SinapUm - não processa mensagens localmente
- ✅ Se SinapUm não estiver disponível, Django retorna erro apropriado (sem fallback local)
- ✅ Agente respeita todos os princípios fundadores do Évora/VitrineZap
- ⚠️ **NÃO há processamento local de IA no Django** - tudo roda no SinapUm

