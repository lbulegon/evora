# 🚨 URGENTE: Aplicar Migration no Railway

## Problema
O erro `null value in column "message_id" violates not-null constraint` ocorre porque a migration `0028_make_whatsapp_product_message_optional.py` ainda não foi aplicada no banco de dados do Railway.

## ✅ Solução - 2 Opções

### Opção 1: Aplicar via Railway CLI (Recomendado)

```bash
# 1. Fazer commit e push da migration
git add app_marketplace/migrations/0028_make_whatsapp_product_message_optional.py
git commit -m "Migration: tornar message opcional em WhatsappProduct"
git push origin main

# 2. Aplicar migration no Railway
railway run python manage.py migrate

# OU se não tiver Railway CLI instalado, use o terminal do Railway via dashboard web
```

### Opção 2: Aplicar SQL Manualmente (Temporário)

Se não conseguir aplicar a migration via Django, execute este SQL diretamente no banco PostgreSQL do Railway:

```sql
ALTER TABLE app_marketplace_whatsappproduct 
ALTER COLUMN message_id DROP NOT NULL;
```

**Como acessar o banco:**
1. Acesse o dashboard do Railway
2. Vá em "PostgreSQL" → "Connect"
3. Execute o SQL acima

## 📋 Arquivos Modificados

- ✅ `app_marketplace/models.py` - Campo `message` agora é opcional (`null=True, blank=True`)
- ✅ `app_marketplace/migrations/0028_make_whatsapp_product_message_optional.py` - Migration criada
- ✅ `app_marketplace/shopper_dashboard_views.py` - Código atualizado para criar produto sem `message`

## ⚠️ IMPORTANTE

Após aplicar a migration ou o SQL, **teste criar um produto novamente**. O erro deve desaparecer.

