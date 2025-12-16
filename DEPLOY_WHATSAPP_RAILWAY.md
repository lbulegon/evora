# Deploy Integração WhatsApp - Railway

## 📋 Informações Importantes

**O projeto `/evora` roda no Railway, não no servidor SinapUm.**

- **Servidor SinapUm (porta 5000)**: MCP_SinapUm - Análise de imagens
- **Railway (Évora)**: Projeto Django - Marketplace e WhatsApp Integration

## 🔧 O que foi implementado

### 1. Modelos Django (PostgreSQL no Railway)

- `EvolutionInstance` - Instâncias do WhatsApp
- `EvolutionMessage` - Todas as mensagens (centralizadas no PostgreSQL)
- `WhatsAppContact` - Contatos WhatsApp
- `WhatsAppMessageLog` - Logs de mensagens

### 2. Serviço Evolution API

**Arquivo:** `app_whatsapp_integration/evolution_service.py`

- Comunicação com Evolution API (http://69.169.102.84:8004)
- Todas as operações salvam no PostgreSQL do Railway
- Sincronização automática de status

### 3. Endpoints Django

- `POST /api/whatsapp/webhook/evolution/` - Recebe webhooks
- `POST /api/whatsapp/send/` - Envia mensagens
- `GET /api/whatsapp/status/` - Status das instâncias

### 4. Configurações

**Settings (`setup/settings.py`):**
```python
EVOLUTION_API_URL = config("EVOLUTION_API_URL", default="http://69.169.102.84:8004")
EVOLUTION_API_KEY = config("EVOLUTION_API_KEY", default="GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg")
EVOLUTION_INSTANCE_NAME = config("EVOLUTION_INSTANCE_NAME", default="default")
```

## 🚀 Deploy no Railway

### 1. Variáveis de Ambiente

Adicionar no Railway:
```env
EVOLUTION_API_URL=http://69.169.102.84:8004
EVOLUTION_API_KEY=GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg
EVOLUTION_INSTANCE_NAME=default
```

### 2. Aplicar Migrations

No Railway, as migrations serão aplicadas automaticamente no deploy, ou você pode executar:

```bash
python manage.py migrate app_whatsapp_integration
```

### 3. Configurar Webhook na Evolution API

Após o deploy no Railway, configurar o webhook:

```bash
curl -X POST "http://69.169.102.84:8004/webhook/set/default" \
  -H "apikey: GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://evora-product.up.railway.app/api/whatsapp/webhook/evolution/",
    "webhook_by_events": true,
    "events": ["MESSAGES_UPSERT", "MESSAGES_UPDATE"]
  }'
```

## 📊 Arquitetura

```
WhatsApp → Evolution API (8004) → Django Railway → PostgreSQL Railway
                                    ↓
                          Centralização de Dados
```

## ✅ Checklist de Deploy

- [x] Modelos criados
- [x] Serviço Evolution API implementado
- [x] Views e endpoints criados
- [x] Admin configurado
- [x] Settings atualizado
- [x] URLs configuradas
- [ ] Deploy no Railway
- [ ] Aplicar migrations no Railway
- [ ] Configurar variáveis de ambiente no Railway
- [ ] Configurar webhook na Evolution API
- [ ] Testar integração

## 🔍 Verificação

Após deploy no Railway:

1. Verificar status: `GET https://evora-product.up.railway.app/api/whatsapp/status/`
2. Testar envio: `POST https://evora-product.up.railway.app/api/whatsapp/send/`
3. Verificar admin: `https://evora-product.up.railway.app/admin/`

## 📝 Notas

- Todas as mensagens são armazenadas no PostgreSQL do Railway
- O Django atua como gateway centralizado
- Mesma lógica do OpenMind (centralização de dados)
- Admin Django para gerenciar instâncias e mensagens

