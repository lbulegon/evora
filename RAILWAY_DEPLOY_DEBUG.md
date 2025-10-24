# 🚂 Railway Deploy Debug - ÉVORA

## 🔍 **Problemas Comuns Railway vs Local**

### **1. Variáveis de Ambiente**
```bash
# Local
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

# Railway
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:port/db
```

### **2. Dependências**
```bash
# Verificar se todas as dependências estão no requirements.txt
pip freeze > requirements.txt
```

### **3. Migrações**
```bash
# Railway executa automaticamente
python manage.py migrate
```

## 🛠️ **Soluções**

### **1. Atualizar settings.py para Railway**
```python
# setup/settings.py
import os
from decouple import config

# Detectar se está no Railway
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

# Configurações baseadas no ambiente
if IS_RAILWAY:
    DEBUG = False
    ALLOWED_HOSTS = ['*']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('PGDATABASE'),
            'USER': os.getenv('PGUSER'),
            'PASSWORD': os.getenv('PGPASSWORD'),
            'HOST': os.getenv('PGHOST'),
            'PORT': os.getenv('PGPORT'),
        }
    }
else:
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

### **2. Verificar Logs do Railway**
```bash
# Ver logs em tempo real
railway logs --tail

# Ver logs específicos
railway logs --service django
```

### **3. Testar Localmente com Configuração Railway**
```bash
# Simular ambiente Railway
export RAILWAY_ENVIRONMENT=production
export PGDATABASE=test_db
export PGUSER=test_user
export PGPASSWORD=test_pass
export PGHOST=localhost
export PGPORT=5432

# Rodar com configuração Railway
python manage.py runserver
```

## 🔧 **Comandos de Debug**

### **1. Verificar Status Railway**
```bash
railway status
railway logs --tail
```

### **2. Verificar Variáveis**
```bash
railway variables
```

### **3. Conectar ao Railway**
```bash
railway connect
```

### **4. Executar Comandos no Railway**
```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

## 📋 **Checklist Railway**

- [ ] ✅ `railway.toml` configurado
- [ ] ✅ `requirements.txt` atualizado
- [ ] ✅ Variáveis de ambiente configuradas
- [ ] ✅ `ALLOWED_HOSTS` configurado
- [ ] ✅ `DEBUG=False` em produção
- [ ] ✅ Banco de dados configurado
- [ ] ✅ Migrações aplicadas
- [ ] ✅ Logs verificados

## 🚨 **Problemas Específicos**

### **Erro: ModuleNotFoundError**
```bash
# Adicionar dependência ao requirements.txt
pip install nome-do-modulo
pip freeze > requirements.txt
```

### **Erro: Database Connection**
```bash
# Verificar variáveis de banco
railway variables | grep PG
```

### **Erro: Static Files**
```python
# Adicionar ao settings.py
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### **Erro: CSRF Token**
```python
# Adicionar domínio Railway
CSRF_TRUSTED_ORIGINS = [
    'https://seu-projeto.up.railway.app',
]
```

## 🎯 **Próximos Passos**

1. **Verificar logs**: `railway logs --tail`
2. **Verificar variáveis**: `railway variables`
3. **Testar localmente**: Simular ambiente Railway
4. **Fazer deploy**: `git push origin main`
5. **Verificar funcionamento**: Acessar URL Railway
