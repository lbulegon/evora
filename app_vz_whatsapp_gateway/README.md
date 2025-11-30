# Évora WhatsApp Gateway

Microserviço de gateway para integração com WhatsApp via provedores externos (Z-API, Evolution API, UltraMsg, etc.).

## 📋 Descrição

Este microserviço atua como intermediário entre:
- **Provedor de WhatsApp** (Z-API, Evolution API, UltraMsg, etc.)
- **Backend Django** (Évora/VitrineZap)

## 🔄 Fluxo de Comunicação

```
WhatsApp → Provedor → Gateway (FastAPI) → Django → Gateway → Provedor → WhatsApp
```

1. Provedor recebe mensagem do WhatsApp
2. Provedor envia webhook para o Gateway
3. Gateway repassa para o backend Django
4. Django processa e retorna resposta (se houver)
5. Gateway envia resposta via provedor
6. Provedor envia mensagem para WhatsApp

## 🚀 Setup

### 1. Instalar Dependências

```bash
cd vz_whatsapp_gateway
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Criar arquivo `.env`:

```env
# Provedor de WhatsApp
PROVIDER_BASE_URL=https://api.z-api.io
PROVIDER_API_KEY=sua_chave_aqui

# Backend Django
DJANGO_BACKEND_URL=http://localhost:8000

# Porta do Gateway
PORT=8001
```

### 3. Executar

```bash
# Desenvolvimento
python -m app.main

# Ou com uvicorn diretamente
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 📡 Endpoints

### `POST /webhook/whatsapp`
Recebe webhooks do provedor de WhatsApp.

**Payload esperado:**
```json
{
  "from": "5511999999999",
  "message": "Olá!",
  "message_id": "msg_123",
  "timestamp": "2025-11-29T20:00:00Z"
}
```

### `GET /health`
Health check do serviço.

### `GET /`
Informações básicas do serviço.

## 🔧 Configuração do Provedor

### Z-API
1. Acesse o painel da Z-API
2. Configure webhook: `https://seu-gateway.up.railway.app/webhook/whatsapp`
3. Copie a API Key
4. Configure no `.env`:
   ```
   PROVIDER_BASE_URL=https://api.z-api.io
   PROVIDER_API_KEY=sua_chave_zapi
   ```

### Evolution API
1. Configure webhook na Evolution API
2. Configure no `.env`:
   ```
   PROVIDER_BASE_URL=https://sua-evolution-api.com
   PROVIDER_API_KEY=seu_token
   ```

## 🚂 Deploy no Railway

### 1. Criar Novo Serviço no Railway

1. Adicionar novo serviço Python
2. Conectar repositório
3. Configurar variáveis de ambiente

### 2. Configurar Procfile

Criar `Procfile` na raiz do projeto:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3. Variáveis de Ambiente no Railway

```
PROVIDER_BASE_URL=https://api.z-api.io
PROVIDER_API_KEY=sua_chave
DJANGO_BACKEND_URL=https://evora-product.up.railway.app
PORT=8080
```

## 🧪 Testar Fluxo Completo

### 1. Testar Webhook Localmente

```bash
# Terminal 1: Rodar gateway
cd vz_whatsapp_gateway
python -m app.main

# Terminal 2: Simular webhook do provedor
curl -X POST http://localhost:8001/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5511999999999",
    "message": "Teste",
    "message_id": "test_123"
  }'
```

### 2. Verificar Comunicação com Django

O gateway deve:
1. Receber o webhook
2. Enviar para Django em `/api/whatsapp/webhook-from-gateway/`
3. Receber resposta do Django
4. Enviar resposta via provedor (se houver)

## 📝 Próximos Passos

- [ ] Implementar envio de imagens
- [ ] Implementar envio de documentos
- [ ] Adicionar suporte a múltiplos provedores simultaneamente
- [ ] Implementar retry logic
- [ ] Adicionar logging estruturado
- [ ] Implementar rate limiting

## 🔗 Integração com Django

O Django deve ter o endpoint:
- `POST /api/whatsapp/webhook-from-gateway/`

Que recebe:
```json
{
  "from": "5511999999999",
  "message": "Texto da mensagem",
  "message_id": "msg_123"
}
```

E retorna:
```json
{
  "reply": "Resposta automática"  // Opcional
}
```
