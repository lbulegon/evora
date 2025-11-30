# 📱 Integração WhatsApp - Évora Connect

## 📋 Visão Geral

Sistema completo de integração com WhatsApp usando Python puro (FastAPI + Django), sem Node.js.

**Arquitetura:**
```
WhatsApp → Provedor (Z-API/Evolution) → Gateway (FastAPI) → Django → Gateway → Provedor → WhatsApp
```

## 🗂️ Estrutura do Projeto

### 1. `app_vz_whatsapp_gateway/` - Microserviço FastAPI
Gateway que recebe webhooks do provedor e comunica com Django.

**Estrutura:**
```
app_vz_whatsapp_gateway/
├── app/
│   ├── main.py              # FastAPI app principal
│   ├── api.py               # Endpoints de webhook
│   ├── services/
│   │   └── provider_client.py  # Cliente do provedor WhatsApp
│   └── models/
│       └── message.py       # Modelos de dados (futuro)
├── requirements.txt
└── README.md
```

### 2. `app_whatsapp_integration/` - App Django
App Django que processa mensagens e gerencia contatos.

**Estrutura:**
```
app_whatsapp_integration/
├── models.py                # WhatsAppContact, WhatsAppMessageLog
├── views.py                 # webhook_from_gateway
├── urls.py                  # Rotas
├── admin.py                 # Interface admin
└── migrations/
```

## 🚀 Setup e Deploy

### Gateway (FastAPI)

1. **Instalar dependências:**
```bash
cd app_vz_whatsapp_gateway
pip install -r requirements.txt
```

2. **Configurar `.env`:**
```env
PROVIDER_BASE_URL=https://api.z-api.io
PROVIDER_API_KEY=sua_chave
DJANGO_BACKEND_URL=https://evora-product.up.railway.app
PORT=8001
```

3. **Executar:**
```bash
python -m app.main
```

### Django

1. **App já está registrado** em `setup/settings.py`:
```python
INSTALLED_APPS = [
    ...
    'app_whatsapp_integration',
]
```

2. **URLs já configuradas** em `setup/urls.py`:
```python
path('', include('app_whatsapp_integration.urls')),
```

3. **Aplicar migrações:**
```bash
python manage.py makemigrations app_whatsapp_integration
python manage.py migrate app_whatsapp_integration
```

## 🔄 Fluxo de Mensagem

1. **WhatsApp → Provedor:** Usuário envia mensagem
2. **Provedor → Gateway:** Webhook POST para `/webhook/whatsapp`
3. **Gateway → Django:** POST para `/api/whatsapp/webhook-from-gateway/`
4. **Django processa:**
   - Cria/busca contato
   - Salva log da mensagem
   - Identifica tipo de usuário (Cliente/Shopper/Keeper)
   - Gera resposta automática
5. **Django → Gateway:** Retorna JSON com `{"reply": "mensagem"}`
6. **Gateway → Provedor:** Envia mensagem via API
7. **Provedor → WhatsApp:** Mensagem entregue

## 📡 Endpoints

### Gateway (FastAPI)
- `POST /webhook/whatsapp` - Recebe webhook do provedor
- `GET /health` - Health check
- `GET /` - Info do serviço

### Django
- `POST /api/whatsapp/webhook-from-gateway/` - Recebe do gateway

## 🔧 Configuração do Provedor

### Z-API
1. Acesse: https://developer.z-api.io
2. Configure webhook: `https://seu-gateway.up.railway.app/webhook/whatsapp`
3. Copie API Key
4. Configure no `.env` do gateway

### Evolution API
1. Configure webhook na Evolution API
2. Use URL do gateway
3. Configure token no `.env`

## 🚂 Deploy no Railway

### Gateway (Serviço Separado)

1. **Criar novo serviço Python no Railway**
2. **Configurar raiz:** `app_vz_whatsapp_gateway/`
3. **Criar `Procfile`:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
4. **Variáveis de ambiente:**
```
PROVIDER_BASE_URL=https://api.z-api.io
PROVIDER_API_KEY=sua_chave
DJANGO_BACKEND_URL=https://evora-product.up.railway.app
PORT=8080
```

### Django (Já Deployado)

O app `app_whatsapp_integration` já está integrado e será deployado junto com o Django.

## 🧪 Testar

### 1. Testar Gateway Localmente

```bash
# Terminal 1: Rodar gateway
cd app_vz_whatsapp_gateway
python -m app.main

# Terminal 2: Simular webhook
curl -X POST http://localhost:8001/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5511999999999",
    "message": "Olá",
    "message_id": "test_123"
  }'
```

### 2. Verificar Logs

- Gateway: Logs no console
- Django: Verificar `WhatsAppMessageLog` no admin

## 📝 Próximos Passos

- [ ] Implementar lógica de DropKeeping/KMN nas respostas
- [ ] Adicionar comandos específicos por tipo de usuário
- [ ] Implementar envio de imagens/documentos
- [ ] Adicionar painel de controle no dashboard
- [ ] Implementar automações avançadas

## 🔗 Documentação Adicional

- Gateway: `app_vz_whatsapp_gateway/README.md`
- Models: `app_whatsapp_integration/models.py`

