# 📱 Módulo de Integração WhatsApp - Évora/VitrineZap

Módulo completo de integração com WhatsApp utilizando **apenas Python**, sem Node.js, com foco nos conceitos de **DropKeeper** e **KMN (Keeper Mesh Network)**.

## 🎯 Visão Geral

Este módulo adiciona capacidades de WhatsApp ao projeto Évora/VitrineZap de forma **incremental e modular**, sem quebrar nenhuma funcionalidade existente.

### Componentes

1. **`vz_whatsapp_gateway/`** - Microserviço FastAPI que atua como gateway intermediário
2. **`whatsapp_integration/`** - App Django que processa mensagens e gerencia contatos

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Provedor WhatsApp                          │
│          (Z-API, Evolution API, UltraMsg, etc.)              │
└───────────────────────┬─────────────────────────────────────┘
                        │ Webhook HTTP
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              VZ WhatsApp Gateway (FastAPI)                  │
│              Porta: 8001 (ou configurável)                   │
│  - Recebe webhooks do provedor                                │
│  - Normaliza payloads                                        │
│  - Comunica com Django                                       │
│  - Envia respostas via provedor                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP POST
                        ↓
┌─────────────────────────────────────────────────────────────┐
│          Backend Django Évora/VitrineZap                     │
│              Porta: 8000                                     │
│  - Recebe mensagens do gateway                               │
│  - Identifica contatos (Keeper/Shopper/Cliente)              │
│  - Processa comandos DropKeeper/KMN                        │
│  - Gera respostas automáticas                               │
└───────────────────────┬─────────────────────────────────────┘
                        │ JSON com campo "reply"
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              VZ WhatsApp Gateway                             │
│  - Envia resposta via API do provedor                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    Cliente Final                              │
│              (Recebe no WhatsApp)                             │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estrutura de Arquivos

```
evora/
├── vz_whatsapp_gateway/          # Microserviço FastAPI
│   ├── app/
│   │   ├── main.py               # Aplicação FastAPI
│   │   ├── api.py                # Rotas e endpoints
│   │   ├── services/
│   │   │   └── provider_client.py  # Cliente para provedores
│   │   └── models/
│   ├── requirements.txt
│   └── README.md
│
├── whatsapp_integration/         # App Django
│   ├── models.py                 # WhatsAppContact, WhatsAppMessageLog
│   ├── views.py                  # webhook_from_gateway
│   ├── urls.py                   # Rotas do app
│   ├── admin.py                  # Interface admin
│   └── migrations/
│
├── setup/
│   └── settings.py              # whatsapp_integration adicionado
│
└── WHATSAPP_MODULE_README.md     # Este arquivo
```

## 🚀 Instalação

### 1. Instalar dependências do Gateway

```bash
cd vz_whatsapp_gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` ou configure no Railway:

```bash
# Gateway FastAPI
DJANGO_BACKEND_URL=http://localhost:8000
PROVIDER_BASE_URL=https://api.z-api.io
PROVIDER_API_KEY=sua-chave-api-aqui

# Opcional
ZAPI_INSTANCE_ID=default
EVOLUTION_INSTANCE=default
```

### 3. Aplicar migrações do Django

```bash
python manage.py makemigrations whatsapp_integration
python manage.py migrate
```

### 4. Criar superusuário (se necessário)

```bash
python manage.py createsuperuser
```

## 🏃 Execução

### Desenvolvimento Local

#### Terminal 1: Django
```bash
python manage.py runserver
```

#### Terminal 2: Gateway FastAPI
```bash
cd vz_whatsapp_gateway
uvicorn app.main:app --reload --port 8001
```

### Produção (Railway)

O gateway pode ser deployado como:
1. **Serviço separado** (recomendado) - Novo serviço no Railway
2. **Mesmo serviço** - Rodando junto com Django (usando script de inicialização)

## 🔄 Fluxo de Mensagem Completo

### 1. Cliente envia mensagem no WhatsApp
```
Cliente: "Olá, quero comprar algo"
```

### 2. Provedor recebe e envia webhook
```json
POST https://seu-gateway.up.railway.app/webhook/whatsapp
{
  "from": "5511999999999",
  "message": "Olá, quero comprar algo",
  "messageId": "123456",
  "timestamp": 1234567890
}
```

### 3. Gateway processa e envia para Django
```json
POST http://localhost:8000/api/whatsapp/webhook-from-gateway/
{
  "from": "5511999999999",
  "message": "Olá, quero comprar algo",
  "message_id": "123456",
  "timestamp": 1234567890,
  "type": "text"
}
```

### 4. Django processa e retorna resposta
```json
{
  "reply": "Olá! Bem-vindo ao VitrineZap. Como posso ajudar?"
}
```

### 5. Gateway envia resposta via provedor
```json
POST https://api.z-api.io/instances/default/token/{token}/send-text
{
  "phone": "5511999999999",
  "message": "Olá! Bem-vindo ao VitrineZap. Como posso ajudar?"
}
```

### 6. Cliente recebe no WhatsApp
```
VitrineZap: "Olá! Bem-vindo ao VitrineZap. Como posso ajudar?"
```

## 🔌 Configurar Webhook no Provedor

### Z-API
1. Acesse o painel da Z-API
2. Configure webhook: `https://seu-gateway.up.railway.app/webhook/whatsapp`
3. Selecione eventos: "Mensagens recebidas"

### Evolution API
1. Configure webhook via API:
```bash
curl -X POST https://seu-servidor.evolution-api.com/webhook/set \
  -H "apikey: sua-chave" \
  -d '{
    "url": "https://seu-gateway.up.railway.app/webhook/whatsapp",
    "events": ["messages.upsert"]
  }'
```

### UltraMsg
1. Configure webhook no painel
2. URL: `https://seu-gateway.up.railway.app/webhook/whatsapp`

## 🧪 Testando

### 1. Testar endpoint do gateway

```bash
curl -X POST http://localhost:8001/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5511999999999",
    "message": "Olá, teste",
    "messageId": "test-123"
  }'
```

### 2. Testar endpoint do Django diretamente

```bash
curl -X POST http://localhost:8000/api/whatsapp/webhook-from-gateway/ \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5511999999999",
    "message": "Olá, teste",
    "message_id": "test-123"
  }'
```

### 3. Verificar logs

- Gateway: Console do uvicorn
- Django: Console do runserver ou logs do Railway

### 4. Verificar no Admin Django

Acesse `http://localhost:8000/admin/` e verifique:
- **WhatsApp Contacts** - Contatos registrados
- **WhatsApp Message Logs** - Histórico de mensagens

## 📊 Models Criados

### WhatsAppContact
- `phone_number` - Número de telefone (único)
- `user` - Relacionamento opcional com User do Django
- `name` - Nome do contato
- `contact_type` - Tipo: cliente, keeper, shopper, unknown
- `is_active` - Se o contato está ativo
- `metadata` - JSON para dados adicionais

### WhatsAppMessageLog
- `contact` - Contato associado
- `direction` - incoming ou outgoing
- `message_text` - Texto da mensagem
- `provider_message_id` - ID do provedor
- `message_type` - text, image, document, etc.
- `processing_status` - pending, processed, error, ignored
- `auto_reply_sent` - Se resposta automática foi enviada
- `message_timestamp` - Quando a mensagem foi enviada/recebida
- `metadata` - JSON para dados adicionais

## 🔮 Próximos Passos (Integração DropKeeper/KMN)

O módulo está preparado para integração futura com:

### 1. Identificação de Contatos
- Integrar com `app_marketplace.models.Agente` (Keepers)
- Integrar com `app_marketplace.models.PersonalShopper`
- Integrar com `app_marketplace.models.Cliente`

### 2. Processamento de Comandos
- `/comprar` - Consultar catálogo via KMN
- `/status` - Verificar pedidos
- `/keeper` - Escolher keeper para entrega
- `/pagar` - Processar pagamento

### 3. Lógica DropKeeper
- Verificar ofertas disponíveis
- Calcular preços com base em trustlines
- Gerenciar estoque via KMN
- Processar pedidos distribuídos

### 4. Automações Avançadas
- Respostas inteligentes com IA
- Tickets de suporte
- Memórias de conversação
- Notificações proativas

## 🔒 Segurança

- ✅ Validação de payloads
- ✅ Normalização de números de telefone
- ✅ Logs de todas as interações
- ⚠️ **TODO**: Autenticação no webhook (token de verificação)
- ⚠️ **TODO**: Rate limiting
- ⚠️ **TODO**: Validação de origem (IP whitelist)

## 📝 Notas Importantes

1. **Não quebra funcionalidades existentes** - Tudo é incremental
2. **Modular** - Pode ser desabilitado sem afetar o sistema
3. **Extensível** - Fácil adicionar novos provedores
4. **Pronto para produção** - Estrutura preparada para Railway

## 🐛 Troubleshooting

### Gateway não recebe webhooks
- Verifique se a URL está correta no provedor
- Verifique logs do gateway
- Teste com curl manualmente

### Django não recebe do gateway
- Verifique `DJANGO_BACKEND_URL` no gateway
- Verifique se Django está rodando
- Verifique CORS se necessário

### Mensagens não são enviadas
- Verifique `PROVIDER_BASE_URL` e `PROVIDER_API_KEY`
- Verifique logs do provedor
- Teste envio manual via API do provedor

## 📚 Documentação Adicional

- [README do Gateway](vz_whatsapp_gateway/README.md)
- [Documentação Django](https://docs.djangoproject.com/)
- [Documentação FastAPI](https://fastapi.tiangolo.com/)

## 🤝 Contribuindo

Ao adicionar novas funcionalidades:
1. Mantenha compatibilidade com código existente
2. Adicione testes quando possível
3. Documente mudanças
4. Siga o padrão de código do projeto

---

**Évora/VitrineZap** - *Integração WhatsApp com DropKeeper e KMN* ✨

