# 🔧 Configurar Variáveis do OpenMind AI no Railway

## ✅ Resposta Rápida

**SIM!** Quando fizer o deploy no Railway, você precisa configurar as variáveis de ambiente **no painel do Railway**.

O arquivo `.env` é apenas para desenvolvimento local. Em produção (Railway), as variáveis são configuradas no painel.

---

## 📋 Variáveis Necessárias

Configure estas 4 variáveis no Railway:

| Variável | Valor |
|----------|-------|
| `AI_SERVICE` | `openmind` |
| `OPENMIND_AI_URL` | `http://69.169.102.84:8000/api/v1` |
| `OPENMIND_AI_KEY` | `om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1` |
| `OPENMIND_AI_TIMEOUT` | `30` (opcional) |

---

## 🚀 Como Configurar no Railway

### Passo 1: Acessar o Painel

1. Vá para https://railway.app
2. Faça login
3. Selecione seu projeto ÉVORA

### Passo 2: Adicionar Variáveis

1. No menu lateral, clique em **"Variables"** (ou vá em **"Settings"** → **"Variables"**)
2. Clique no botão **"+ New Variable"** ou **"Add Variable"**
3. Para cada variável:

   **Variável 1:**
   - **Name:** `AI_SERVICE`
   - **Value:** `openmind`
   - Clique em **"Add"**

   **Variável 2:**
   - **Name:** `OPENMIND_AI_URL`
   - **Value:** `http://69.169.102.84:8000/api/v1`
   - Clique em **"Add"**

   **Variável 3:**
   - **Name:** `OPENMIND_AI_KEY`
   - **Value:** `om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1`
   - Clique em **"Add"**

   **Variável 4 (Opcional):**
   - **Name:** `OPENMIND_AI_TIMEOUT`
   - **Value:** `30`
   - Clique em **"Add"**

### Passo 3: Redeploy Automático

O Railway detecta as mudanças e faz redeploy automaticamente. Ou você pode:

1. Ir em **"Deployments"**
2. Clicar em **"Redeploy"** no último deploy

---

## 💻 Via CLI (Alternativa)

Se preferir usar o terminal:

```bash
# Instalar Railway CLI (se ainda não tiver)
npm i -g @railway/cli

# Login
railway login

# Vincular projeto (se ainda não vinculou)
railway link

# Adicionar variáveis
railway variables set AI_SERVICE=openmind
railway variables set OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
railway variables set OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
railway variables set OPENMIND_AI_TIMEOUT=30

# Ver todas as variáveis configuradas
railway variables
```

---

## ✅ Verificar se Funcionou

Após configurar e fazer deploy:

1. Acesse o ÉVORA no Railway
2. Vá em "Cadastrar por Foto"
3. Tire uma foto de um produto
4. Deve funcionar usando o OpenMind AI!

**Ou verifique nos logs:**
```bash
railway logs
```

Procure por mensagens relacionadas ao OpenMind AI ou erros de conexão.

---

## 📝 Resumo

### Desenvolvimento Local
- ✅ Use o arquivo `.env` na sua máquina
- ✅ Configure as variáveis lá

### Produção (Railway)
- ✅ Configure no painel do Railway
- ✅ O `.env` não é usado
- ✅ Variáveis do Railway têm prioridade

### Ambas funcionam!
O código já está preparado para ler as variáveis de ambiente usando `decouple.config()`, então funciona tanto local quanto no Railway. 🎉

---

## 🔐 Segurança

- ✅ Variáveis no Railway são criptografadas
- ✅ Não ficam expostas no código
- ✅ Apenas você/equipe tem acesso
- ✅ Podem ser alteradas facilmente sem mexer no código

---

**Pronto! Quando fizer o deploy, é só adicionar essas variáveis no Railway!** 🚀
