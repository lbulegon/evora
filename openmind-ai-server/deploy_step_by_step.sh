#!/bin/bash
# Script passo a passo interativo para deploy no SinapUm
# Execute no servidor: bash deploy_step_by_step.sh

echo "🚀 Deploy do OpenMind AI Server - Passo a Passo"
echo "=================================================="
echo ""

# Passo 1: Atualizar sistema
echo "📦 PASSO 1: Atualizando sistema..."
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl wget

# Passo 2: Criar diretório
echo ""
echo "📁 PASSO 2: Criando diretório do projeto..."
mkdir -p /opt/openmind-ai
cd /opt/openmind-ai

# Passo 3: Ambiente virtual
echo ""
echo "🐍 PASSO 3: Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Ambiente virtual criado"
else
    echo "✅ Ambiente virtual já existe"
fi

source venv/bin/activate

# Passo 4: Instalar dependências
echo ""
echo "📚 PASSO 4: Instalando dependências Python..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependências instaladas"
else
    echo "⚠️  requirements.txt não encontrado. Instalando dependências básicas..."
    pip install fastapi uvicorn python-multipart pillow requests pydantic pydantic-settings python-dotenv openai
fi

# Passo 5: Configurar .env
echo ""
echo "⚙️  PASSO 5: Configurando variáveis de ambiente..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# OpenMind AI Server - Configuração
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000

# IA Backend
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# Configurações
RATE_LIMIT_PER_MINUTE=100
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=jpeg,jpg,png,webp
IMAGE_MAX_DIMENSION=2048
LOG_LEVEL=INFO
CORS_ORIGINS=*
EOF
    echo "✅ Arquivo .env criado!"
    echo ""
    echo "⚠️  IMPORTANTE: Configure OPENAI_API_KEY no arquivo .env se usar OpenAI"
    echo "   nano .env"
else
    echo "✅ Arquivo .env já existe"
fi

# Passo 6: Criar diretório de logs
echo ""
echo "📝 PASSO 6: Criando diretório de logs..."
mkdir -p /var/log/openmind-ai
chmod 755 /var/log/openmind-ai

# Passo 7: Criar estrutura de arquivos se não existir
echo ""
echo "📋 PASSO 7: Verificando estrutura de arquivos..."

if [ ! -d "app" ]; then
    echo "⚠️  Diretório 'app' não encontrado!"
    echo "   Certifique-se de que todos os arquivos foram transferidos para /opt/openmind-ai/"
    echo "   Você pode copiar do diretório local ou criar manualmente."
    exit 1
fi

# Passo 8: Testar servidor
echo ""
echo "🧪 PASSO 8: Testando servidor..."
python3 -c "from app.main import app; print('✅ Servidor OK')" 2>&1 || {
    echo "❌ Erro ao testar servidor. Verifique os arquivos."
    exit 1
}

# Passo 9: Criar serviço systemd
echo ""
echo "🔧 PASSO 9: Criando serviço systemd..."
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

systemctl daemon-reload
echo "✅ Serviço systemd criado"

# Passo 10: Configurar firewall
echo ""
echo "🔥 PASSO 10: Configurando firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 8000/tcp
    echo "✅ Porta 8000 liberada no firewall"
else
    echo "⚠️  UFW não instalado. Configure manualmente se necessário."
fi

# Resumo
echo ""
echo "=================================================="
echo "✅ DEPLOY CONCLUÍDO!"
echo "=================================================="
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Configure o .env se necessário:"
echo "   nano /opt/openmind-ai/.env"
echo ""
echo "2. Iniciar servidor manualmente (teste):"
echo "   cd /opt/openmind-ai"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "3. OU iniciar como serviço (produção):"
echo "   systemctl start openmind-ai"
echo "   systemctl enable openmind-ai"
echo "   systemctl status openmind-ai"
echo ""
echo "4. Testar:"
echo "   curl http://localhost:8000/health"
echo ""
echo "5. Documentação da API:"
echo "   http://69.169.102.84:8000/docs"
echo ""
echo "🎉 Pronto para usar!"
