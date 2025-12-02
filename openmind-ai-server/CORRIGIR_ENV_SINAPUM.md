# 🔧 Corrigir .env do Servidor SinapUm

## ⚠️ Problema

O servidor está reclamando de variáveis extras no `.env`:
- `OPENMIND_AI_TIMEOUT` (esta variável é do ÉVORA, não do servidor!)

## ✅ Solução

No servidor SinapUm, o arquivo `.env` deve ter **APENAS** estas 3 variáveis:

```bash
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

## 🔧 Comandos para Corrigir

```bash
ssh root@69.169.102.84
cd /opt/openmind-ai
nano .env
```

**Remover todas as variáveis que não são as 3 acima!**

Especialmente remover:
- `OPENMIND_AI_TIMEOUT`
- `OPENMIND_AI_URL`
- Qualquer outra variável do ÉVORA

Depois:
```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```
