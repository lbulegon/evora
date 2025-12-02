# 🔧 Corrigir Erro: "Extra inputs are not permitted"

## ⚠️ Problema

O servidor está dando erro:
```
Extra inputs are not permitted
OPENMIND_AI_TIMEOUT
```

Isso acontece porque o arquivo `.env` do servidor tem variáveis que não estão definidas no `config.py`.

## ✅ Solução Aplicada

Atualizei o código para **ignorar variáveis extras** no `.env` que não estão definidas.

## 🔄 Próximo Passo

**No servidor SinapUm, você tem 2 opções:**

### Opção 1: Reiniciar o Serviço (Código já corrigido)

```bash
ssh root@69.169.102.84
cd /opt/openmind-ai
git pull  # Se você tem git configurado
# OU copiar o arquivo atualizado manualmente

systemctl restart openmind-ai
systemctl status openmind-ai
```

### Opção 2: Limpar o .env (Remover variáveis extras)

No servidor, editar `.env` e manter **APENAS**:

```bash
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

Remover todas as outras variáveis (especialmente `OPENMIND_AI_TIMEOUT`).

---

## ✅ Com o Código Atualizado

O código agora **ignora variáveis extras**, então mesmo que tenha outras variáveis no `.env`, não dará erro!

**Precisa fazer deploy do código atualizado no servidor!** 🚀
