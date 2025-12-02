# 🔧 Corrigir - OpenMind AI Não Analisa Imagens

## ❌ Problema Identificado

A conexão funciona (200 OK), mas o servidor OpenMind AI **não está analisando as imagens** e retornando dados vazios ou genéricos.

---

## 🔍 Causa Provável

**O servidor OpenMind AI não tem a chave da OpenAI configurada!**

O servidor precisa da chave da OpenAI para realmente analisar as imagens. Sem ela, ele retorna dados genéricos ou falha silenciosamente.

---

## ✅ Solução

### Passo 1: Verificar Logs do Servidor

No servidor SinapUm:

```bash
ssh root@69.169.102.84
journalctl -u openmind-ai -n 100 --no-pager
```

Procure por erros como:
- "OPENAI_API_KEY não configurada"
- "OpenAI não está disponível"
- Erros de processamento de imagem

### Passo 2: Obter Chave da OpenAI

1. Acesse: https://platform.openai.com/api-keys
2. Faça login ou crie uma conta
3. Clique em "Create new secret key"
4. Copie a chave (ela começa com `sk-...`)

### Passo 3: Configurar no Servidor OpenMind AI

No servidor:

```bash
cd /opt/openmind-ai
nano .env
```

Adicione ou edite a linha:
```bash
OPENAI_API_KEY=sk-sua-chave-openai-aqui
```

**Salve:** Ctrl+O, Enter, Ctrl+X

### Passo 4: Reiniciar Serviço

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```

### Passo 5: Testar Análise

```bash
# Teste manual (precisa de uma imagem)
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" \
  -F "image=@/caminho/para/imagem.jpg"
```

**Deve retornar dados reais do produto, não dados genéricos!**

---

## 🧪 Verificar se Está Funcionando

### No Servidor:

```bash
# Ver logs em tempo real
journalctl -u openmind-ai -f
```

### Teste do ÉVORA:

1. Acesse o ÉVORA
2. Vá em "Cadastrar por Foto"
3. Tire uma foto de um produto
4. Deve preencher o formulário com dados reais!

---

## 📝 Checklist

- [ ] Verificar logs do servidor
- [ ] Obter chave da OpenAI
- [ ] Configurar no `.env` do servidor
- [ ] Reiniciar serviço
- [ ] Testar análise manual
- [ ] Testar no ÉVORA

---

## ⚠️ Importante

A chave da OpenAI tem custo por uso. Você precisa ter créditos na conta OpenAI para usar.

**Alternativa futura:** Implementar modelo próprio ou usar Ollama (open-source).

---

**Depois de configurar, a análise deve funcionar perfeitamente!** 🚀
