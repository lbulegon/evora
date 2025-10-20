# 🚂 Configuração Railway - ÉVORA Connect

## 📋 Pré-requisitos

- Conta no [Railway.app](https://railway.app)
- Railway CLI instalado
- Git instalado

## 🚀 Setup Completo no Railway

### 1️⃣ Preparar Projeto Local

```bash
# Certifique-se de estar na pasta do projeto
cd evora

# Fazer commit de todas as mudanças
git add .
git commit -m "Preparar deploy Railway com WPPConnect"
```

### 2️⃣ Instalar Railway CLI (se ainda não tiver)

```bash
# Windows (PowerShell)
npm i -g @railway/cli

# Ou via Scoop
scoop install railway

# Verificar instalação
railway --version
```

### 3️⃣ Login no Railway

```bash
railway login
```

Isso abrirá o navegador para autenticação.

### 4️⃣ Vincular ao Projeto Existente

```bash
# Usar seu projeto ID
railway link -p 3d0f75f4-cab0-4751-ba59-f664bd9c896e
```

## 🗄️ Configurar Serviços no Railway

### Serviço 1: PostgreSQL (já existe)

✅ Seu projeto já tem PostgreSQL configurado.

**Verificar variável:**
- `DATABASE_URL` → deve estar disponível automaticamente

### Serviço 2: Redis

1. No painel Railway, clique em **"+ New"**
2. Selecione **"Redis"**
3. Railway criará automaticamente
4. Variável `REDIS_URL` estará disponível

### Serviço 3: Django App (este repositório)

1. No painel Railway, clique em **"+ New"**
2. Selecione **"GitHub Repo"** ou **"Empty Service"**
3. Se usar GitHub:
   - Conecte seu repositório `evora`
   - Railway detectará o `Dockerfile` automaticamente
4. Se usar Empty Service:
   - Use `railway up` no terminal para fazer deploy

**Variáveis de Ambiente Necessárias:**

```bash
# No painel Railway, adicione estas variáveis ao serviço Django:

DATABASE_URL=${DATABASE_URL}  # Referência do serviço PostgreSQL
REDIS_URL=${REDIS_URL}        # Referência do serviço Redis
DJANGO_SECRET_KEY=sua-chave-super-secreta-aqui-mude-isso
ALLOWED_HOSTS=*
DJANGO_DEBUG=0
OPENAI_API_KEY=sua-chave-openai (se usar)
```

**Comandos de Deploy:**

Railway executará automaticamente:
```bash
python manage.py migrate
gunicorn setup.wsgi:application --bind 0.0.0.0:$PORT
```

### Serviço 4: WPPConnect (WhatsApp Bot)

**⚠️ IMPORTANTE:** O WPPConnect precisa de volume persistente para manter a sessão do WhatsApp.

#### Opção A: Usar Railway Volume (Recomendado)

1. No painel Railway, clique em **"+ New"**
2. Selecione **"Empty Service"**
3. Vá em **Settings** → **Deploy**
4. Configure:
   - **Docker Image:** `wppconnectteam/wppconnect-server:latest`
   - **Port:** `21465`

5. Adicione **Volume**:
   - Clique em **"+ Add Volume"**
   - Mount Path: `/usr/src/app/userDataDir`
   - Size: 1GB

6. **Variáveis de Ambiente:**

```bash
BASE_URL=https://seu-wppconnect.railway.app
HOST=0.0.0.0
PORT=21465
WEBHOOK_URL=https://seu-django.railway.app/webhooks/whatsapp/
WEBHOOK_BY_EVENTS=true
WEBHOOK_ALLOWED_EVENTS=onmessage,onstatechange,onack
SESSION_SECRET_KEY=EVORA_SECRET_KEY_2024
```

7. **Gerar Domain:**
   - Settings → Networking → Generate Domain
   - Anote o domínio (ex: `wppconnect-production-xxxx.railway.app`)
   - Use esse domínio no `BASE_URL` acima

#### Opção B: Usar Dockerfile Customizado

Crie `Dockerfile.wppconnect`:

```dockerfile
FROM wppconnectteam/wppconnect-server:latest

# Variáveis padrão
ENV BASE_URL=http://localhost:21465
ENV HOST=0.0.0.0
ENV PORT=21465

VOLUME ["/usr/src/app/userDataDir", "/usr/src/app/tokens"]

EXPOSE 21465

CMD ["node", "dist/server.js"]
```

Depois faça deploy separado para este serviço.

## 📱 Conectar WhatsApp ao Bot

### 1. Acessar Interface do WPPConnect

Abra no navegador:
```
https://seu-wppconnect.railway.app
```

### 2. Gerar QR Code

**Endpoint:**
```
GET https://seu-wppconnect.railway.app/api/session-evora/qrcode
```

Você pode:
- Abrir direto no navegador
- Usar Postman/Insomnia
- Usar curl:

```bash
curl https://seu-wppconnect.railway.app/api/session-evora/qrcode
```

### 3. Escanear com WhatsApp

1. Abra WhatsApp no celular
2. Menu → **Dispositivos conectados**
3. **Conectar dispositivo**
4. Escaneie o QR Code que apareceu

### 4. Verificar Conexão

```bash
curl https://seu-wppconnect.railway.app/api/session-evora/check-connection-session
```

Deve retornar:
```json
{
  "status": "connected",
  "message": "Session is connected"
}
```

## 🔧 Configurar Webhook no Django

Certifique-se de que a URL do webhook no WPPConnect aponta para seu Django:

```
WEBHOOK_URL=https://seu-django-app.railway.app/webhooks/whatsapp/
```

**Testar webhook:**

```bash
# Envie uma mensagem de teste para o bot
# Verifique os logs do Django:
railway logs -s evora-web
```

## 🔐 Variáveis de Ambiente Completas

### Django Service

```bash
# Banco de dados (Railway gerencia)
DATABASE_URL=${DATABASE_URL}

# Redis (Railway gerencia)
REDIS_URL=${REDIS_URL}

# Django Settings
DJANGO_SECRET_KEY=gere-uma-chave-segura-aqui
DJANGO_DEBUG=0
ALLOWED_HOSTS=*

# WhatsApp
WPP_BASE=https://seu-wppconnect.railway.app
WPP_SESSION=session-evora

# OpenAI (opcional)
OPENAI_API_KEY=sua-chave-aqui

# Câmbio USD→BRL (opcional, usar API externa)
USD_BRL=5.0
```

### WPPConnect Service

```bash
BASE_URL=https://seu-wppconnect.railway.app
HOST=0.0.0.0
PORT=21465
WEBHOOK_URL=https://seu-django.railway.app/webhooks/whatsapp/
WEBHOOK_BY_EVENTS=true
WEBHOOK_ALLOWED_EVENTS=onmessage,onstatechange
SESSION_SECRET_KEY=evora-secret-2024
```

## 🚀 Deploy

### Deploy Django

```bash
# Via CLI (na pasta do projeto)
railway up

# Ou fazer push no Git (se conectado ao GitHub)
git push origin main
# Railway fará deploy automaticamente
```

### Executar Migrações

```bash
# Via CLI
railway run python manage.py migrate

# Ou configure no railway.toml (já feito):
# startCommand = "python manage.py migrate && gunicorn ..."
```

### Criar Superusuário

```bash
railway run python manage.py createsuperuser
```

## 📊 Verificar Status

```bash
# Ver logs do Django
railway logs -s evora-web

# Ver logs do WPPConnect
railway logs -s wppconnect

# Ver status dos serviços
railway status
```

## 🧪 Testar Integração Completa

### 1. Criar Token no Admin

```
https://seu-django.railway.app/admin/
```

1. Login com superusuário
2. Ir em **"Shopper Onboarding Tokens"**
3. Criar novo token (ex: `SHOP-ABC123`)

### 2. Cadastrar Shopper via WhatsApp

Mande mensagem privada para o bot:
```
/sou_shopper ABC123
```

### 3. Criar Grupo e Vincular

1. Criar grupo no WhatsApp
2. Adicionar o número do bot
3. No admin Django, criar **Group Link Request**
4. No grupo, enviar: `/vincular XYZ789`

### 4. Testar Comandos

No grupo:
```
/comprar 2x Victoria's Secret Body Splash
/entrega keeper
/pagar pix
/status
```

## 📈 Monitoramento

### Railway Dashboard

- **Metrics:** CPU, RAM, Network
- **Logs:** Real-time logs de cada serviço
- **Deployments:** Histórico de deploys

### Logs Importantes

```bash
# Django (todos os comandos WhatsApp)
railway logs -s evora-web --tail

# WPPConnect (conexão WhatsApp)
railway logs -s wppconnect --tail

# Celery (tarefas assíncronas - se configurado)
railway logs -s celery --tail
```

## 🔧 Troubleshooting

### WPPConnect perde conexão

**Causa:** Volume não persistido ou QR Code expirou

**Solução:**
1. Verificar se o volume está montado
2. Gerar novo QR Code
3. Reconectar WhatsApp

### Webhook não funciona

**Causa:** URL incorreta ou Django não acessível

**Verificar:**
```bash
# Testar webhook manualmente
curl -X POST https://seu-django.railway.app/webhooks/whatsapp/ \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

### Banco de dados não conecta

**Verificar:**
```bash
railway variables
# Procurar DATABASE_URL
```

### Migrações não aplicadas

```bash
# Forçar migrações
railway run python manage.py migrate --run-syncdb
```

## 💰 Custos Estimados Railway

| Serviço | Uso | Custo/mês |
|---------|-----|-----------|
| PostgreSQL | Plano Hobby | $5 |
| Redis | Plano Hobby | $5 |
| Django (Web) | Plano Hobby | $5 |
| WPPConnect | Plano Hobby | $5 |
| **TOTAL** | | **$20/mês** |

_Plan Hobby: 500MB RAM, 1GB storage, 500 horas/mês_

### Plano Gratuito (Trial)

Railway oferece $5 de crédito grátis/mês:
- Perfeito para testes
- Suficiente para 1-2 serviços pequenos
- Sem cartão de crédito necessário inicialmente

## 🔄 Atualização/Redeploy

```bash
# Fazer mudanças no código
git add .
git commit -m "Nova funcionalidade"
git push origin main

# Ou via CLI
railway up
```

Railway fará redeploy automaticamente.

## 🆘 Suporte

- **Railway Docs:** https://docs.railway.app
- **WPPConnect Docs:** https://wppconnect.io
- **Discord Railway:** https://discord.gg/railway

---

## ✅ Checklist de Deploy

- [ ] Railway CLI instalado
- [ ] Projeto vinculado (`railway link`)
- [ ] PostgreSQL ativo
- [ ] Redis adicionado
- [ ] Django deployado
- [ ] Variáveis de ambiente configuradas
- [ ] Migrações aplicadas
- [ ] Superusuário criado
- [ ] WPPConnect deployado com volume
- [ ] QR Code escaneado
- [ ] WhatsApp conectado
- [ ] Webhook configurado
- [ ] Token de teste criado
- [ ] Grupo vinculado
- [ ] Comandos testados

---

**🎉 Pronto! Seu ÉVORA Connect está rodando no Railway com WhatsApp integrado!**

✨ **Minimalist, Sophisticated Style** ✨







