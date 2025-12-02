# Guia de Deploy - OpenMind AI no SinapUm

Guia passo a passo para deploy do servidor OpenMind AI no servidor SinapUm.

---

## 📋 Pré-requisitos

- Acesso SSH ao servidor SinapUm (`ssh root@69.169.102.84`)
- Python 3.8 ou superior
- Conexão com internet para instalar dependências

---

## 🚀 Passo a Passo

### 1. Conectar ao Servidor

```bash
ssh root@69.169.102.84
# Senha: (ver arquivo .env)
```

### 2. Instalar Dependências do Sistema

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl wget
```

### 3. Criar Diretório do Projeto

```bash
mkdir -p /opt/openmind-ai
cd /opt/openmind-ai
```

### 4. Transferir Código para o Servidor

**Opção A: Via Git (recomendado)**
```bash
git clone <seu-repositorio> .
```

**Opção B: Via SCP (do seu computador local)**
```bash
# No seu computador local:
scp -r openmind-ai-server/* root@69.169.102.84:/opt/openmind-ai/
```

**Opção C: Criar arquivos manualmente**
```bash
# Criar estrutura e arquivos conforme documentação
```

### 5. Criar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. Instalar Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
nano .env
```

Configure pelo menos:
```bash
OPENMIND_AI_API_KEY=gerar-uma-chave-secreta-aqui
OPENAI_API_KEY=sk-sua-chave-openai  # Se usar OpenAI
```

**Gerar API Key segura:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 8. Testar Servidor

```bash
# Iniciar em modo desenvolvimento
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Testar em outro terminal:
```bash
# Health check
curl http://localhost:8000/health

# Teste de análise (precisa de uma imagem)
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "image=@/caminho/para/imagem.jpg"
```

### 9. Criar Serviço Systemd (Produção)

```bash
nano /etc/systemd/system/openmind-ai.service
```

Conteúdo:
```ini
[Unit]
Description=OpenMind AI Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/openmind-ai
Environment="PATH=/opt/openmind-ai/venv/bin"
ExecStart=/opt/openmind-ai/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
systemctl daemon-reload
systemctl enable openmind-ai
systemctl start openmind-ai
systemctl status openmind-ai
```

### 10. Configurar Firewall

```bash
# Permitir porta 8000
ufw allow 8000/tcp
ufw reload
```

### 11. Configurar Nginx (Opcional, para HTTPS)

```bash
apt install -y nginx certbot python3-certbot-nginx

nano /etc/nginx/sites-available/openmind-ai
```

Conteúdo:
```nginx
server {
    listen 80;
    server_name sinapum.com;  # ou IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar:
```bash
ln -s /etc/nginx/sites-available/openmind-ai /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 12. Configurar SSL (Opcional)

```bash
certbot --nginx -d sinapum.com
```

---

## ✅ Verificação

### Testar do ÉVORA

No arquivo `.env` do ÉVORA:
```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=sua-api-key
```

Testar cadastro de produto por foto no ÉVORA.

---

## 📊 Logs

```bash
# Ver logs do serviço
journalctl -u openmind-ai -f

# Ver logs da aplicação (se configurado)
tail -f /var/log/openmind-ai/server.log
```

---

## 🔧 Comandos Úteis

```bash
# Reiniciar serviço
systemctl restart openmind-ai

# Parar serviço
systemctl stop openmind-ai

# Ver status
systemctl status openmind-ai

# Atualizar código
cd /opt/openmind-ai
git pull  # ou transferir novos arquivos
systemctl restart openmind-ai
```

---

## 🐛 Troubleshooting

### Serviço não inicia
```bash
journalctl -u openmind-ai -n 50
```

### Porta já em uso
```bash
lsof -i :8000
kill -9 <PID>
```

### Erro de permissões
```bash
chown -R root:root /opt/openmind-ai
chmod +x /opt/openmind-ai/run.sh
```

---

**Pronto para produção!** 🚀
