# 🚂 Configuração ÉVORA no Railway - Python Buildpack

## ✅ Configuração Simplificada (Sem Docker)

O Railway agora usa o buildpack Python nativo, muito mais simples e eficiente.

---

## 📋 Pré-requisitos

- ✅ Conta no Railway
- ✅ Projeto ÉVORA já conectado
- ✅ PostgreSQL e Redis adicionados ao projeto

---

## 🚀 Configuração Passo a Passo

### 1️⃣ Configurar Buildpack Python

O Railway detecta automaticamente que é um projeto Python pelo `requirements.txt`.

**Não precisa de Dockerfile!** ✅

### 2️⃣ Variáveis de Ambiente

Configure estas variáveis no Railway:

```bash
# Django
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=sua-chave-secreta-super-segura-aqui
ALLOWED_HOSTS=*.up.railway.app,localhost

# Database (copie do serviço PostgreSQL)
DATABASE_URL=${{PostgreSQL.DATABASE_URL}}

# Redis (copie do serviço Redis)  
REDIS_URL=${{Redis.REDIS_URL}}

# WhatsApp (opcional - para integração futura)
WPP_BASE=https://seu-wppconnect.up.railway.app
WPP_SESSION=session-evora

# OpenAI (se usar IA)
OPENAI_API_KEY=sua-chave-openai-aqui
```

### 3️⃣ Deploy Automático

1. **Push para GitHub** - Railway detecta mudanças automaticamente
2. **Build automático** - Instala dependências Python
3. **Deploy automático** - Aplica migrações e sobe o servidor

### 4️⃣ Verificar Deploy

Acesse: `https://seu-projeto.up.railway.app/admin/`

---

## 🎯 Vantagens do Buildpack Python

| Aspecto | Docker | Python Buildpack |
|---------|--------|------------------|
| **Configuração** | Complexa | Simples |
| **Build time** | 2-3 min | 30-60 seg |
| **Tamanho** | ~500MB | ~100MB |
| **Debug** | Difícil | Fácil |
| **Updates** | Rebuild completo | Hot reload |

---

## 🔧 Comandos Úteis

### Ver logs em tempo real:
```bash
railway logs --tail
```

### Executar comando no Railway:
```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

### Acessar shell:
```bash
railway shell
```

---

## 📊 Monitoramento

### Health Check
- **URL:** `/admin/`
- **Timeout:** 100s
- **Retry:** 10x

### Métricas
- **CPU:** Automático
- **RAM:** 512MB padrão
- **Storage:** 1GB (se necessário)

---

## 🆘 Troubleshooting

### Build falha
```bash
# Ver logs detalhados
railway logs --tail

# Verificar dependências
railway run pip list
```

### Migrations não aplicam
```bash
# Aplicar manualmente
railway run python manage.py migrate
```

### Static files não carregam
```bash
# Coletar estáticos
railway run python manage.py collectstatic --noinput
```

---

## 💰 Custos Estimados

| Serviço | Custo/mês |
|---------|-----------|
| Django (Python) | $5 |
| PostgreSQL | $5 |
| Redis | $5 |
| **TOTAL** | **$15/mês** |

💡 **Plano Hobby:** $5 grátis/mês

---

## 🎉 Pronto!

Seu ÉVORA está rodando nativamente no Railway com Python buildpack!

### Próximos passos:
1. ✅ Configurar domínio personalizado (opcional)
2. ✅ Adicionar SSL automático
3. ✅ Configurar backup do banco
4. ✅ Monitorar performance

---

**ÉVORA Connect** - *Minimalist, Sophisticated Style* ✨
