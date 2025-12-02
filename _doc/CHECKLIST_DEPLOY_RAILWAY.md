# ✅ Checklist - Deploy ÉVORA no Railway com OpenMind AI

Checklist completo para garantir que tudo funcione no Railway.

---

## 📋 Antes do Deploy

### 1. Servidor OpenMind AI
- [x] Servidor rodando no SinapUm (69.169.102.84:8000)
- [x] Health check funcionando
- [x] API acessível externamente

### 2. Código ÉVORA
- [x] Código atualizado para usar OpenMind AI
- [x] Variáveis de ambiente configuradas no código
- [x] `.env` local configurado para testes

---

## 🚀 Durante o Deploy no Railway

### 3. Configurar Variáveis de Ambiente

Adicione estas variáveis no painel do Railway:

- [ ] `AI_SERVICE` = `openmind`
- [ ] `OPENMIND_AI_URL` = `http://69.169.102.84:8000/api/v1`
- [ ] `OPENMIND_AI_KEY` = `om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1`
- [ ] `OPENMIND_AI_TIMEOUT` = `30` (opcional)

### 4. Outras Variáveis do Railway

Certifique-se de ter também:
- [ ] `SECRET_KEY` (Django)
- [ ] `DATABASE_URL` (Railway preenche automaticamente)
- [ ] `ALLOWED_HOSTS` (se necessário)
- [ ] Outras variáveis específicas do seu projeto

---

## ✅ Após o Deploy

### 5. Verificar Deploy
- [ ] Deploy concluído sem erros
- [ ] Aplicação rodando
- [ ] Health check do Railway OK

### 6. Testar Integração
- [ ] Acessar o ÉVORA no Railway
- [ ] Ir em "Cadastrar por Foto"
- [ ] Tirar foto de um produto
- [ ] Verificar se a análise funciona
- [ ] Verificar se dados são extraídos corretamente

### 7. Verificar Logs
- [ ] Sem erros de conexão com OpenMind AI
- [ ] Sem erros de autenticação
- [ ] Respostas da API corretas

---

## 🐛 Troubleshooting

### Se não funcionar:

1. **Verificar variáveis:**
   ```bash
   railway variables
   ```

2. **Ver logs:**
   ```bash
   railway logs
   ```

3. **Testar servidor OpenMind AI:**
   ```bash
   curl http://69.169.102.84:8000/health
   ```

4. **Verificar conectividade:**
   - O Railway consegue acessar o servidor SinapUm?
   - Firewall do SinapUm permite conexões externas?

---

## 📝 Checklist Rápido

**No Railway:**
- [ ] Variáveis configuradas
- [ ] Deploy feito
- [ ] Aplicação rodando

**Testar:**
- [ ] Cadastro por foto funciona
- [ ] Análise de imagem funciona
- [ ] Dados extraídos corretamente

**Pronto!** 🎉
