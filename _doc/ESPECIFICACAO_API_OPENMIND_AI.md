# Especificação da API OpenMind AI para ÉVORA Connect

Este documento define a especificação da API que o servidor OpenMind AI deve implementar para integração com o ÉVORA Connect.

**Servidor:** SinapUm

---

## Endpoint Principal

### POST /api/v1/analyze-product-image

Analisa uma imagem de produto e extrai informações no formato JSON ÉVORA.

---

## Request

### Headers

```
Content-Type: multipart/form-data
Authorization: Bearer {OPENMIND_AI_KEY}
```

ou

```
Content-Type: application/json
Authorization: Bearer {OPENMIND_AI_KEY}
```

### Body (multipart/form-data)

```
image: <arquivo de imagem>
```

### Body (JSON com base64)

```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

### Query Parameters (opcional)

```
?model=default&language=pt-BR&format=evora
```

---

## Response

### Sucesso (200 OK)

```json
{
  "success": true,
  "data": {
    "nome_produto": "Samsung Type-C Earphones Sound by AKG",
    "categoria": "Eletrônicos",
    "subcategoria": "Fones de Ouvido",
    "descricao": "Fones de ouvido Samsung com conector USB Type-C, calibrados pela AKG.",
    "caracteristicas": {
      "marca": "Samsung",
      "modelo": "EO-IC100",
      "tipo_conexao": "USB Type-C",
      "design": "In-ear",
      "cor": "Branco",
      "material": "Plástico e silicone"
    },
    "compatibilidade": {
      "smartphones_samsung": ["Galaxy Fold", "Galaxy Note10"],
      "outros_dispositivos": "Aparelhos com porta USB-C"
    },
    "codigo_barras": "8806090270031",
    "dimensoes_embalagem": {
      "altura_cm": null,
      "largura_cm": null,
      "profundidade_cm": null
    },
    "peso_embalagem_gramas": null,
    "preco_visivel": null
  },
  "confidence": 0.95,
  "processing_time_ms": 1234
}
```

### Erro (400 Bad Request)

```json
{
  "success": false,
  "error": "Imagem inválida ou muito grande",
  "error_code": "INVALID_IMAGE"
}
```

### Erro (401 Unauthorized)

```json
{
  "success": false,
  "error": "API key inválida",
  "error_code": "UNAUTHORIZED"
}
```

### Erro (500 Internal Server Error)

```json
{
  "success": false,
  "error": "Erro interno do servidor",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Formato JSON ÉVORA

O servidor OpenMind AI deve retornar dados no **formato JSON ÉVORA completo** conforme especificado em `_doc/FLUXO_CADASTRO_FOTO_PRODUTO.md`.

### Campos Obrigatórios

- `nome_produto` (string): Nome do produto
- `categoria` (string): Categoria principal
- `descricao` (string): Descrição detalhada

### Campos Opcionais

- `subcategoria` (string)
- `caracteristicas` (object)
- `compatibilidade` (object)
- `codigo_barras` (string)
- `dimensoes_embalagem` (object)
- `peso_embalagem_gramas` (number)
- `preco_visivel` (string): Apenas se estiver na embalagem

---

## Autenticação

O servidor deve aceitar autenticação via:

1. **Bearer Token** no header `Authorization`
2. **API Key** como query parameter `?api_key=...`
3. **Header customizado** `X-API-Key: ...`

---

## Limites e Rate Limiting

- **Tamanho máximo da imagem**: 10MB
- **Formatos aceitos**: JPEG, PNG, WebP
- **Rate limit**: Configurável (ex: 100 requests/minuto por API key)
- **Timeout**: 30 segundos

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| `INVALID_IMAGE` | Imagem inválida ou corrompida |
| `IMAGE_TOO_LARGE` | Imagem excede o tamanho máximo |
| `UNSUPPORTED_FORMAT` | Formato de imagem não suportado |
| `UNAUTHORIZED` | API key inválida ou ausente |
| `RATE_LIMIT_EXCEEDED` | Limite de requisições excedido |
| `PROCESSING_ERROR` | Erro ao processar a imagem |
| `INTERNAL_ERROR` | Erro interno do servidor |

---

## Exemplos de Implementação

### Python (Flask/FastAPI)

```python
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)

@app.route('/api/v1/analyze-product-image', methods=['POST'])
def analyze_product_image():
    # Verificar autenticação
    api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not validate_api_key(api_key):
        return jsonify({
            'success': False,
            'error': 'API key inválida',
            'error_code': 'UNAUTHORIZED'
        }), 401
    
    # Obter imagem
    if 'image' in request.files:
        image_file = request.files['image']
    elif 'image_base64' in request.json:
        image_data = base64.b64decode(request.json['image_base64'])
    else:
        return jsonify({
            'success': False,
            'error': 'Imagem não fornecida',
            'error_code': 'INVALID_IMAGE'
        }), 400
    
    # Processar imagem com IA
    result = process_image_with_ai(image_file)
    
    return jsonify({
        'success': True,
        'data': result,
        'confidence': 0.95,
        'processing_time_ms': 1234
    })

def process_image_with_ai(image_file):
    # Implementar análise de imagem
    # Retornar dados no formato JSON ÉVORA
    pass
```

---

## Testes

### Teste com cURL

```bash
# Exemplo (URL real do servidor SinapUm será configurada)
curl -X POST https://sinapum.com/api/v1/analyze-product-image \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "image=@product_image.jpg"
```

### Teste com Python

```python
import requests

# URL do servidor SinapUm (será configurada)
url = "https://sinapum.com/api/v1/analyze-product-image"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
files = {"image": open("product_image.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

---

## Próximos Passos

1. ✅ Documentar especificação da API
2. ⏳ Implementar endpoint no servidor OpenMind AI
3. ⏳ Criar módulo de integração no ÉVORA
4. ⏳ Testar integração end-to-end
5. ⏳ Migrar gradualmente do OpenAI para OpenMind AI

---

## Referências

- [Formato JSON ÉVORA](_doc/FLUXO_CADASTRO_FOTO_PRODUTO.md)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
