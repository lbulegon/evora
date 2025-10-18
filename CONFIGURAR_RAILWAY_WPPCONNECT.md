# 🚂 Como Configurar WPPConnect no Railway - Guia Simplificado

## ✅ SIM! Pode ser configurado totalmente no Railway

O Railway suporta Docker perfeitamente. Vou te guiar passo a passo.

---

## 📋 Pré-requisitos

- ✅ Conta no Railway
- ✅ Projeto ÉVORA já vinculado
- ✅ Um chip/número WhatsApp dedicado (pode ser pré-pago comum)

---

## 🚀 Passo a Passo (15 minutos)

### 1️⃣ Adicionar Serviço Redis

1. Abra seu projeto no Railway: https://railway.app/project/3d0f75f4-cab0-4751-ba59-f664bd9c896e
2. Clique em **"+ New"**
3. Selecione **"Database" → "Add Redis"**
4. Pronto! O Railway cria automaticamente e gera a variável `REDIS_URL`

### 2️⃣ Deploy do Django (atualizado)

O Django já está rodando. Precisamos apenas adicionar variáveis:

1. Clique no serviço **Django/Web** (evora-product)
2. Vá em **"Variables"**
3. Adicione estas variáveis:

```bash
# Redis (copie do serviço Redis)
REDIS_URL=${{Redis.REDIS_URL}}

# WhatsApp (preencher depois que criar o serviço WPPConnect)
WPP_BASE=https://seu-wppconnect.up.railway.app
WPP_SESSION=session-evora

# Câmbio (opcional)
USD_BRL=5.0
```

4. Clique em **"Deploy"** (ou aguarde deploy automático)

### 3️⃣ Adicionar Serviço WPPConnect

1. No projeto Railway, clique em **"+ New"**
2. Selecione **"Empty Service"**
3. Dê um nome: `wppconnect`
4. Vá em **"Settings"**

#### A) Configurar Docker Image

1. Em **"Source"**, selecione **"Docker Image"**
2. Cole a imagem:
   ```
   wppconnectteam/wppconnect-server:latest
   ```

#### B) Configurar Port

1. Em **"Networking" → "Port"**
2. Defina: `21465`

#### C) Adicionar Volume (IMPORTANTE!)

⚠️ **Sem volume, o bot perde a sessão a cada restart!**

1. Em **"Settings"**, procure **"Volumes"**
2. Clique em **"+ Add Volume"**
3. Configure:
   - **Mount Path:** `/usr/src/app/userDataDir`
   - **Size:** 1 GB

#### D) Variáveis de Ambiente

Adicione estas variáveis ao serviço WPPConnect:

```bash
# URL base (será preenchida automaticamente após gerar domain)
BASE_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}

# Configurações
HOST=0.0.0.0
PORT=21465

# Webhook (URL do seu Django)
WEBHOOK_URL=https://evora-product.up.railway.app/webhooks/whatsapp/

# Eventos a enviar
WEBHOOK_BY_EVENTS=true
WEBHOOK_ALLOWED_EVENTS=onmessage,onstatechange,onack

# Secret (pode manter este)
SESSION_SECRET_KEY=EVORA_SECRET_2024

# Modo headless
HEADLESS=true
```

#### E) Gerar Domain Público

1. Em **"Settings" → "Networking"**
2. Clique em **"Generate Domain"**
3. Copie o domínio gerado (ex: `wppconnect-production-xxxx.up.railway.app`)
4. Volte em **"Variables"** e atualize:
   ```bash
   BASE_URL=https://wppconnect-production-xxxx.up.railway.app
   ```

#### F) Fazer Deploy

1. Clique em **"Deploy"**
2. Aguarde o serviço subir (1-2 minutos)

### 4️⃣ Conectar WhatsApp (Escanear QR Code)

#### Método 1: Via Navegador (Mais Fácil)

1. Abra no navegador:
   ```
   https://seu-wppconnect.up.railway.app/api/session-evora/qrcode
   ```

2. Você verá uma página com o QR Code

3. Abra WhatsApp no celular:
   - Menu (⋮) → **Dispositivos conectados**
   - **Conectar dispositivo**
   - Escanei o QR Code

4. Aguarde conexão (5-10 segundos)

#### Método 2: Via API/Postman

```bash
# Gerar QR Code (retorna base64)
curl https://seu-wppconnect.up.railway.app/api/session-evora/qr-code

# Verificar status
curl https://seu-wppconnect.up.railway.app/api/session-evora/check-connection-session
```

### 5️⃣ Verificar Integração

#### A) Teste o Webhook

Envie mensagem para o número do bot e veja os logs:

```bash
railway logs -s wppconnect --tail
railway logs -s evora-product --tail
```

Você deve ver a mensagem chegando no Django.

#### B) Teste no Admin

1. Acesse: https://evora-product.up.railway.app/admin/
2. Vá em **"Grupos WhatsApp"**
3. Veja se aparecem registros quando você vincular grupos

---

## 🎯 Resumo da Arquitetura no Railway

```
┌─────────────────────────────────────┐
│        Railway Project               │
├─────────────────────────────────────┤
│                                      │
│  [PostgreSQL]  (já existe)           │
│       ↓                              │
│  [Redis]  (novo - adicionar)         │
│       ↓                              │
│  [Django/Web]  (evora-product)       │
│       ↑                              │
│  [WPPConnect]  (novo - Docker)       │
│     + Volume (1GB)                   │
│                                      │
└─────────────────────────────────────┘
         ↓
    WhatsApp (via QR Code)
```

---

## 💰 Custos no Railway

| Serviço | RAM | Custo/mês |
|---------|-----|-----------|
| PostgreSQL (existente) | 256MB | $5 |
| Redis (novo) | 256MB | $5 |
| Django | 512MB | $5 |
| WPPConnect + Volume | 512MB + 1GB | $7 |
| **TOTAL** | | **$22/mês** |

💡 **Plano Hobby do Railway:** Inclui $5 grátis/mês

---

## 🔧 Troubleshooting

### WPPConnect não sobe

**Verificar:**
- ✅ Image correta: `wppconnectteam/wppconnect-server:latest`
- ✅ Port: `21465`
- ✅ Volume montado em `/usr/src/app/userDataDir`

**Logs:**
```bash
railway logs -s wppconnect
```

### QR Code não aparece

**Solução:**
```bash
# Gerar via API
curl https://seu-wppconnect.railway.app/api/session-evora/qr-code
```

### WhatsApp desconecta

**Causa:** Volume não persistido ou sessão expirada

**Solução:**
1. Verificar se o volume está ativo
2. Reescanear QR Code
3. Verificar logs para mensagens de erro

### Webhook não funciona

**Verificar:**
1. ✅ URL do webhook correta em WPPConnect
2. ✅ Django responde em `/webhooks/whatsapp/`
3. ✅ CSRF desabilitado no endpoint (@csrf_exempt)

**Testar:**
```bash
# Teste manual
curl -X POST https://evora-product.up.railway.app/webhooks/whatsapp/ \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

---

## ✅ Checklist de Configuração

- [ ] Redis adicionado ao projeto
- [ ] Variáveis configuradas no Django (REDIS_URL, WPP_BASE)
- [ ] Serviço WPPConnect criado
- [ ] Docker image configurada
- [ ] Port 21465 configurado
- [ ] Volume 1GB criado e montado
- [ ] Variáveis do WPPConnect configuradas
- [ ] Domain público gerado para WPPConnect
- [ ] QR Code escaneado
- [ ] WhatsApp conectado (check-connection-session)
- [ ] Teste de mensagem enviada
- [ ] Logs verificados (mensagem chegou no webhook)

---

## 📱 Testar Sistema Completo

### 1. Criar Token de Vinculação

```bash
railway run python manage.py shell

# No shell:
from app_marketplace.models import PersonalShopper, GroupLinkRequest
from django.contrib.auth.models import User

# Pegar um shopper existente ou criar
user = User.objects.first()
shopper = PersonalShopper.objects.get(user=user)

# Gerar token
token = GroupLinkRequest.generate_token(shopper)
print(f"Token: {token.token}")
exit()
```

### 2. Vincular Grupo

1. Crie grupo no WhatsApp
2. Adicione o número do bot
3. Envie no grupo:
   ```
   /vincular ABC123
   ```
   (substitua ABC123 pelo token gerado)

4. Bot deve responder:
   ```
   ✅ Grupo vinculado com sucesso!
   ```

### 3. Testar Comandos

```
/comprar 2x Victoria's Secret Body Splash
/entrega keeper
/pagar pix
/status
```

---

## 🎉 Pronto!

Seu ÉVORA Connect está rodando no Railway com WhatsApp totalmente funcional!

### Próximos Passos:

1. ✅ Convidar shoppers e keepers
2. ✅ Gerar tokens de cadastro
3. ✅ Testar fluxo completo de pedido
4. ✅ Configurar pagamentos (Stripe/Mercado Pago)
5. ✅ Criar dashboard web (futuro)

---

## 📞 Suporte Railway

- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

---

**ÉVORA Connect** - *Minimalist, Sophisticated Style* ✨

**Automatização WhatsApp configurada com sucesso no Railway!** 🚀





