# 🚨 Problema: Servidor Retornando Fallback (Dados Genéricos)

## ⚠️ Diagnóstico

O servidor SinapUm está retornando dados genéricos:
- `"nome_produto": "Produto identificado"` (genérico)
- `"categoria": "Não identificada"` (genérico)
- `"descricao": "Análise de imagem em desenvolvimento"` (fallback)

**Isso significa que as variáveis de ambiente do OpenMind.org não estão configuradas ou não estão funcionando!**

## ✅ Solução: Configurar Variáveis no Servidor SinapUm

### Passo 1: Conectar ao Servidor

```bash
ssh root@69.169.102.84
```

### Passo 2: Ir para o Diretório do Servidor

```bash
cd /opt/openmind-ai
```

### Passo 3: Verificar Arquivo .env Atual

```bash
cat .env
```

### Passo 4: Editar o Arquivo .env

```bash
nano .env
```

### Passo 5: Adicionar/Verificar Estas Variáveis

```bash
# Autenticação do próprio servidor
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1

# OpenMind.org - LLM principal (VOCÊ JÁ PAGOU POR ISSO!)
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

**Importante:** As variáveis `OPENMIND_ORG_API_KEY` e `OPENMIND_ORG_BASE_URL` são OBRIGATÓRIAS!

### Passo 6: Salvar o Arquivo

- Pressione: `Ctrl + O` (salvar)
- Pressione: `Enter` (confirmar)
- Pressione: `Ctrl + X` (sair)

### Passo 7: Verificar se as Variáveis Foram Lidas

```bash
# Testar se as variáveis estão acessíveis
python3 -c "from app.core.config import settings; print('API Key:', settings.OPENMIND_ORG_API_KEY[:20] + '...'); print('Base URL:', settings.OPENMIND_ORG_BASE_URL)"
```

### Passo 8: Reiniciar o Serviço

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```

### Passo 9: Verificar Logs

```bash
journalctl -u openmind-ai -f --no-pager | tail -20
```

### Passo 10: Testar Análise

Faça upload de uma imagem novamente. Agora deve usar o OpenMind.org e retornar dados reais! 🎉

---

## 🔍 Verificar o Problema Atual

Se quiser verificar por que está caindo no fallback, execute:

```bash
# Ver logs do servidor
journalctl -u openmind-ai -n 50 --no-pager

# Verificar variáveis de ambiente
cd /opt/openmind-ai
python3 -c "import os; from app.core.config import settings; print('OPENMIND_ORG_API_KEY:', '✅ Configurada' if settings.OPENMIND_ORG_API_KEY else '❌ Não configurada'); print('OPENMIND_ORG_BASE_URL:', settings.OPENMIND_ORG_BASE_URL)"
```

---

## 📋 Checklist

- [ ] Conectado ao servidor SinapUm via SSH
- [ ] Editado arquivo `.env` em `/opt/openmind-ai`
- [ ] Adicionado `OPENMIND_ORG_API_KEY`
- [ ] Adicionado `OPENMIND_ORG_BASE_URL`
- [ ] Adicionado `OPENMIND_ORG_MODEL`
- [ ] Salvo o arquivo `.env`
- [ ] Verificado variáveis com comando Python
- [ ] Reiniciado serviço `openmind-ai`
- [ ] Testado análise de imagem

---

## 🎯 Resultado Esperado

Após configurar as variáveis, ao analisar uma imagem, você deve ver:

```json
{
  "nome_produto": "Nome real do produto extraído",
  "categoria": "Categoria real identificada",
  "descricao": "Descrição detalhada baseada na imagem",
  "caracteristicas": {
    "marca": "Marca real",
    ...
  },
  ...
}
```

**Em vez de valores genéricos!**

---

## 🆘 Se Ainda Não Funcionar

1. Verifique os logs do servidor:
   ```bash
   journalctl -u openmind-ai -f
   ```

2. Verifique se as variáveis estão no `.env`:
   ```bash
   cat /opt/openmind-ai/.env | grep OPENMIND_ORG
   ```

3. Verifique se o serviço está usando o `.env`:
   ```bash
   systemctl show openmind-ai | grep Environment
   ```

4. Teste manualmente:
   ```bash
   cd /opt/openmind-ai
   python3 -c "from app.core.config import settings; print(settings.OPENMIND_ORG_BASE_URL)"
   ```

