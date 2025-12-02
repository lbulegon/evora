# 🔧 Guia Completo - Configurar OpenAI no Servidor SinapUm

## 📋 Passo a Passo Completo

---

## 1️⃣ Obter a Chave da OpenAI (Se Não Tiver)

### Opção A: Usar a Chave do Railway

Se você já tem a chave configurada no Railway:
1. Acesse o painel do Railway
2. Vá em "Variables"
3. Procure por `OPENAI_API_KEY`
4. **Copie o valor** (começa com `sk-...`)

### Opção B: Criar Nova Chave

1. Acesse: **https://platform.openai.com/api-keys**
2. Faça login (ou crie conta)
3. Clique em **"+ Create new secret key"**
4. Dê um nome (ex: "OpenMind AI - SinapUm")
5. **Copie a chave** (ela só aparece uma vez!)

---

## 2️⃣ Conectar ao Servidor SinapUm

No seu terminal:

```bash
ssh root@69.169.102.84
```

Digite a senha quando solicitado.

---

## 3️⃣ Editar Arquivo .env

```bash
cd /opt/openmind-ai
nano .env
```

---

## 4️⃣ Adicionar/Editar a Chave

No editor `nano`, procure pela linha:

```bash
OPENAI_API_KEY=
```

**Se existir**, substitua por:
```bash
OPENAI_API_KEY=sk-sua-chave-openai-aqui
```

**Se não existir**, adicione uma nova linha:
```bash
OPENAI_API_KEY=sk-sua-chave-openai-aqui
```

**Exemplo completo do arquivo:**
```bash
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000
OPENAI_API_KEY=sk-sua-chave-aqui
OPENAI_MODEL=gpt-4o
RATE_LIMIT_PER_MINUTE=100
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=jpeg,jpg,png,webp
IMAGE_MAX_DIMENSION=2048
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

---

## 5️⃣ Salvar o Arquivo

1. Pressione **Ctrl+O** (para salvar)
2. Pressione **Enter** (para confirmar nome do arquivo)
3. Pressione **Ctrl+X** (para sair)

---

## 6️⃣ Verificar se Foi Salvo

```bash
cat .env | grep OPENAI_API_KEY
```

Deve mostrar:
```
OPENAI_API_KEY=sk-...
```

---

## 7️⃣ Reiniciar o Serviço

```bash
systemctl restart openmind-ai
```

Aguarde alguns segundos e verifique o status:

```bash
systemctl status openmind-ai
```

Deve mostrar `Active: active (running)`

---

## 8️⃣ Verificar Logs

Para ver os logs em tempo real:

```bash
journalctl -u openmind-ai -f
```

Mantenha aberto e teste a análise. Quando processar uma imagem, você verá logs da OpenAI.

---

## ✅ Testar

### Opção 1: Testar no ÉVORA

1. Acesse o ÉVORA
2. Vá em "Cadastrar por Foto"
3. Tire uma foto de um produto
4. **Deve preencher o formulário com dados reais!**

### Opção 2: Testar Manualmente (No Servidor)

```bash
# Baixe uma imagem de teste primeiro
# Ou use uma que já existe

curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" \
  -F "image=@/caminho/para/imagem.jpg"
```

Deve retornar dados reais do produto, não dados genéricos!

---

## 🔍 Verificar se Está Funcionando

Os logs devem mostrar algo assim quando processar uma imagem:

```
INFO Analisando imagem: produto.jpg, tamanho: 123456 bytes
INFO Chamando OpenAI Vision API...
INFO Análise concluída em 2345ms
```

---

## ⚠️ Problemas Comuns

### Erro: "OPENAI_API_KEY não encontrada"

**Solução:** Verifique se você salvou o arquivo corretamente (Ctrl+O, Enter, Ctrl+X)

### Serviço não reinicia

**Solução:** Verifique os logs:
```bash
journalctl -u openmind-ai -n 50 --no-pager
```

### Chave inválida

**Solução:** Verifique se a chave está correta e ativa na OpenAI

---

## ✅ Pronto!

Depois de configurar, a análise de imagens vai funcionar perfeitamente! 🚀

---

**Bora configurar!** 🎯
