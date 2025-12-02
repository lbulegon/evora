# 📋 Variáveis Padronizadas - Lista Completa

## 🎯 Padrão Único para Todos os Ambientes

Todas as variáveis seguem o mesmo padrão em **todos os lugares**!

---

## 📍 1. ÉVORA - Local (Desenvolvimento)

**Arquivo:** `.env` (na raiz do projeto ÉVORA)

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

---

## 📍 2. ÉVORA - Railway (Produção)

**Local:** Railway Dashboard → Projeto ÉVORA → Variables

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_TIMEOUT=30
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

---

## 📍 3. Servidor OpenMind AI - SinapUm

**Arquivo:** `/opt/openmind-ai/.env` (no servidor SinapUm)

```bash
# =============================================================================
# Autenticação do Servidor OpenMind AI
# =============================================================================
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000

# =============================================================================
# OpenMind.org - LLM principal (você já pagou!)
# =============================================================================
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

---

## ✅ Resumo das Variáveis

### Para ÉVORA (Local e Railway):

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `AI_SERVICE` | `openmind` | Escolhe usar servidor próprio |
| `OPENMIND_AI_URL` | `http://69.169.102.84:8000/api/v1` | URL do servidor SinapUm |
| `OPENMIND_AI_KEY` | `om1_live_...` | Chave para autenticar no servidor |
| `OPENMIND_AI_TIMEOUT` | `30` | Timeout em segundos |
| `OPENMIND_ORG_MODEL` | `qwen2.5-vl-72b-instruct` | Modelo de visão do OpenMind.org |

### Para Servidor SinapUm:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `OPENMIND_AI_API_KEY` | `om1_live_...` | Chave de autenticação do servidor |
| `OPENMIND_AI_HOST` | `0.0.0.0` | Host do servidor |
| `OPENMIND_AI_PORT` | `8000` | Porta do servidor |
| `OPENMIND_ORG_API_KEY` | `om1_live_...` | Chave do OpenMind.org |
| `OPENMIND_ORG_BASE_URL` | `https://api.openmind.org/api/core/openai` | URL base do OpenMind.org |
| `OPENMIND_ORG_MODEL` | `qwen2.5-vl-72b-instruct` | Modelo de visão |

---

## 📝 Valores Completos

### Chave OpenMind (usada em vários lugares):
```
om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

### URLs:
- Servidor SinapUm: `http://69.169.102.84:8000/api/v1`
- OpenMind.org: `https://api.openmind.org/api/core/openai`

### Modelo:
- `qwen2.5-vl-72b-instruct`

---

## ✅ Checklist de Configuração

### ÉVORA Local:
- [ ] Criar arquivo `.env` na raiz do projeto
- [ ] Adicionar as 5 variáveis acima

### ÉVORA Railway:
- [ ] Adicionar as 5 variáveis no Railway Dashboard

### Servidor SinapUm:
- [ ] SSH no servidor
- [ ] Editar `/opt/openmind-ai/.env`
- [ ] Adicionar as 6 variáveis acima
- [ ] Reiniciar serviço: `systemctl restart openmind-ai`

---

## 🎯 Pronto!

**Todas as variáveis padronizadas e prontas para usar!** 🚀
