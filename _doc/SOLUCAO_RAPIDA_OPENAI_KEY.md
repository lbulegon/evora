# ⚡ Solução Rápida - Configurar OpenAI API Key

## 🎯 O Problema

O servidor OpenMind AI está retornando dados genéricos porque **não tem a chave da OpenAI configurada**.

---

## ✅ Solução em 3 Passos

### Passo 1: Obter Chave da OpenAI

1. Acesse: **https://platform.openai.com/api-keys**
2. Faça login (ou crie conta)
3. Clique em **"Create new secret key"**
4. **Copie a chave** (começa com `sk-...`)

---

### Passo 2: Configurar no Servidor

No servidor SinapUm, execute:

```bash
ssh root@69.169.102.84

cd /opt/openmind-ai
nano .env
```

**Adicione ou edite:**
```bash
OPENAI_API_KEY=sk-sua-chave-aqui
```

**Salve:** Ctrl+O, Enter, Ctrl+X

---

### Passo 3: Reiniciar Serviço

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```

---

## ✅ Pronto!

Agora teste no ÉVORA:
1. Acesse "Cadastrar por Foto"
2. Tire uma foto de um produto
3. **Deve preencher com dados reais!**

---

## 🧪 Verificar se Funcionou

No servidor, veja os logs:

```bash
journalctl -u openmind-ai -f
```

Quando analisar uma imagem, deve aparecer logs de processamento da OpenAI.

---

**Depois de configurar, a análise vai funcionar! 🚀**
