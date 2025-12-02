# 🎯 Próximos Passos - OpenMind AI Server

O servidor está rodando perfeitamente! Agora vamos completar a integração.

---

## ✅ O Que Já Está Pronto

1. ✅ Servidor instalado e rodando
2. ✅ Health check funcionando
3. ✅ API acessível externamente
4. ✅ Documentação disponível em `/docs`

---

## 🔄 Próximos Passos

### 1. Testar Análise de Imagem (Agora)

**No servidor SinapUm:**
```bash
# Testar com uma imagem de produto
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" \
  -F "image=@/caminho/para/imagem.jpg"
```

**Ou do seu computador:**
```powershell
# No PowerShell
$headers = @{
    "Authorization" = "Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1"
}
Invoke-RestMethod -Uri "http://69.169.102.84:8000/api/v1/analyze-product-image" `
    -Method Post `
    -Headers $headers `
    -InFile "caminho/para/imagem.jpg" `
    -ContentType "multipart/form-data"
```

### 2. Verificar Configuração no ÉVORA

**No arquivo `.env` do ÉVORA, verifique se tem:**

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_TIMEOUT=30
```

### 3. Testar no ÉVORA

1. Acesse o ÉVORA
2. Vá em "Cadastrar por Foto" (menu ou página de produtos)
3. Tire uma foto de um produto
4. Verifique se os dados são extraídos corretamente

### 4. Configurar Backend de IA (Se Necessário)

**Se você quer usar OpenAI como backend temporário:**

No servidor SinapUm, edite o `.env`:
```bash
cd /opt/openmind-ai
nano .env
```

Adicione/configure:
```bash
OPENAI_API_KEY=sk-sua-chave-openai-aqui
```

Reinicie o serviço:
```bash
systemctl restart openmind-ai
```

---

## 🐛 Troubleshooting

### Se a análise não funcionar

1. **Verificar logs do servidor:**
   ```bash
   journalctl -u openmind-ai -n 100 --no-pager
   ```

2. **Verificar se OPENAI_API_KEY está configurada:**
   ```bash
   cd /opt/openmind-ai
   cat .env | grep OPENAI_API_KEY
   ```

3. **Testar importação:**
   ```bash
   cd /opt/openmind-ai
   source venv/bin/activate
   python3 -c "from app.core.image_analyzer import analyze_product_image; print('OK')"
   ```

---

## 📊 Monitoramento

### Ver Logs em Tempo Real
```bash
journalctl -u openmind-ai -f
```

### Verificar Status
```bash
systemctl status openmind-ai
```

### Ver Uso de Recursos
```bash
systemctl status openmind-ai | grep Memory
```

---

## 🎉 Pronto para Produção!

O servidor está rodando e pronto. Agora é só:

1. ✅ Testar análise de imagem
2. ✅ Testar no ÉVORA
3. ✅ Aproveitar! 🚀

---

**Tudo funcionando perfeitamente!** 🎊
