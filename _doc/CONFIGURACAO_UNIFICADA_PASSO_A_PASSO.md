# 🚀 Configuração Unificada - Passo a Passo

## ✅ Ordem de Configuração

1. **.env local (ÉVORA)**
2. **.env do servidor SinapUm**
3. **Railway**

---

## 📍 PASSO 1: .env Local (ÉVORA)

### Arquivo: `.env` na raiz do projeto ÉVORA

```bash
# =============================================================================
# OPENMIND AI - Servidor SinapUm
# =============================================================================
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_TIMEOUT=30
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

**Ação:**
- Criar/editar arquivo `.env` na raiz do projeto
- Adicionar as 5 variáveis acima

---

## 📍 PASSO 2: .env do Servidor SinapUm

### Arquivo: `/opt/openmind-ai/.env` no servidor

```bash
# =============================================================================
# OpenMind AI Server - Configuração Unificada
# =============================================================================

# Autenticação do servidor (usa a mesma chave do Railway)
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1

# OpenMind.org - LLM principal
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

**Ação via SSH:**
```bash
ssh root@69.169.102.84
cd /opt/openmind-ai
nano .env
# Adicionar as 3 variáveis acima
# Salvar: Ctrl+O, Enter, Ctrl+X
systemctl restart openmind-ai
```

---

## 📍 PASSO 3: Railway

### Dashboard Railway → Projeto ÉVORA → Variables

Adicionar estas 5 variáveis:

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_TIMEOUT=30
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

**Ação:**
- Ir no Railway Dashboard
- Projeto ÉVORA → Variables
- Adicionar cada variável uma por uma

---

## ✅ Resumo

- **Local (.env):** 5 variáveis
- **SinapUm (.env):** 3 variáveis  
- **Railway:** 5 variáveis (mesmas do local)

**Tudo unificado e simples!** 🎉
