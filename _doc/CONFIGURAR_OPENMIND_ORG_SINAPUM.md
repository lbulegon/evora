# 🔧 Configurar OpenMind.org no Servidor SinapUm

## ✅ Código Adaptado!

O código já foi adaptado para usar o OpenMind.org! Agora é só configurar.

---

## 📋 Configuração no Servidor

### Passo 1: Editar Arquivo .env

No servidor SinapUm:

```bash
cd /opt/openmind-ai
nano .env
```

### Passo 2: Adicionar Configurações do OpenMind.org

Adicione estas linhas:

```bash
# OpenMind.org - LLM principal (você já pagou por isso!)
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

### Passo 3: Salvar e Reiniciar

```bash
# Salvar: Ctrl+O, Enter, Ctrl+X

# Reiniciar serviço
systemctl restart openmind-ai

# Verificar status
systemctl status openmind-ai
```

---

## ✅ Pronto!

Agora o servidor vai usar o **OpenMind.org** que você já pagou!

**Teste no ÉVORA:**
1. Acesse "Cadastrar por Foto"
2. Tire uma foto de um produto
3. Deve funcionar usando OpenMind.org! 🎉

---

## 🔍 Verificar se Está Funcionando

Veja os logs:

```bash
journalctl -u openmind-ai -f
```

Quando analisar uma imagem, deve mostrar logs usando OpenMind.org.

---

**Agora sim! Usando o LLM que você já pagou!** 🚀
