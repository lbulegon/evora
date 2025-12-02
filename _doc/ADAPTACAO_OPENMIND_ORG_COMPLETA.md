# ✅ Adaptação Completa - Usar OpenMind.org

Baseado na documentação: https://docs.openmind.org/api-reference/introduction

---

## 🎯 O Que Foi Feito

### 1. Adicionado Suporte ao OpenMind.org

O código agora **prioriza o OpenMind.org** sobre OpenAI!

**Fluxo:**
1. ✅ Tenta usar OpenMind.org primeiro (se configurado)
2. ⚠️ Fallback para OpenAI (se OpenMind.org não configurado)
3. ❌ Retorna dados genéricos (se nada configurado)

---

## 🔑 Configuração Necessária

### No Servidor SinapUm (arquivo `.env`):

```bash
# OpenMind.org - LLM principal (você já pagou!)
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

---

## 📋 Informações da API OpenMind.org

### URL Base:
```
https://api.openmind.org/api/core/openai
```

### Autenticação:
```
Authorization: Bearer om1_live_...
```

### Endpoint:
```
POST /chat/completions
```

### Modelo de Visão Recomendado:
- **qwen2.5-vl-72b-instruct** - $0.59 por 1M tokens (mais barato!)

---

## ✅ Arquivos Modificados

1. ✅ `openmind-ai-server/app/core/config.py`
   - Adicionadas configurações do OpenMind.org

2. ✅ `openmind-ai-server/app/core/image_analyzer.py`
   - Adicionada função `_analyze_with_openmind_org()`
   - Prioriza OpenMind.org sobre OpenAI

3. ✅ `openmind-ai-server/ENV_EXAMPLE.txt`
   - Atualizado com configurações do OpenMind.org

---

## 🚀 Próximo Passo

**Configure no servidor SinapUm:**

```bash
cd /opt/openmind-ai
nano .env
```

Adicione:
```bash
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

Salve e reinicie:
```bash
systemctl restart openmind-ai
```

---

## ✅ Pronto!

Agora o servidor vai usar o OpenMind.org que você já pagou! 🎉

**Sem custo adicional!** Você usa o serviço que já tem! 💪
