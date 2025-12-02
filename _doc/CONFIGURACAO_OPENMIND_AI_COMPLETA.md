# 🔐 Configuração Completa - OpenMind AI

Configuração completa do OpenMind AI para o ÉVORA Connect.

---

## 📋 Chave da API

A chave do OpenMind AI já está configurada:

```
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

---

## ⚙️ Configuração no ÉVORA

### Arquivo `.env` do ÉVORA

```bash
# Escolher serviço de IA
AI_SERVICE=openmind  # Usar OpenMind AI (servidor próprio)

# Configuração do OpenMind AI
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_TIMEOUT=30
```

---

## 🔧 Configuração no Servidor SinapUm

### Arquivo `.env` do Servidor OpenMind AI

```bash
# API Key do servidor (mesma chave usada no ÉVORA)
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1

# Configurações do servidor
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000

# Backend de IA (OpenAI temporário)
OPENAI_API_KEY=sk-sua-chave-openai-aqui
OPENAI_MODEL=gpt-4o
```

---

## ✅ Validação

### 1. Verificar se o servidor está rodando

```bash
curl http://69.169.102.84:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "OpenMind AI Server"
}
```

### 2. Testar análise de imagem

```bash
curl -X POST http://69.169.102.84:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" \
  -F "image=@imagem_produto.jpg"
```

### 3. Testar do ÉVORA

1. Configure o `.env` do ÉVORA com as variáveis acima
2. Acesse a página "Cadastrar por Foto"
3. Tire uma foto de um produto
4. Verifique se os dados são extraídos corretamente

---

## 🔒 Segurança

⚠️ **IMPORTANTE:**
- A chave está no repositório apenas como referência
- No servidor, use a mesma chave configurada
- Nunca commitar o arquivo `.env` real
- Considere rotacionar a chave periodicamente

---

## 📝 Notas

- A mesma chave é usada tanto no ÉVORA quanto no servidor OpenMind AI
- O servidor valida a chave no header `Authorization: Bearer {KEY}`
- Timeout padrão: 30 segundos (ajustável via `OPENMIND_AI_TIMEOUT`)

---

**Tudo configurado e pronto para uso!** 🚀
