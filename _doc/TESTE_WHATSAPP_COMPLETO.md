# 🧪 Guia Completo de Teste - Integração WhatsApp ÉVORA

## ✅ Dados de Teste Criados

### 👥 Usuários de Teste
- **Shopper**: `shopper_teste` / `123456`
- **Keeper**: `keeper_teste` / `123456`  
- **Cliente**: `cliente_teste` / `123456`

### 📱 Dados WhatsApp
- **Grupo Shopper**: "Compras Orlando - Maria" (2 participantes)
- **Grupo Keeper**: "Keeper Orlando - João"
- **Mensagens**: 2 mensagens de teste
- **Produtos**: 2 produtos (VS Body Splash + Nike Air Max)
- **Pedidos**: 2 pedidos (1 pendente + 1 pago)

---

## 🚀 Como Testar

### 1️⃣ **Teste do Admin Django**

#### Acessar Admin
```
URL: http://localhost:8000/admin/
Login: shopper_teste
Senha: 123456
```

#### Verificar Isolamento de Dados
1. **Grupos WhatsApp** → Deve ver apenas 1 grupo
2. **Participantes WhatsApp** → Deve ver 2 participantes
3. **Produtos WhatsApp** → Deve ver 2 produtos
4. **Pedidos WhatsApp** → Deve ver 2 pedidos
5. **Mensagens WhatsApp** → Deve ver 2 mensagens

#### Testar Keeper (Isolamento)
```
Login: keeper_teste / 123456
```
- Deve ver apenas 1 grupo (diferente do shopper)
- Não deve ver dados do shopper

### 2️⃣ **Teste do Dashboard WhatsApp**

#### Acessar Dashboard
```
URL: http://localhost:8000/whatsapp/dashboard/
Login: shopper_teste / 123456
```

#### Verificar Funcionalidades
- ✅ **Estatísticas**: Grupos, participantes, pedidos, receita
- ✅ **Grupos Recentes**: Lista dos grupos
- ✅ **Pedidos Recentes**: Lista dos pedidos
- ✅ **Produtos Populares**: Produtos mais vendidos

### 3️⃣ **Teste de Navegação**

#### Lista de Grupos
```
URL: http://localhost:8000/whatsapp/groups/
```
- ✅ Ver lista de grupos
- ✅ Filtros funcionando
- ✅ Paginação funcionando

#### Detalhes do Grupo
```
URL: http://localhost:8000/whatsapp/groups/1/
```
- ✅ Estatísticas do grupo
- ✅ Lista de participantes
- ✅ Mensagens recentes
- ✅ Produtos do grupo
- ✅ Pedidos do grupo

#### Produtos do Grupo
```
URL: http://localhost:8000/whatsapp/groups/1/products/
```
- ✅ Lista de produtos
- ✅ Filtros por categoria
- ✅ Busca funcionando

#### Pedidos do Grupo
```
URL: http://localhost:8000/whatsapp/groups/1/orders/
```
- ✅ Lista de pedidos
- ✅ Filtros por status
- ✅ Busca funcionando

### 4️⃣ **Teste de APIs**

#### Criar Novo Grupo
```bash
curl -X POST http://localhost:8000/api/whatsapp/groups/create/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: SEU_CSRF_TOKEN" \
  -d '{
    "name": "Grupo Teste API",
    "chat_id": "120363123456789999@g.us"
  }'
```

#### Atualizar Grupo
```bash
curl -X POST http://localhost:8000/api/whatsapp/groups/1/update/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: SEU_CSRF_TOKEN" \
  -d '{
    "name": "Nome Atualizado",
    "active": true
  }'
```

#### Adicionar Participante
```bash
curl -X POST http://localhost:8000/api/whatsapp/groups/1/participants/add/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: SEU_CSRF_TOKEN" \
  -d '{
    "phone": "+5511777777777",
    "name": "João Teste"
  }'
```

#### Criar Produto
```bash
curl -X POST http://localhost:8000/api/whatsapp/groups/1/products/create/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: SEU_CSRF_TOKEN" \
  -d '{
    "name": "Produto Teste API",
    "price": "29.99",
    "currency": "USD",
    "brand": "Marca Teste"
  }'
```

#### Atualizar Status do Pedido
```bash
curl -X POST http://localhost:8000/api/whatsapp/orders/1/update-status/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: SEU_CSRF_TOKEN" \
  -d '{
    "status": "paid"
  }'
```

#### Enviar Mensagem para Grupo
```bash
curl -X POST http://localhost:8000/api/whatsapp/groups/1/send-message/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: SEU_CSRF_TOKEN" \
  -d '{
    "message": "Mensagem de teste via API!"
  }'
```

### 5️⃣ **Teste de Isolamento**

#### Verificar que cada usuário vê apenas seus dados:

**Como Shopper:**
```python
# No Django shell
from django.contrib.auth.models import User
from app_marketplace.models import WhatsappGroup

shopper = User.objects.get(username='shopper_teste')
groups = WhatsappGroup.objects.filter(owner=shopper)
print(f"Grupos do Shopper: {groups.count()}")  # Deve ser 1
```

**Como Keeper:**
```python
keeper = User.objects.get(username='keeper_teste')
groups = WhatsappGroup.objects.filter(owner=keeper)
print(f"Grupos do Keeper: {groups.count()}")  # Deve ser 1
```

### 6️⃣ **Teste de Integração WhatsApp Real**

#### Configurar WPPConnect (Railway)
1. **Adicionar serviço WPPConnect** no Railway
2. **Configurar variáveis**:
   ```bash
   BASE_URL=https://seu-wppconnect.up.railway.app
   HOST=0.0.0.0
   PORT=21465
   WEBHOOK_URL=https://seu-django.up.railway.app/webhooks/whatsapp/
   WEBHOOK_BY_EVENTS=true
   WEBHOOK_ALLOWED_EVENTS=onmessage,onstatechange
   ```

#### Conectar WhatsApp
1. **Acessar QR Code**: `https://seu-wppconnect.up.railway.app/api/session-evora/qrcode`
2. **Escanear com WhatsApp**: Dispositivos conectados → Conectar dispositivo
3. **Verificar conexão**: `https://seu-wppconnect.up.railway.app/api/session-evora/check-connection-session`

#### Testar Mensagens
1. **Enviar mensagem** para o grupo no WhatsApp
2. **Verificar webhook**: Deve aparecer nos logs do Django
3. **Verificar dashboard**: Mensagem deve aparecer no dashboard

---

## 🔍 Checklist de Teste

### ✅ **Funcionalidades Básicas**
- [ ] Login com diferentes usuários
- [ ] Isolamento de dados funcionando
- [ ] Dashboard carregando corretamente
- [ ] Navegação entre páginas
- [ ] Filtros e buscas funcionando

### ✅ **APIs**
- [ ] Criar grupo via API
- [ ] Atualizar grupo via API
- [ ] Adicionar participante via API
- [ ] Criar produto via API
- [ ] Atualizar status do pedido via API
- [ ] Enviar mensagem via API

### ✅ **Integração WhatsApp**
- [ ] WPPConnect configurado
- [ ] QR Code escaneado
- [ ] WhatsApp conectado
- [ ] Webhook recebendo mensagens
- [ ] Mensagens aparecendo no dashboard

### ✅ **Isolamento de Dados**
- [ ] Shopper vê apenas seus dados
- [ ] Keeper vê apenas seus dados
- [ ] Impossível acessar dados de outros usuários
- [ ] Admin filtra corretamente por usuário

---

## 🐛 Troubleshooting

### **Erro 403 - Acesso Restrito**
- Verificar se está logado
- Verificar se é shopper ou keeper

### **Erro 404 - Grupo não encontrado**
- Verificar se o grupo pertence ao usuário
- Verificar se o grupo existe

### **Erro 500 - Erro interno**
- Verificar logs do Django
- Verificar se as migrações foram aplicadas

### **WhatsApp não conecta**
- Verificar se WPPConnect está rodando
- Verificar configurações do webhook
- Verificar logs do WPPConnect

---

## 📊 Resultados Esperados

### **Dashboard Shopper**
- 1 grupo ativo
- 2 participantes
- 2 produtos
- 2 pedidos
- Receita total: $137.98

### **Dashboard Keeper**
- 1 grupo ativo
- 0 participantes (grupo vazio)
- 0 produtos
- 0 pedidos

### **Isolamento**
- Cada usuário vê apenas seus dados
- Impossível acessar dados de outros usuários
- Filtros automáticos por usuário

---

## 🎉 Conclusão

Se todos os testes passarem, a integração WhatsApp está **100% funcional** com:

- ✅ **Isolamento total** de dados por usuário
- ✅ **Dashboard completo** para gerenciamento
- ✅ **APIs funcionais** para integração
- ✅ **Segurança garantida** entre usuários
- ✅ **Escalabilidade** para milhares de usuários

**ÉVORA Connect** está pronto para produção! 🚀
