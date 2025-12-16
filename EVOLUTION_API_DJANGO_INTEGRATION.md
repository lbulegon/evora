# Integração Evolution API via Django (Porta 5000)

## 🎯 Arquitetura

Seguindo a mesma lógica do OpenMind, toda comunicação com Evolution API passa pelo Django (porta 5000), centralizando todas as informações no PostgreSQL do Django.

```
WhatsApp → Evolution API (8004) → Django (5000) → PostgreSQL
                                    ↓
                              Centralização de Dados
```

## 📊 Modelos Criados

### 1. EvolutionInstance
Armazena informações sobre instâncias do WhatsApp:
- `name` - Nome da instância
- `status` - Status (open, close, connecting, etc)
- `phone_number` - Número conectado
- `qrcode` - QR Code para conectar
- `is_active` - Se está ativa
- `is_default` - Se é a instância padrão
- `metadata` - Metadados da Evolution API

### 2. EvolutionMessage
Armazena todas as mensagens no PostgreSQL:
- `instance` - Instância que enviou/recebeu
- `contact` - Contato relacionado
- `evolution_message_id` - ID da Evolution API
- `phone` - Número de telefone
- `direction` - Recebida ou Enviada
- `message_type` - Tipo (text, image, video, etc)
- `content` - Conteúdo da mensagem
- `status` - Status (sent, delivered, read, error)
- `raw_payload` - Payload completo da Evolution API

### 3. WhatsAppContact (já existia)
Contatos WhatsApp vinculados a usuários.

### 4. WhatsAppMessageLog (já existia)
Logs de mensagens (mantido para compatibilidade).

## 🔌 Serviço Evolution API

### Classe: `EvolutionAPIService`

Localização: `app_whatsapp_integration/evolution_service.py`

**Métodos:**
- `get_instance_status()` - Sincroniza status com banco Django
- `send_text_message()` - Envia mensagem e salva no banco
- `send_image()` - Envia imagem
- `send_product_message()` - Envia produto formatado
- `create_instance()` - Cria instância
- `get_qrcode()` - Obtém QR Code

**Características:**
- ✅ Todas as operações salvam no PostgreSQL do Django
- ✅ Sincroniza status das instâncias automaticamente
- ✅ Armazena mensagens enviadas e recebidas
- ✅ Mantém histórico completo

## 🌐 Endpoints Criados

### 1. Webhook Evolution API
```
POST /api/whatsapp/webhook/evolution/
```
Recebe webhooks da Evolution API e salva no banco Django.

### 2. Enviar Mensagem
```
POST /api/whatsapp/send/
Body: {
    "phone": "+5511999999999",
    "message": "Texto da mensagem",
    "instance_name": "default"  // opcional
}
```
Envia mensagem via Evolution API e salva no banco.

### 3. Status da Instância
```
GET /api/whatsapp/status/
GET /api/whatsapp/status/?instance=default
```
Retorna status sincronizado do banco Django.

## 📝 Configurações

### Settings (`setup/settings.py`)

```python
# Evolution API - WhatsApp Integration
EVOLUTION_API_URL = config("EVOLUTION_API_URL", default="http://69.169.102.84:8004")
EVOLUTION_API_KEY = config("EVOLUTION_API_KEY", default="GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg")
EVOLUTION_INSTANCE_NAME = config("EVOLUTION_INSTANCE_NAME", default="default")
```

## 🗄️ Banco de Dados

Todas as informações são armazenadas no **PostgreSQL do Django**:

- ✅ Instâncias Evolution API
- ✅ Todas as mensagens (enviadas e recebidas)
- ✅ Contatos WhatsApp
- ✅ Status e metadados
- ✅ Histórico completo

## 🔧 Admin Django

Interface administrativa para:
- Gerenciar instâncias Evolution API
- Ver todas as mensagens
- Sincronizar status com Evolution API
- Gerenciar contatos

## 📋 Próximos Passos

1. **Criar Migration:**
   ```bash
   python manage.py makemigrations app_whatsapp_integration --name add_evolution_models
   python manage.py migrate app_whatsapp_integration
   ```

2. **Configurar Webhook na Evolution API:**
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

3. **Testar Integração:**
   - Verificar status: `GET /api/whatsapp/status/`
   - Enviar mensagem: `POST /api/whatsapp/send/`
   - Verificar no admin Django

## ✅ Vantagens da Arquitetura

1. **Centralização:** Todos os dados no PostgreSQL do Django
2. **Consistência:** Mesma lógica do OpenMind
3. **Consultas:** Fácil fazer queries e relatórios
4. **Histórico:** Todas as mensagens armazenadas
5. **Integração:** Fácil integrar com outros módulos do Django
6. **Admin:** Interface administrativa completa

## 🔐 Segurança

- API Key configurada no settings
- Validação de payloads
- Logs de todas as operações
- Transações atômicas para consistência

