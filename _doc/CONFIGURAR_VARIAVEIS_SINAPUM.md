# 🔧 Configurar Variáveis no Servidor SinapUm

## ⚠️ Ação Necessária

As variáveis **NÃO foram adicionadas no servidor** ainda! Você precisa fazer isso manualmente via SSH.

---

## 📋 Variáveis para Adicionar no Servidor SinapUm

### 1. Conectar ao Servidor

```bash
ssh root@69.169.102.84
```

### 2. Ir para o Diretório do Servidor

```bash
cd /opt/openmind-ai
```

### 3. Editar o Arquivo .env

```bash
nano .env
```

### 4. Adicionar/Verificar estas Variáveis

```bash
# Autenticação do próprio servidor
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1

# OpenMind.org - LLM principal (você já pagou!)
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

### 5. Salvar

- Pressione: `Ctrl + O` (salvar)
- Pressione: `Enter` (confirmar)
- Pressione: `Ctrl + X` (sair)

### 6. Reiniciar o Serviço

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```

---

## ✅ Verificar se Funcionou

```bash
# Ver logs
journalctl -u openmind-ai -f
```

Quando analisar uma imagem, deve usar o OpenMind.org! 🎉

---

## 📝 Resumo

**O que foi feito:**
- ✅ Código atualizado
- ✅ Arquivos de exemplo atualizados
- ✅ Documentação atualizada

**O que precisa fazer:**
- ⚠️ Adicionar variáveis no servidor SinapUm via SSH
- ⚠️ Reiniciar o serviço

**Quer ajuda para fazer isso agora?** 🚀
