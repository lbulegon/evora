# 🧪 Teste de Configuração - OpenMind AI

## ✅ Checklist Antes de Testar

- [ ] .env local criado com as 5 variáveis
- [ ] Servidor SinapUm configurado com as 3 variáveis
- [ ] Railway configurado com as 5 variáveis
- [ ] Serviço OpenMind AI rodando no SinapUm

---

## 🧪 TESTE 1: Verificar Servidor SinapUm

### 1.1 Health Check

```bash
curl http://69.169.102.84:8000/health
```

**Esperado:** `{"status": "healthy", "service": "OpenMind AI Server"}`

### 1.2 Verificar Logs do Servidor

```bash
ssh root@69.169.102.84
journalctl -u openmind-ai -n 20
```

**Esperado:** Serviço rodando sem erros

---

## 🧪 TESTE 2: Testar Análise de Imagem

### 2.1 Teste Direto no Servidor SinapUm

```bash
curl -X POST http://69.169.102.84:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" \
  -F "image=@/caminho/para/sua/imagem.jpg"
```

**Esperado:** JSON com dados do produto extraídos

---

## 🧪 TESTE 3: Testar no ÉVORA Local

### 3.1 Verificar Variáveis

```bash
# No projeto ÉVORA
python manage.py shell

# No shell do Django:
import os
from django.conf import settings

print("AI_SERVICE:", settings.AI_SERVICE)
print("OPENMIND_AI_URL:", settings.OPENMIND_AI_URL)
print("OPENMIND_AI_KEY:", settings.OPENMIND_AI_KEY[:20] + "...")
print("OPENMIND_ORG_MODEL:", settings.OPENMIND_ORG_MODEL)
```

**Esperado:** Todas as variáveis mostradas corretamente

### 3.2 Testar Upload de Foto no ÉVORA

1. Iniciar servidor local:
   ```bash
   python manage.py runserver
   ```

2. Acessar: http://localhost:8000/products/cadastrar-por-foto/

3. Tirar/fazer upload de uma foto de produto

4. Verificar se analisa corretamente

**Esperado:** Produto analisado e dados preenchidos automaticamente

---

## 🧪 TESTE 4: Testar no Railway

1. Acessar: https://evora-product.up.railway.app/products/cadastrar-por-foto/

2. Fazer upload de uma foto

3. Verificar análise

**Esperado:** Funciona igual ao local

---

## 🔍 Verificar Logs

### Logs do ÉVORA (Railway)

Ver logs no Railway Dashboard para ver se há erros de conexão.

### Logs do Servidor SinapUm

```bash
ssh root@69.169.102.84
journalctl -u openmind-ai -f
```

**Durante o teste:** Ver se mostra requisições chegando e análise sendo feita.

---

## ❌ Possíveis Problemas

### Erro 401 (Unauthorized)
- Verificar se `OPENMIND_AI_KEY` está correto
- Verificar se chave no servidor SinapUm está correta

### Erro de Conexão
- Verificar se servidor SinapUm está rodando: `systemctl status openmind-ai`
- Verificar se porta 8000 está aberta

### Erro "OpenMind.org não configurado"
- Verificar se `OPENMIND_ORG_BASE_URL` está no .env do servidor
- Verificar se `OPENMIND_ORG_MODEL` está configurado

---

## ✅ Próximos Passos

Se tudo funcionar:
1. ✅ Configuração completa e funcionando!
2. ✅ Servidor usando OpenMind.org que você já pagou
3. ✅ Pronto para produção!

**Vamos testar agora?** 🚀
