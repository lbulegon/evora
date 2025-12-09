#!/bin/bash
# Script de Deploy Rápido para SinapUm
# Executa todos os passos necessários para atualizar o servidor

set -e  # Parar em caso de erro

echo "🚀 Deploy Rápido - OpenMind AI Server"
echo "======================================"
echo ""

# Verificar se estamos no diretório correto
if [ ! -d "app" ]; then
    echo "❌ Erro: Execute este script dentro de /opt/openmind-ai"
    exit 1
fi

# Diretório atual
CURRENT_DIR=$(pwd)
echo "📁 Diretório: $CURRENT_DIR"
echo ""

# Fazer backup
echo "💾 Fazendo backup do código atual..."
BACKUP_DIR="app.backup.$(date +%Y%m%d_%H%M%S)"
if [ -d "app" ]; then
    cp -r app "$BACKUP_DIR"
    echo "✅ Backup criado: $BACKUP_DIR"
else
    echo "⚠️  Pasta app não encontrada, pulando backup"
fi
echo ""

# Ativar ambiente virtual
echo "🐍 Ativando ambiente virtual..."
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "   Execute: python3 -m venv venv"
    exit 1
fi

source venv/bin/activate
echo "✅ Ambiente virtual ativado"
echo ""

# Atualizar dependências
echo "📚 Atualizando dependências Python..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependências atualizadas"
echo ""

# Criar diretório de logs
echo "📝 Configurando diretório de logs..."
mkdir -p /var/log/openmind-ai
chmod 755 /var/log/openmind-ai
echo "✅ Diretório de logs configurado: /var/log/openmind-ai"
echo ""

# Verificar variáveis de ambiente
echo "⚙️  Verificando variáveis de ambiente..."
if [ -f ".env" ]; then
    if grep -q "LOG_FORMAT" .env; then
        echo "✅ Variáveis de logging já configuradas"
    else
        echo "📝 Adicionando variáveis de logging opcionais..."
        echo "" >> .env
        echo "# Logging - Grafana/Loki (Opcional)" >> .env
        echo "LOG_FORMAT=json" >> .env
        echo "LOG_DIR=/var/log/openmind-ai" >> .env
        echo "✅ Variáveis de logging adicionadas"
    fi
else
    echo "⚠️  Arquivo .env não encontrado!"
    echo "   Criando a partir de ENV_EXAMPLE.txt..."
    if [ -f "ENV_EXAMPLE.txt" ]; then
        cp ENV_EXAMPLE.txt .env
        echo "⚠️  IMPORTANTE: Configure o arquivo .env antes de iniciar!"
        echo "   nano .env"
    fi
fi
echo ""

# Testar importações
echo "🧪 Testando importações..."
if python3 -c "from app.main import app; print('✅ Importações OK')" 2>/dev/null; then
    echo "✅ Importações OK"
else
    echo "❌ Erro nas importações!"
    echo "   Verifique os erros acima"
    exit 1
fi
echo ""

# Reiniciar serviço
echo "🔄 Reiniciando serviço..."
if systemctl is-active --quiet openmind-ai; then
    systemctl restart openmind-ai
    sleep 2
    
    if systemctl is-active --quiet openmind-ai; then
        echo "✅ Serviço reiniciado com sucesso"
    else
        echo "❌ Erro ao reiniciar serviço!"
        echo "   Verifique os logs: journalctl -u openmind-ai -n 50"
        exit 1
    fi
else
    echo "⚠️  Serviço não está rodando. Iniciando..."
    systemctl start openmind-ai
    sleep 2
    
    if systemctl is-active --quiet openmind-ai; then
        echo "✅ Serviço iniciado com sucesso"
    else
        echo "❌ Erro ao iniciar serviço!"
        echo "   Verifique os logs: journalctl -u openmind-ai -n 50"
        exit 1
    fi
fi
echo ""

# Mostrar status
echo "📊 Status do serviço:"
systemctl status openmind-ai --no-pager -l | head -15
echo ""

# Verificar logs
echo "📋 Verificando logs..."
if [ -f "/var/log/openmind-ai/app.log" ]; then
    echo "✅ Logs sendo gerados:"
    tail -3 /var/log/openmind-ai/app.log
else
    echo "⚠️  Arquivo de log ainda não foi criado (será criado no primeiro uso)"
fi
echo ""

# Testar health check
echo "🧪 Testando health check..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Servidor respondendo corretamente!"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "⚠️  Servidor pode não estar respondendo ainda"
    echo "   Aguarde alguns segundos e tente: curl http://localhost:8000/health"
fi
echo ""

echo "======================================"
echo "✅ Deploy concluído com sucesso!"
echo ""
echo "📚 Próximos passos:"
echo "   - Ver logs: tail -f /var/log/openmind-ai/app.log"
echo "   - Ver status: systemctl status openmind-ai"
echo "   - Testar API: curl http://localhost:8000/health"
echo "   - Configurar Grafana: Ver GRAFANA_SETUP.md"
echo ""



