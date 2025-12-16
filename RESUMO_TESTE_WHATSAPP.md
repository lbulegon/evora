# 📋 Resumo - Teste de Envio de Produtos via WhatsApp

## ✅ O que foi implementado

1. **Endpoint de envio de produtos**: `POST /api/whatsapp/send-product/`
2. **Suporte para dois modelos**: `ProdutoJSON` e `Produto` tradicional
3. **Scripts de teste**: `test_send_product_simple.py` e `test_whatsapp_now.py`
4. **Documentação completa**: `TESTE_WHATSAPP_PRODUTOS.md`

## ⚠️ Problema identificado

As migrations do `app_whatsapp_integration` não foram aplicadas no banco do Railway.

**Erro:**
```
relation "app_whatsapp_integration_evolutioninstance" does not exist
```

## 🔧 Solução - Aplicar Migrations no Railway

### Opção 1: Via Railway CLI

```bash
# Conectar ao Railway
railway link

# Aplicar migrations
railway run python manage.py migrate app_whatsapp_integration
```

### Opção 2: Via Railway Dashboard

1. Acesse o Railway Dashboard
2. Vá em seu projeto Évora
3. Abra o terminal do serviço
4. Execute:
```bash
python manage.py migrate app_whatsapp_integration
```

### Opção 3: Criar tabelas manualmente (se necessário)

Se as migrations falharem, você pode criar as tabelas manualmente via SQL ou usar:

```bash
python manage.py migrate app_whatsapp_integration --run-syncdb
```

## 🧪 Como testar após aplicar migrations

### 1. Verificar status da instância

```bash
curl https://evora-product.up.railway.app/api/whatsapp/status/
```

**Resposta esperada:**
```json
{
  "success": true,
  "status": "open",
  "instance": {
    "name": "default",
    "status": "open",
    "phone_number": "+5511999999999"
  }
}
```

### 2. Testar envio de produto

**Via cURL:**
```bash
curl -X POST "https://evora-product.up.railway.app/api/whatsapp/send-product/" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+5511999999999",
    "product_data": {
      "produto": {
        "nome": "Cerveja Polar",
        "marca": "Polar",
        "categoria": "Bebidas",
        "preco": "R$ 5,99",
        "descricao": "Cerveja Polar gelada"
      }
    }
  }'
```

**Via Python:**
```bash
python test_send_product_simple.py
```

## 📊 Status atual

- ✅ Código implementado e testado localmente
- ✅ Endpoints criados e funcionais
- ✅ Suporte para ProdutoJSON e Produto
- ⚠️ Migrations precisam ser aplicadas no Railway
- ⚠️ Instância Evolution precisa estar conectada

## 🎯 Próximos passos

1. **Aplicar migrations no Railway** (prioridade)
2. **Verificar conexão da instância Evolution API**
3. **Configurar webhook na Evolution API** (se ainda não estiver)
4. **Testar envio real de produtos**

## 📝 Notas importantes

- O endpoint funciona mesmo sem instância conectada (mas a mensagem não será enviada)
- Produtos podem ser enviados usando `product_id` (busca no banco) ou `product_data` (dados diretos)
- Imagens são suportadas via `image_url` no payload
- Todas as mensagens são salvas no banco Django (PostgreSQL)

## 🔍 Verificar logs

Após aplicar migrations e testar, verifique:

1. **Admin Django**: `https://evora-product.up.railway.app/admin/`
   - `Evolution Instance` - Ver status da instância
   - `Evolution Message` - Ver mensagens enviadas/recebidas
   - `WhatsApp Contact` - Ver contatos

2. **Logs do Railway**: Verificar erros ou sucessos

