# 🔧 Configurar Variáveis de Ambiente no Railway

Quando você fizer o deploy do ÉVORA para o Railway, precisa configurar as variáveis de ambiente **no painel do Railway**, não apenas no arquivo `.env` local.

---

## 📋 Por Que?

- **`.env` local:** Usado apenas para desenvolvimento na sua máquina
- **Railway:** Precisa das variáveis configuradas no painel para produção
- **Segurança:** O Railway não usa o arquivo `.env` do seu repositório (e nem deve, pois contém credenciais)

---

## ✅ Variáveis Necessárias para OpenMind AI no Railway

Quando fizer o deploy do ÉVORA no Railway, configure estas variáveis:

```bash
# Escolher serviço de IA
AI_SERVICE=openmind

# Configuração do OpenMind AI (servidor SinapUm)
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_TIMEOUT=30
```

---

## 🚀 Como Configurar no Railway

### Opção 1: Via Painel Web (Mais Fácil)

1. Acesse o painel do Railway: https://railway.app
2. Selecione seu projeto ÉVORA
3. Vá em **"Variables"** (ou **"Settings"** → **"Variables"**)
4. Clique em **"New Variable"**
5. Adicione cada variável:

   ```
   Nome: AI_SERVICE
   Valor: openmind
   ```

   ```
   Nome: OPENMIND_AI_URL
   Valor: http://69.169.102.84:8000/api/v1
   ```

   ```
   Nome: OPENMIND_AI_KEY
   Valor: om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
   ```

   ```
   Nome: OPENMIND_AI_TIMEOUT
   Valor: 30
   ```

6. Clique em **"Add"** para cada uma
7. O Railway vai fazer redeploy automaticamente

### Opção 2: Via CLI do Railway

```bash
# Instalar Railway CLI (se ainda não tiver)
npm i -g @railway/cli

# Login
railway login

# Vincular projeto
railway link

# Adicionar variáveis
railway variables set AI_SERVICE=openmind
railway variables set OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
railway variables set OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
railway variables set OPENMIND_AI_TIMEOUT=30

# Ver variáveis configuradas
railway variables
```

### Opção 3: Via arquivo `railway.json` ou `.env.example`

Você pode criar um arquivo de referência (mas **NÃO** commitar o `.env` real):

```json
// railway.json (opcional)
{
  "variables": {
    "AI_SERVICE": "openmind",
    "OPENMIND_AI_URL": "http://69.169.102.84:8000/api/v1",
    "OPENMIND_AI_TIMEOUT": "30"
  }
}
```

---

## 📝 Checklist para Deploy no Railway

- [ ] Configurar `AI_SERVICE=openmind` no Railway
- [ ] Configurar `OPENMIND_AI_URL` no Railway
- [ ] Configurar `OPENMIND_AI_KEY` no Railway
- [ ] Configurar `OPENMIND_AI_TIMEOUT` no Railway (opcional, padrão 30)
- [ ] Verificar se o servidor SinapUm está acessível do Railway
- [ ] Fazer deploy e testar

---

## 🔍 Verificar se Está Funcionando

Após configurar as variáveis e fazer o deploy:

1. Acesse o ÉVORA no Railway
2. Vá em "Cadastrar por Foto"
3. Tire uma foto de um produto
4. Verifique se a análise funciona

**Ou teste via logs do Railway:**
```bash
railway logs
```

---

## ⚠️ Importante

1. **NÃO commitar o `.env`** com credenciais reais no Git
2. O arquivo `.env` é apenas para desenvolvimento local
3. Em produção (Railway), use as variáveis de ambiente do painel
4. As variáveis do Railway têm prioridade sobre qualquer `.env`

---

## 🔐 Segurança

- ✅ Variáveis no Railway são criptografadas
- ✅ Apenas você tem acesso (ou sua equipe configurada)
- ✅ Não ficam expostas no código
- ✅ Podem ser rotacionadas facilmente

---

## 🎯 Resumo

**Desenvolvimento Local:**
- Use o arquivo `.env` local
- Configure as variáveis do OpenMind AI lá

**Produção (Railway):**
- Configure as variáveis no painel do Railway
- Não use o `.env` do repositório
- Railway vai ler as variáveis do painel

**Ambos funcionam da mesma forma, apenas em lugares diferentes!** ✅

---

**Pronto! Quando fizer o deploy, é só adicionar essas variáveis no Railway! 🚀**
