# ✅ Variáveis Padronizadas - Padrão Railway

## 🎯 Padrão Definido

Todas as variáveis seguem o mesmo padrão do Railway em **todos os lugares**!

---

## 📋 Variáveis Padrão (Railway)

### ✅ Para ÉVORA (Railway):

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_...
OPENMIND_AI_TIMEOUT=30
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct  # ✨ ADICIONADO!
```

---

## 🔄 Fluxo das Variáveis

### 1. ÉVORA → Servidor SinapUm

**ÉVORA usa:**
- `AI_SERVICE` - Escolhe serviço ("openmind" ou "openai")
- `OPENMIND_AI_URL` - URL do servidor SinapUm
- `OPENMIND_AI_KEY` - Autentica no servidor SinapUm
- `OPENMIND_AI_TIMEOUT` - Timeout das requisições

### 2. Servidor SinapUm → OpenMind.org

**Servidor SinapUm usa:**
- `OPENMIND_ORG_API_KEY` - Chave do OpenMind.org
- `OPENMIND_ORG_BASE_URL` - URL do OpenMind.org
- `OPENMIND_ORG_MODEL` - Modelo de visão (padrão: qwen2.5-vl-72b-instruct)

---

## ✅ Onde Cada Variável Está Configurada

### ÉVORA (Railway):
```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_...
OPENMIND_AI_TIMEOUT=30
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

### Servidor SinapUm (.env):
```bash
# Autenticação do servidor
OPENMIND_AI_API_KEY=om1_live_...

# Configuração OpenMind.org
OPENMIND_ORG_API_KEY=om1_live_...
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

---

## 📁 Arquivos Atualizados

1. ✅ `setup/settings.py` - Adicionado `OPENMIND_ORG_MODEL`
2. ✅ `environment_variables.example` - Padronizado
3. ✅ `openmind-ai-server/app/core/config.py` - Padronizado
4. ✅ `openmind-ai-server/ENV_EXAMPLE.txt` - Padronizado

---

## 🎯 Resultado

**Todas as variáveis estão padronizadas!** Use os mesmos nomes em todos os lugares:

- ✅ Railway (ÉVORA)
- ✅ Servidor SinapUm
- ✅ Código
- ✅ Documentação

**Pronto para usar!** 🚀
