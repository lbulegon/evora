# 📱 Guia: Conectar WhatsApp ao Évora

## 🎯 Objetivo

Conectar seu celular WhatsApp ao sistema Évora para receber e enviar mensagens automaticamente.

---

## 📋 Pré-requisitos

1. **Evolution API rodando**
   ```bash
   cd /root/MCP_SinapUm/services/evolution_api
   docker compose ps  # Verificar se está rodando
   docker compose up -d  # Se não estiver, subir
   ```

2. **Django Évora rodando**
   ```bash
   cd /root/evora
   python manage.py runserver 0.0.0.0:8001  # Ou como estiver configurado
   ```

---

## 🚀 Passo a Passo

### 1. Verificar Evolution API

```bash
cd /root/evora
python verificar_whatsapp.py
```

Isso mostra o status atual da instância WhatsApp.

### 2. Conectar WhatsApp

```bash
cd /root/evora
python conectar_whatsapp.py
```

Este script irá:
- ✅ Verificar se Evolution API está rodando
- ✅ Criar instância WhatsApp (se não existir)
- ✅ Gerar QR Code para conectar celular
- ✅ Configurar webhook para receber mensagens no Django

### 3. Escanear QR Code

1. O script gerará um arquivo HTML com o QR Code em `/tmp/qrcode_default.html`
2. Abra o arquivo no navegador:
   ```bash
   # No servidor (se tiver interface gráfica)
   xdg-open /tmp/qrcode_default.html
   
   # Ou copie o arquivo para sua máquina local e abra
   # Ou acesse a URL do QR Code que será exibida
   ```

3. Abra o WhatsApp no seu celular
4. Vá em **Configurações > Aparelhos conectados > Conectar um aparelho**
5. Escaneie o QR Code exibido

### 4. Aguardar Conexão

Após escanear, aguarde alguns segundos. O status mudará para `open` quando conectado.

Verifique o status:
```bash
python verificar_whatsapp.py
```

### 5. Testar Recebimento

Envie uma mensagem de teste para o número conectado. A mensagem deve:
- ✅ Chegar no Django via webhook
- ✅ Ser processada pelo `WhatsAppFlowEngine`
- ✅ Aparecer nos logs do Django

---

## 🔧 Configuração do Webhook

O webhook já está configurado automaticamente pelo script para:
```
http://69.169.102.84:8001/api/whatsapp/webhook/evolution/
```

**Importante:** Se o Django estiver em outra URL, edite a variável `DJANGO_WEBHOOK_URL` no arquivo `conectar_whatsapp.py`.

---

## 📊 Verificar Status

```bash
python verificar_whatsapp.py
```

Status possíveis:
- `open` - ✅ Conectado e funcionando
- `close` - ❌ Desconectado (precisa reconectar)
- `connecting` - 🔄 Conectando...
- `unpaired` - ⚠️ Precisa escanear QR Code novamente

---

## 🔄 Reconectar WhatsApp

Se o WhatsApp desconectar:

1. Execute novamente:
   ```bash
   python conectar_whatsapp.py
   ```

2. Escaneie o novo QR Code

3. Verifique o status:
   ```bash
   python verificar_whatsapp.py
   ```

---

## 🐛 Troubleshooting

### Evolution API não está rodando

```bash
cd /root/MCP_SinapUm/services/evolution_api
docker compose up -d
docker compose logs -f evolution_api
```

### QR Code não aparece

- Verifique se a instância foi criada
- Tente deletar e criar novamente
- Verifique logs da Evolution API

### Mensagens não chegam no Django

1. Verifique se o webhook está configurado:
   ```bash
   # Verificar logs do Django
   tail -f /var/log/django/whatsapp.log  # ou onde estiver configurado
   ```

2. Verifique se a URL do webhook está acessível:
   ```bash
   curl http://69.169.102.84:8001/api/whatsapp/webhook/evolution/
   ```

3. Verifique logs da Evolution API:
   ```bash
   cd /root/MCP_SinapUm/services/evolution_api
   docker compose logs evolution_api | grep webhook
   ```

### Instância já existe mas não conecta

Você pode deletar a instância e criar novamente via API da Evolution API ou pelo script.

---

## 📝 Variáveis de Ambiente

As seguintes variáveis são usadas (já configuradas em `setup/settings.py`):

```python
EVOLUTION_API_URL = "http://69.169.102.84:8004"
EVOLUTION_API_KEY = "GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg"
EVOLUTION_INSTANCE_NAME = "default"
```

---

## ✅ Checklist de Conectividade

- [ ] Evolution API está rodando
- [ ] Django está rodando
- [ ] Instância WhatsApp criada
- [ ] QR Code escaneado
- [ ] Status = `open`
- [ ] Webhook configurado
- [ ] Mensagem de teste recebida no Django

---

## 🎉 Pronto!

Quando tudo estiver conectado, o sistema está pronto para:
- ✅ Receber mensagens do WhatsApp
- ✅ Processar fluxo conversacional
- ✅ Enviar respostas automáticas
- ✅ Gerenciar grupos e conversas privadas
- ✅ Criar pedidos via WhatsApp

---

**Última atualização:** 21/12/2025

