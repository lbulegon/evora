# ⚠️ Ação Necessária - Adicionar Variáveis no Servidor SinapUm

## ❌ Status Atual

**As variáveis NÃO foram adicionadas no servidor ainda!**

O que foi feito:
- ✅ Código atualizado para usar as variáveis padronizadas
- ✅ Arquivos de exemplo atualizados
- ❌ **Variáveis não configuradas no servidor SinapUm**

---

## 🔧 Configurar no Servidor SinapUm

### Passo 1: Conectar ao Servidor

```bash
ssh root@69.169.102.84
```

### Passo 2: Ir para o Diretório

```bash
cd /opt/openmind-ai
```

### Passo 3: Editar o Arquivo .env

```bash
nano .env
```

### Passo 4: Adicionar/Verificar estas Variáveis

Adicione estas linhas (se não existirem):

```bash
# OpenMind.org - LLM principal (você já pagou!)
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

### Passo 5: Salvar

1. Pressione `Ctrl + O` (salvar)
2. Pressione `Enter` (confirmar)
3. Pressione `Ctrl + X` (sair)

### Passo 6: Reiniciar o Serviço

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```

---

## ✅ Verificar se Funcionou

```bash
# Ver logs em tempo real
journalctl -u openmind-ai -f
```

Quando analisar uma imagem, deve mostrar logs usando OpenMind.org! 🎉

---

## 📋 Resumo do Que Precisa Fazer

1. ⚠️ Conectar ao servidor SinapUm via SSH
2. ⚠️ Editar o arquivo `.env` em `/opt/openmind-ai`
3. ⚠️ Adicionar as 3 variáveis do OpenMind.org
4. ⚠️ Salvar e reiniciar o serviço

**Quer que eu te ajude passo a passo agora?** 🚀
