# ✅ Padronização Completa - Variáveis OpenMind AI

## 🎯 Objetivo

Padronizar **todas as variáveis** para usar os mesmos nomes em todos os lugares, seguindo o padrão que você criou no Railway.

---

## ✅ Variáveis Padrão (Railway)

Todas as variáveis seguem este padrão:

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_...
OPENMIND_AI_TIMEOUT=30
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct  # ✨ ADICIONADO!
```

---

## 📁 Arquivos Atualizados

### 1. ✅ ÉVORA (Django)

**`setup/settings.py`:**
- ✅ Adicionado `OPENMIND_ORG_MODEL` para padronização

**`environment_variables.example`:**
- ✅ Adicionado `OPENMIND_ORG_MODEL`
- ✅ Comentários atualizados com "Padrão Railway"

### 2. ✅ Servidor OpenMind AI (SinapUm)

**`openmind-ai-server/app/core/config.py`:**
- ✅ `OPENMIND_ORG_MODEL` padronizado com valor padrão

**`openmind-ai-server/ENV_EXAMPLE.txt`:**
- ✅ Adicionado comentário sobre padronização Railway

### 3. ✅ Documentação

**`README.md`:**
- ✅ Atualizado com todas as variáveis padronizadas

---

## 🎯 Variáveis no Railway

Você já tem configurado no Railway:

1. ✅ `AI_SERVICE` = `openmind`
2. ✅ `OPENMIND_AI_KEY` = `om1_live_...`
3. ✅ `OPENMIND_AI_TIMEOUT` = `30`
4. ✅ `OPENMIND_AI_URL` = `http://69.169.102.84:8000/api/v1`
5. ✅ `OPENMIND_ORG_MODEL` = `qwen2.5-vl-72b-instruct` (novo!)

---

## 🔄 Como Funciona

### ÉVORA (Railway) → Servidor SinapUm

ÉVORA usa:
- `AI_SERVICE` - Escolhe "openmind"
- `OPENMIND_AI_URL` - URL do servidor SinapUm
- `OPENMIND_AI_KEY` - Autentica no servidor SinapUm
- `OPENMIND_AI_TIMEOUT` - Timeout

### Servidor SinapUm → OpenMind.org

Servidor SinapUm precisa no `.env`:
- `OPENMIND_ORG_API_KEY` - Chave do OpenMind.org
- `OPENMIND_ORG_BASE_URL` - URL do OpenMind.org
- `OPENMIND_ORG_MODEL` - Modelo (padrão: qwen2.5-vl-72b-instruct)

---

## ✅ Resultado Final

**Todas as variáveis estão padronizadas!**

- ✅ Mesmos nomes em todos os lugares
- ✅ Segue o padrão do Railway
- ✅ Documentação atualizada
- ✅ Código consistente

**Pronto para usar!** 🚀

---

## 📝 Próximo Passo

**No servidor SinapUm**, adicione no `.env`:

```bash
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

E está tudo funcionando! 🎉
