# 🔍 Esclarecimento - Duas Configurações Diferentes

## ✅ Situação Atual

Você já tem as configurações no README.md! Mas são para **lugares diferentes**:

---

## 📍 1. ÉVORA (Railway) → Servidor OpenMind AI (SinapUm)

**Variáveis que você já está usando:**

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_...
OPENMIND_AI_TIMEOUT=30
```

**O que faz:**
- ÉVORA envia a imagem para o servidor OpenMind AI no SinapUm
- Servidor SinapUm recebe e processa
- **✅ Já está configurado corretamente!**

---

## 📍 2. Servidor OpenMind AI (SinapUm) → OpenMind.org

**Variáveis que precisam estar no servidor SinapUm:**

```bash
OPENMIND_ORG_API_KEY=om1_live_...
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

**O que faz:**
- Servidor OpenMind AI no SinapUm usa o OpenMind.org para analisar a imagem
- É aqui que você usa o LLM que pagou!

**⚠️ Precisa configurar no servidor SinapUm!**

---

## 🎯 Fluxo Completo

```
1. ÉVORA (Railway)
   ↓ Usa OPENMIND_AI_URL e OPENMIND_AI_KEY
   ↓
2. Servidor OpenMind AI (SinapUm) - http://69.169.102.84:8000
   ↓ Recebe a imagem
   ↓ Usa OPENMIND_ORG_API_KEY e OPENMIND_ORG_BASE_URL
   ↓
3. OpenMind.org - https://api.openmind.org
   ↓ Analisa a imagem com LLM
   ↓ Retorna JSON
   ↓
4. Servidor OpenMind AI (SinapUm)
   ↓ Formata resposta
   ↓
5. ÉVORA (Railway)
   ↓ Mostra resultado ao usuário
```

---

## ✅ O Que Fazer

### No ÉVORA (Railway):
✅ **Já está OK!** Você já configurou as variáveis corretas.

### No Servidor OpenMind AI (SinapUm):
⚠️ **Precisa configurar** para usar OpenMind.org:

```bash
ssh root@69.169.102.84
cd /opt/openmind-ai
nano .env
```

Adicione:
```bash
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

---

## 🎯 Resumo

- **ÉVORA**: ✅ Já configurado corretamente!
- **SinapUm**: ⚠️ Precisa adicionar variáveis do OpenMind.org no `.env`

**As variáveis no README são para o ÉVORA, mas o servidor SinapUm também precisa das suas próprias variáveis!**
