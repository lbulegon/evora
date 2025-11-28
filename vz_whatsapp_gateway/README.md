# VZ WhatsApp Gateway

Microserviço FastAPI que atua como gateway intermediário entre provedores de WhatsApp (Z-API, Evolution API, UltraMsg, etc.) e o backend Django Évora/VitrineZap.

## 🎯 Objetivo

Este gateway recebe webhooks dos provedores de WhatsApp, repassa as mensagens para o backend Django, e envia respostas automáticas de volta ao WhatsApp quando o Django fornecer o campo `reply`.

## 🏗️ Arquitetura

```
Provedor WhatsApp (Z-API/Evolution/etc.)
    ↓ (webhook)
VZ WhatsApp Gateway (FastAPI)
    ↓ (HTTP POST)
Backend Django Évora/VitrineZap
    ↓ (JSON com campo "reply")
VZ WhatsApp Gateway
    ↓ (API do provedor)
Provedor WhatsApp → Cliente final
```

## 📁 Estrutura

```
vz_whatsapp_gateway/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação FastAPI principal
│   ├── api.py               # Rotas e endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── provider_client.py  # Cliente para provedores WhatsApp
│   └── models/
│       └── __init__.py
├── requirements.txt
└── README.md
```

## 🚀 Instalação

```bash
cd vz_whatsapp_gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Configuração

Configure as variáveis de ambiente:

```bash
# URL do backend Django
DJANGO_BACKEND_URL=http://localhost:8000

# Configurações do provedor WhatsApp
PROVIDER_BASE_URL=https://api.z-api.io
PROVIDER_API_KEY=sua-chave-api-aqui

# Opcional: ID da instância (depende do provedor)
ZAPI_INSTANCE_ID=default
EVOLUTION_INSTANCE=default
```

## 🏃 Execução

### Desenvolvimento

```bash
uvicorn app.main:app --reload --port 8001
```

### Produção (Railway)

O gateway pode ser deployado como um serviço separado no Railway, ou pode rodar na mesma instância do Django usando um processo separado.

## 📡 Endpoints

### `GET /`
Health check simples

### `GET /health`
Health check detalhado com status das configurações

### `POST /webhook/whatsapp`
Endpoint que recebe webhooks do provedor de WhatsApp

**Payload esperado (exemplo Z-API):**
```json
{
  "from": "5511999999999",
  "message": "Olá, quero comprar algo",
  "messageId": "123456",
  "timestamp": 1234567890,
  "type": "text"
}
```

**Resposta:**
```json
{
  "status": "ok",
  "message": "Processado com sucesso",
  "reply_sent": true
}
```

## 🔄 Fluxo de Mensagem

1. **Cliente envia mensagem no WhatsApp** → Provedor recebe
2. **Provedor envia webhook** → `POST /webhook/whatsapp`
3. **Gateway normaliza payload** → Extrai `from` e `message`
4. **Gateway envia para Django** → `POST /api/whatsapp/webhook-from-gateway/`
5. **Django processa e retorna** → `{ "reply": "mensagem automática" }`
6. **Gateway envia resposta** → Via API do provedor
7. **Cliente recebe no WhatsApp** ← Provedor entrega

## 🔌 Provedores Suportados

### Z-API
- Base URL: `https://api.z-api.io`
- Endpoint: `/instances/{instance}/token/{token}/send-text`

### Evolution API
- Base URL: `https://seu-servidor.evolution-api.com`
- Endpoint: `/message/sendText/{instance}`
- Header: `apikey: {api_key}`

### UltraMsg
- Base URL: `https://api.ultramsg.com`
- Endpoint: `/api/send`
- Payload: `{ "token": "...", "to": "...", "body": "..." }`

### Genérico
O gateway tenta detectar automaticamente o formato e tenta endpoints comuns.

## 🧪 Testando o Fluxo

### 1. Configurar webhook no provedor

Configure o webhook do seu provedor para apontar para:
```
https://seu-gateway.up.railway.app/webhook/whatsapp
```

### 2. Testar recebimento de webhook

```bash
curl -X POST http://localhost:8001/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5511999999999",
    "message": "Olá, teste",
    "messageId": "test-123"
  }'
```

### 3. Verificar logs

O gateway registra todas as operações:
- 📥 Webhook recebido
- 📤 Envio para Django
- 📥 Resposta do Django
- 📱 Envio de resposta via provedor

## 🚂 Deploy no Railway

### Opção 1: Serviço Separado (Recomendado)

1. Crie um novo serviço no Railway
2. Configure as variáveis de ambiente
3. Use o `Procfile` ou `nixpacks.toml` para iniciar o FastAPI

**Procfile:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Opção 2: Mesmo Serviço do Django

Você pode rodar ambos no mesmo serviço usando um script de inicialização que inicia Django e FastAPI em processos separados.

## 🔒 Segurança

- Em produção, configure CORS adequadamente
- Use autenticação no webhook (token de verificação)
- Valide payloads antes de processar
- Use HTTPS sempre

## 📝 Próximos Passos

- [ ] Implementar envio de imagens
- [ ] Implementar envio de documentos
- [ ] Adicionar autenticação no webhook
- [ ] Suporte a múltiplas instâncias
- [ ] Rate limiting
- [ ] Retry logic para falhas
- [ ] Métricas e monitoramento

## 🤝 Integração com Django

O gateway se comunica com o Django através do endpoint:
```
POST /api/whatsapp/webhook-from-gateway/
```

Payload enviado:
```json
{
  "from": "5511999999999",
  "message": "texto da mensagem",
  "message_id": "123",
  "timestamp": 1234567890,
  "type": "text"
}
```

Resposta esperada:
```json
{
  "reply": "Mensagem de resposta automática"
}
```

Se não houver campo `reply`, nenhuma mensagem é enviada de volta.

