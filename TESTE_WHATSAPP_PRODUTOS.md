# 🧪 Guia de Teste - Envio de Produtos via WhatsApp

## 📋 Pré-requisitos

1. **Instância Evolution API conectada** - Verificar status:
   ```bash
   curl https://evora-product.up.railway.app/api/whatsapp/status/
   ```

2. **Número de WhatsApp válido** - Formato: `+5511999999999`

3. **Produtos no banco** (opcional, se usar `product_id`)

---

## 🚀 Métodos de Teste

### 1. Via cURL (Terminal)

#### Teste 1: Enviar produto usando `product_id` (busca no banco)

```bash
curl -X POST "https://evora-product.up.railway.app/api/whatsapp/send-product/" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+5511999999999",
    "product_id": 1
  }'
```

#### Teste 2: Enviar produto usando `product_data` (dados diretos)

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
        "subcategoria": "Cerveja",
        "preco": "R$ 5,99",
        "descricao": "Cerveja Polar gelada, 1 litro. Desde 1912."
      }
    },
    "image_url": "https://exemplo.com/imagem.jpg"
  }'
```

---

### 2. Via Python Script

Execute o script de teste:

```bash
python test_send_product_whatsapp.py
```

O script irá:
- Pedir seu número de WhatsApp
- Oferecer opções de teste
- Mostrar resposta detalhada

---

### 3. Via Postman ou Insomnia

#### Configuração:
- **Método**: `POST`
- **URL**: `https://evora-product.up.railway.app/api/whatsapp/send-product/`
- **Headers**: 
  ```
  Content-Type: application/json
  ```

#### Body (JSON):

**Opção A - Com product_id:**
```json
{
  "phone": "+5511999999999",
  "product_id": 1
}
```

**Opção B - Com product_data:**
```json
{
  "phone": "+5511999999999",
  "product_data": {
    "produto": {
      "nome": "Cerveja Polar",
      "marca": "Polar",
      "categoria": "Bebidas",
      "subcategoria": "Cerveja",
      "preco": "R$ 5,99",
      "descricao": "Cerveja Polar gelada, 1 litro."
    }
  },
  "image_url": "https://exemplo.com/imagem.jpg"
}
```

---

### 4. Via Django Shell

```python
# Abrir shell
python manage.py shell

# Importar serviço
from app_whatsapp_integration.evolution_service import EvolutionAPIService

# Criar instância do serviço
service = EvolutionAPIService()

# Dados do produto
product_data = {
    "produto": {
        "nome": "Cerveja Polar",
        "marca": "Polar",
        "categoria": "Bebidas",
        "subcategoria": "Cerveja",
        "preco": "R$ 5,99",
        "descricao": "Cerveja Polar gelada, 1 litro."
    }
}

# Enviar produto
result = service.send_product_message(
    phone="+5511999999999",
    product_data=product_data,
    image_url="https://exemplo.com/imagem.jpg"  # opcional
)

print(result)
```

---

## 📊 Verificar Produtos no Banco

### Listar Produtos JSON:

```python
python manage.py shell

from app_marketplace.models import ProdutoJSON

# Listar todos
produtos = ProdutoJSON.objects.all()
for p in produtos:
    print(f"ID: {p.id} - {p.nome_produto} - Marca: {p.marca}")

# Buscar por ID
produto = ProdutoJSON.objects.get(id=1)
print(produto.dados_json)
```

### Listar Produtos Tradicionais:

```python
from app_marketplace.models import Produto

produtos = Produto.objects.all()
for p in produtos:
    print(f"ID: {p.id} - {p.nome} - Preço: {p.preco}")
```

---

## ✅ Respostas Esperadas

### Sucesso:
```json
{
  "success": true,
  "message": "Produto enviado com sucesso"
}
```

### Erro:
```json
{
  "success": false,
  "error": "Mensagem de erro aqui"
}
```

---

## 🔍 Troubleshooting

### Erro: "Instância não encontrada"
- Verificar se a instância Evolution está criada e conectada
- Verificar variáveis de ambiente: `EVOLUTION_INSTANCE_NAME`

### Erro: "Produto não encontrado"
- Verificar se o `product_id` existe no banco
- Usar `product_data` diretamente se não tiver produtos cadastrados

### Erro: "Erro ao enviar mensagem"
- Verificar se a instância Evolution está com status `open`
- Verificar logs no admin Django: `EvolutionMessage`

### Mensagem não chega no WhatsApp
- Verificar se o número está no formato correto: `+5511999999999`
- Verificar se a instância Evolution está conectada
- Verificar logs em `app_whatsapp_integration/admin` → `EvolutionMessage`

---

## 📝 Exemplo Completo

```bash
# 1. Verificar status da instância
curl https://evora-product.up.railway.app/api/whatsapp/status/

# 2. Enviar produto de teste
curl -X POST "https://evora-product.up.railway.app/api/whatsapp/send-product/" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+5511999999999",
    "product_data": {
      "produto": {
        "nome": "Teste de Produto",
        "marca": "Marca Teste",
        "categoria": "Teste",
        "preco": "R$ 10,00",
        "descricao": "Este é um produto de teste"
      }
    }
  }'

# 3. Verificar mensagem no admin
# Acesse: https://evora-product.up.railway.app/admin/
# Vá em: Evolution Messages
```

---

## 🎯 Próximos Passos

Após testar com sucesso:
1. Integrar com interface web (botão "Enviar via WhatsApp")
2. Criar templates de produtos pré-formatados
3. Adicionar notificações de sucesso/erro
4. Implementar fila de envio para múltiplos produtos

