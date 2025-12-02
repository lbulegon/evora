# 🚀 Guia Completo de Deploy - OpenMind AI no SinapUm

Guia passo a passo completo para deploy do servidor OpenMind AI no servidor SinapUm.

---

## 📋 Pré-requisitos

- Acesso SSH ao servidor SinapUm
- Python 3.8+ (será instalado automaticamente)
- Conexão com internet

---

## 🎯 Opção 1: Deploy Automatizado (Recomendado)

### No Servidor SinapUm:

```bash
# 1. Conectar ao servidor
ssh root@69.169.102.84

# 2. Ir para o diretório do projeto (após transferir arquivos)
cd /opt/openmind-ai

# 3. Dar permissão de execução ao script
chmod +x deploy_step_by_step.sh

# 4. Executar script de deploy
bash deploy_step_by_step.sh
```

O script fará tudo automaticamente:
- ✅ Instalar dependências do sistema
- ✅ Criar ambiente virtual
- ✅ Instalar dependências Python
- ✅ Configurar arquivo .env
- ✅ Criar serviço systemd
- ✅ Configurar firewall

---

## 📦 Opção 2: Deploy Manual (Passo a Passo)

### Passo 1: Transferir Arquivos para o Servidor

**Do seu computador local:**

```bash
# No PowerShell (Windows) ou Terminal (Mac/Linux)
cd C:\Users\lbule\OneDrive\Documentos\Source\evora

# Transferir todos os arquivos
scp -r openmind-ai-server/* root@69.169.102.84:/opt/openmind-ai/
```

**Ou criar diretório e arquivos manualmente no servidor**

### Passo 2: Conectar ao Servidor

```bash
ssh root@69.169.102.84
# Senha: (ver arquivo .env)
```

### Passo 3: Instalar Dependências do Sistema

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl wget
```

### Passo 4: Criar Estrutura do Projeto

```bash
mkdir -p /opt/openmind-ai
cd /opt/openmind-ai
```

**Se os arquivos já foram transferidos via SCP, pule para o Passo 5.**

### Passo 5: Criar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### Passo 6: Instalar Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Se o `requirements.txt` não estiver disponível, instale manualmente:

```bash
pip install fastapi uvicorn python-multipart pillow requests \
    pydantic pydantic-settings python-dotenv openai
```

### Passo 7: Configurar Arquivo .env

```bash
nano .env
```

Cole o seguinte conteúdo:

```bash
# OpenMind AI Server - Configuração
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000

# IA Backend (OpenAI temporário)
OPENAI_API_KEY=sk-sua-chave-openai-aqui
OPENAI_MODEL=gpt-4o

# Configurações
RATE_LIMIT_PER_MINUTE=100
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=jpeg,jpg,png,webp
IMAGE_MAX_DIMENSION=2048
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

Salve com `Ctrl+O`, `Enter`, `Ctrl+X`

### Passo 8: Testar Servidor

```bash
# Ativar ambiente virtual (se não estiver ativo)
source venv/bin/activate

# Iniciar servidor em modo desenvolvimento
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Em outro terminal, testar:**

```bash
# Health check
curl http://localhost:8000/health

# Deve retornar:
# {"status":"healthy","version":"1.0.0","service":"OpenMind AI Server"}
```

Se funcionar, pare o servidor com `Ctrl+C`.

### Passo 9: Criar Serviço Systemd (Produção)

```bash
nano /etc/systemd/system/openmind-ai.service
```

Cole o seguinte conteúdo:

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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Salve e ative o serviço:

```bash
systemctl daemon-reload
systemctl enable openmind-ai
systemctl start openmind-ai
systemctl status openmind-ai
```

### Passo 10: Configurar Firewall

```bash
# Instalar UFW se não estiver instalado
apt install -y ufw

# Permitir porta 8000
ufw allow 8000/tcp
ufw reload

# Verificar status
ufw status
```

---

## ✅ Verificação Final

### 1. Verificar se o serviço está rodando

```bash
systemctl status openmind-ai
```

### 2. Testar health check

```bash
curl http://localhost:8000/health
```

### 3. Testar análise de imagem

```bash
# Baixar uma imagem de teste (ou usar uma local)
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" \
  -F "image=@/caminho/para/imagem.jpg"
```

### 4. Testar do ÉVORA

No arquivo `.env` do ÉVORA, configure:

```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

Depois teste o cadastro de produto por foto no ÉVORA!

---

## 📊 Logs e Monitoramento

### Ver logs do serviço

```bash
# Logs em tempo real
journalctl -u openmind-ai -f

# Últimas 50 linhas
journalctl -u openmind-ai -n 50

# Logs de hoje
journalctl -u openmind-ai --since today
```

### Verificar se o servidor está acessível externamente

```bash
# De outro computador
curl http://69.169.102.84:8000/health
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

# Ver logs
journalctl -u openmind-ai -f

# Atualizar código (após git pull ou transferir novos arquivos)
cd /opt/openmind-ai
source venv/bin/activate
pip install -r requirements.txt  # Se houver novas dependências
systemctl restart openmind-ai
```

---

## 🐛 Troubleshooting

### Serviço não inicia

```bash
# Ver logs de erro
journalctl -u openmind-ai -n 100

# Verificar sintaxe do arquivo .env
cd /opt/openmind-ai
source venv/bin/activate
python3 -c "from app.core.config import settings; print('Config OK')"
```

### Porta já em uso

```bash
# Ver qual processo está usando a porta
lsof -i :8000

# Parar processo (substituir PID)
kill -9 <PID>
```

### Erro de importação

```bash
# Verificar se todas as dependências estão instaladas
cd /opt/openmind-ai
source venv/bin/activate
pip install -r requirements.txt
```

### Erro de permissões

```bash
chown -R root:root /opt/openmind-ai
chmod +x /opt/openmind-ai/run.sh
```

---

## 🎉 Pronto!

O servidor OpenMind AI está rodando e pronto para receber requisições do ÉVORA!

**Documentação da API:** http://69.169.102.84:8000/docs

**Health Check:** http://69.169.102.84:8000/health

---

**Vamos fazer o deploy agora! 🚀**
