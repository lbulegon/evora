# 🔍 Troubleshooting Healthcheck - Railway

## O que é o Healthcheck?

O **Healthcheck** é um endpoint que o Railway usa para verificar se sua aplicação está funcionando corretamente. 

- **Endpoint configurado**: `/health/`
- **Timeout**: 300 segundos (5 minutos)
- **Frequência**: Railway tenta a cada poucos segundos

Se o healthcheck falhar, o Railway considera que a aplicação não está funcionando e pode reiniciar o serviço.

---

## 🚨 Problema: Healthcheck Falhando

### Possíveis Causas

1. **Servidor não está iniciando**
   - Erro no comando de start
   - Migrações falhando
   - Erro de importação

2. **Servidor demora muito para iniciar**
   - Timeout de 300s pode não ser suficiente
   - Migrações demoradas

3. **Endpoint `/health/` não acessível**
   - URL incorreta
   - Middleware bloqueando
   - Erro na view

4. **Banco de dados não conectado**
   - Variáveis de ambiente faltando
   - PostgreSQL não configurado

---

## ✅ Soluções

### 1. Verificar Logs do Railway

```bash
railway logs --tail
```

Procure por:
- Erros de migração
- Erros de importação
- Erros de conexão com banco
- Erros do Gunicorn

### 2. Testar Endpoint Localmente

```bash
# Iniciar servidor
python manage.py runserver

# Em outro terminal, testar healthcheck
curl http://localhost:8000/health/
```

Deve retornar:
```json
{
  "status": "ok",
  "message": "VitrineZap is running",
  "version": "1.0.0"
}
```

### 3. Verificar Variáveis de Ambiente

No Railway, verifique se estas variáveis estão configuradas:

- `SECRET_KEY` ⚠️ **OBRIGATÓRIA**
- `PGDATABASE` (Railway preenche automaticamente)
- `PGUSER` (Railway preenche automaticamente)
- `PGPASSWORD` (Railway preenche automaticamente)
- `PGHOST` (Railway preenche automaticamente)
- `PGPORT` (Railway preenche automaticamente)

### 4. Separar Migrações do Start

O Procfile atual executa migrações e start no mesmo comando. Se as migrações falharem, o servidor não inicia.

**Solução**: Usar `;` em vez de `&&` para que o servidor inicie mesmo se migrações falharem:

```bash
web: python manage.py migrate --noinput; gunicorn setup.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --max-requests 1000 --log-level info --access-logfile - --error-logfile -
```

### 5. Adicionar CSRF Exempt no Healthcheck

O healthcheck pode estar sendo bloqueado por CSRF. Adicione `@csrf_exempt`:

```python
@csrf_exempt
@never_cache
def health_check(request):
    return JsonResponse({...}, status=200)
```

### 6. Aumentar Timeout do Healthcheck

No `railway.json`, aumentar o timeout:

```json
{
  "deploy": {
    "healthcheckPath": "/health/",
    "healthcheckTimeout": 600,  // 10 minutos
    ...
  }
}
```

### 7. Usar Endpoint Mais Simples

Se `/health/` não funcionar, usar `/admin/` temporariamente:

```json
{
  "deploy": {
    "healthcheckPath": "/admin/",
    ...
  }
}
```

---

## 🔧 Comandos de Debug

### Verificar se servidor está rodando

```bash
railway run ps aux | grep gunicorn
```

### Testar conexão com banco

```bash
railway run python manage.py dbshell
```

### Executar migrações manualmente

```bash
railway run python manage.py migrate
```

### Verificar configuração

```bash
railway run python manage.py check --deploy
```

### Testar healthcheck diretamente

```bash
railway run curl http://localhost:$PORT/health/
```

---

## 📝 Checklist de Verificação

- [ ] Logs do Railway verificados
- [ ] Endpoint `/health/` testado localmente
- [ ] Variáveis de ambiente configuradas
- [ ] PostgreSQL conectado
- [ ] Migrações executadas com sucesso
- [ ] Servidor Gunicorn iniciando
- [ ] Healthcheck retornando 200 OK

---

## 🎯 Próximos Passos

1. Verificar logs do Railway
2. Testar endpoint localmente
3. Verificar variáveis de ambiente
4. Aplicar correções sugeridas
5. Fazer novo deploy

---

**Última atualização**: $(date)

