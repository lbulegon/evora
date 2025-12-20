#!/bin/bash
# Script de Deploy do Agente Ágnosto - SinapUm
# Uso: ./SCRIPT_DEPLOY_AGENTE.sh

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do Agente Ágnosto no SinapUm..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está no diretório correto
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}❌ Erro: Execute este script no diretório openmind-ai-server${NC}"
    exit 1
fi

# Verificar se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Ambiente virtual não encontrado. Criando...${NC}"
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "📦 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar/atualizar dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar se arquivos do agente existem
echo "🔍 Verificando arquivos do agente..."

if [ ! -f "app/core/agnostic_agent.py" ]; then
    echo -e "${RED}❌ Erro: app/core/agnostic_agent.py não encontrado${NC}"
    exit 1
fi

if [ ! -f "app/api/v1/endpoints/agent.py" ]; then
    echo -e "${RED}❌ Erro: app/api/v1/endpoints/agent.py não encontrado${NC}"
    exit 1
fi

# Verificar se main.py tem a rota do agente
echo "🔍 Verificando configuração do main.py..."
if ! grep -q "from app.api.v1.endpoints import analyze, agent" app/main.py; then
    echo -e "${YELLOW}⚠️  Adicionando import do agente em app/main.py...${NC}"
    # Backup
    cp app/main.py app/main.py.bak
    
    # Adicionar import (se não existir)
    if ! grep -q "from app.api.v1.endpoints import agent" app/main.py; then
        sed -i 's/from app.api.v1.endpoints import analyze/from app.api.v1.endpoints import analyze, agent/' app/main.py
    fi
fi

if ! grep -q "app.include_router(agent.router" app/main.py; then
    echo -e "${YELLOW}⚠️  Adicionando rota do agente em app/main.py...${NC}"
    # Adicionar após a rota de analyze
    sed -i '/app.include_router(analyze.router,/,/tags=\["Análise"\]/a\
\
app.include_router(\
    agent.router,\
    prefix="/api/v1",\
    tags=["Agente"]\
)' app/main.py
fi

# Verificar variáveis de ambiente
echo "🔍 Verificando variáveis de ambiente..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado. Criando template...${NC}"
    cat > .env << EOF
OPENMIND_AI_API_KEY=sua-chave-secreta-aqui
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000
CORS_ORIGINS=http://localhost:8000
LOG_LEVEL=INFO
EOF
    echo -e "${YELLOW}⚠️  Configure OPENMIND_AI_API_KEY no arquivo .env${NC}"
fi

# Testar sintaxe Python
echo "🔍 Verificando sintaxe Python..."
python3 -m py_compile app/core/agnostic_agent.py
python3 -m py_compile app/api/v1/endpoints/agent.py
python3 -m py_compile app/main.py
echo -e "${GREEN}✅ Sintaxe Python OK${NC}"

# Verificar se servidor está rodando
echo "🔍 Verificando se servidor está rodando..."
if systemctl is-active --quiet openmind-ai 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Servidor está rodando. Reiniciando...${NC}"
    systemctl restart openmind-ai
    sleep 2
    systemctl status openmind-ai --no-pager -l
elif pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo -e "${YELLOW}⚠️  Processo uvicorn encontrado. Você precisa reiniciar manualmente.${NC}"
    echo "   Execute: pkill -f 'uvicorn.*app.main:app'"
    echo "   Depois: uvicorn app.main:app --host 0.0.0.0 --port 8000"
else
    echo -e "${GREEN}✅ Servidor não está rodando. Você pode iniciar com:${NC}"
    echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000"
fi

# Testar endpoints (se servidor estiver rodando)
echo ""
echo "🧪 Testando endpoints..."

# Aguardar servidor iniciar
sleep 3

# Teste 1: Health check
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check OK${NC}"
else
    echo -e "${YELLOW}⚠️  Health check falhou (servidor pode não estar rodando)${NC}"
fi

# Teste 2: Listar papéis (se API key estiver configurada)
API_KEY=$(grep OPENMIND_AI_API_KEY .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
if [ "$API_KEY" != "sua-chave-secreta-aqui" ] && [ ! -z "$API_KEY" ]; then
    if curl -s -H "Authorization: Bearer $API_KEY" http://localhost:8000/api/v1/agent/roles > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Endpoint /api/v1/agent/roles OK${NC}"
    else
        echo -e "${YELLOW}⚠️  Endpoint /api/v1/agent/roles falhou${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  API key não configurada. Configure OPENMIND_AI_API_KEY no .env${NC}"
fi

echo ""
echo -e "${GREEN}✅ Deploy concluído!${NC}"
echo ""
echo "📋 Próximos passos:"
echo "   1. Configure OPENMIND_AI_API_KEY no arquivo .env"
echo "   2. Reinicie o servidor se necessário"
echo "   3. Teste os endpoints: http://localhost:8000/docs"
echo "   4. Configure integração com Django"
echo ""
echo "📖 Documentação completa: DEPLOY_AGENTE_AGNOSTO.md"

