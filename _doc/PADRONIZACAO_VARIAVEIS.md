# 📋 Padronização de Variáveis - OpenMind AI

## ✅ Padrão Definido (Baseado no Railway)

Todas as variáveis seguem este padrão em **todos os lugares**:

---

## 🎯 Variáveis Padrão

### Para ÉVORA conectar ao Servidor SinapUm:

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_...
OPENMIND_AI_TIMEOUT=30
```

### Para Servidor SinapUm conectar ao OpenMind.org:

```bash
OPENMIND_AI_KEY=om1_live_...  # Mesma chave (autenticação do servidor)
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct  # Modelo de visão
```

**Nota:** O servidor SinapUm usa `OPENMIND_AI_KEY` para autenticação própria e também precisa das variáveis do OpenMind.org (que estão no código).

---

## 📍 Onde Cada Variável é Usada

### ÉVORA (Railway):
- `AI_SERVICE` - Escolhe entre "openmind" ou "openai"
- `OPENMIND_AI_URL` - URL do servidor SinapUm
- `OPENMIND_AI_KEY` - Chave para autenticar no servidor SinapUm
- `OPENMIND_AI_TIMEOUT` - Timeout para requisições

### Servidor OpenMind AI (SinapUm):
- `OPENMIND_AI_API_KEY` - Chave para autenticação do próprio servidor (diferente de OPENMIND_AI_KEY)
- `OPENMIND_AI_KEY` - Pode ser usado também (padronização)
- `OPENMIND_ORG_MODEL` - Modelo do OpenMind.org para usar

---

## ✅ Padrão Final

**ÉVORA (.env ou Railway):**
```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_...
OPENMIND_AI_TIMEOUT=30
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

**Servidor SinapUm (.env):**
```bash
OPENMIND_AI_API_KEY=om1_live_...  # Para autenticação do servidor
OPENMIND_AI_KEY=om1_live_...  # Mesma chave (padronização)
OPENMIND_ORG_API_KEY=om1_live_...  # Para conectar ao OpenMind.org
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```
