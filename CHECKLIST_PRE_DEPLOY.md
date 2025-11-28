# ✅ CHECKLIST PRÉ-DEPLOY - Évora/VitrineZap

## 📋 VERIFICAÇÕES REALIZADAS

### ✅ 1. Migrations
- [x] Todas as migrations criadas
- [x] Nenhuma migration pendente
- [x] Migrations aplicadas localmente

### ✅ 2. Modelos Unificados
- [x] `Keeper` → `AddressKeeper` (renomeado)
- [x] `Estabelecimento` → `Empresa` (unificado)
- [x] ForeignKeys atualizados
- [x] Admin atualizado

### ✅ 3. Configurações de Produção
- [x] `DEBUG=False` em produção (via variável de ambiente)
- [x] `SECRET_KEY` configurado (via variável de ambiente)
- [x] `ALLOWED_HOSTS` configurado
- [x] WhiteNoise configurado para arquivos estáticos
- [x] PostgreSQL configurado

### ✅ 4. Arquivos de Deploy
- [x] `Procfile` configurado
- [x] `railway.json` configurado
- [x] `requirements.txt` atualizado

### ✅ 5. Sistema
- [x] Healthcheck endpoint (`/health/`)
- [x] Gunicorn configurado
- [x] Static files (collectstatic)

---

## 🚀 COMANDOS PARA DEPLOY

### 1. Verificar Git Status
```bash
git status
git add .
git commit -m "Unificação Empresa/Estabelecimento e renomeação Keeper/AddressKeeper"
```

### 2. Push para GitHub
```bash
git push origin main
```

### 3. No Railway
- O deploy será automático após o push
- Verificar logs no Railway
- Verificar healthcheck

---

## ⚠️ VARIÁVEIS DE AMBIENTE NECESSÁRIAS NO RAILWAY

Certifique-se de que estas variáveis estão configuradas:

- `SECRET_KEY` - Chave secreta do Django
- `DEBUG=False` - Modo produção
- `ALLOWED_HOSTS=evora-product.up.railway.app` - Domínio permitido
- `DATABASE_URL` ou variáveis PostgreSQL:
  - `PGDATABASE`
  - `PGUSER`
  - `PGPASSWORD`
  - `PGHOST`
  - `PGPORT`

---

## 📝 ALTERAÇÕES REALIZADAS NESTA SESSÃO

1. ✅ Renomeação `Keeper` → `AddressKeeper`
2. ✅ Unificação `Empresa` + `Estabelecimento` → `Empresa`
3. ✅ Recriação de lojas de Orlando
4. ✅ Atualização de Admin para mostrar tudo em uma tela
5. ✅ Migrations criadas e aplicadas

---

**Status**: ✅ **PRONTO PARA DEPLOY**  
**Data**: 2025-01-27



