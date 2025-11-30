# 🚂 Railway Deploy Guide - ÉVORA

## 🔧 **Configuração Atualizada**

### **1. Settings.py Otimizado**
- ✅ DEBUG=False em produção
- ✅ Banco PostgreSQL (sempre)
- ✅ Arquivos estáticos configurados

### **2. Railway.toml Configurado**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python manage.py migrate && gunicorn setup.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120"
healthcheckPath = "/admin/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

## 🚀 **Deploy Steps**

### **1. Verificar Configuração Local**
```bash
# Testar configuração
python test_railway_deploy.py

# Verificar se tudo está funcionando
python manage.py runserver
```

### **2. Fazer Deploy**
```bash
# Commit mudanças
git add .
git commit -m "Fix Railway deploy configuration"
git push origin main

# Railway fará deploy automático
```

### **3. Verificar Deploy**
```bash
# Ver logs
railway logs --tail

# Ver status
railway status

# Ver variáveis
railway variables
```

## 🔍 **Troubleshooting**

### **Problema: 500 Error**
```bash
# Ver logs detalhados
railway logs --tail --service django

# Verificar migrações
railway run python manage.py migrate

# Verificar banco
railway run python manage.py dbshell
```

### **Problema: Static Files**
```bash
# Coletar arquivos estáticos
railway run python manage.py collectstatic --noinput
```

### **Problema: Database Connection**
```bash
# Verificar variáveis de banco
railway variables | grep PG

# Testar conexão
railway run python manage.py dbshell
```

### **Problema: CSRF Token**
```python
# Adicionar domínio Railway ao CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [
    'https://seu-projeto.up.railway.app',
    'http://127.0.0.1:8000',
    'http://localhost:8000'
]
```

## 📊 **Diferenças Local vs Railway**

| Configuração | Local | Railway |
|--------------|-------|---------|
| DEBUG | True | False |
| Database | PostgreSQL | PostgreSQL |
| Static Files | STATICFILES_DIRS | STATIC_ROOT |
| ALLOWED_HOSTS | localhost | * |
| Environment | Development | Production |

## 🎯 **Checklist Deploy**

- [ ] ✅ `settings.py` configurado para Railway
- [ ] ✅ `railway.toml` configurado
- [ ] ✅ `requirements.txt` atualizado
- [ ] ✅ Variáveis de ambiente configuradas
- [ ] ✅ Migrações aplicadas
- [ ] ✅ Arquivos estáticos coletados
- [ ] ✅ Logs verificados
- [ ] ✅ URL Railway funcionando

## 🚀 **Comandos Úteis**

### **Railway CLI**
```bash
# Login
railway login

# Link projeto
railway link

# Ver logs
railway logs --tail

# Executar comando
railway run python manage.py migrate

# Ver variáveis
railway variables

# Conectar ao banco
railway connect
```

### **Django Commands**
```bash
# Migrações
python manage.py migrate

# Superusuário
python manage.py createsuperuser

# Arquivos estáticos
python manage.py collectstatic

# Verificar configuração
python manage.py check --deploy
```

## 🎉 **Resultado Esperado**

Após o deploy, você deve ter:
- ✅ **URL Railway funcionando**
- ✅ **Admin Django acessível**
- ✅ **Banco PostgreSQL funcionando**
- ✅ **Arquivos estáticos servidos**
- ✅ **Logs sem erros**

## 📞 **Suporte**

Se encontrar problemas:
1. **Verificar logs**: `railway logs --tail`
2. **Verificar variáveis**: `railway variables`
3. **Testar localmente**: `python test_railway_deploy.py`
4. **Verificar configuração**: `python manage.py check --deploy`
