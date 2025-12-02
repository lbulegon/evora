#!/bin/bash
# Script para corrigir problemas encontrados durante o deploy

echo "🔧 Corrigindo problemas do deploy..."

cd /opt/openmind-ai
source venv/bin/activate

# 1. Corrigir requirements.txt (remover python-cors que não existe)
echo "📝 Corrigindo requirements.txt..."
sed -i '/python-cors/d' requirements.txt

# 2. Reinstalar dependências
echo "📦 Reinstalando dependências..."
pip install -r requirements.txt

# 3. Verificar se os arquivos do app existem
echo "📁 Verificando arquivos..."
if [ ! -d "app" ]; then
    echo "❌ ERRO: Diretório 'app' não encontrado!"
    echo "   Você precisa transferir os arquivos do servidor primeiro."
    echo "   Execute no seu computador:"
    echo "   scp -r openmind-ai-server/* root@69.169.102.84:/opt/openmind-ai/"
    exit 1
fi

# 4. Testar importação
echo "🧪 Testando importações..."
python3 -c "from app.main import app; print('✅ Importações OK')" 2>&1 || {
    echo "❌ Erro ao importar. Verificando logs..."
    exit 1
}

# 5. Verificar logs do serviço
echo "📋 Verificando logs do serviço..."
journalctl -u openmind-ai -n 50 --no-pager

# 6. Reiniciar serviço
echo "🔄 Reiniciando serviço..."
systemctl restart openmind-ai
sleep 2

# 7. Verificar status
echo "📊 Status do serviço:"
systemctl status openmind-ai --no-pager -l

# 8. Testar health check
echo ""
echo "🏥 Testando health check..."
curl -s http://localhost:8000/health || echo "❌ Serviço ainda não está respondendo. Veja os logs acima."
