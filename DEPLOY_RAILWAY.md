# 🚀 Deploy ÉVORA no Railway - Guia Rápido

## ✅ Configuração Simplificada (Python Buildpack)

### 1️⃣ Conectar ao Railway

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Conectar projeto
railway link
```

### 2️⃣ Adicionar Serviços

No dashboard Railway:

1. **+ New → Database → PostgreSQL**
2. **+ New → Database → Redis** 
3. **+ New → Service → GitHub** (conectar repositório)

### 3️⃣ Configurar Variáveis

No serviço Django, adicionar:

```bash
# Django
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=sua-chave-super-secreta-aqui
ALLOWED_HOSTS=*.up.railway.app

# Database (Railway preenche automaticamente)
DATABASE_URL=${{PostgreSQL.DATABASE_URL}}

# Redis (Railway preenche automaticamente)  
REDIS_URL=${{Redis.REDIS_URL}}

# OpenAI (opcional)
OPENAI_API_KEY=sua-chave-openai
```

### 4️⃣ Deploy Automático

```bash
# Push para GitHub
git add .
git commit -m "Deploy Railway Python buildpack"
git push origin main
```

Railway detecta automaticamente e faz deploy! 🎉

### 5️⃣ Verificar

Acesse: `https://seu-projeto.up.railway.app/admin/`

---

## 🔧 Comandos Úteis

```bash
# Ver logs
railway logs --tail

# Executar comando
railway run python manage.py migrate
railway run python manage.py createsuperuser

# Acessar shell
railway shell
```

---

## 📊 Status

- ✅ **Buildpack:** Python (Nixpacks)
- ✅ **Runtime:** Python 3.13
- ✅ **Web Server:** Gunicorn
- ✅ **Database:** PostgreSQL
- ✅ **Cache:** Redis
- ✅ **SSL:** Automático

---

**ÉVORA Connect** - *Deploy simplificado no Railway* ✨
