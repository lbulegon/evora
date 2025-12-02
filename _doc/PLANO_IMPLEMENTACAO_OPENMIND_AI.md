# Plano de Implementação - Servidor OpenMind AI no SinapUm

🎯 **Objetivo:** Criar servidor de IA próprio para análise de imagens de produtos, substituindo a OpenAI.

---

## 🏗️ Estrutura do Projeto

```
/opt/openmind-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           └── analyze.py  # Endpoint de análise
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configurações
│   │   ├── security.py      # Autenticação
│   │   └── image_analyzer.py # Lógica de análise
│   └── models/
│       └── schemas.py       # Schemas Pydantic
├── requirements.txt
├── .env
├── .env.example
├── README.md
└── run.sh                   # Script de inicialização
```

---

## 🚀 Tecnologias Escolhidas

### FastAPI (Recomendado)
- ✅ API moderna e rápida
- ✅ Documentação automática (Swagger)
- ✅ Validação automática com Pydantic
- ✅ Suporte nativo a async/await
- ✅ Fácil integração com modelos de IA

### Alternativas
- Flask (mais simples, mas menos recursos)
- Django REST Framework (mais complexo para este caso)

---

## 📋 Implementação Passo a Passo

### Fase 1: Setup Inicial do Servidor SinapUm

```bash
# 1. Conectar via SSH
ssh root@69.169.102.84

# 2. Instalar dependências do sistema
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl

# 3. Criar diretório do projeto
mkdir -p /opt/openmind-ai
cd /opt/openmind-ai

# 4. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 5. Instalar FastAPI e dependências básicas
pip install fastapi uvicorn python-multipart pillow requests
```

### Fase 2: Estrutura do Projeto

Criar arquivos base conforme estrutura acima.

### Fase 3: Implementar Endpoint Principal

**Endpoint:** `POST /api/v1/analyze-product-image`

**Funcionalidades:**
- Receber imagem (multipart/form-data)
- Validar autenticação (Bearer Token)
- Processar imagem com modelo de IA
- Retornar JSON no formato ÉVORA

### Fase 4: Integração com Modelo de IA

**Opções:**
1. **OpenAI API** (temporário, para MVP)
2. **Ollama** (local, modelos open-source)
3. **Modelo customizado** (futuro)

**Recomendação para MVP:** Usar OpenAI API ou Ollama para começar rápido.

### Fase 5: Deploy e Serviço

```bash
# Criar serviço systemd
# Configurar nginx como reverse proxy
# Configurar SSL/HTTPS
```

---

## 🔐 Segurança

1. **Autenticação:** Bearer Token (API Key)
2. **Rate Limiting:** Limitar requisições por minuto
3. **Validação:** Validar tamanho/formato de imagens
4. **Logs:** Registrar todas as requisições

---

## 🧪 Testes

```bash
# Teste local
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "image=@product_image.jpg"

# Teste do ÉVORA
# Configurar OPENMIND_AI_URL no .env do ÉVORA
```

---

## 📊 Monitoramento

- Logs estruturados
- Métricas de performance
- Health check endpoint

---

## 🎯 Próximos Passos Imediatos

1. ✅ Criar estrutura do projeto
2. ✅ Implementar endpoint básico
3. ✅ Configurar autenticação
4. ✅ Integrar modelo de IA
5. ✅ Testar com ÉVORA
6. ✅ Deploy em produção

---

Vamos começar! 🚀
