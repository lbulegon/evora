# 📱 Integração WhatsApp - ÉVORA Connect

## 🎯 Visão Geral

A integração WhatsApp permite que **shoppers**, **keepers** e **clientes** usem o WhatsApp normalmente para fazer compras em Orlando, gerenciar produtos e coordenar entregas - **sem precisar instalar nenhum app**.

### Como Funciona

```
┌─────────────────┐
│  Grupo WhatsApp │ ←── Shoppers, Keepers, Clientes conversam normalmente
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Bot ÉVORA     │ ←── Lê mensagens e entende comandos
│  (WPPConnect)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Django ÉVORA   │ ←── Processa, cria pedidos, gerencia pagamentos
└─────────────────┘
```

---

## 🚀 Fluxo Completo (Zero Instalação)

### 1️⃣ Cadastro de Shopper (via WhatsApp)

1. **Admin** cria token no painel ÉVORA → gera `SHOP-ABC123`
2. **Shopper** manda mensagem **privada** para o bot:
   ```
   /sou_shopper SHOP-ABC123
   ```
3. Bot responde pedindo dados:
   ```
   ✅ Token válido! Vamos completar seu cadastro:
   
   Por favor, envie seu nome completo:
   ```
4. Shopper responde:
   ```
   Maria Silva
   ```
5. Bot continua:
   ```
   Perfeito! Agora, qual sua chave PIX para receber repasses?
   ```
6. Shopper responde:
   ```
   maria.silva@email.com
   ```
7. Bot finaliza:
   ```
   🎉 Cadastro completo!
   
   Agora você pode:
   - Criar grupo com seus clientes
   - Adicionar este número ao grupo
   - Usar /vincular para conectar o grupo
   ```

### 2️⃣ Vinculação do Grupo WhatsApp

1. **Shopper** cria grupo no WhatsApp (ex: "Compras Orlando - Maria")
2. Adiciona clientes ao grupo
3. Adiciona o número do bot ÉVORA
4. No painel ÉVORA, clica em "Vincular Grupo" → gera token `VNC-XYZ789`
5. No grupo, manda:
   ```
   /vincular XYZ789
   ```
6. Bot responde no grupo:
   ```
   ✅ Grupo vinculado à conta de @maria.silva
   
   A partir de agora, todos podem usar comandos aqui!
   ```

### 3️⃣ Cadastro de Keeper (via WhatsApp)

Processo similar ao Shopper:

1. Admin cria token: `KEEP-987ZYX`
2. Keeper manda no privado:
   ```
   /sou_keeper KEEP-987ZYX
   ```
3. Bot pede dados:
   - Nome completo
   - Endereço em Orlando
   - Horários de funcionamento
   - Chave PIX
   - Capacidade de armazenamento

---

## 📋 Comandos Disponíveis

### 👥 Cliente (no grupo ou DM)

#### Fazer Pedido
```
/comprar 2x Victoria's Secret Body Splash Love Spell (250ml)
/comprar 1x Nike Air Max 42 branco
```

#### Escolher Forma de Entrega
```
/entrega keeper                    → Retirar pessoalmente no keeper
/entrega keeper-correio CEP 90000-000  → Keeper envia por correio
/entrega comprador-traz            → Shopper traz ao Brasil
```

#### Pagar
```
/pagar pix                → PIX à vista
/pagar cartao 6x          → Cartão em 6 vezes
/pagar boleto             → Boleto
```

#### Acompanhar
```
/status                   → Status do último pedido
/status PED#1234          → Status de pedido específico
/rastrear PED#1234        → Rastreamento
```

#### Agendar Retirada
```
/retirar hoje 16h
/retirar sábado 10h
```

---

### 🛍️ Shopper/Comprador (no grupo)

#### Postar Produto/Oferta
```
#produto
Marca: Victoria's Secret
Nome: Body Splash Love Spell
Var: 250ml
Preço: $7.99
Loja: VS Florida Mall
#ofertar
```

**Ou simplesmente:**
```
Victoria's Secret Body Splash $7.99 - cupom SUDSY hoje!
```
_(O bot detecta automaticamente marca, preço e promoções)_

#### Marcar Compra Realizada
```
/comprado PED#1234 nota=IMG123 valor=$48,32
```

#### Informar Viagem ao Brasil
```
/entrega-br PED#1234 voo=AA922 data=10/11
```

#### Ver Status
```
/status PED#1234
```

---

### 📦 Keeper (no grupo ou DM)

#### Check-in de Pacote
```
/checkin PED#1234 3 volumes
```
_(pode anexar foto)_

#### Alocar em Slot
```
/slot PED#1234 -> A3-14
```

#### Registrar Postagem
```
/mail PED#1234 rastreio=USPS123 custo=$26,80
```

#### Confirmar Entrega/Retirada
```
/entregue PED#1234
```

---

## 🔧 Configuração Técnica

### Requisitos

1. **Railway** (recomendado) ou **VPS**
2. **Número WhatsApp dedicado** (chip pré-pago comum)
3. **Python 3.13+**

### Stack

- **WPPConnect** - Cliente WhatsApp não-oficial
- **Django** - Backend ÉVORA
- **PostgreSQL** - Banco de dados
- **Redis** - Fila de tarefas (Celery)

### Railway (Recomendado)

```bash
# 1. Adicionar serviços no Railway
# - PostgreSQL Database
# - Redis Database  
# - Python Service (Django)

# 2. Configurar variáveis
DATABASE_URL=${{PostgreSQL.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
WPP_BASE=https://seu-wppconnect.up.railway.app

# 3. Deploy automático
git push origin main
```

Ver guia completo: [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md)

### Primeiro Setup (Railway)

```bash
# 1. Deploy no Railway
git push origin main

# 2. Aplicar migrações
railway run python manage.py migrate

# 3. Criar superusuário
railway run python manage.py createsuperuser

# 4. Acessar admin
# https://seu-projeto.up.railway.app/admin/
```

---

## 🔐 Segurança

### Tokens

- **Validade:** 30 minutos por padrão
- **Uso único:** Token expira após uso
- **Verificação de telefone:** Sistema registra quem usou

### Privacidade (LGPD)

- Bot avisa sobre coleta de dados no primeiro contato
- Comando `/sair` para opt-out
- Dados armazenados: telefone, nome, PIX, endereço (keepers)
- Sem acesso a contatos ou conversas privadas

### Limites Anti-Ban

- Máximo de 10 mensagens por minuto (configur

ável)
- Sem envios massivos ou spam
- Apenas grupos onde o bot foi adicionado

---

## 💰 Custos Estimados

| Item | Descrição | Custo/mês |
|------|-----------|-----------|
| Servidor VPS | Railway/Render/Hetzner | ~$10 |
| Chip WhatsApp | Pré-pago dedicado | ~$5 |
| Storage (S3) | Imagens e notas fiscais | ~$1 |
| **TOTAL** | | **~$16/mês** |

_Não há custos com WhatsApp Business API (usamos cliente não-oficial)_

---

## 🧪 Testando Local

```bash
# 1. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar .env
cp environment_variables.example .env
# Editar DATABASE_URL, REDIS_URL, etc.

# 4. Migrar banco
python manage.py migrate

# 5. Criar admin
python manage.py createsuperuser

# 6. Rodar servidor
python manage.py runserver
```

Para integração WhatsApp, use o Railway: [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md)

---

## 📊 Monitoramento

### Logs Importantes

```bash
# Railway - todos os logs
railway logs --tail

# Logs específicos por serviço
railway logs --service django
railway logs --service wppconnect
```

### Métricas no Admin

- **Grupos Ativos** - Dashboard
- **Tokens Gerados** - Administração > Tokens
- **Mensagens Processadas** - Logs
- **Taxa de Conversão** - Pedidos criados vs mensagens

---

## 🆘 Troubleshooting

### Bot não responde no grupo

1. ✅ Verificar se o bot foi adicionado ao grupo
2. ✅ Verificar logs do WPPConnect: `railway logs --tail`
3. ✅ Verificar se o webhook está configurado corretamente
4. ✅ Testar enviar mensagem direta para o bot

### QR Code não aparece

```bash
# Verificar logs do WPPConnect
railway logs --tail

# Reiniciar serviço WPPConnect
railway restart
```

### Grupo não vincula

1. ✅ Token ainda válido? (expira em 30min)
2. ✅ Shopper existe no sistema?
3. ✅ Formato correto: `/vincular TOKEN` (sem SHOP- ou KEEP-)

### Comandos não funcionam

1. ✅ Verificar se começa com `/`
2. ✅ Ver logs do Django para erros de parse
3. ✅ Testar comando mais simples: `/status`

---

## 🔄 Fluxo Completo de Pedido

```
1. Cliente: /comprar 2x VS Body Splash
   ├─> Bot: "Adicionado ao carrinho! Use /entrega e /pagar"

2. Cliente: /entrega keeper
   ├─> Bot: "Entrega definida: retirada no keeper"

3. Cliente: /pagar pix
   ├─> Bot cria pedido PED#20241017001
   ├─> Envia link/QR Code PIX
   └─> "Aguardando pagamento..."

4. Cliente paga PIX
   ├─> Sistema detecta pagamento
   ├─> Muda status → "Pago"
   └─> Bot: "✅ Pagamento confirmado! Seu pedido está em compra."

5. Shopper vê no painel: "Pedido PED#20241017001 - aguardando compra"
   ├─> Vai à loja em Orlando
   ├─> Compra os produtos
   └─> /comprado PED#20241017001 nota=IMG123 valor=$15,98

6. Sistema:
   ├─> Libera repasse para Shopper (custo + comissão)
   ├─> Muda status → "Comprado"
   └─> Notifica Keeper

7. Keeper: /checkin PED#20241017001 2 volumes
   ├─> /slot PED#20241017001 -> A3-14
   └─> Status → "Em guarda"

8a. Se retirada local:
    Cliente: /retirar sábado 10h
    └─> Keeper agenda e confirma
    
8b. Se envio por correio:
    Keeper: /mail PED#20241017001 rastreio=USPS123
    └─> Cliente recebe tracking

9. Keeper: /entregue PED#20241017001
   ├─> Sistema libera repasse para Keeper
   ├─> Status → "Entregue"
   └─> Pedido finalizado ✅
```

---

## 🎨 Personalização

### Adicionar Novas Marcas

Edite `app_marketplace/whatsapp_integration.py`:

```python
BRAND_MAP = {
    "victoria's secret": ["victoria's secret", "vs", "victoria"],
    "sua marca": ["sua marca", "alias1", "alias2"],
    # ...
}
```

### Modificar Mensagens do Bot

Crie `app_marketplace/whatsapp_messages.py`:

```python
MSG_WELCOME = "Bem-vindo ao ÉVORA Connect! 🎉"
MSG_CART_ADDED = "🧺 Item adicionado: {item}"
MSG_ORDER_CREATED = "✅ Pedido {number} criado!"
# ...
```

### Adicionar Novos Comandos

Em `whatsapp_integration.py`, função `parse_intent()`:

```python
if low.startswith("/meucomando"):
    # sua lógica
    return Intent("MEU_COMANDO", {"args": "valores"})
```

---

## 📚 Próximos Passos

1. ✅ **Implementar webhook** - Receber mensagens do WhatsApp
2. ✅ **Criar handlers** - Processar comandos
3. ✅ **Integrar pagamentos** - Stripe/Mercado Pago/PIX
4. ⏳ **Dashboard** - Interface web para shoppers/keepers
5. ⏳ **Notificações** - Alertas importantes via WhatsApp
6. ⏳ **Relatórios** - Analytics de vendas e desempenho

---

## 🤝 Suporte

Para dúvidas ou problemas:

1. Ver logs: `docker-compose logs -f`
2. Verificar admin Django: `http://localhost:8000/admin/`
3. Testar comandos no grupo de testes primeiro

---

**ÉVORA Connect** - *Minimalist, Sophisticated Style*  
*Onde tecnologia encontra humanidade.*









