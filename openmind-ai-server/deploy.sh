#!/bin/bash
# Script de Deploy Automatizado - OpenMind AI Server no SinapUm
# Uso: ./deploy.sh

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do OpenMind AI Server no SinapUm..."

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verificar se estamos no diretório correto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erro: Execute este script do diretório openmind-ai-server/${NC}"
    exit 1
fi

# 2. Verificar Python
echo -e "${YELLOW}📦 Verificando Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Instalando Python3...${NC}"
    apt update
    apt install -y python3 python3-pip python3-venv
fi
python3 --version

# 3. Criar ambiente virtual
echo -e "${YELLOW}🐍 Criando ambiente virtual...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 4. Instalar/Atualizar dependências
echo -e "${YELLOW}📚 Instalando dependências...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configurar .env se não existir
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Criando arquivo .env...${NC}"
    cp ENV_EXAMPLE.txt .env
    echo -e "${GREEN}✅ Arquivo .env criado!${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANTE: Edite o arquivo .env e configure:${NC}"
    echo "   - OPENMIND_AI_API_KEY"
    echo "   - OPENAI_API_KEY (se usar OpenAI)"
    echo ""
    echo "   nano .env"
    exit 1
fi

# 6. Verificar se .env tem as configurações necessárias
if ! grep -q "OPENMIND_AI_API_KEY" .env || grep -q "OPENMIND_AI_API_KEY=your-secret-api-key" .env; then
    echo -e "${RED}❌ Configure OPENMIND_AI_API_KEY no arquivo .env${NC}"
    echo "   nano .env"
    exit 1
fi

# 7. Criar diretório de logs
echo -e "${YELLOW}📝 Criando diretório de logs...${NC}"
mkdir -p /var/log/openmind-ai
chmod 755 /var/log/openmind-ai

# 8. Testar importações
echo -e "${YELLOW}🧪 Testando importações...${NC}"
python3 -c "from app.main import app; print('✅ Importações OK')"

# 9. Iniciar servidor
echo -e "${GREEN}✅ Deploy concluído!${NC}"
echo ""
echo -e "${GREEN}🎯 Para iniciar o servidor:${NC}"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo -e "${GREEN}📚 Documentação da API:${NC}"
echo "   http://localhost:8000/docs"
echo ""
echo -e "${GREEN}❤️  Health check:${NC}"
echo "   http://localhost:8000/health"
