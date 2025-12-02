# ⚡ Deploy Rápido - OpenMind AI Server

## 🚀 Comandos Prontos para Copiar e Colar

---

## 📤 PASSO 1: Transferir Arquivos (No seu computador)

Abra PowerShell e execute:

```powershell
cd C:\Users\lbule\OneDrive\Documentos\Source\evora
scp -r openmind-ai-server/* root@69.169.102.84:/opt/openmind-ai/
```

**Digite a senha quando solicitado.**

---

## 📥 PASSO 2: Deploy no Servidor (No servidor SinapUm)

Conecte-se ao servidor:

```bash
ssh root@69.169.102.84
```

Depois execute este bloco completo de comandos:

```bash
# Ir para o diretório
mkdir -p /opt/openmind-ai && cd /opt/openmind-ai

# Instalar dependências
apt update && apt install -y python3 python3-pip python3-venv git curl wget

# Ambiente virtual
python3 -m venv venv && source venv/bin/activate

# Dependências Python
pip install --upgrade pip && pip install -r requirements.txt

# Criar .env
cat > .env << 'EOF'
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
RATE_LIMIT_PER_MINUTE=100
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=jpeg,jpg,png,webp
IMAGE_MAX_DIMENSION=2048
LOG_LEVEL=INFO
CORS_ORIGINS=*
EOF

# Criar logs
mkdir -p /var/log/openmind-ai && chmod 755 /var/log/openmind-ai

# Criar serviço systemd
cat > /etc/systemd/system/openmind-ai.service << 'EOF'
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Ativar serviço
systemctl daemon-reload
systemctl enable openmind-ai
systemctl start openmind-ai

# Configurar firewall
ufw allow 8000/tcp 2>/dev/null || echo "Firewall já configurado ou não disponível"

# Testar
curl http://localhost:8000/health
```

---

## ✅ PASSO 3: Verificar se Funcionou

```bash
# Ver status do serviço
systemctl status openmind-ai

# Ver logs em tempo real
journalctl -u openmind-ai -f
```

**Deve mostrar:** `{"status":"healthy","version":"1.0.0","service":"OpenMind AI Server"}`

---

## 🧪 PASSO 4: Testar do Seu Computador

No PowerShell do seu computador:

```powershell
curl http://69.169.102.84:8000/health
```

Deve retornar a resposta JSON de health check.

---

## 🎉 Pronto!

Acesse a documentação da API:
- **Swagger UI:** http://69.169.102.84:8000/docs
- **Health Check:** http://69.169.102.84:8000/health

---

## 📝 Próximo Passo: Configurar no ÉVORA

Verifique se o `.env` do ÉVORA tem:

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

Depois teste o cadastro por foto no ÉVORA! 🚀
