# Análise dos Logs do Railway - Dezembro 2025

Este documento analisa os problemas identificados nos logs do Railway e propõe soluções.

---

## Problemas Identificados

### 1. ⚠️ Arquivos Estáticos Duplicados

**Erro:**
```
Found another file with the destination path 'app_marketplace/manifest.json'. It will be ignored since only the first encountered file is collected.
```

**Causa:**
Arquivos PWA (manifest.json, sw.js, ícones, etc.) estão sendo coletados de múltiplos locais durante o `collectstatic`.

**Impacto:**
- Avisos durante o build (não crítico)
- Possível confusão sobre qual arquivo está sendo usado

**Solução:**
- Verificar se há arquivos duplicados em diferentes diretórios
- Garantir que arquivos PWA estejam apenas em `app_marketplace/static/app_marketplace/`
- Considerar usar `STATICFILES_FINDERS` para controlar a ordem de busca

---

### 2. ❌ Bad Request (400) na Detecção por Foto

**Erro:**
```
WARNING 2025-12-01 03:57:35,293 log 6 140049103628096 Bad Request: /api/produtos/detectar_por_foto/
```

**Causa Possível:**
- Blob da imagem não está sendo enviado corretamente
- Validação de tipo de arquivo falhando
- Problema na criação do FormData

**Solução Implementada:**
- ✅ Melhorada validação no backend com logs detalhados
- ✅ Melhorada criação do File a partir do Blob no frontend
- ✅ Adicionada validação de blob antes do envio
- ✅ Melhoradas mensagens de erro no frontend

**Próximos Passos:**
- Monitorar logs para identificar causa específica
- Testar com diferentes tipos de imagem
- Verificar se o problema é específico do ambiente Railway

---

### 3. ⚠️ Arquivos de Mídia Não Encontrados (404)

**Erro:**
```
WARNING 2025-12-01 03:51:20,341 log 6 140049103628096 Not Found: /media/produtos/15/20251201_021756_Coca_cola.jpg
```

**Causa:**
Arquivos de mídia foram salvos no banco de dados, mas os arquivos físicos não existem mais ou não foram persistidos no Railway.

**Explicação:**
- Railway usa sistema de arquivos efêmero (ephemeral filesystem)
- Arquivos salvos em `/media/` são perdidos quando o container reinicia
- Arquivos de mídia precisam ser salvos em storage persistente (S3, etc.)

**Solução Necessária:**
1. **Imediato:** Usar storage externo (AWS S3, Cloudflare R2, etc.)
2. **Configurar:** Django Storages para salvar arquivos em S3
3. **Migrar:** Mover arquivos existentes para storage externo

**Implementação Sugerida:**
```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
```

---

### 4. ⚠️ Erros CSRF no Login (Alguns Casos)

**Erro:**
```
WARNING 2025-12-01 03:50:17,182 log 5 140049103628096 Forbidden (CSRF token from POST incorrect.): /login/
```

**Causa:**
Alguns clientes (especialmente mobile) estão tendo problemas com tokens CSRF.

**Impacto:**
- Alguns usuários não conseguem fazer login
- Principalmente em dispositivos Android (Chrome Mobile)

**Solução Atual:**
- ✅ Configurações CSRF já ajustadas para Railway
- ✅ `CSRF_TRUSTED_ORIGINS` configurado
- ✅ `SESSION_COOKIE_SAMESITE = 'Lax'`

**Observação:**
Erros CSRF são intermitentes - a maioria dos logins funciona. Pode ser relacionado a cache do navegador ou cookies.

---

## Resumo das Ações

### ✅ Já Implementado
1. Melhor tratamento de erros na detecção por foto
2. Validação melhorada de blob no frontend
3. Mensagens de erro mais detalhadas

### 🔄 Em Progresso
1. Monitoramento de logs para identificar causa do erro 400
2. Investigação de arquivos estáticos duplicados

### 📋 Próximos Passos
1. **CRÍTICO:** Implementar storage externo para arquivos de mídia (S3, etc.)
2. Configurar `STATICFILES_FINDERS` para evitar duplicação
3. Adicionar monitoramento/alertas para erros 400 e 404
4. Considerar usar CDN para arquivos estáticos e mídia

---

## Recomendações

1. **Storage de Mídia:** Migrar para S3 ou similar é **crítico** para produção
2. **Logs:** Implementar log aggregation (Sentry, DataDog, etc.)
3. **Monitoring:** Adicionar health checks para endpoints críticos
4. **Documentation:** Documentar processo de deploy e troubleshooting

---

## Referências

- [Django Storages Documentation](https://django-storages.readthedocs.io/)
- [Railway Ephemeral Filesystem](https://docs.railway.app/guides/railway-volumes)
- [Django Static Files](https://docs.djangoproject.com/en/5.2/howto/static-files/)

