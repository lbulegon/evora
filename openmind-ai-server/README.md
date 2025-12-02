# OpenMind AI Server

Servidor de Inteligência Artificial para análise de imagens de produtos.

**Objetivo:** Analisar imagens de produtos e extrair informações no formato JSON ÉVORA.

---

## 🚀 Instalação no SinapUm

### 1. Conectar ao Servidor

```bash
ssh root@69.169.102.84
```

### 2. Instalar Dependências do Sistema

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl
```

### 3. Clonar/Criar Projeto

```bash
mkdir -p /opt/openmind-ai
cd /opt/openmind-ai
```

### 4. Criar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Instalar Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
nano .env
```

Configure:
```bash
OPENMIND_AI_API_KEY=sua-chave-secreta-aqui
OPENAI_API_KEY=sk-...  # Se usar OpenAI como backend
```

### 7. Iniciar Servidor

```bash
# Desenvolvimento
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Produção (com systemd)
systemctl start openmind-ai
systemctl enable openmind-ai
```

---

## 📡 Endpoint Principal

### POST /api/v1/analyze-product-image

Analisa uma imagem de produto e retorna dados no formato JSON ÉVORA.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "image=@product_image.jpg"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "nome_produto": "...",
    "categoria": "...",
    ...
  },
  "confidence": 0.95,
  "processing_time_ms": 1234
}
```

---

## 📚 Documentação da API

Após iniciar o servidor, acesse:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🔧 Configuração

Veja `.env.example` para todas as variáveis de ambiente disponíveis.

---

## 🧪 Testes

```bash
# Teste de health check
curl http://localhost:8000/health

# Teste de análise (com imagem)
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "image=@test_image.jpg"
```

---

## 📝 Estrutura do Projeto

```
openmind-ai-server/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── analyze.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── image_analyzer.py
│   └── models/
│       └── schemas.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔐 Segurança

- ✅ Autenticação via Bearer Token
- ✅ Rate Limiting configurável
- ✅ Validação de imagens (tamanho, formato)
- ✅ Logs de todas as requisições

---

## 🐳 Docker (Opcional)

```bash
docker build -t openmind-ai .
docker run -p 8000:8000 --env-file .env openmind-ai
```

---

**Desenvolvido para ÉVORA Connect** 🚀
