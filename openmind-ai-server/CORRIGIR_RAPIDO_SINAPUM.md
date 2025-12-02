# ⚡ Correção Rápida - Erro no Servidor SinapUm

## ⚠️ Erro Identificado

O servidor está dando erro:
```
Extra inputs are not permitted
OPENMIND_AI_TIMEOUT
```

## ✅ Solução Rápida

Você tem 2 opções:

---

### Opção 1: Atualizar Código (Recomendado)

O código já foi corrigido para ignorar variáveis extras. Precisa atualizar no servidor:

```bash
ssh root@69.169.102.84
cd /opt/openmind-ai

# Editar o arquivo config.py
nano app/core/config.py
```

**Na linha 70, depois de `case_sensitive = True`, adicionar:**
```python
extra = "ignore"  # Ignora variáveis extras no .env que não estão definidas
```

Salvar (Ctrl+O, Enter, Ctrl+X) e reiniciar:
```bash
systemctl restart openmind-ai
```

---

### Opção 2: Remover Variável do .env (Mais Rápido)

```bash
ssh root@69.169.102.84
cd /opt/openmind-ai
nano .env
```

**Remover a linha:**
```
OPENMIND_AI_TIMEOUT=30
```

Salvar e reiniciar:
```bash
systemctl restart openmind-ai
```

---

## ✅ Depois de Corrigir

Testar:
```bash
curl http://localhost:8000/health
```

**Esperado:** `{"status": "healthy", ...}`

---

**Qual opção você prefere?** 🚀
