# ✅ Checklist de Deploy - Évora/VitrineZap

## 📋 Avaliação Pré-Deploy

### ✅ 1. Configurações do Railway

- [x] **railway.json** configurado corretamente
  - Healthcheck: `/health/`
  - Timeout: 300s
  - Restart policy: ON_FAILURE
  
- [x] **Procfile** presente e correto
  - Comando: `python manage.py migrate --noinput && gunicorn setup.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --max-requests 1000 --log-level info --access-logfile - --error-logfile -`

- [x] **Sem nixpacks.toml** (usando detecção automática)
- [x] **Sem package.json** na raiz (removido Node.js)
- [x] **runtime.txt** especifica Python 3.12.3

### ✅ 2. Configurações Django (setup/settings.py)

- [x] **Detecção Railway** funcionando
  ```python
  IS_RAILWAY = (
      os.getenv('RAILWAY_ENVIRONMENT') is not None or
      os.getenv('RAILWAY_PROJECT_ID') is not None or
      os.getenv('RAILWAY_SERVICE_ID') is not None or
      (os.getenv('PORT') is not None and os.getenv('PGHOST') is not None)
  )
  ```

- [x] **DEBUG** desabilitado em produção
  ```python
  DEBUG = not IS_RAILWAY  # False no Railway
  ```

- [x] **ALLOWED_HOSTS** configurado
  ```python
  ALLOWED_HOSTS = ['*']  # Permite todos os hosts
  ```

- [x] **SECRET_KEY** usa variável de ambiente
  ```python
  SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key')
  ```
  ⚠️ **ATENÇÃO**: Configure `SECRET_KEY` no Railway!

- [x] **Database** configurado para Railway
  ```python
  if IS_RAILWAY:
      DATABASES = {
          'default': {
              'ENGINE': 'django.db.backends.postgresql',
              'NAME': os.getenv('PGDATABASE', 'railway'),
              'USER': os.getenv('PGUSER', 'postgres'),
              'PASSWORD': os.getenv('PGPASSWORD', ''),
              'HOST': os.getenv('PGHOST', 'localhost'),
              'PORT': os.getenv('PGPORT', '5432'),
          }
      }
  ```

- [x] **Static Files** configurados
  ```python
  STATIC_URL = '/static/'
  STATIC_ROOT = BASE_DIR / 'staticfiles'
  ```

- [x] **CSRF_TRUSTED_ORIGINS** configurado
  ```python
  CSRF_TRUSTED_ORIGINS = [
      'https://evora-product.up.railway.app',
      'http://127.0.0.1:8000',
      'http://localhost:8000'
  ]
  ```
  ⚠️ **ATENÇÃO**: Atualize com o domínio real do Railway após deploy!

### ✅ 3. URLs Configuradas

- [x] **Healthcheck** endpoint: `/health/`
- [x] **Admin** endpoint: `/admin/`
- [x] **WhatsApp Integration** endpoint: `/api/whatsapp/webhook-from-gateway/`
- [x] **App Marketplace** URLs incluídas

### ✅ 4. Dependências (requirements.txt)

- [x] Django 5.2.8
- [x] djangorestframework 3.16.1
- [x] gunicorn 23.0.0
- [x] psycopg2-binary 2.9.10 (PostgreSQL)
- [x] python-decouple 3.8
- [x] pillow 11.3.0
- [x] django-cors-headers 4.7.0
- [x] django-filter 25.1
- [x] drf-yasg 1.21.11
- [x] httpx 0.28.1
- [x] redis 6.4.0
- [x] django-redis 6.0.0

### ✅ 5. Migrações

- [x] **Migrações verificadas**
  - Todas as migrações existentes estão aplicadas
  - `app_marketplace`: 17 migrações aplicadas
  - `admin`, `auth`, `contenttypes`, `sessions`: Todas aplicadas
  
- [x] **whatsapp_integration** - Migrações criadas ✅
  - `0001_initial.py` criada com sucesso
  - Models: WhatsAppContact e WhatsAppMessageLog
  - Índices criados corretamente

### 🔐 6. Variáveis de Ambiente Obrigatórias no Railway

Configure estas variáveis no dashboard do Railway:

#### Obrigatórias:
- [ ] `SECRET_KEY` - Chave secreta do Django (gerar uma nova!)
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

#### Automáticas (Railway preenche):
- [x] `PGDATABASE` - Nome do banco PostgreSQL
- [x] `PGUSER` - Usuário PostgreSQL
- [x] `PGPASSWORD` - Senha PostgreSQL
- [x] `PGHOST` - Host PostgreSQL
- [x] `PGPORT` - Porta PostgreSQL
- [x] `PORT` - Porta do serviço (Railway define automaticamente)

#### Opcionais:
- [ ] `OPENAI_API_KEY` - Se usar funcionalidades de IA
- [ ] `REDIS_URL` - Se usar Redis (Railway pode preencher automaticamente)

### 🚨 7. Problemas Potenciais Identificados

#### ⚠️ CRÍTICO - Corrigir Antes do Deploy:

1. **SECRET_KEY não configurado**
   - **Problema**: Usa fallback inseguro
   - **Solução**: Gerar e configurar no Railway
   - **Comando**: Ver seção 6 acima

2. **CSRF_TRUSTED_ORIGINS com domínio antigo**
   - **Problema**: `'https://evora-product.up.railway.app'` pode não ser o domínio atual
   - **Solução**: Atualizar após descobrir o domínio real do Railway
   - **Como descobrir**: Após primeiro deploy, verificar URL no dashboard Railway

3. **Migrações do whatsapp_integration**
   - **Problema**: App novo pode não ter migrações
   - **Solução**: Executar `python manage.py makemigrations whatsapp_integration` antes do deploy

#### ⚠️ MÉDIO - Verificar Após Deploy:

4. **Static Files**
   - **Verificar**: Se `collectstatic` está sendo executado no build
   - **Solução**: Adicionar ao Procfile se necessário (já está no comando de start)

5. **Healthcheck**
   - **Verificar**: Se `/health/` responde corretamente
   - **Teste**: `curl https://seu-app.up.railway.app/health/`

### 📝 8. Checklist de Deploy

#### Antes do Deploy:
- [ ] Gerar `SECRET_KEY` e configurar no Railway
- [ ] Verificar migrações pendentes
- [ ] Executar `python manage.py makemigrations` se necessário
- [ ] Testar localmente: `python manage.py runserver`
- [ ] Verificar se não há erros de importação
- [ ] Commit e push das mudanças

#### Durante o Deploy:
- [ ] Monitorar logs do Railway: `railway logs --tail`
- [ ] Verificar se build completa com sucesso
- [ ] Verificar se healthcheck passa
- [ ] Verificar se servidor inicia corretamente

#### Após o Deploy:
- [ ] Testar endpoint `/health/`
- [ ] Testar endpoint `/admin/`
- [ ] Verificar logs para erros
- [ ] Atualizar `CSRF_TRUSTED_ORIGINS` com domínio real
- [ ] Criar superusuário: `railway run python manage.py createsuperuser`
- [ ] Testar funcionalidades principais

### 🔧 9. Comandos Úteis Pós-Deploy

```bash
# Ver logs em tempo real
railway logs --tail

# Executar migrações manualmente (se necessário)
railway run python manage.py migrate

# Criar superusuário
railway run python manage.py createsuperuser

# Coletar arquivos estáticos manualmente
railway run python manage.py collectstatic --noinput

# Verificar configuração
railway run python manage.py check --deploy

# Acessar shell Django
railway run python manage.py shell

# Ver variáveis de ambiente
railway variables
```

### 📊 10. Resumo da Configuração

**Status Geral**: ✅ **PRONTO PARA DEPLOY** (após corrigir itens críticos)

**Itens Críticos a Corrigir**:
1. ⚠️ Configurar `SECRET_KEY` no Railway
2. ⚠️ Verificar/Criar migrações do `whatsapp_integration`
3. ⚠️ Atualizar `CSRF_TRUSTED_ORIGINS` após descobrir domínio

**Configuração Atual**:
- ✅ Python 3.12.3
- ✅ Django 5.2.8
- ✅ PostgreSQL (via Railway)
- ✅ Gunicorn como servidor
- ✅ Healthcheck configurado
- ✅ Detecção automática Railway
- ✅ Sem Node.js (100% Python)

---

**Última atualização**: $(date)
**Próximo passo**: Corrigir itens críticos e fazer deploy! 🚀

